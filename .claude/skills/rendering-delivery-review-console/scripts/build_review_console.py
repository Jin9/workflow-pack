#!/usr/bin/env python3
"""build_review_console.py — assemble one offline, byte-deterministic
delivery-review.html "Delivery Review Console" from a pipeline run directory.

The left-nav menus are pipeline stages (Epics&Stories, UX Brief, Design&ADRs,
Plan Review, ...). It supersedes the per-stage viewers. Diagrams are embedded as
offline inline SVG (via the sibling drawio_to_svg transcoder) plus a path chip.
The 12 test gates roll into a Quality-Gate Board (R/A/G).

Design contract (see references/console-rendering-spec.md):
  - OFFLINE: the written HTML contains none of http(s)://, src=, @import,
    @font-face, url(, <link, <img, <script src. Data-borne URLs are sanitized to
    bare host text. The transcoder SVG is re-asserted offline-clean before baking.
  - DETERMINISTIC: no clock, no randomness, stable key ordering. Same RUN_DIR ->
    byte-identical HTML on re-run.
  - GRACEFUL PARTIAL: a missing stage/file/field never throws; the section is
    omitted or rendered as a muted "pending" card.

Stdlib only. Public CLI:
    python3 build_review_console.py RUN_DIR [-o OUT.html]
"""

import argparse
import json
import os
import re
import sys

# Import the offline .drawio -> inline <svg> transcoder (sibling script).
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import drawio_to_svg  # noqa: E402

TEMPLATE = os.path.join(os.path.dirname(_HERE), "templates", "delivery-review.template.html")
SKILL_DIR = os.path.dirname(_HERE)
RENDERER_SKILL = "rendering-delivery-review-console"
RENDERER_VERSION = "1.2.0"
PACK_SCHEMA_VERSION = "1"
CONSOLE_MARKER = "<title>Delivery Review Console</title>"

# Every file consumed during assembly — the output-collision guard refuses to
# write over any of them (the write would destroy an authoritative input).
READ_FILES = set()


class _Malformed:
    """Falsy sentinel: the file EXISTS but is not readable JSON — distinct from absent."""
    def __bool__(self):
        return False


MALFORMED = _Malformed()

# Tokens that must NEVER appear in the written HTML (hard offline bar).
FORBIDDEN = (
    "http://", "https://", "src=", "@import", "@font-face",
    "url(", "<link", "<img", "<script src",
)

# The 12 T-gate evidence files, in board order, with display metadata.
# verdict_map ENCODES the three vocabularies (do NOT hardcode PASS/FAIL):
#   T10 pass|conditional|fail -> G|A|R ; T12 promote|hold|rollback -> G|A|R ;
#   all others PASS|FAIL|ERROR -> G|R|R.
STD_MAP = {"PASS": "G", "FAIL": "R", "ERROR": "R"}
GATES = [
    ("T1", "backend-unit-tests.json", "Backend unit tests", "auto", STD_MAP),
    ("T2", "frontend-unit-tests.json", "Frontend unit tests", "auto", STD_MAP),
    ("T3", "sast-gate.json", "SAST gate", "auto+exc", STD_MAP),
    ("T4", "accessibility-tests.json", "Accessibility tests", "auto", STD_MAP),
    ("T5", "contract-tests.json", "Contract tests", "auto", STD_MAP),
    ("T6", "integration-tests.json", "Integration tests", "auto", STD_MAP),
    ("T7", "appsec-scan.json", "AppSec scan", "auto+exc", STD_MAP),
    ("T8", "e2e-tests.json", "End-to-end tests", "auto", STD_MAP),
    ("T9", "perf-load-test.json", "Performance / load test", "auto", STD_MAP),
    ("T10", "adversarial-pentest.json", "Adversarial pentest",
     "human (L3)", {"PASS": "G", "CONDITIONAL": "A", "FAIL": "R"}),
    ("T11", "smoke-tests.json", "Smoke tests", "auto", STD_MAP),
    ("T12", "canary-analysis.json", "Canary analysis",
     "auto+exc", {"PROMOTE": "G", "HOLD": "A", "ROLLBACK": "R"}),
]

# Bare producer skill name per gate evidence file (audit provenance labels).
GATE_SKILLS = {
    "backend-unit-tests.json": "executing-backend-unit-tests",
    "frontend-unit-tests.json": "executing-frontend-unit-tests",
    "sast-gate.json": "running-sast-security-gate",
    "accessibility-tests.json": "running-accessibility-tests",
    "contract-tests.json": "contract-testing-pact",
    "integration-tests.json": "executing-integration-tests",
    "appsec-scan.json": "scanning-appsec-pipeline-gate",
    "e2e-tests.json": "authoring-e2e-test-suite",
    "perf-load-test.json": "running-performance-load-test",
    "adversarial-pentest.json": "validating-banking-implementation",
    "smoke-tests.json": "running-smoke-tests",
    "canary-analysis.json": "analyzing-canary-rollout",
}

# Authoritative audit provenance sources: (stage label, artifact relpath, bare producer
# skill). audit_ids are COPIED VERBATIM from these producer-stamped artifacts — the
# renderer never generates one, and an artifact id is not an events.jsonl attempt id.
STAGE_AUDIT_SOURCES = [
    ("S0-intake", "S0-intake/run-plan.json", "scoping-ba-intake"),
    ("S1a-ba-discovery", "S1a-ba-discovery/discovery.json", "researching-ba-problem-space"),
    ("S1b-breakdown", "S1b-breakdown/INDEX.json", "breaking-down-ba-scope"),
    ("S1c-brief", "S1c-brief/INDEX.json", "elaborating-user-stories"),
    ("S1b-ba-brief", "S1b-ba-brief/INDEX.json", "eliciting-banking-brief"),  # pre-2026-07-28 runs
    ("S1.5-ux-intake", "S1.5-ux-intake/output.json", "generate-ux-pack"),
    ("S2-tl-design", "S2-tl-design/output.json", "designing-tech-lead-handoff"),
    ("S2.5-plan-review", "S2.5-plan-review/plan-review.json", "red-teaming-implementation-plan"),
    ("S3-contracts", "S3-contracts/befe-contracts.json", "befe-contract-design"),
    ("S4a-backend", "S4a-backend/backend-artifacts.json", "implement-backend-feature"),
    ("S4a-backend/review", "S4a-backend/review/backend-review.json", "review-backend-code"),
    ("S4b-frontend", "S4b-frontend/frontend-artifacts.json", "implement-frontend-feature"),
    ("S4b-frontend/review", "S4b-frontend/review/frontend-review.json", "review-frontend-code"),
    ("S4c-qa-test-design", "S4c-qa-test-design/qa-plan.json", "planning-banking-tests"),
    ("S5-qa-validation", "S5-qa-validation/qa-evidence.json", "executing-qa-test-suite"),
    ("S6-deploy", "S6-deploy/handoff-receipt.json", "handoff-to-deploy"),
    ("S7-prod-validation", "S7-prod-validation/smoke-slo.json", "validating-production-slo"),
]

