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

# Stub stages (README-only, not yet produced) -> honest "pending" entries.
PENDING_MENUS = [
    ("m0", "S0 Intake", "S0", 0, "scoping-ba-intake"),
    ("m5", "Contracts", "S3", 5, "befe-contract"),
    ("m6", "Impl & Reviews", "S4", 6, "backend/frontend implement"),
    ("m9", "QA Validation", "S5", 9, "qa-validation"),
    ("m10", "Release & Prod", "S6", 10, "handoff-to-deploy"),
    ("m11", "Prod Validation", "S7", 11, "smoke-slo-rollback"),
]

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
            return json.load(fh)
    except (OSError, ValueError, UnicodeDecodeError):
        return None


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
    s1b = find_dir(run_dir, "S1b-ba-brief")

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

    # Brief + epics/stories (S1b)
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
                "source_path": "S1b-ba-brief/brief.json",
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
                "source_path": "S1b-ba-brief/INDEX.json",
                "payload": {
                    "count_check": index.get("count_check"),
                    "governance_gaps": index.get("governance_gaps", []),
                    "open_questions": index.get("open_questions", []),
                    "epics": epics_payload, "stories": stories,
                },
            })

    if not sections:
        return None, []
    menu = {"id": "m1", "label": "Epics & Stories", "stage": "S1", "order": 1, "present": True}
    return menu, sections


def build_ux_menu(run_dir):
    s15 = find_dir(run_dir, "S1.5-ux-intake")
    out = read_json(os.path.join(s15, "output.json")) if s15 else None
    if not isinstance(out, dict):
        return None, []
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
        return None, []
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
            except Exception:
                # A diagram that cannot be transcoded is skipped, not fatal.
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
        return None, []
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
# Quality-Gate Board (menu7)
# ---------------------------------------------------------------------------
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
                found[n] = os.path.join(gates_dir, n)
    for root, dirs, files in os.walk(run_dir):
        dirs.sort()
        for n in sorted(files):
            if n in wanted and n not in found:
                found[n] = os.path.join(root, n)
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
            headline = detail.get("headline") or detail.get("summary") or ("verdict " + str(raw))
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
    if not have_any:
        rollup = "PENDING"
        gates = []  # honest empty state: render nothing
    else:
        rollup = {"R": "RED", "A": "AMBER", "G": "GREEN"}.get(worst, "PENDING")
    section = {
        "id": "gate-board", "menu": "m7", "title": "Quality-Gate Board", "kind": "gate_board",
        "source_path": "(T*.json discovered under the run dir / gates/)",
        "payload": {"rollup": rollup, "counts": counts, "gates": gates},
    }
    menu = {"id": "m7", "label": "Quality", "stage": "T1-T12", "order": 7, "present": have_any}
    return menu, [section]


# ---------------------------------------------------------------------------
# Pending stub menus
# ---------------------------------------------------------------------------
def build_pending_menus():
    menus, sections = [], []
    for mid, label, stage, order, skill in PENDING_MENUS:
        menus.append({"id": mid, "label": label, "stage": stage, "order": order, "present": False})
        sections.append({
            "id": mid + "-pending", "menu": mid, "title": label, "kind": "pending",
            "status": "pending", "source_path": stage,
            "payload": {"stage": stage, "expected_skill": skill,
                        "note": "This stage has not run in this pipeline yet; no contract artifact is present."},
        })
    return menus, sections


# ---------------------------------------------------------------------------
# Run header
# ---------------------------------------------------------------------------
def build_run_header(run_dir, all_sections):
    index = read_json(os.path.join(run_dir, "S1b-ba-brief", "INDEX.json")) or \
        read_json(os.path.join(run_dir, "INDEX.json")) or {}
    run_id = os.path.basename(os.path.normpath(run_dir))
    project = None
    brief = read_json(os.path.join(run_dir, "S1b-ba-brief", "brief.json"))
    if isinstance(brief, dict):
        project = (brief.get("initiative") or {}).get("title")
    # audit index from each section that carries an audit_id
    audit_index = []
    seen = set()
    for sec in all_sections:
        aid = sec.get("audit_id") or (sec.get("payload") or {}).get("audit_id")
        if aid and aid not in seen:
            seen.add(aid)
            audit_index.append({
                "stage": sec.get("source_path", "").split("/")[0] or sec.get("menu"),
                "audit_id": aid,
                "skill": (sec.get("payload") or {}).get("skill") or sec.get("kind"),
                "status": sec.get("status") or sec.get("verdict"),
            })
    return {
        "run_id": run_id,
        "project": project or index.get("task_id") or run_id,
        "stage_span": _stage_span(all_sections),
        "produced_by": index.get("produced_by") or "delivery pipeline run",
        "schemaVersion": index.get("schemaVersion") or "1.0",
        "generated_from": os.path.relpath(run_dir) if not os.path.isabs(run_dir) else run_dir,
        "audit_index": audit_index,
        "gate_ledger": GATE_LEDGER,
    }


def _stage_span(sections):
    stages = []
    for prefix, label in [("S1a", "S1a"), ("S1.5", "S1.5"), ("S2-", "S2"), ("S2.5", "S2.5")]:
        if any(s.get("source_path", "").startswith(prefix) for s in sections):
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

    for builder in (build_epics_menu, build_ux_menu, build_design_menu, build_plan_review_menu):
        menu, secs = builder(run_dir)
        if menu:
            menus.append(menu)
            sections.extend(secs)

    gmenu, gsecs = build_gate_board_menu(run_dir)
    menus.append(gmenu)
    sections.extend(gsecs)

    pmenus, psecs = build_pending_menus()
    menus.extend(pmenus)
    sections.extend(psecs)

    run = build_run_header(run_dir, sections)

    pack = {"run": run, "menus": menus, "sections": sections}
    # Sanitize every string value to bare host text before baking.
    pack = sanitize(pack)
    return pack


def build(run_dir, out_path):
    try:
        with open(TEMPLATE, "r", encoding="utf-8") as fh:
            template = fh.read()
    except OSError as exc:
        raise SystemExit("error: cannot read template %s: %s" % (TEMPLATE, exc))

    pack = assemble(run_dir)
    html = inject_pack(template, pack)
    check_offline(html)  # fail closed before writing

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
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