# Stub stages now have first-class builders below (build_intake_menu, build_contracts_menu,
# build_impl_menu, build_qa_plan_menu, build_qa_validate_menu, build_release_menu,
# build_prod_menu); each falls back to an honest "pending" menu via _pending_menu() when its
# artifact is absent, so the full S0..S7 shape always renders.

# L3 sync-named gate ledger (from output-contract-and-review-design.md s6).
GATE_LEDGER = [
    {"stage": "S2", "gate": "sync NAMED (L3)", "owner": "Tech Lead + governance"},
    {"stage": "S2.5", "gate": "red-team gate (HITL)", "owner": "Tech Lead"},
    {"stage": "S4c", "gate": "sync conditional-go (L3)", "owner": "QA-squad lead"},
    {"stage": "T10", "gate": "human (L3)", "owner": "security"},
    {"stage": "S5", "gate": "sync (L3)", "owner": "QA-squad lead"},
    {"stage": "S6", "gate": "sync NAMED (L3) - IRREVERSIBLE", "owner": "Release Manager"},
    {"stage": "S7", "gate": "sync (L3)", "owner": "On-call / Release Mgr"},
]


# ---------------------------------------------------------------------------
# Offline sanitizer
# ---------------------------------------------------------------------------
_SCHEME_RE = re.compile(r"https?://", re.IGNORECASE)


def bare_host(s):
    """Strip the http(s):// scheme from any URL inside a string, leaving the
    bare host text (the workspace web-citation rule). Idempotent."""
    if not isinstance(s, str):
        return s
    return _SCHEME_RE.sub("", s)


def sanitize(value):
    """Recursively sanitize all string values so no scheme survives into the
    baked data. Keys are left as-is (they are never URLs). Order preserved."""
    if isinstance(value, str):
        return bare_host(value)
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items()}
    return value


# ---------------------------------------------------------------------------
# IO helpers (graceful — never throw on a missing/garbled file)
# ---------------------------------------------------------------------------
def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            READ_FILES.add(os.path.realpath(path))
            return json.load(fh)
    except OSError:
        return None  # absent / unreadable at the OS level
    except (ValueError, UnicodeDecodeError):
        return MALFORMED  # present but not valid JSON — render honestly as malformed


def find_first(run_dir, *names):
    """Return the first existing path among names (relative to run_dir)."""
    for n in names:
        p = os.path.join(run_dir, n)
        if os.path.isfile(p):
            return p
    return None


def find_dir(run_dir, *names):
    for n in names:
        p = os.path.join(run_dir, n)
        if os.path.isdir(p):
            return p
    return None


# ---------------------------------------------------------------------------
# Per-stage section builders. Each returns (menu_dict_or_None, [section, ...]).
# All are guarded: a missing file yields no sections (the menu is omitted).
# ---------------------------------------------------------------------------
def build_epics_menu(run_dir):
    """S1a discovery + S1b brief/INDEX/EPIC/STORY -> menu1 Epics & Stories."""
    sections = []
    s1a = find_dir(run_dir, "S1a-ba-discovery")
    # BA leg v2 splits the old S1b into a breakdown pack and an elaborated brief;
    # both names are accepted so a pre-2026-07-28 run still renders.
    s1bd = find_dir(run_dir, "S1b-breakdown")
    s1b = find_dir(run_dir, "S1c-brief", "S1b-ba-brief")

    # Discovery (S1a)
    if s1a:
        disc = read_json(os.path.join(s1a, "discovery.json"))
        if isinstance(disc, dict):
            payload = {
                "skill": "researching-ba-problem-space",
                "problem_framing": disc.get("problem_framing"),
                "opportunities": disc.get("opportunities", []),
                "assumptions": disc.get("assumptions", []),
                "regulatory_regimes": disc.get("regulatory_regimes", []),
                "recommendation": disc.get("recommendation"),
                "audit_id": disc.get("audit_id"),
            }
            sections.append({
                "id": "s1a-discovery", "menu": "m1", "title": "Discovery",
                "kind": "discovery", "status": disc.get("recommendation"),
                "audit_id": disc.get("audit_id"),
                "source_path": "S1a-ba-discovery/discovery.json", "payload": payload,
            })

    # Breakdown (S1b) — the agreed shape the three amigos reviewed
    if s1bd:
        bidx = read_json(os.path.join(s1bd, "INDEX.json"))
        if isinstance(bidx, dict):
            rules = read_json(os.path.join(s1bd, bidx.get("rules_file") or "RULES.json")) or {}
            domain = read_json(os.path.join(s1bd, bidx.get("domain_file") or "DOMAIN.json")) or {}
            epic_files = []
            for e in bidx.get("epics", []) or []:
                obj = read_json(os.path.join(s1bd, e.get("file") or ""))
                if isinstance(obj, dict):
                    epic_files.append({
                        "id": obj.get("id"), "title": obj.get("title"),
                        "business_value": obj.get("business_value"),
                        "decoupling": obj.get("decoupling"),
                    })
            sections.append({
                "id": "s1b-breakdown", "menu": "m1", "title": "Breakdown",
                "kind": "breakdown", "status": bidx.get("state"),
                "audit_id": bidx.get("audit_id"),
                "source_path": "S1b-breakdown/INDEX.json",
                "payload": {
                    "skill": "breaking-down-ba-scope",
                    "scope_kind": bidx.get("scope_kind"),
                    "legal_status": bidx.get("legal_status"),
                    "blocks_elaboration": bidx.get("blocks_elaboration"),
                    "count_check": bidx.get("count_check"),
                    "epics": epic_files,
                    "rules": (rules.get("rules") or []),
                    "entities": (domain.get("entities") or []),
                    "glossary": (domain.get("glossary") or []),
                    "flows": bidx.get("flows", []),
                    "open_questions": bidx.get("open_questions", []),
                    "governance_gaps": bidx.get("governance_gaps", []),
                },
            })

    # Brief + epics/stories (S1c; pre-v2 runs put both in S1b-ba-brief)
    if s1b:
        index = read_json(os.path.join(s1b, "INDEX.json"))
        brief = read_json(os.path.join(s1b, "brief.json"))

        if isinstance(brief, dict):
            init = brief.get("initiative", {}) or {}
            cm = brief.get("ba_compliance_checklist", {}) or {}
            counts = {
                "epics": len(brief.get("epics", []) or []),
                "stories": len(brief.get("stories", []) or []),
                "governance_gaps": len(brief.get("governance_gaps", []) or []),
                "regulatory_dependencies": len(brief.get("regulatory_dependencies", []) or []),
                "pii_inventory": len(brief.get("pii_inventory", []) or []),
                "open_questions": len(brief.get("open_questions", []) or []),
                "assumptions_made": len(brief.get("assumptions_made", []) or []),
                "glossary": len(brief.get("glossary", []) or []),
            }
            sections.append({
                "id": "s1b-brief", "menu": "m1", "title": "Brief",
                "kind": "brief", "status": (brief.get("frontmatter") or {}).get("status"),
                "tier": (brief.get("frontmatter") or {}).get("workload_tier"),
                "source_path": "brief.json (legacy run)",
                "payload": {
                    "title": init.get("title"),
                    "summary": init.get("summary"),
                    "scope_kind": brief.get("scope_kind"),
                    "status": (brief.get("frontmatter") or {}).get("status"),
                    "ba_confidence": (brief.get("frontmatter") or {}).get("ba_confidence"),
                    "tier": (brief.get("frontmatter") or {}).get("workload_tier"),
                    "blocks_tl_handoff": brief.get("blocks_tl_handoff"),
                    "epic_ids": init.get("epic_ids", []),
                    "counts": counts,
                    "regulatory": [r.get("regulator") for r in brief.get("regulatory_dependencies", []) or [] if isinstance(r, dict)],
                    "pii_fields": [p.get("field") for p in brief.get("pii_inventory", []) or [] if isinstance(p, dict)],
                    "compliance": cm,
                },
            })

        # The epic accordion + story reader is sourced from the INDEX ref-chain,
        # which uses the canonical STORY-* ids and per-epic folders.
        if isinstance(index, dict):
            epics_payload = []
            stories = {}
            for ep in index.get("epics", []) or []:
                epic_full = read_json(os.path.join(s1b, ep.get("file", ""))) if ep.get("file") else None
                if not isinstance(epic_full, dict):
                    epic_full = {}
                epics_payload.append({
                    "id": ep.get("id"),
                    "title": ep.get("title") or epic_full.get("title"),
                    "story_ids": ep.get("story_ids", []),
                    "problem_statement": epic_full.get("problem_statement"),
                    "why_now": epic_full.get("why_now"),
                    "hypothesis": epic_full.get("hypothesis"),
                    "success_criteria": epic_full.get("success_criteria", []),
                    "scope": epic_full.get("scope", {}),
                    "stakeholders": epic_full.get("stakeholders", []),
                    "inferred_tier": epic_full.get("inferred_tier"),
                    "legal_status": epic_full.get("legal_status"),
                })
            for sf in index.get("story_files", []) or []:
                full = read_json(os.path.join(s1b, sf.get("file", ""))) if sf.get("file") else None
                if isinstance(full, dict):
                    rec = dict(full)
                    rec.setdefault("id", sf.get("id"))
                    rec.setdefault("epic_id", sf.get("epic_id"))
                    rec["file"] = sf.get("file")
                    stories[sf.get("id")] = rec
                else:
                    stories[sf.get("id")] = {
                        "id": sf.get("id"), "epic_id": sf.get("epic_id"),
                        "title": sf.get("title"), "priority": sf.get("priority"),
                        "_missing": True,
                    }
            sections.append({
                "id": "s1b-epics", "menu": "m1", "title": "Epics & Stories",
                "kind": "epics",
                "source_path": os.path.relpath(os.path.join(s1b, "INDEX.json"), run_dir),
                "payload": {
                    "count_check": index.get("count_check"),
                    "rule_coverage": index.get("rule_coverage"),
                    "hidden_requirements_sweep": index.get("hidden_requirements_sweep"),
                    "governance_gaps": index.get("governance_gaps", []),
                    "open_questions": index.get("open_questions", []),
                    "epics": epics_payload, "stories": stories,
                },
            })

    if not sections:
        status = "pending"
        if (s1b and read_json(os.path.join(s1b, "INDEX.json")) is MALFORMED) or \
                (s1a and read_json(os.path.join(s1a, "discovery.json")) is MALFORMED):
            status = "unreadable-or-malformed"
        return _pending_menu("m1", "Epics & Stories", "S1", 1,
                             "elaborating-user-stories", "S1c-brief", status)
    menu = {"id": "m1", "label": "Epics & Stories", "stage": "S1", "order": 1, "present": True}
    return menu, sections


def build_ux_menu(run_dir):
    s15 = find_dir(run_dir, "S1.5-ux-intake")
    out = read_json(os.path.join(s15, "output.json")) if s15 else None
    if not isinstance(out, dict):
        return _pending_menu("m2", "UX Brief", "S1.5", 2, "generate-ux-pack", "S1.5-ux-intake",
                             "unreadable-or-malformed" if out is MALFORMED else "pending")
    path_refs = sorted(
        v for k, v in out.items()
        if (k.endswith("_path") or k.endswith("_dir")) and isinstance(v, str)
    )
    payload = {
        "output_type": out.get("output_type"),
        "pack_dir": out.get("pack_dir"),
        "maturity_level": out.get("maturity_level"),
        "status": out.get("status"),
        "path_refs": path_refs,
        "p1_findings": out.get("p1_findings", []),
        "p2_findings": out.get("p2_findings", []),
        "ba_stories_without_ux_coverage": out.get("ba_stories_without_ux_coverage", []),
        "ux_routes_without_ba_story": out.get("ux_routes_without_ba_story", []),
        "audit_id": out.get("audit_id"),
    }
    section = {
        "id": "s15-ux", "menu": "m2", "title": "UX Brief", "kind": "ux_pack",
        "status": out.get("status"), "audit_id": out.get("audit_id"),
        "source_path": "S1.5-ux-intake/output.json", "payload": payload,
    }
    menu = {"id": "m2", "label": "UX Brief", "stage": "S1.5", "order": 2, "present": True}
    return menu, [section]


def build_design_menu(run_dir):
    s2 = find_dir(run_dir, "S2-tl-design")
    out = read_json(os.path.join(s2, "output.json")) if s2 else None
    if not isinstance(out, dict):
        return _pending_menu("m3", "Design & ADRs", "S2", 3, "designing-tech-lead-handoff",
                             "S2-tl-design",
                             "unreadable-or-malformed" if out is MALFORMED else "pending")
    sections = []
    # api_contracts -> dedicated endpoint table
    api = out.get("api_contracts") or {}
    if api.get("contracts"):
        sections.append({
            "id": "s2-api", "menu": "m3", "title": "API contracts", "kind": "api_contracts",
            "source_path": "S2-tl-design/output.json",
            "payload": {"contracts": api.get("contracts", [])},
        })
    # design groups (collapsible)
    sections.append({
        "id": "s2-design", "menu": "m3", "title": "Design", "kind": "design",
        "tier": (out.get("processing_metadata") or {}).get("tier"),
        "audit_id": out.get("audit_id"),
        "source_path": "S2-tl-design/output.json",
        "payload": {
            "component_map": out.get("component_map"),
            "event_catalog": out.get("event_catalog"),
            "adrs": out.get("adrs"),
            "l4_specs": out.get("l4_specs"),
            "coverage_gaps": out.get("coverage_gaps"),
            "architecture_smells": out.get("architecture_smells"),
            "open_questions": out.get("open_questions"),
            "audit_id": out.get("audit_id"),
        },
    })
    # diagrams -> inline SVG (the ONE trusted-markup exception)
    diagrams_dir = find_dir(s2, "diagrams") if s2 else None
    if diagrams_dir:
        for fname in sorted(os.listdir(diagrams_dir)):
            if not fname.endswith(".drawio"):
                continue
            dpath = os.path.join(diagrams_dir, fname)
            try:
                svg = drawio_to_svg.transcode(dpath)
            except Exception as exc:
                # A failed transcode is a VISIBLE diagnostic, never a silent skip.
                sections.append({
                    "id": "s2-diagram-error-" + re.sub(r"[^a-z0-9]+", "-", fname.lower()),
                    "menu": "m3", "title": "Diagram (transcode failed) - " + fname,
                    "kind": "pending", "status": "transcode-failed",
                    "source_path": os.path.join("S2-tl-design/diagrams", fname),
                    "payload": {"skill": "designing-tech-lead-handoff",
                                "error": str(exc)[:300]},
                })
                continue
            assert_svg_offline(svg, fname)  # fail the build if it is not clean
            caption = fname[:-len(".drawio")].replace("-", " ").replace("_", " ")
            sections.append({
                "id": "s2-diagram-" + re.sub(r"[^a-z0-9]+", "-", fname.lower()),
                "menu": "m3", "title": "Diagram · " + caption, "kind": "diagram_svg",
                "source_path": os.path.join("S2-tl-design/diagrams", fname),
                "payload": {
                    "svg": svg, "caption": caption,
                    "path": os.path.join("S2-tl-design/diagrams", fname),
                },
            })
    menu = {"id": "m3", "label": "Design & ADRs", "stage": "S2", "order": 3, "present": True}
    return menu, sections


def build_plan_review_menu(run_dir):
    s25 = find_dir(run_dir, "S2.5-plan-review")
    pr = read_json(os.path.join(s25, "plan-review.json")) if s25 else None
    if not isinstance(pr, dict):
        return _pending_menu("m4", "Plan Review", "S2.5", 4, "red-teaming-implementation-plan",
                             "S2.5-plan-review",
                             "unreadable-or-malformed" if pr is MALFORMED else "pending")
    section = {
        "id": "s25-review", "menu": "m4", "title": "Plan Review", "kind": "plan_review",
        "verdict": pr.get("verdict"), "audit_id": pr.get("audit_id"),
        "source_path": "S2.5-plan-review/plan-review.json",
        "payload": {
            "verdict": pr.get("verdict"), "steelman": pr.get("steelman"),
            "findings": pr.get("findings", []), "bias_checks": pr.get("bias_checks", []),
            "confidence": pr.get("confidence"), "audit_id": pr.get("audit_id"),
        },
    }
    menu = {"id": "m4", "label": "Plan Review", "stage": "S2.5", "order": 4, "present": True}
    return menu, [section]


# ---------------------------------------------------------------------------
# Downstream stage builders (S0 + S3..S7). Each returns a PRESENT menu+sections
# when its artifact exists, else an honest "pending" menu+stub. Wired into
# assemble() so one console renders the full S0..S7 run, not just S1..S2.5.
# ---------------------------------------------------------------------------
def _pending_menu(mid, label, stage, order, skill, src, status="pending"):
    menu = {"id": mid, "label": label, "stage": stage, "order": order, "present": False}
    sec = {
        "id": mid + "-pending", "menu": mid, "title": label, "kind": "pending",
        "status": status, "source_path": src,
        "payload": {"stage": stage, "expected_skill": skill,
                    "note": "This stage has not run in this pipeline yet; no contract artifact is present."},
    }
    return menu, [sec]


def build_intake_menu(run_dir):
    """S0 scoping-ba-intake -> menu0 Intake (scope sheet / run plan)."""
    d = find_dir(run_dir, "S0-intake")
    out = read_json(os.path.join(d, "run-plan.json")) if d else None
    if not isinstance(out, dict):
        return _pending_menu("m0", "S0 Intake", "S0", 0, "scoping-ba-intake", "S0-intake")
    sec = {
        "id": "s0-intake", "menu": "m0", "title": "Scope sheet / run plan", "kind": "scope_sheet",
        "audit_id": out.get("audit_id"), "source_path": "S0-intake/run-plan.json",
        "payload": {
            "normalized_request": out.get("normalized_request"),
            "run_plan": out.get("run_plan"),
            "scope_sheet": out.get("scope_sheet") or {},
            "audit_id": out.get("audit_id"),
        },
    }
    return {"id": "m0", "label": "S0 Intake", "stage": "S0", "order": 0, "present": True}, [sec]


def build_contracts_menu(run_dir):
    """S3 befe-contract-design -> menu5 Contracts (BE/FE contract design)."""
    d = find_dir(run_dir, "S3-contracts")
    out = read_json(os.path.join(d, "befe-contracts.json")) if d else None
    if not isinstance(out, dict):
        return _pending_menu("m5", "Contracts", "S3", 5, "befe-contract-design", "S3-contracts")
    files = []
    for sub in ("be", "fe"):
        sd = os.path.join(d, sub)
        if os.path.isdir(sd):
            for n in sorted(os.listdir(sd)):
                if n.endswith(".md"):
                    files.append("S3-contracts/%s/%s" % (sub, n))
    sec = {
        "id": "s3-contracts", "menu": "m5", "title": "BE/FE contracts", "kind": "befe_contracts",
        "audit_id": out.get("audit_id"), "source_path": "S3-contracts/befe-contracts.json",
        "payload": {
            "contract_spec": out.get("contract_spec"), "client_types": out.get("client_types"),
            "mock_plan": out.get("mock_plan"), "list_conventions": out.get("list_conventions"),
            "bff": out.get("bff"), "fe_state_binding": out.get("fe_state_binding"),
            "files": files, "audit_id": out.get("audit_id"),
        },
    }
    return {"id": "m5", "label": "Contracts", "stage": "S3", "order": 5, "present": True}, [sec]


def build_impl_menu(run_dir):
    """S4a/S4b implement + their reviews -> menu6 Impl & Reviews (up to 4 sections)."""
    ba = find_dir(run_dir, "S4a-backend")
    fb = find_dir(run_dir, "S4b-frontend")
    be = read_json(os.path.join(ba, "backend-artifacts.json")) if ba else None
    ber = read_json(os.path.join(ba, "review", "backend-review.json")) if ba else None
    fe = read_json(os.path.join(fb, "frontend-artifacts.json")) if fb else None
    fer = read_json(os.path.join(fb, "review", "frontend-review.json")) if fb else None
    sections = []
    if isinstance(be, dict):
        sections.append({
            "id": "s4a-impl", "menu": "m6", "title": "Backend implementation (S4a)", "kind": "impl_artifacts",
            "source_path": "S4a-backend/backend-artifacts.json",
            "payload": {"leg": "backend", "files_generated": be.get("files_generated", []),
                        "tests_generated": be.get("tests_generated", []),
                        "idempotency_strategy": be.get("idempotency_strategy"),
                        "audit_events_emitted": be.get("audit_events_emitted", []),
                        "compensating_actions": be.get("compensating_actions", [])}})
    if isinstance(ber, dict):
        sections.append({
            "id": "s4a-review", "menu": "m6", "title": "Backend review (S4a-r)", "kind": "code_review",
            "verdict": ber.get("verdict"), "source_path": "S4a-backend/review/backend-review.json",
            "payload": {"verdict": ber.get("verdict"), "loop_back_target_stage": ber.get("loop_back_target_stage"),
                        "findings": ber.get("findings", []), "claims_verified": ber.get("claims_verified", []),
                        "claims_unverified": ber.get("claims_unverified", []), "audit_metadata": ber.get("audit_metadata", {})}})
    if isinstance(fe, dict):
        sections.append({
            "id": "s4b-impl", "menu": "m6", "title": "Frontend implementation (S4b)", "kind": "impl_artifacts",
            "source_path": "S4b-frontend/frontend-artifacts.json",
            "payload": {"leg": "frontend", "files_generated": fe.get("files_generated", []),
                        "tests_generated": fe.get("tests_generated", []),
                        "a11y_compliance": fe.get("a11y_compliance", {}), "security_review": fe.get("security_review", {}),
                        "bundle_impact_estimate_kb": fe.get("bundle_impact_estimate_kb"),
                        "audit_events_emitted": fe.get("audit_events_emitted", []),
                        "compensating_actions": fe.get("compensating_actions", [])}})
    if isinstance(fer, dict):
        sections.append({
            "id": "s4b-review", "menu": "m6", "title": "Frontend review (S4b-r)", "kind": "code_review",
            "verdict": fer.get("verdict"), "source_path": "S4b-frontend/review/frontend-review.json",
            "payload": {"verdict": fer.get("verdict"), "loop_back_target_stage": fer.get("loop_back_target_stage"),
                        "findings": fer.get("findings", []), "claims_verified": fer.get("claims_verified", []),
                        "claims_unverified": fer.get("claims_unverified", []),
                        "a11y_verdict": fer.get("a11y_verdict", {}), "security_verdict": fer.get("security_verdict", {}),
                        "audit_metadata": fer.get("audit_metadata", {})}})
    if not sections:
        return _pending_menu("m6", "Impl & Reviews", "S4", 6, "implement-backend/frontend-feature", "S4a-backend")
    return {"id": "m6", "label": "Impl & Reviews", "stage": "S4", "order": 6, "present": True}, sections


def build_qa_plan_menu(run_dir):
    """S4c planning-banking-tests -> menu6c QA Test Design."""
    d = find_dir(run_dir, "S4c-qa-test-design")
    out = read_json(os.path.join(d, "qa-plan.json")) if d else None
    if not isinstance(out, dict):
        return _pending_menu("m6c", "QA Test Design", "S4c", 7, "planning-banking-tests", "S4c-qa-test-design")
    fm = out.get("frontmatter") or {}
    sec = {
        "id": "s4c-qa-plan", "menu": "m6c", "title": "QA test plan", "kind": "qa_plan",
        "status": fm.get("status"), "tier": fm.get("workload_tier"),
        "source_path": "S4c-qa-test-design/qa-plan.json",
        "payload": {"output_type": out.get("output_type"), "status": fm.get("status"),
                    "test_plan_id": fm.get("test_plan_id"), "strategy": out.get("strategy", {}),
                    "test_cases": out.get("test_cases", []), "smoke_subset": out.get("smoke_subset", {}),
                    "signoff_criteria": out.get("signoff_criteria", {})},
    }
    return {"id": "m6c", "label": "QA Test Design", "stage": "S4c", "order": 7, "present": True}, [sec]


def build_qa_validate_menu(run_dir):
    """S5 executing-qa-test-suite -> menu9 QA Validation."""
    d = find_dir(run_dir, "S5-qa-validation")
    out = read_json(os.path.join(d, "qa-evidence.json")) if d else None
    if not isinstance(out, dict):
        return _pending_menu("m9", "QA Validation", "S5", 8, "executing-qa-test-suite", "S5-qa-validation")
    sec = {
        "id": "s5-qa", "menu": "m9", "title": "QA validation evidence", "kind": "qa_evidence",
        "verdict": out.get("verdict"), "audit_id": out.get("audit_id"),
        "source_path": "S5-qa-validation/qa-evidence.json",
        "payload": {"verdict": out.get("verdict"), "totals": out.get("totals", {}),
                    "coverage_measured": out.get("coverage_measured"), "flaky": out.get("flaky", []),
                    "defects": out.get("defects", []), "audit_id": out.get("audit_id")},
    }
    return {"id": "m9", "label": "QA Validation", "stage": "S5", "order": 8, "present": True}, [sec]


def build_release_menu(run_dir):
    """S6 handoff-to-deploy -> menu10 Release Handoff."""
    d = find_dir(run_dir, "S6-deploy")
    out = read_json(os.path.join(d, "handoff-receipt.json")) if d else None
    if not isinstance(out, dict):
        return _pending_menu("m10", "Release Handoff", "S6", 9, "handoff-to-deploy", "S6-deploy")
    sec = {
        "id": "s6-release", "menu": "m10", "title": "Release handoff receipt", "kind": "handoff_receipt",
        "status": out.get("status"), "audit_id": out.get("audit_id"),
        "source_path": "S6-deploy/handoff-receipt.json",
        "payload": {"receipt_id": out.get("receipt_id"), "status": out.get("status"),
                    "release_ref": out.get("release_ref"), "approver": out.get("approver") or {},
                    "audit_id": out.get("audit_id")},
    }
    return {"id": "m10", "label": "Release Handoff", "stage": "S6", "order": 9, "present": True}, [sec]


def build_prod_menu(run_dir):
    """S7 validating-production-slo -> menu11 Prod Validation."""
    d = find_dir(run_dir, "S7-prod-validation")
    out = read_json(os.path.join(d, "smoke-slo.json")) if d else None
    if not isinstance(out, dict):
        return _pending_menu("m11", "Prod Validation", "S7", 10, "validating-production-slo", "S7-prod-validation")
    sec = {
        "id": "s7-prod", "menu": "m11", "title": "Production SLO validation", "kind": "slo_validation",
        "verdict": out.get("verdict"), "audit_id": out.get("audit_id"),
        "source_path": "S7-prod-validation/smoke-slo.json",
        "payload": {"verdict": out.get("verdict"), "grade": out.get("grade"),
                    "per_slo": out.get("per_slo", []), "window": out.get("window"),
                    "audit_id": out.get("audit_id")},
    }
    return {"id": "m11", "label": "Prod Validation", "stage": "S7", "order": 10, "present": True}, [sec]


# ---------------------------------------------------------------------------
# Quality-Gate Board (menu7)
# ---------------------------------------------------------------------------
def _gate_headline(d, raw):
    """Synthesize a board headline from the gate's own (schema-clean) fields —
    the gate evidence schemas are additionalProperties:false, so there is no
    free-text headline field to read."""
    if d.get("headline"):
        return d["headline"]
    if d.get("summary"):
        return d["summary"]
    t = d.get("totals")
    if isinstance(t, dict) and "executed" in t:
        cov = d.get("coverage_measured")
        cs = (", cov %d%%" % round(cov * 100)) if isinstance(cov, (int, float)) else ""
        return "%s/%s passed%s" % (t.get("passed"), t.get("executed"), cs)
    if isinstance(d.get("scenarios"), list):
        return "%d scenario(s) · verdict %s" % (len(d["scenarios"]), raw)
    if isinstance(d.get("probes"), list):
        return "%d probe(s) · verdict %s" % (len(d["probes"]), raw)
    if isinstance(d.get("per_metric"), list):
        return "%d metric(s) · verdict %s" % (len(d["per_metric"]), raw)
    if isinstance(d.get("metrics"), dict):
        return "p95 %s · err %s · verdict %s" % (d["metrics"].get("p95"), d["metrics"].get("error_rate"), raw)
    if "pacts" in d:
        return "can_i_deploy=%s · verdict %s" % (d.get("can_i_deploy"), raw)
    if "secrets" in d:
        return "%s secret(s) · verdict %s" % (d.get("secrets"), raw)
    if "persona_findings" in d:
        return "%d persona finding(s) · verdict %s" % (len(d.get("persona_findings") or []), raw)
    return "verdict " + str(raw)
def _discover_gate_files(run_dir):
    """Find every T-gate evidence file by filename anywhere under run_dir, plus a
    top-level gates/ dir. Returns {filename: abspath} (first hit wins,
    deterministic by sorted walk order)."""
    wanted = {g[1] for g in GATES}
    found = {}
    gates_dir = find_dir(run_dir, "gates")
    if gates_dir:
        for n in sorted(os.listdir(gates_dir)):
            if n in wanted and n not in found:
                found[n] = os.path.join(gates_dir, n)  # canonical gates/<file> is authoritative
    # Legacy fallback: recursive filename discovery, ONLY for gates with no canonical
    # file. More than one candidate is a run-integrity problem — fail closed with an
    # ambiguity diagnostic instead of silently picking the first sorted path.
    candidates = {}
    for root, dirs, files in os.walk(run_dir):
        dirs.sort()
        for n in sorted(files):
            if n in wanted and n not in found:
                candidates.setdefault(n, []).append(os.path.join(root, n))
    for n, paths in sorted(candidates.items()):
        if len(paths) > 1:
            raise SystemExit(
                "error: ambiguous gate evidence for %s (no canonical gates/%s): %s"
                % (n, n, ", ".join(os.path.relpath(p, run_dir) for p in paths)))
        found[n] = paths[0]
    return found


def build_gate_board_menu(run_dir):
    files = _discover_gate_files(run_dir)
    gates = []
    counts = {"green": 0, "amber": 0, "red": 0}
    worst = None  # track worst-of: R > A > G
    for gate_id, fname, name, level, vmap in GATES:
        path = files.get(fname)
        detail = read_json(path) if path else None
        if isinstance(detail, dict):
            raw = detail.get("verdict")
            status = vmap.get(str(raw).upper(), "R") if raw is not None else "P"
            headline = _gate_headline(detail, raw)
            rel = os.path.relpath(path, run_dir)
        else:
            raw, status, headline, rel = None, "P", "no evidence yet", None
        if status == "G":
            counts["green"] += 1
        elif status == "A":
            counts["amber"] += 1
        elif status == "R":
            counts["red"] += 1
        # worst-of rollup, only over gates that HAVE evidence
        if status in ("G", "A", "R"):
            order = {"G": 0, "A": 1, "R": 2}
            if worst is None or order[status] > order[worst]:
                worst = status
        gates.append({
            "id": gate_id, "name": name, "level": level, "gate_policy": "verdict_map",
            "status": status, "headline": headline,
            "verdict": raw, "audit_id": (detail or {}).get("audit_id"),
            "source": rel, "detail": detail,
        })
    have_any = bool(files)
    evidence_count = counts["green"] + counts["amber"] + counts["red"]
    missing_gates = [g["id"] for g in gates if g["status"] == "P"]
    worst_observed = {"R": "RED", "A": "AMBER", "G": "GREEN"}.get(worst, "PENDING")
    if not have_any:
        rollup = "PENDING"
        gates = []  # honest empty state: render nothing
    elif evidence_count < len(GATES):
        # Partial evidence NEVER rolls up to an unqualified colour.
        rollup = "INCOMPLETE"
    else:
        rollup = worst_observed
    section = {
        "id": "gate-board", "menu": "m7", "title": "Quality-Gate Board", "kind": "gate_board",
        "source_path": "(gates/<file> canonical; recursive discovery is a legacy fallback)",
        "payload": {"rollup": rollup, "counts": counts, "gates": gates,
                    "expected_count": len(GATES), "evidence_count": evidence_count,
                    "missing_gates": missing_gates,
                    "evidence_complete": evidence_count == len(GATES),
                    "worst_observed": worst_observed},
    }
    menu = {"id": "m7", "label": "Quality", "stage": "T1-T12", "order": 11, "present": have_any}
    return menu, [section]


# ---------------------------------------------------------------------------
# Run header
# ---------------------------------------------------------------------------
def build_run_header(run_dir, all_sections):
    index = read_json(os.path.join(run_dir, "S1c-brief", "INDEX.json")) or \
        read_json(os.path.join(run_dir, "S1b-ba-brief", "INDEX.json")) or \
        read_json(os.path.join(run_dir, "INDEX.json")) or {}
    run_id = os.path.basename(os.path.normpath(run_dir))
    project = None
    brief = read_json(os.path.join(run_dir, "S1b-ba-brief", "brief.json"))
    if isinstance(brief, dict):
        project = (brief.get("initiative") or {}).get("title")
    if not project:
        # v2 has no brief.json; the epic titles carry the initiative instead.
        epics = index.get("epics") or []
        if epics:
            project = " · ".join(e.get("title", "") for e in epics if e.get("title"))[:120] or None
    # Audit index from AUTHORITATIVE artifacts first (audit_ids copied verbatim —
    # producer-stamped provenance; the renderer never generates or validates one).
    audit_index = []
    seen = set()
    for stage_label, rel, skill_name in STAGE_AUDIT_SOURCES:
        art = read_json(os.path.join(run_dir, rel))
        if isinstance(art, dict):
            aid = art.get("audit_id")
            if aid and aid not in seen:
                seen.add(aid)
                entry = {"stage": stage_label, "audit_id": aid, "skill": skill_name}
                status = art.get("status") or art.get("verdict")
                if status:
                    entry["status"] = status
                audit_index.append(entry)
    for sec in all_sections:
        if sec.get("kind") != "gate_board":
            continue
        for g in (sec.get("payload") or {}).get("gates", []):
            aid = g.get("audit_id")
            if aid and aid not in seen:
                seen.add(aid)
                audit_index.append({"stage": g.get("id"), "audit_id": aid,
                                    "skill": GATE_SKILLS.get((g.get("source") or "").split("/")[-1],
                                                             g.get("id"))})
    # Fallback: any remaining section-envelope audit_id (kept for unknown layouts).
    for sec in all_sections:
        aid = sec.get("audit_id") or (sec.get("payload") or {}).get("audit_id")
        if aid and aid not in seen:
            seen.add(aid)
            audit_index.append({
                "stage": sec.get("source_path", "").split("/")[0] or sec.get("menu"),
                "audit_id": aid,
                "skill": (sec.get("payload") or {}).get("skill") or sec.get("kind"),
            })
    return {
        "run_id": run_id,
        "project": project or index.get("task_id") or run_id,
        "stage_span": _stage_span(all_sections),
        # produced_by / schemaVersion come ONLY from the S1b INDEX (BA provenance).
        "produced_by": index.get("produced_by") or "delivery pipeline run",
        "schemaVersion": index.get("schemaVersion") or "1.0",
        # Portable: the run id, never a workstation-absolute path.
        "generated_from": run_id,
        "renderer": {"renderer_skill": RENDERER_SKILL, "renderer_version": RENDERER_VERSION,
                     "pack_schema_version": PACK_SCHEMA_VERSION},
        "audit_index": audit_index,
        "gate_ledger": GATE_LEDGER,
    }


def _stage_span(sections):
    order = [
        ("S0-intake", "S0"), ("S1a", "S1"), ("S1.5", "S1.5"), ("S2-", "S2"), ("S2.5", "S2.5"),
        ("S3-", "S3"), ("S4a", "S4"), ("S4b", "S4"), ("S4c", "S4c"),
        ("S5-", "S5"), ("S6-", "S6"), ("S7-", "S7"),
    ]
    stages = []
    for prefix, label in order:
        if label not in stages and any(s.get("source_path", "").startswith(prefix) for s in sections):
            stages.append(label)
    if not stages:
        return "—"
    return stages[0] + ("–" + stages[-1] if len(stages) > 1 else "")


# ---------------------------------------------------------------------------
# Offline self-checks
# ---------------------------------------------------------------------------
def assert_svg_offline(svg, label):
    low = svg.lower()
    hits = [t for t in FORBIDDEN if t in low]
    if hits:
        raise SystemExit(
            "error: transcoded SVG for %s contains forbidden token(s): %s — "
            "refusing to ship." % (label, ", ".join(hits))
        )


def check_offline(html):
    low = html.lower()
    hits = [t for t in FORBIDDEN if t in low]
    if hits:
        raise SystemExit(
            "error: assembled console contains forbidden external reference "
            "token(s): %s — refusing to write." % ", ".join(hits)
        )


# ---------------------------------------------------------------------------
# Injection
# ---------------------------------------------------------------------------
INJECT_RE = re.compile(
    r"(/\* INJECT.*?\*/\s*window\.PACK\s*=\s*)\{.*?\};",
    re.DOTALL,
)


def inject_pack(template_text, pack):
    # ensure_ascii=False keeps Thai/long text readable; sort_keys=True for stable
    # ordering on dicts (lists already preserve read order). Determinism: no clock.
    blob = json.dumps(pack, ensure_ascii=False, sort_keys=True, indent=None)
    # neutralise any sequence that could break the surrounding <script> / comment
    blob = blob.replace("</", "<\\/")
    if not INJECT_RE.search(template_text):
        raise SystemExit("error: template is missing the /* INJECT ... */ window.PACK marker")
    return INJECT_RE.sub(lambda m: m.group(1) + blob + ";", template_text, count=1)


# ---------------------------------------------------------------------------
# Top-level assembly
# ---------------------------------------------------------------------------
def assemble(run_dir):
    run_dir = os.path.normpath(run_dir)
    menus, sections = [], []

    # Full S0..S7 spine, in pipeline order. Each builder yields a present menu when
    # its artifact exists, else an honest pending stub — so the whole shape stays visible.
    builders = (
        build_intake_menu,        # S0
        build_epics_menu,         # S1 (a+b)
        build_ux_menu,            # S1.5
        build_design_menu,        # S2
        build_plan_review_menu,   # S2.5
        build_contracts_menu,     # S3
        build_impl_menu,          # S4a/S4b + reviews
        build_qa_plan_menu,       # S4c
        build_qa_validate_menu,   # S5
        build_release_menu,       # S6
        build_prod_menu,          # S7
    )
    for builder in builders:
        menu, secs = builder(run_dir)
        if menu:
            menus.append(menu)
            sections.extend(secs)

    gmenu, gsecs = build_gate_board_menu(run_dir)  # T1..T12 (menu order 11)
    menus.append(gmenu)
    sections.extend(gsecs)

    run = build_run_header(run_dir, sections)

    pack = {"run": run, "menus": menus, "sections": sections}
    # Sanitize every string value to bare host text before baking.
    pack = sanitize(pack)
    return pack


def _guard_output_path(out_path, run_dir):
    """The output must be a .html file, outside the skill dir, distinct from every
    consumed artifact, and only replace the default console or a file that carries
    the console marker. Violations exit 2 — the write would destroy an input."""
    real_out = os.path.realpath(out_path)
    if not out_path.endswith(".html"):
        raise SystemExit("error: output must be a .html path: %s" % out_path)
    if real_out == os.path.realpath(TEMPLATE) or             real_out.startswith(os.path.realpath(SKILL_DIR) + os.sep):
        raise SystemExit("error: output path lies inside the skill directory: %s" % out_path)
    if real_out in READ_FILES:
        raise SystemExit("error: output path resolves to a consumed run artifact: %s" % out_path)
    if os.path.isfile(out_path) and os.path.basename(out_path) != "delivery-review.html":
        try:
            with open(out_path, "r", encoding="utf-8", errors="replace") as fh:
                head = fh.read(4096)
        except OSError:
            head = ""
        if CONSOLE_MARKER not in head:
            raise SystemExit(
                "error: refusing to overwrite an existing non-console file: %s" % out_path)
    _ = run_dir  # reserved for future run-scoped rules


def build(run_dir, out_path):
    try:
        with open(TEMPLATE, "r", encoding="utf-8") as fh:
            template = fh.read()
    except OSError as exc:
        raise SystemExit("error: cannot read template %s: %s" % (TEMPLATE, exc))

    pack = assemble(run_dir)         # populates READ_FILES
    _guard_output_path(out_path, run_dir)
    html = inject_pack(template, pack)
    check_offline(html)  # fail closed before writing

    tmp = out_path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(html)
        os.replace(tmp, out_path)  # atomic: a failed build never truncates a console
    except OSError:
        if os.path.isfile(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise
    return pack


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Assemble an offline, deterministic delivery-review.html console from a run dir."
    )
    ap.add_argument("run_dir", help="path to the pipeline run directory")
    ap.add_argument("-o", "--output", help="output HTML path (default: RUN_DIR/delivery-review.html)")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.run_dir):
        sys.stderr.write("error: run dir not found: %s\n" % args.run_dir)
        return 2

    out = args.output or os.path.join(args.run_dir, "delivery-review.html")
    pack = build(args.run_dir, out)

    present = sum(1 for m in pack["menus"] if m.get("present"))
    board = next((s for s in pack["sections"] if s.get("kind") == "gate_board"), {})
    rollup = (board.get("payload") or {}).get("rollup", "?")
    sys.stdout.write(
        "wrote %s (%d bytes) · %d/%d menus present · gate rollup %s\n"
        % (out, os.path.getsize(out), present, len(pack["menus"]), rollup)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
