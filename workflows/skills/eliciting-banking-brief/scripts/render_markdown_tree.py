#!/usr/bin/env python3
"""
render_markdown_tree.py — Deterministic Markdown renderer for eliciting-banking-brief v1.2.2.

Reads an `eliciting-banking-brief` output.json (canonical artifact), validates it
against `schemas/output.json` if `jsonschema` is available, and emits the
structured Markdown directory tree defined in
`references/markdown-rendering-spec.md`.

v1.2.0 adds `09-hidden-requirements.md` (conditional on Step 9.5 sweep findings)
and runtime enforcement of FM-15 sweep invariants.

v1.2.1 (surfacing polish, no behavior change) adds three derived surfaces:
  - README `Why this is blocked` leads with a DoR-failure bullet when
    `ba_compliance_checklist.definition_of_ready_met` is false.
  - README emits `## Minimum unblock set` between why-blocked and provenance
    when `blocks_tl_handoff` is true; computed as the union of blocking gov
    gaps, P1 OQs, and structural-blocker gov-gap types; grouped by resolver.
  - `02-open-questions.md` opens with `## At a glance` (counts, top frames,
    most-impacted stories, top-5 recommended-first) right under the H1.

v1.2.2 (enforcement: catches the misses found in v1.2.0 and v1.2.1 holdout runs):
  - `validate_idempotency_replay()` — FM-16: every story with
    `banking_grade_concerns.idempotency.status == "applies"` MUST carry
    at least one AC with `scenario_type == "banking_grade_idempotency"`.
    Mirrors the schema if/then constraint added to Story definition.
  - `validate_frame4_subtopics()` — FM-17: when Frame 4 is in `frames_applied`
    AND the input activates regulatory triggers (PII / payment / named
    jurisdiction / consumer-facing), the brief MUST cover the required
    sub-topics per `references/hidden-requirements-frames.md`. Coverage
    detected by keyword matching against OQ text + assumption text.

v1.3.0 (refactor): `FRAME4_SUBTOPIC_RULES` lifted from inline constant to
`references/frame-rule-data.json` (loaded at import time). Behavior
preserved byte-identically; markdown table drift caught by F-7
(`scripts/check_frame_rule_data_drift.py`).

v1.3.1 (cap-exception protocol): `validate_cap_exceptions()` — warning-grade
check that when `findings_per_frame[F]` exceeds the soft cap for frame F
(per `references/hidden-requirements-frames.md`),
`processing_metadata.hidden_requirements_sweep.cap_exceptions[str(F)]`
declares the overshoot with `{cap, observed_count, reason (minLength 8)}`.
Most common driver: FM-17 mandatory sub-topic coverage on Frame 4 with
multiple active triggers (v6 elicitation emitted 22 vs cap 10). Warning-grade
in v1.3.1; promoted to must-pass in v1.3.2 (assertion F-8 in
`tests/assertions/frame-coverage-completeness.md`).

v1.4.0 (bilingual emission): `localize_data()` deep-copies the input data and
substitutes per-object `translations[<lang>]` field values when emitting non-
English trees. `render_tree()` now reads
`processing_metadata.bilingual_output` (default `["en"]`) and emits one tree
per language at `output-{idem8}/<LANG_UPPER>/`. The canonical `output.json`
lives once at the tree root (`output-{idem8}/output.json`). Sub-agent contract
for translations: see `references/bilingual-emission.md`.

v1.4.1 (UI-string localization): renderer-emitted UI strings (headings,
labels, table headers like "Open Questions", "Why it matters", "At a glance")
are now localized via `references/ui-strings.json` consulted through the
module-level `t(key)` helper. `_render_language_tree()` sets the module-level
`_CURRENT_LANG` before each per-language render pass. Missing translations
fall back to the English source key (so adding a new emission site doesn't
break TH rendering — it just shows the EN string until the JSON is updated).

Pure function. No `now()` calls. No LLM calls. Byte-identical on re-run.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKILL_VERSION = "1.4.1"
CREATED_BY = f"eliciting-banking-brief-v{SKILL_VERSION}"

# FM-17: Frame 4 sub-topic coverage requirements (v1.2.2+; data lifted v1.3.0+).
# Source-of-truth is references/frame-rule-data.json. Maps each activation
# trigger to the sub-topics that MUST get >=1 OQ/assumption when that trigger
# fires.
#
# Coverage rule: for each ACTIVATED trigger, each listed sub-topic must have
# at least one OQ or assumption whose `question` + `why_matters` (or
# `assumption` + `why_made`) contain at least ONE of the coverage keywords
# (case-insensitive substring match). Missing sub-topics -> FM-17 finding.


def find_frame_rule_data_path(start: Path) -> Optional[Path]:
    """Walk up from script location to find references/frame-rule-data.json.
    Mirrors find_schema_path()."""
    here = start.resolve()
    for parent in [here] + list(here.parents):
        cand = parent / "references" / "frame-rule-data.json"
        if cand.exists():
            return cand
    return None


_FRAME4_KNOWN_TRIGGERS = {
    "pii_collection",
    "jurisdiction_thailand",
    "payment_processing",
    "audit_logging",
    "consumer_facing",
}

# Per-frame soft cap on Step 9.5 findings (v1.3.1+). Values match the canonical
# declarations in references/hidden-requirements-frames.md (per-frame "Cap:"
# lines at 32, 62, 92, 122, 246, 279, 313, 349, 383, 411). The cap is a soft
# guideline for "rank by blast radius" discretionary findings; mandatory FM-17
# sub-topic coverage on Frame 4 may legitimately overshoot, in which case the
# brief MUST declare cap_exceptions[str(F)] per v1.3.1 assertion F-8.
FRAME_CAPS = {1: 5, 2: 5, 3: 5, 4: 10, 5: 5, 6: 7, 7: 5, 8: 5, 9: 5, 10: 5}


# --- v1.4.1+: UI-string localization infrastructure ---------------------------
# Renderer-emitted UI strings (section headings, labels, table headers) are
# localized via references/ui-strings.json. The module-level `_CURRENT_LANG`
# variable is set by `_render_language_tree()` before each per-language render
# pass; the `t(key)` helper looks up the active language and falls back to the
# English source key when a translation is missing (graceful degradation).

_CURRENT_LANG = "en"


def find_ui_strings_path(start: Path) -> Optional[Path]:
    """Walk up from script location to find references/ui-strings.json.
    Mirrors find_frame_rule_data_path()."""
    here = start.resolve()
    for parent in [here] + list(here.parents):
        cand = parent / "references" / "ui-strings.json"
        if cand.exists():
            return cand
    return None


def _load_ui_strings() -> Dict[str, Dict[str, str]]:
    """Load `references/ui-strings.json` once at import time. Returns the
    `strings` sub-object: `{lang: {english_key: translated_value}}`. Returns
    an empty dict if the file is missing so the renderer degrades to English-
    only emission rather than failing hard (UI localization is best-effort)."""
    path = find_ui_strings_path(Path(__file__).parent)
    if path is None:
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            doc = json.load(fh)
        return doc.get("strings") or {}
    except (OSError, json.JSONDecodeError):
        return {}


UI_STRINGS: Dict[str, Dict[str, str]] = _load_ui_strings()


def t(key: str) -> str:
    """v1.4.1+. Translate a renderer-emitted UI string into the active language
    (`_CURRENT_LANG`). Falls back to the English source `key` when:
    - the active language has no `strings/<lang>` block in ui-strings.json, OR
    - the key is missing from that language's block.

    Active language is set by `_render_language_tree()` at the start of each
    per-language render pass. For monolingual emission (default ["en"]) the
    helper effectively returns the key unchanged."""
    if _CURRENT_LANG == "en":
        return key
    lang_block = UI_STRINGS.get(_CURRENT_LANG) or {}
    return lang_block.get(key, key)


def _load_frame4_subtopic_rules() -> Dict[str, List[Tuple[str, List[str]]]]:
    """Load FM-17 Frame 4 sub-topic rules from references/frame-rule-data.json.
    Converts JSON object-shape entries to the (sub_topic_id, keywords) tuple
    shape consumed by validate_frame4_subtopics(). Fails fast at import time
    if the file is missing, malformed, or has an unknown trigger key. v1.3.0+."""
    path = find_frame_rule_data_path(Path(__file__).parent)
    if path is None:
        raise RuntimeError(
            "references/frame-rule-data.json not found; "
            "v1.3.0+ lifted FRAME4_SUBTOPIC_RULES to external data."
        )
    with path.open("r", encoding="utf-8") as fh:
        doc = json.load(fh)
    out: Dict[str, List[Tuple[str, List[str]]]] = {}
    for trig, entries in (doc.get("triggers") or {}).items():
        if trig not in _FRAME4_KNOWN_TRIGGERS:
            raise RuntimeError(
                f"frame-rule-data.json: unknown trigger '{trig}'. "
                f"v1.3-pending triggers must not appear under 'triggers' until "
                f"detection logic lands."
            )
        out[trig] = [
            (e["sub_topic_id"], list(e["coverage_keywords"])) for e in entries
        ]
    return out


FRAME4_SUBTOPIC_RULES: Dict[str, List[Tuple[str, List[str]]]] = _load_frame4_subtopic_rules()

# Trigger-detection rules: map trigger ID to a function deciding whether the
# trigger fires for a given brief. Pure-data inspections only.
FRAME4_TRIGGER_DETECTORS: Dict[str, str] = {
    # Sentinel keys checked against PII inventory, governance_gaps, glossary,
    # processing_metadata.language_inventory, etc. Each rule lives in
    # _detect_frame4_triggers(); the dict here is informational for spec docs.
    "pii_collection": "pii_inventory has ≥1 direct/regulatory entry",
    "jurisdiction_thailand": "language_inventory mentions Thai, OR glossary/OQ text mentions PDPA",
    "payment_processing": "any story mentions payment/PSP/mock provider/checkout",
    "audit_logging": "any banking_grade_concerns.audit_events.status == applies",
    "consumer_facing": "any epic has stakeholders with type=affected named 'customer' OR scope_kind != purely internal",
}

# Fixed-order resolver groups for v1.2.1 Minimum-unblock-set grouping.
# An item with a multi-resolver string (e.g. "PM + Legal") is assigned to the
# FIRST matching group in this list — PM wins over Legal, Legal wins over DPO,
# etc. Matching uses word boundaries so "po" (in PM keywords) does NOT match
# inside "dpo" and "ops" does NOT match inside other words. Items with no
# matching keyword land in "other".
RESOLVER_GROUPS: List[Tuple[str, List[str]]] = [
    ("PM", ["pm", "product manager", "product owner"]),
    ("Legal", ["legal", "lawyer", "counsel"]),
    ("DPO", ["dpo", "privacy"]),
    ("Finance", ["finance", "finops", "accounting", "tax", "treasury"]),
    ("Compliance", ["compliance", "regulator"]),
    ("Ops", ["operations", "ops", "logistics", "support", "customer support", "merchant", "fulfillment"]),
    ("InfoSec", ["infosec", "security", "appsec", "secops"]),
]
RESOLVER_GROUP_ORDER = [g for g, _ in RESOLVER_GROUPS] + ["other"]

# Structural-blocker gov-gap types — included in Minimum-unblock-set even when
# their individual `blocks_tl_handoff` is false (per spec §3.1 item 6).
STRUCTURAL_BLOCKER_TYPES = {
    "pii_inventory_missing",
    "regulatory_citation_unresolved",
    "retention_policy_unstated",
}

FRAME_NAMES = {
    1: "Scale & capacity",
    2: "Time & timing",
    3: "Money & economics",
    4: "Regulatory & legal",
    5: "Operational & organizational",
    6: "Failure & edge cases",
    7: "Integration & dependencies",
    8: "Localization & culture",
    9: "Lifecycle",
    10: "Customer experience",
}

FAILURE_OUTPUT_TYPES = {
    "needs_clarification",
    "preprocessing_failure",
    "pii_echo_blocked",
    "schema_validation_failure",
    "meta_response",
}

SUCCESS_OUTPUT_TYPES = {"brief", "blocked_partial_brief", "partial_brief"}

BANKING_GRADE_ROWS = [
    "pii_fields",
    "audit_events",
    "idempotency",
    "reversibility",
    "authn_authz",
    "regulatory",
    "tipping_off",
]

DOR_KEYS = [
    "format_clear",
    "happy_path_present",
    "error_path_present",
    "banking_grade_evaluated",
    "priority_set",
    "dependencies_identified",
    "sizing_done",
    "no_blocking_ambiguities",
]

COMPLIANCE_KEYS = [
    "all_pii_identified",
    "audit_trail_stated",
    "regulatory_refs_included",
    "no_irreversible_without_compensation",
    "all_stories_pass_invest",
    "all_acs_in_gherkin",
    "definition_of_ready_met",
    "moscow_complete",
    "open_questions_explicit",
    "dependencies_mapped",
]

STOPWORDS = {
    "a", "an", "the", "and", "or", "with", "for", "of", "to",
    "in", "on", "at", "by", "from",
}

SEVERITY_ORDER = {"P1": 0, "P2": 1, "P3": 2}

# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------


def slugify(title: str, max_len: int = 60) -> str:
    """Per spec §2: lowercase, alphanumeric+hyphen only, drop stopwords, max 60."""
    text = (title or "").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    tokens = [t for t in text.split("-") if t and t not in STOPWORDS]
    slug = "-".join(tokens)[:max_len].rstrip("-")
    return slug or "untitled"


def story_trailing_int(story_id: str) -> str:
    m = re.search(r"-(\d+)$", story_id or "")
    return m.group(1) if m else "0"


def story_filename(story: Dict[str, Any], collision_guard: bool = False) -> str:
    n = story_trailing_int(story.get("id", ""))
    slug = slugify(story.get("title", ""))
    if collision_guard:
        slug = f"{slug}-{n}"[:60].rstrip("-")
    return f"STORY-{n}-{slug}.md"


# ---------------------------------------------------------------------------
# YAML emission (manual, byte-deterministic)
# ---------------------------------------------------------------------------

_YAML_QUOTE_TRIGGERS = re.compile(r"[:#\[\]{}&*!|>='\"%@`]|^[-?]| #")
_YAML_RESERVED = {"true", "false", "null", "yes", "no", "on", "off", "~"}


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    if s == "":
        return '""'
    if s.lower() in _YAML_RESERVED:
        return f'"{s}"'
    if _YAML_QUOTE_TRIGGERS.search(s) or s.startswith(" ") or s.endswith(" "):
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return s


def _yaml_inline_list(values: List[Any]) -> str:
    if not values:
        return "[]"
    return "[" + ", ".join(_yaml_scalar(v) for v in values) + "]"


def emit_frontmatter(fields: List[Tuple[str, Any]]) -> str:
    """Emit YAML frontmatter from an ordered list of (key, value) pairs.

    Values can be: scalar, list (flow style), or a list-of-(key, value) for
    nested mapping (block style, one level deep).
    """
    lines = ["---"]
    for key, value in fields:
        if value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, list) and value and isinstance(value[0], tuple):
            lines.append(f"{key}:")
            for sub_key, sub_value in value:
                lines.append(f"  {sub_key}: {_yaml_scalar(sub_value)}")
        elif isinstance(value, list):
            lines.append(f"{key}: {_yaml_inline_list(value)}")
        else:
            lines.append(f"{key}: {_yaml_scalar(value)}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Common frontmatter blocks
# ---------------------------------------------------------------------------


def routing_fields(data: Dict[str, Any], artifact_type: str) -> List[Tuple[str, Any]]:
    fm = data.get("frontmatter", {}) or {}
    return [
        ("artifact_type", artifact_type),
        ("brief_id", fm.get("id")),
        ("idempotency_key", fm.get("idempotency_key")),
        ("workload_tier", fm.get("workload_tier")),
        ("output_type", data.get("output_type")),
        ("scope_kind", data.get("scope_kind")),
        ("status", fm.get("status")),
        ("blocks_tl_handoff", bool(data.get("blocks_tl_handoff", False))),
        ("created_at", fm.get("created_at")),
        ("created_by", CREATED_BY),
        ("source_type", fm.get("source_type")),
        ("downstream_consumer", [("stage", "2-tl-design"), ("role", "tech-lead")]),
    ]


def minimal_fields(data: Dict[str, Any], artifact_type: str) -> List[Tuple[str, Any]]:
    fm = data.get("frontmatter", {}) or {}
    return [
        ("artifact_type", artifact_type),
        ("brief_id", fm.get("id")),
        ("idempotency_key", fm.get("idempotency_key")),
    ]


# ---------------------------------------------------------------------------
# Counting helpers
# ---------------------------------------------------------------------------


def count_by_severity(items: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"P1": 0, "P2": 0, "P3": 0}
    for item in items or []:
        sev = item.get("severity")
        if sev in counts:
            counts[sev] += 1
    return counts


def p1_governance_gaps(gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [g for g in (gaps or []) if g.get("severity") == "P1"]


def gap_anchor(gap_type: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", (gap_type or "").lower()).strip("-")


# ---------------------------------------------------------------------------
# Story / epic helpers
# ---------------------------------------------------------------------------


def _resolver_group(resolver: Optional[str]) -> str:
    """Map a free-text resolver string to one of the 8 fixed groups.

    Strings mentioning multiple roles route to the FIRST matching group in
    `RESOLVER_GROUPS` order (PM > Legal > DPO > Finance > Compliance > Ops >
    InfoSec). Strings with no recognized keyword land in `other`.

    Matching uses word boundaries: keyword "po" will NOT match inside "dpo";
    "ops" will NOT match inside an unrelated word. This avoids the
    substring-collision bug where `pii_inventory_missing` (resolver "DPO + Legal")
    was routed to PM because "po" appeared inside "dpo".
    """
    if not resolver:
        return "other"
    lower = resolver.lower()
    for group, keywords in RESOLVER_GROUPS:
        for kw in keywords:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, lower):
                return group
    return "other"


def _gap_resolver(gap: Dict[str, Any]) -> str:
    """Best-effort resolver extraction from a governance gap row."""
    for key in ("resolver", "required_action_owner", "suggested_resolver", "promisor", "owner"):
        v = gap.get(key)
        if isinstance(v, str) and v.strip():
            return v
    # Heuristic: governance gap types imply default owners.
    type_default = {
        "legal_absent_on_regulatory": "Legal",
        "pii_inventory_missing": "DPO + Legal",
        "regulatory_citation_unresolved": "Legal + Compliance",
        "retention_policy_unstated": "Legal + DPO",
        "tipping_off_violation": "Legal",
        "dual_approval_named_owner_missing": "Compliance",
        "compensating_action_missing": "Ops",
    }
    return type_default.get(gap.get("type", ""), "")


def _gap_summary(gap: Dict[str, Any]) -> str:
    """One-sentence summary of a gov-gap for the Minimum-unblock-set line."""
    parts: List[str] = []
    if gap.get("reason"):
        parts.append(gap["reason"])
    elif gap.get("required_action"):
        parts.append(gap["required_action"])
    elif gap.get("evidence"):
        ev = gap["evidence"]
        first = ev[0] if isinstance(ev, list) and ev else ev
        if isinstance(first, str):
            parts.append(first)
    summary = (parts[0] if parts else "").strip()
    # Truncate to ~140 chars for one-line readability
    if len(summary) > 140:
        summary = summary[:137].rstrip() + "…"
    return summary or "(see governance-gaps file)"


def _oq_summary(oq: Dict[str, Any]) -> str:
    q = (oq.get("question") or "").strip().replace("\n", " ")
    if len(q) > 140:
        q = q[:137].rstrip() + "…"
    return q


def _oq_anchor(oq_id: str) -> str:
    """Stable anchor id for a question (lowercase, normalized)."""
    return re.sub(r"[^a-z0-9]+", "-", (oq_id or "").lower()).strip("-")


def minimum_unblock_set(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Compute the v1.2.1 Minimum-unblock-set per spec §3.1 item 6.

    Returns a list of dicts with shape:
      {"kind": "gap"|"oq", "id": str, "summary": str, "severity": str,
       "resolver": str, "resolver_group": str, "link": str, "sort_key": tuple}

    Deterministic ordering: items are returned in spec order (gaps first by
    JSON-array insertion, then OQs by JSON-array insertion). Caller applies
    resolver-group bucketing for rendering.
    """
    items: List[Dict[str, Any]] = []
    seen: set = set()
    for gap in (data.get("governance_gaps") or []):
        gap_id = gap.get("id") or f"gov-gap:{gap.get('type', '')}"
        if gap_id in seen:
            continue
        is_blocking = bool(gap.get("blocks_tl_handoff", False))
        is_structural = gap.get("type") in STRUCTURAL_BLOCKER_TYPES
        if not (is_blocking or is_structural):
            continue
        seen.add(gap_id)
        resolver = _gap_resolver(gap)
        items.append({
            "kind": "gap",
            "id": gap.get("type", gap_id),
            "summary": _gap_summary(gap),
            "severity": gap.get("severity", "—"),
            "resolver": resolver,
            "resolver_group": _resolver_group(resolver),
            "link": f"01-governance-gaps.md#{gap_anchor(gap.get('type', ''))}",
        })
    for oq in (data.get("open_questions") or []):
        if oq.get("severity") != "P1":
            continue
        oq_id = oq.get("id") or ""
        if oq_id in seen:
            continue
        seen.add(oq_id)
        resolver = oq.get("suggested_resolver") or ""
        items.append({
            "kind": "oq",
            "id": oq_id,
            "summary": _oq_summary(oq),
            "severity": "P1",
            "resolver": resolver,
            "resolver_group": _resolver_group(resolver),
            "link": f"02-open-questions.md#{_oq_anchor(oq_id)}",
            "_related_count": len(oq.get("related_story_ids") or []),
        })
    return items


def epic_dir_name(epic_id: str) -> str:
    return epic_id  # epic.id already constrained to ^EPIC-[A-Z0-9-]+$


def stories_for_epic(stories: List[Dict[str, Any]], epic_id: str) -> List[Dict[str, Any]]:
    return [
        s for s in (stories or [])
        if (s.get("id", "").rsplit("-", 1)[0] == epic_id)
        or (s.get("epic_id") == epic_id)
    ]


def banking_grade_applies(story: Dict[str, Any]) -> List[str]:
    bg = story.get("banking_grade_concerns", {}) or {}
    return [k for k in BANKING_GRADE_ROWS if (bg.get(k) or {}).get("status") == "applies"]


def related_oqs(story_id: str, open_questions: List[Dict[str, Any]]) -> List[str]:
    return [
        oq.get("id") for oq in (open_questions or [])
        if story_id in (oq.get("related_story_ids") or []) and oq.get("id")
    ]


def dor_ready(story: Dict[str, Any]) -> bool:
    dor = story.get("dor_checklist", {}) or {}
    return all(bool(dor.get(k)) for k in DOR_KEYS)


def find_story_path_map(data: Dict[str, Any]) -> Dict[str, str]:
    """Map story_id → relative path from output root. Handles slug collisions per spec §2."""
    out: Dict[str, str] = {}
    epics = data.get("epics") or ([data["epic"]] if data.get("epic") else [])
    for epic in epics:
        epic_id = epic.get("id")
        stories = stories_for_epic(data.get("stories", []), epic_id)
        seen_slugs: Dict[str, int] = {}
        # First pass: detect collisions
        slug_counts: Dict[str, int] = {}
        for s in stories:
            slug_counts[slugify(s.get("title", ""))] = slug_counts.get(slugify(s.get("title", "")), 0) + 1
        for s in stories:
            collision = slug_counts.get(slugify(s.get("title", "")), 0) > 1
            fname = story_filename(s, collision_guard=collision)
            out[s["id"]] = f"epics/{epic_dir_name(epic_id)}/stories/{fname}"
    return out


# ---------------------------------------------------------------------------
# File renderers
# ---------------------------------------------------------------------------


def render_readme(data: Dict[str, Any]) -> str:
    fm = data.get("frontmatter", {}) or {}
    output_type = data.get("output_type", "")
    blocks = bool(data.get("blocks_tl_handoff", False))
    epics = data.get("epics") or ([data["epic"]] if data.get("epic") else [])
    stories = data.get("stories", []) or []
    oq_counts = count_by_severity(data.get("open_questions", []))
    gov_gaps = data.get("governance_gaps", []) or []
    pii_count = len(data.get("pii_inventory", []) or [])

    title = ""
    if data.get("initiative", {}).get("title"):
        title = data["initiative"]["title"]
    elif epics:
        title = epics[0].get("title") or fm.get("id", "")
    else:
        title = fm.get("id", "BA Brief")

    if output_type in FAILURE_OUTPUT_TYPES:
        banner = f"{t('Failed')} — see [FAILURE.md](FAILURE.md) (`{output_type}`)"
    elif blocks:
        p1_gaps = p1_governance_gaps(gov_gaps)
        banner = f"{t('Blocked for TL handoff')} — {len(p1_gaps)} P1 governance gap(s) unresolved"
    elif oq_counts["P2"] > 0:
        banner = f"{t('Draft')} — {oq_counts['P2']} P2 open question(s) require BA decision"
    else:
        banner = t("Ready for TL handoff")

    body = [
        emit_frontmatter(routing_fields(data, "ba-brief-index")),
        f"# {t('BA Brief')} — {title}",
        "",
        f"> **{t('Status')}:** {banner}",
        "",
        f"## {t('At a glance')}",
        "",
        f"| {t('Metric')} | {t('Value')} |",
        "|---|---|",
        f"| {t('Workload tier')} | {fm.get('workload_tier', '—')} |",
        f"| {t('Scope kind')} | {data.get('scope_kind', '—')} |",
        f"| {t('Epics')} | {len(epics)} |",
        f"| {t('Stories')} | {len(stories)} |",
        f"| {t('Open questions (P1 / P2 / P3)')} | {oq_counts['P1']} / {oq_counts['P2']} / {oq_counts['P3']} |",
        f"| {t('Governance gaps')} | {len(gov_gaps)} |",
        f"| {t('PII inventory fields')} | {pii_count} |",
        "",
    ]

    if output_type in FAILURE_OUTPUT_TYPES:
        body += [
            f"## {t('Files')}",
            "",
            "- [output.json](output.json) — canonical JSON with `failure_state`",
            "- [FAILURE.md](FAILURE.md) — human-readable failure explanation and recommended next action",
            "",
        ]
    else:
        body += [
            f"## {t('Navigation')}",
            "",
            "- [output.json](output.json) — canonical JSON contract for Stage 2 (TL design)",
            "- [00-BRIEF.md](00-BRIEF.md) — initiative or epic synthesis",
            "- [01-governance-gaps.md](01-governance-gaps.md) — governance gaps; drives `blocks_tl_handoff`",
            "- [02-open-questions.md](02-open-questions.md) — open questions grouped by severity",
            "- [03-assumptions.md](03-assumptions.md) — assumptions made and why",
            "- [04-glossary.md](04-glossary.md) — domain terms",
            "- [05-pii-inventory.md](05-pii-inventory.md) — PII fields and treatment",
            "- [06-regulatory-dependencies.md](06-regulatory-dependencies.md) — regulators and citation status",
            "- [07-processing-metadata.md](07-processing-metadata.md) — tier decisions, parsing, language",
            "- [08-audit-trace.md](08-audit-trace.md) — BA reasoning trace and compliance checklist",
        ]
        if has_hidden_requirements(data):
            body.append("- [09-hidden-requirements.md](09-hidden-requirements.md) — elicitation-gap sweep findings (10 frames)")
        body += [
            "- `epics/` — one directory per epic, containing `EPIC.md` and `stories/STORY-N-*.md`",
            "",
        ]
        for epic in epics:
            eid = epic.get("id", "")
            epic_stories = stories_for_epic(stories, eid)
            body.append(f"  - **{eid}** — [EPIC.md](epics/{eid}/EPIC.md) ({len(epic_stories)} story file(s))")
        body.append("")

        if blocks:
            body += [f"## {t('Why this is blocked')}", ""]
            # v1.2.1: DoR-failure bullet leads when DoR is false.
            dor_met = bool((data.get("ba_compliance_checklist") or {}).get("definition_of_ready_met", True))
            if not dor_met:
                body.append(
                    "- **definition_of_ready_met: false** — see "
                    "[08-audit-trace.md](08-audit-trace.md#ba-compliance-checklist) "
                    "for the per-checklist breakdown"
                )
            for gap in p1_governance_gaps(gov_gaps):
                body.append(
                    f"- **{gap.get('type')}** — see "
                    f"[01-governance-gaps.md#{gap_anchor(gap.get('type', ''))}]"
                    f"(01-governance-gaps.md#{gap_anchor(gap.get('type', ''))})"
                )
            body.append("")

            # v1.2.1: Minimum unblock set section, emitted only when blocks_tl_handoff=true.
            unblock = minimum_unblock_set(data)
            if unblock:
                body += [f"## {t('Minimum unblock set')}", ""]
                body += [
                    "Resolving the items below together flips `blocks_tl_handoff` from `true` to `false`. Grouped by suggested resolver.",
                    "",
                ]
                grouped: Dict[str, List[Dict[str, Any]]] = {g: [] for g in RESOLVER_GROUP_ORDER}
                for item in unblock:
                    grouped.setdefault(item["resolver_group"], []).append(item)
                for group in RESOLVER_GROUP_ORDER:
                    items = grouped.get(group, [])
                    if not items:
                        continue
                    # Within group: gov gaps first (kind="gap"), then OQs (kind="oq"); preserve insertion order.
                    items.sort(key=lambda x: (0 if x["kind"] == "gap" else 1,))
                    body.append(f"### {group}")
                    body.append("")
                    for item in items:
                        resolver_suffix = f" _(resolver: {item['resolver']})_" if item["resolver"] else ""
                        body.append(
                            f"- **{item['id']}** [{item['severity']}] — {item['summary']} "
                            f"→ [{item['link'].split('#', 1)[0]}]({item['link']}){resolver_suffix}"
                        )
                    body.append("")

    body += [
        f"## {t('Provenance')}",
        "",
        f"- {t('Source type')}: `{fm.get('source_type', '—')}`",
        f"- {t('Idempotency key')}: `{fm.get('idempotency_key', '—')}`",
        f"- {t('Created at')}: `{fm.get('created_at', '—')}`",
        f"- {t('Created by')}: `{CREATED_BY}`",
        "",
    ]

    return "\n".join(body)


def render_brief_summary(data: Dict[str, Any]) -> str:
    fm = data.get("frontmatter", {}) or {}
    initiative = data.get("initiative") or {}
    epics = data.get("epics") or ([data["epic"]] if data.get("epic") else [])
    pm = data.get("processing_metadata", {}) or {}

    lines = [emit_frontmatter(routing_fields(data, "ba-brief-summary"))]

    if data.get("scope_kind") == "multi-epic" and initiative:
        lines += [
            f"# {initiative.get('title', fm.get('id', 'BA Brief'))}",
            "",
            initiative.get("summary", "") or "_(no summary)_",
            "",
            f"## {t('Per-Epic Tier Map')}",
            "",
            f"| {t('Epic')} | {t('Workload tier')} | {t('Why')} |",
            "|---|---|---|",
        ]
        for entry in initiative.get("per_epic_tier", []) or []:
            lines.append(
                f"| `{entry.get('epic_id', '')}` | "
                f"{entry.get('tier', '')} | "
                f"{entry.get('justification', '').replace(chr(10), ' ')} |"
            )
        _h_scope = t("What's in scope across all epics")
        lines += ["", f"## {_h_scope}", ""]
        epic_titles = ", ".join(f"`{e.get('id')}` ({e.get('title')})" for e in epics)
        lines.append(f"This initiative decomposes into {len(epics)} epic(s): {epic_titles}.")
        lines.append("")
    elif epics:
        epic = epics[0]
        lines += [
            f"# {epic.get('title', fm.get('id', 'Epic'))}",
            "",
            f"## {t('Problem Statement')}",
            "",
            epic.get("problem_statement", "") or "_(none stated)_",
            "",
            f"## {t('Why Now')}",
            "",
            epic.get("why_now", "") or "_(none stated)_",
            "",
        ]
        if epic.get("hypothesis"):
            lines += [f"## {t('Hypothesis')}", "", epic["hypothesis"], ""]
        sc = epic.get("success_criteria", []) or []
        if sc:
            lines += [
                f"## {t('Success Criteria')}",
                "",
                f"| {t('Metric')} | Baseline | Target | Measurement |",
                "|---|---|---|---|",
            ]
            for c in sc:
                lines.append(
                    f"| {c.get('metric', '')} | {c.get('baseline', '')} | "
                    f"{c.get('target', '')} | {c.get('measurement_method', '')} |"
                )
            lines.append("")

    td = pm.get("tier_decisions", []) or []
    if td:
        lines += [
            f"## {t('Processing — Tier Decisions')}",
            "",
            f"| {t('Epic')} | {t('Workload tier')} | {t('Tier Signals')} |",
            "|---|---|---|",
        ]
        for entry in td:
            signals = "; ".join(entry.get("signals", []) or [])
            lines.append(
                f"| `{entry.get('epic_id', '')}` | "
                f"{entry.get('inferred_tier', '')} | "
                f"{signals} |"
            )
        lines.append("")

    return "\n".join(lines)


def render_epic(data: Dict[str, Any], epic: Dict[str, Any]) -> str:
    fm = data.get("frontmatter", {}) or {}
    eid = epic.get("id", "")
    epic_stories = stories_for_epic(data.get("stories", []), eid)
    inferred = epic.get("inferred_tier")
    manual = epic.get("manual_tier") or fm.get("workload_tier")
    higher = bool(epic.get("inferred_higher_than_manual", False))

    initiative = data.get("initiative") or {}
    per_epic = {e.get("epic_id"): e.get("tier") for e in initiative.get("per_epic_tier", []) or []}
    tier = inferred or per_epic.get(eid) or fm.get("workload_tier")

    fields = [
        ("artifact_type", "ba-epic"),
        ("epic_id", eid),
        ("brief_id", fm.get("id")),
        ("title", epic.get("title", "")),
        ("workload_tier", tier),
        ("inferred_tier", inferred),
        ("manual_tier", manual),
        ("inferred_higher_than_manual", higher),
        ("legal_status", epic.get("legal_status")),
        ("story_count", len(epic_stories)),
        ("story_ids", [s.get("id") for s in epic_stories]),
        ("blocks_tl_handoff", bool(data.get("blocks_tl_handoff", False))),
        ("downstream_consumer", [("stage", "2-tl-design"), ("role", "tech-lead")]),
    ]

    lines = [emit_frontmatter(fields)]
    lines += [
        f"# {t('Epic')}: {epic.get('title', '')}",
        "",
        f"**{t('Workload tier')}**: {tier or '—'} · **Legal status**: {epic.get('legal_status', '—')} · **{t('Stories')}**: {len(epic_stories)}",
        "",
        f"## {t('Problem Statement')}",
        "",
        epic.get("problem_statement", "") or "_(none stated)_",
        "",
        f"## {t('Why Now')}",
        "",
        epic.get("why_now", "") or "_(none stated)_",
        "",
    ]
    if epic.get("hypothesis"):
        lines += [f"## {t('Hypothesis')}", "", epic["hypothesis"], ""]

    sc = epic.get("success_criteria", []) or []
    if sc:
        lines += [
            f"## {t('Success Criteria')}",
            "",
            f"| {t('Metric')} | Baseline | Target | Measurement |",
            "|---|---|---|---|",
        ]
        for c in sc:
            lines.append(
                f"| {c.get('metric', '')} | {c.get('baseline', '')} | "
                f"{c.get('target', '')} | {c.get('measurement_method', '')} |"
            )
        lines.append("")

    scope = epic.get("scope", {}) or {}
    lines += [f"## {t('Scope')}", ""]
    for header_key, key in [("In", "in"), ("Out (explicit)", "out_explicit"), ("Out (deferred)", "out_deferred")]:
        lines.append(f"### {t(header_key)}")
        lines.append("")
        items = scope.get(key, []) or []
        if items:
            for item in items:
                lines.append(f"- {item}")
        else:
            lines.append("_(none)_")
        lines.append("")

    stakeholders = epic.get("stakeholders", []) or []
    if stakeholders:
        lines += [
            f"## {t('Stakeholders')}",
            "",
            f"| Role | Type | {t('Status')} | Decision Authority | Engagement Required For |",
            "|---|---|---|---|---|",
        ]
        for s in stakeholders:
            role = s.get("role", "")
            status = s.get("status", "active")
            row_role = f"**{role}**" if status in ("absent", "mentioned_only") else role
            lines.append(
                f"| {row_role} | {s.get('type', '')} | {status} | "
                f"{s.get('decision_authority', '—')} | "
                f"{s.get('engagement_required_for', '—')} |"
            )
        lines.append("")

    ts = epic.get("tier_signals", []) or []
    if ts:
        lines += [f"## {t('Tier Signals')}", ""]
        for sig in ts:
            quote = (sig.get("evidence_quote") or "").replace("\n", " ")
            lines.append(f"- **{sig.get('signal', '')}** (weight: {sig.get('weight', '—')}) — \"{quote}\"")
        lines.append("")

    return "\n".join(lines)


def render_story(data: Dict[str, Any], story: Dict[str, Any], epic: Dict[str, Any]) -> str:
    fm = data.get("frontmatter", {}) or {}
    sid = story.get("id", "")
    eid = epic.get("id", "")
    sizing = story.get("sizing", {}) or {}
    deps = story.get("dependencies", {}) or {}

    initiative = data.get("initiative") or {}
    per_epic = {e.get("epic_id"): e.get("tier") for e in initiative.get("per_epic_tier", []) or []}
    tier = epic.get("inferred_tier") or per_epic.get(eid) or fm.get("workload_tier")

    fields = [
        ("artifact_type", "ba-story"),
        ("story_id", sid),
        ("epic_id", eid),
        ("brief_id", fm.get("id")),
        ("title", story.get("title", "")),
        ("format", story.get("format", "classic_user_story")),
        ("priority", story.get("priority", "")),
        ("story_points", sizing.get("story_points", "TBD_by_TL") if sizing.get("story_points") is not None else "TBD_by_TL"),
        ("complexity", sizing.get("complexity", "unknown")),
        ("workload_tier", tier),
        ("depends_on", list(deps.get("depends_on", []) or [])),
        ("blocks", list(deps.get("blocks", []) or [])),
        ("banking_grade_applies", banking_grade_applies(story)),
        ("related_open_questions", related_oqs(sid, data.get("open_questions", []))),
        ("dor_ready", dor_ready(story)),
        ("downstream_consumer", [("stage", "2-tl-design"), ("role", "tech-lead")]),
    ]

    lines = [emit_frontmatter(fields)]
    lines += [
        f"# {t('Story')} {sid}: {story.get('title', '')}",
        "",
        f"**{t('Format')}**: {story.get('format', 'classic_user_story')} · "
        f"**{t('Priority')}**: {story.get('priority', '—')} · "
        f"**{t('Sizing')}**: {sizing.get('story_points', 'TBD')} SP ({sizing.get('complexity', '—')})",
        "",
    ]

    card = story.get("card", {}) or {}
    if story.get("format") == "job_story":
        lines += [
            f"> **{t('When')}** {card.get('when', '—')},",
            f"> **{t('I want to')}** {card.get('i_want_to', '—')}",
            f"> **{t('so I can')}** {card.get('so_i_can', '—')}.",
            "",
        ]
    else:
        lines += [
            f"> **{t('As a')}** {card.get('as_a', '—')},",
            f"> **{t('I want')}** {card.get('i_want', '—')}",
            f"> **{t('so that')}** {card.get('so_that', '—')}.",
            "",
        ]

    if story.get("context"):
        lines += [f"## {t('Context')}", "", story["context"], ""]

    lines += [f"## {t('Acceptance Criteria')}", ""]
    for ac in story.get("acceptance_criteria", []) or []:
        scen = ac.get("scenario_name", "")
        stype = ac.get("scenario_type", "")
        lines.append("```gherkin")
        lines.append(f"# [{stype}] {scen}")
        for g in ac.get("given", []) or []:
            lines.append(f"Given {g}")
        when_val = ac.get("when")
        if isinstance(when_val, list):
            for w in when_val:
                lines.append(f"When {w}")
        elif when_val:
            lines.append(f"When {when_val}")
        # NOTE: loop var renamed from `t` to `then_step` to avoid shadowing the
        # module-level t(key) UI-string helper introduced in v1.4.1.
        for then_step in ac.get("then", []) or []:
            lines.append(f"Then {then_step}")
        lines.append("```")
        lines.append("")

    lines += [
        f"## {t('Banking-Grade Concerns')}",
        "",
        "| Concern | Status | Justification |",
        "|---|---|---|",
    ]
    bg = story.get("banking_grade_concerns", {}) or {}
    for row in BANKING_GRADE_ROWS:
        entry = bg.get(row) or {}
        status = entry.get("status", "—")
        just = (entry.get("justification") or "—").replace("\n", " ").replace("|", "\\|")
        lines.append(f"| `{row}` | {status} | {just} |")
    lines.append("")

    depends = deps.get("depends_on", []) or []
    blocks = deps.get("blocks", []) or []
    lines += [
        f"## {t('Dependencies')}",
        "",
        f"**{t('Depends on')}**: {', '.join(f'`{d}`' for d in depends) if depends else '—'} · "
        f"**{t('Blocks')}**: {', '.join(f'`{b}`' for b in blocks) if blocks else '—'}",
        "",
    ]

    dor = story.get("dor_checklist", {}) or {}
    lines += [f"## {t('Definition of Ready')}", ""]
    for key in DOR_KEYS:
        mark = "[x]" if bool(dor.get(key)) else "[ ]"
        lines.append(f"- {mark} {key}")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Cross-cutting renderers (01–08)
# ---------------------------------------------------------------------------


def _sorted_by_severity(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(items or [], key=lambda x: (SEVERITY_ORDER.get(x.get("severity", "P3"), 9),))


def render_governance_gaps(data: Dict[str, Any], path_map: Dict[str, str]) -> str:
    gaps = _sorted_by_severity(data.get("governance_gaps", []) or [])
    lines = [emit_frontmatter(minimal_fields(data, "ba-governance"))]
    lines += [f"# {t('Governance Gaps')}", ""]
    if not gaps:
        lines += [f"_{t('No governance gaps')}._", ""]
        return "\n".join(lines)
    for gap in gaps:
        anchor = gap_anchor(gap.get("type", ""))
        lines.append(f'## <a id="{anchor}"></a>{gap.get("type")} — {gap.get("severity")}')
        lines.append("")
        lines.append(f"**{t('Blocks TL handoff')}**: {bool(gap.get('blocks_tl_handoff', False))}")
        lines.append("")
        evidence = gap.get("evidence", []) or []
        if evidence:
            lines.append(f"**{t('Evidence')}:**")
            lines.append("")
            for ev in evidence:
                lines.append(f"- {ev}")
            lines.append("")
        if gap.get("reason"):
            lines += [f"**{t('Reason')}:** {gap['reason']}", ""]
        if gap.get("required_action"):
            lines += [f"**{t('Required action')}:** {gap['required_action']}", ""]
        if gap.get("resolver"):
            lines += [f"**{t('Resolver')}:** {gap['resolver']}", ""]
        related = gap.get("related_story_ids") or []
        if related:
            lines.append(f"**{t('Affected stories')}:**")
            lines.append("")
            for sid in related:
                p = path_map.get(sid)
                if p:
                    lines.append(f"- [{sid}]({p})")
                else:
                    lines.append(f"- `{sid}`")
            lines.append("")
    return "\n".join(lines)


def _provenance_badge(item: Dict[str, Any]) -> str:
    prov = item.get("provenance")
    frame = item.get("frame")
    if prov == "hidden_frame_sweep" and frame:
        return f" `[frame {frame} · {FRAME_NAMES.get(frame, '?')}]`"
    return ""


def _at_a_glance_block(data: Dict[str, Any]) -> List[str]:
    """v1.2.1: derive the At-a-glance summary lines from open_questions[] + stories[].

    All four lines emit even when zero OQs are present (empty-state-stable).
    Counts and ranks are derived solely from open_questions[] — NOT from
    processing_metadata.hidden_requirements_sweep.findings_per_frame, which
    counts findings broadly (incl. assumptions promoted out of OQs).
    """
    oqs = data.get("open_questions") or []
    counts = {"P1": 0, "P2": 0, "P3": 0}
    frame_counts: Dict[int, int] = {}
    prose_count = 0
    for oq in oqs:
        sev = oq.get("severity")
        if sev in counts:
            counts[sev] += 1
        prov = oq.get("provenance")
        if prov == "hidden_frame_sweep":
            f = oq.get("frame")
            if isinstance(f, int):
                frame_counts[f] = frame_counts.get(f, 0) + 1
        elif prov == "prose_ambiguity":
            prose_count += 1
    total = counts["P1"] + counts["P2"] + counts["P3"]

    # Top 3 frames: descending by count, tiebreak by ascending frame number
    top_frames = sorted(frame_counts.items(), key=lambda x: (-x[1], x[0]))[:3]

    # Top 5 stories by inverse count of OQs mentioning the story
    story_counts: Dict[str, int] = {}
    for oq in oqs:
        for sid in (oq.get("related_story_ids") or []):
            if sid:
                story_counts[sid] = story_counts.get(sid, 0) + 1
    top_stories = sorted(story_counts.items(), key=lambda x: (-x[1], x[0]))[:5]

    # Recommended first: top 5 OQs from Minimum-unblock-set ranked by severity, then
    # descending related-count, then id lexical
    unblock = minimum_unblock_set(data)
    oq_candidates = [item for item in unblock if item["kind"] == "oq"]
    sev_rank = {"P1": 0, "P2": 1, "P3": 2}
    oq_candidates.sort(key=lambda x: (
        sev_rank.get(x["severity"], 9),
        -x.get("_related_count", 0),
        x["id"],
    ))
    recommended = oq_candidates[:5]

    lines: List[str] = [f"## {t('At a glance')}", ""]
    lines.append(f"P1: {counts['P1']} · P2: {counts['P2']} · P3: {counts['P3']} · Total: {total}")
    lines.append("")
    theme_parts = [f"{t('Frame')} {f} ({FRAME_NAMES.get(f, '?')}): {c}" for f, c in top_frames]
    theme_parts.append(f"Prose ambiguity: {prose_count}")
    lines.append(f"**{t('By theme')}:** {' · '.join(theme_parts)}")
    lines.append("")
    story_parts = [f"`{sid}` ({c})" for sid, c in top_stories]
    lines.append(f"**{t('Most-impacted stories')}:** {' · '.join(story_parts) if story_parts else '_(none)_'}")
    lines.append("")
    rec_parts = [f"[{item['id']}](#{_oq_anchor(item['id'])})" for item in recommended]
    lines.append(f"**{t('Recommended first')}:** {' · '.join(rec_parts) if rec_parts else '_(none)_'}")
    lines.append("")
    return lines


def render_open_questions(data: Dict[str, Any], path_map: Dict[str, str]) -> str:
    oqs = _sorted_by_severity(data.get("open_questions", []) or [])
    lines = [emit_frontmatter(minimal_fields(data, "ba-oq"))]
    lines += [f"# {t('Open Questions')}", ""]
    # v1.2.1: At-a-glance summary immediately after H1.
    lines += _at_a_glance_block(data)
    if not oqs:
        lines += [f"_{t('No open questions')}._", ""]
        return "\n".join(lines)
    current_sev = None
    for oq in oqs:
        sev = oq.get("severity", "P3")
        if sev != current_sev:
            lines += [f"## {sev}", ""]
            current_sev = sev
        badge = _provenance_badge(oq)
        anchor = _oq_anchor(oq.get('id', ''))
        # v1.2.1: explicit anchor enables stable Recommended-first links.
        lines.append(
            f'### <a id="{anchor}"></a>{oq.get("id", "(no id)")} — {oq.get("question", "")}{badge}'
        )
        lines.append("")
        if oq.get("why_matters"):
            lines += [f"**{t('Why it matters')}:** {oq['why_matters']}", ""]
        if oq.get("suggested_resolver"):
            lines += [f"**{t('Suggested resolver')}:** {oq['suggested_resolver']}", ""]
        related = oq.get("related_story_ids") or []
        if related:
            lines.append(f"**{t('Related stories')}:**")
            lines.append("")
            for sid in related:
                p = path_map.get(sid)
                if p:
                    lines.append(f"- [{sid}]({p})")
                else:
                    lines.append(f"- `{sid}`")
            lines.append("")
    return "\n".join(lines)


def render_assumptions(data: Dict[str, Any], path_map: Dict[str, str]) -> str:
    items = data.get("assumptions_made", []) or []
    lines = [emit_frontmatter(minimal_fields(data, "ba-assumptions"))]
    lines += [f"# {t('Assumptions Made')}", ""]
    if not items:
        lines += [f"_{t('No assumptions')}._", ""]
        return "\n".join(lines)
    for i, a in enumerate(items, 1):
        badge = _provenance_badge(a)
        lines.append(f"## A{i}. {a.get('assumption', '')}{badge}")
        lines.append("")
        if a.get("why_made"):
            lines += [f"**{t('Why')}:** {a['why_made']}", ""]
        if a.get("source"):
            lines += [f"**{t('Source')}:** {a['source']}", ""]
        if a.get("confidence"):
            lines += [f"**{t('Confidence')}:** {a['confidence']}", ""]
        if a.get("default_revisit_trigger"):
            lines += [f"**{t('Revisit trigger')}:** {a['default_revisit_trigger']}", ""]
        related = a.get("related_story_ids") or []
        if related:
            lines.append(f"**{t('Related stories')}:**")
            lines.append("")
            for sid in related:
                p = path_map.get(sid)
                if p:
                    lines.append(f"- [{sid}]({p})")
                else:
                    lines.append(f"- `{sid}`")
            lines.append("")
    return "\n".join(lines)


def render_hidden_requirements(data: Dict[str, Any], path_map: Dict[str, str]) -> str:
    """Render 09-hidden-requirements.md. Only called when sweep has findings."""
    oqs = [oq for oq in (data.get("open_questions") or [])
           if oq.get("provenance") == "hidden_frame_sweep"]
    assumptions = [a for a in (data.get("assumptions_made") or [])
                   if a.get("provenance") == "hidden_frame_sweep"]
    sweep = (data.get("processing_metadata") or {}).get("hidden_requirements_sweep") or {}

    fm = data.get("frontmatter", {}) or {}
    pm_sweep_coverage = ((data.get("processing_metadata") or {}).get("hidden_requirements_sweep") or {}).get("coverage_score")
    hr_fields = [
        ("artifact_type", "ba-hidden-requirements"),
        ("brief_id", fm.get("id")),
        ("idempotency_key", fm.get("idempotency_key")),
        ("workload_tier", fm.get("workload_tier")),
        ("output_type", data.get("output_type")),
        ("scope_kind", data.get("scope_kind")),
        ("status", fm.get("status")),
        ("blocks_tl_handoff", bool(data.get("blocks_tl_handoff", False))),
        ("coverage_score", pm_sweep_coverage),
        ("created_at", fm.get("created_at")),
        ("created_by", CREATED_BY),
        ("source_type", fm.get("source_type")),
        ("downstream_consumer", [("stage", "2-tl-design"), ("role", "tech-lead")]),
    ]
    lines = [emit_frontmatter(hr_fields)]
    lines += [
        f"# {t('Hidden Requirements (Elicitation-Gap Sweep)')}",
        "",
        "> Findings from the 10-frame sweep (Step 9.5). These are gaps the input did NOT state — the PM didn't think to ask. Cross-referenced from `open_questions[]` and `assumptions_made[]` carrying `provenance: hidden_frame_sweep`.",
        "",
    ]

    by_frame: Dict[int, Dict[str, List[Dict[str, Any]]]] = {}
    for oq in oqs:
        f = oq.get("frame")
        if not isinstance(f, int):
            continue
        by_frame.setdefault(f, {"oqs": [], "assumptions": []})["oqs"].append(oq)
    for a in assumptions:
        f = a.get("frame")
        if not isinstance(f, int):
            continue
        by_frame.setdefault(f, {"oqs": [], "assumptions": []})["assumptions"].append(a)

    for fnum in sorted(by_frame.keys()):
        bucket = by_frame[fnum]
        fname = FRAME_NAMES.get(fnum, f"Frame {fnum}")
        lines += [f"## {t('Frame')} {fnum} — {fname}", ""]
        if bucket["oqs"]:
            lines += [f"### {t('Open Questions')}", ""]
            for oq in bucket["oqs"]:
                lines.append(
                    f"- **[{oq.get('severity', '—')}] {oq.get('id', '?')}** — {oq.get('question', '')}"
                )
                if oq.get("why_matters"):
                    lines.append(f"  - {t('Why')}: {oq['why_matters']}")
                if oq.get("suggested_resolver"):
                    lines.append(f"  - {t('Resolver')}: {oq['suggested_resolver']}")
                related = oq.get("related_story_ids") or []
                if related:
                    refs = ", ".join(
                        f"[{sid}]({path_map[sid]})" if sid in path_map else f"`{sid}`"
                        for sid in related
                    )
                    lines.append(f"  - {t('Stories')}: {refs}")
            lines.append("")
        if bucket["assumptions"]:
            lines += [f"### {t('Assumed defaults (revisit triggers required)')}", ""]
            for a in bucket["assumptions"]:
                lines.append(f"- **{t('Assumptions Made')}**: {a.get('assumption', '')}")
                if a.get("why_made"):
                    lines.append(f"  - {t('Why')}: {a['why_made']}")
                if a.get("default_revisit_trigger"):
                    lines.append(f"  - {t('Revisit trigger')}: **{a['default_revisit_trigger']}**")
                related = a.get("related_story_ids") or []
                if related:
                    refs = ", ".join(
                        f"[{sid}]({path_map[sid]})" if sid in path_map else f"`{sid}`"
                        for sid in related
                    )
                    lines.append(f"  - {t('Stories')}: {refs}")
            lines.append("")

    if sweep:
        lines += [
            f"## {t('Frame coverage')}",
            "",
            f"- **Coverage score**: `{sweep.get('coverage_score', '—')}`",
            f"- **Frames applied**: {', '.join(str(f) for f in sweep.get('frames_applied', []))}",
        ]
        skipped = sweep.get("frames_skipped") or []
        if skipped:
            lines.append(f"- **Frames skipped**: {', '.join(str(f) for f in skipped)}")
            reasons = sweep.get("frames_skipped_reasons") or {}
            for f_str, reason in sorted(reasons.items()):
                lines.append(f"  - {t('Frame')} {f_str}: {reason}")
        per_frame = sweep.get("findings_per_frame") or {}
        if per_frame:
            lines.append("- **Findings per frame**:")
            for f_str in sorted(per_frame.keys(), key=lambda x: int(x) if str(x).isdigit() else 0):
                count = per_frame[f_str]
                fname = FRAME_NAMES.get(int(f_str), "?") if str(f_str).isdigit() else "?"
                lines.append(f"  - {t('Frame')} {f_str} ({fname}): {count}")
        if sweep.get("deferred_findings_count") is not None:
            lines.append(f"- **{t('Deferred (beyond per-frame cap)')}**: {sweep['deferred_findings_count']}")
        if sweep.get("total_findings") is not None:
            lines.append(f"- **{t('Total findings')}**: {sweep['total_findings']}")
        lines.append("")
    return "\n".join(lines)


def has_hidden_requirements(data: Dict[str, Any]) -> bool:
    sweep = (data.get("processing_metadata") or {}).get("hidden_requirements_sweep") or {}
    if sweep.get("total_findings", 0) > 0:
        return True
    for oq in (data.get("open_questions") or []):
        if oq.get("provenance") == "hidden_frame_sweep":
            return True
    for a in (data.get("assumptions_made") or []):
        if a.get("provenance") == "hidden_frame_sweep":
            return True
    return False


def validate_idempotency_replay(data: Dict[str, Any]) -> List[str]:
    """FM-16 (v1.2.2+): every story declaring bgc.idempotency.status == 'applies'
    MUST carry at least one acceptance_criterion with
    scenario_type == 'banking_grade_idempotency'.

    Mirrors the schema if/then constraint at Story object level. Provides a
    clearer error message than raw jsonschema output: names each offending
    story by id.
    """
    errors: List[str] = []
    for story in (data.get("stories") or []):
        sid = story.get("id", "?")
        bgc = story.get("banking_grade_concerns") or {}
        idem = bgc.get("idempotency") or {}
        if idem.get("status") != "applies":
            continue
        acs = story.get("acceptance_criteria") or []
        has_replay = any(
            (ac or {}).get("scenario_type") == "banking_grade_idempotency"
            for ac in acs
        )
        if not has_replay:
            errors.append(
                f"FM-16: story {sid} declares banking_grade_concerns.idempotency.status='applies' "
                f"but has no acceptance_criteria entry with scenario_type='banking_grade_idempotency'. "
                f"Per AP-4.3 (auto-emit on state-change ops), add a replay scenario or downgrade idempotency.status "
                f"to 'not_applicable' with workflow-class justification per AP-4.1."
            )
    return errors


def _detect_frame4_triggers(data: Dict[str, Any]) -> List[str]:
    """Detect which Frame 4 activation triggers fire on this brief.

    Triggers fire when concrete signal is present in the JSON. Each trigger is
    independently testable (no LLM calls, no fuzzy semantics).
    """
    triggers: List[str] = []

    # pii_collection: any direct or regulatory PII inventory entry
    pii = data.get("pii_inventory") or []
    for entry in pii:
        cat = (entry.get("category") or "").lower()
        if cat in ("direct", "regulatory"):
            triggers.append("pii_collection")
            break

    # jurisdiction_thailand: explicit signal in language_inventory or
    # regulatory_dependencies or glossary regulatory_tie
    lang = (data.get("processing_metadata") or {}).get("language_inventory") or []
    for l in lang:
        if "thai" in (l.get("script") or "").lower():
            triggers.append("jurisdiction_thailand")
            break
    else:
        for reg in (data.get("regulatory_dependencies") or []):
            code = (reg.get("code") or "").upper()
            if "PDPA" in code or "THAI" in (reg.get("regulator") or "").upper():
                triggers.append("jurisdiction_thailand")
                break

    # payment_processing: any story or epic title/context mentions payment
    payment_kw = ("payment", "checkout", "psp", "mock provider", "card", "wallet")
    payment_hit = False
    for ep in (data.get("epics") or []):
        blob = (ep.get("title", "") + " " + ep.get("problem_statement", "")).lower()
        if any(kw in blob for kw in payment_kw):
            payment_hit = True
            break
    if not payment_hit:
        for s in (data.get("stories") or []):
            blob = (s.get("title", "") + " " + s.get("context", "")).lower()
            if any(kw in blob for kw in payment_kw):
                payment_hit = True
                break
    if payment_hit:
        triggers.append("payment_processing")

    # audit_logging: any story declares audit_events.status == applies
    for s in (data.get("stories") or []):
        bgc = s.get("banking_grade_concerns") or {}
        ae = bgc.get("audit_events") or {}
        if ae.get("status") == "applies":
            triggers.append("audit_logging")
            break

    # consumer_facing: any epic stakeholders include a customer/end-user role
    consumer_kw = ("customer", "end user", "end-user", "shopper", "buyer", "consumer")
    consumer_hit = False
    for ep in (data.get("epics") or []):
        for sh in (ep.get("stakeholders") or []):
            role = (sh.get("role") or "").lower()
            if any(kw in role for kw in consumer_kw):
                consumer_hit = True
                break
        if consumer_hit:
            break
    if consumer_hit:
        triggers.append("consumer_facing")

    return sorted(set(triggers))


def validate_frame4_subtopics(data: Dict[str, Any]) -> List[str]:
    """FM-17 (v1.2.2+): when Frame 4 is in frames_applied AND an activation
    trigger fires, each required sub-topic for that trigger MUST get ≥1 OQ or
    assumption mentioning a coverage keyword.

    Returns list of error strings naming each missing sub-topic.
    """
    errors: List[str] = []
    sweep = (data.get("processing_metadata") or {}).get("hidden_requirements_sweep") or {}
    frames_applied = set(sweep.get("frames_applied") or [])
    if 4 not in frames_applied:
        return errors  # Frame 4 not active; FM-17 doesn't fire

    triggers = _detect_frame4_triggers(data)
    if not triggers:
        return errors

    # Build the haystack: every OQ + every assumption's relevant text fields
    haystack: List[str] = []
    for oq in (data.get("open_questions") or []):
        haystack.append((oq.get("question") or "").lower())
        haystack.append((oq.get("why_matters") or "").lower())
    for a in (data.get("assumptions_made") or []):
        haystack.append((a.get("assumption") or "").lower())
        haystack.append((a.get("why_made") or "").lower())
    combined = " ".join(haystack)

    # Also honor explicit skip declarations in frames_skipped_reasons under a
    # sub-topic namespace (e.g. {"4:pci_dss_scope": "Out of scope; merchant
    # uses fully-tokenized vendor"}). When such a key is present, the sub-topic
    # is considered intentionally skipped and does NOT count as a violation.
    skip_reasons = sweep.get("frames_skipped_reasons") or {}

    for trigger in triggers:
        for sub_id, keywords in FRAME4_SUBTOPIC_RULES.get(trigger, []):
            skip_key = f"4:{sub_id}"
            if skip_key in skip_reasons:
                continue  # explicit skip with reason — accepted
            covered = any(kw.lower() in combined for kw in keywords)
            if not covered:
                errors.append(
                    f"FM-17: Frame 4 sub-topic '{sub_id}' (trigger='{trigger}') has no covering OQ or assumption. "
                    f"Required when Frame 4 is active and trigger '{trigger}' fires. Coverage keywords: "
                    f"{', '.join(keywords[:3])}. Add an OQ/assumption mentioning one of these, OR add "
                    f"'4:{sub_id}' to processing_metadata.hidden_requirements_sweep.frames_skipped_reasons "
                    f"with a justification ≥8 chars to mark it as an intentional skip."
                )
    return errors


def validate_cap_exceptions(data: Dict[str, Any]) -> List[str]:
    """v1.3.1+ cap-exception protocol (assertion F-8, warning-grade).

    For each frame F whose findings_per_frame[F] exceeds the soft cap declared
    in FRAME_CAPS, require processing_metadata.hidden_requirements_sweep
    .cap_exceptions[str(F)] to declare {cap, observed_count, reason (>=8 chars)}.

    Returns a list of warning strings (empty = pass). Warnings are surfaced via
    the renderer's `warnings` channel but do NOT block emission (warning-grade
    in v1.3.1; promoted to must-pass error in v1.3.2).

    Most common driver: FM-17 mandatory sub-topic coverage on Frame 4 with
    multiple active triggers — v6 elicitation emitted 22 findings vs cap of 10.
    """
    warnings: List[str] = []
    sweep = (data.get("processing_metadata") or {}).get("hidden_requirements_sweep")
    if not sweep:
        return warnings
    findings = sweep.get("findings_per_frame") or {}
    exceptions = sweep.get("cap_exceptions") or {}
    for frame_key, count in findings.items():
        # findings_per_frame may key by string or int depending on JSON shape;
        # normalize to int for cap lookup, str for cap_exceptions lookup.
        try:
            frame_int = int(frame_key)
        except (TypeError, ValueError):
            continue
        frame_str = str(frame_int)
        cap = FRAME_CAPS.get(frame_int)
        if cap is None or not isinstance(count, int) or count <= cap:
            continue
        exc = exceptions.get(frame_str)
        if not exc:
            warnings.append(
                f"F-8 (warning): Frame {frame_int} findings_per_frame={count} exceeds "
                f"soft cap {cap}; declare processing_metadata.hidden_requirements_sweep"
                f".cap_exceptions[\"{frame_str}\"] = {{\"cap\": {cap}, "
                f"\"observed_count\": {count}, \"reason\": \"<>=8-char reason>\"}}. "
                f"Most common driver: FM-17 mandatory sub-topic coverage."
            )
            continue
        # Exception declared — verify shape matches observed.
        if exc.get("observed_count") != count:
            warnings.append(
                f"F-8 (warning): Frame {frame_int} cap_exceptions.observed_count="
                f"{exc.get('observed_count')} does not match findings_per_frame={count}."
            )
        if exc.get("cap") != cap:
            warnings.append(
                f"F-8 (warning): Frame {frame_int} cap_exceptions.cap="
                f"{exc.get('cap')} does not match FRAME_CAPS[{frame_int}]={cap}."
            )
        if len((exc.get("reason") or "")) < 8:
            warnings.append(
                f"F-8 (warning): Frame {frame_int} cap_exceptions.reason must be >=8 chars."
            )
    return warnings


def validate_sweep_invariants(data: Dict[str, Any]) -> List[str]:
    """FM-15 sweep invariants. Returns list of error strings (empty = pass)."""
    errors: List[str] = []
    sweep = (data.get("processing_metadata") or {}).get("hidden_requirements_sweep")
    output_type = data.get("output_type", "")
    if not sweep:
        return errors

    applied = set(sweep.get("frames_applied") or [])
    skipped = set(sweep.get("frames_skipped") or [])
    reasons = sweep.get("frames_skipped_reasons") or {}
    coverage = sweep.get("coverage_score")

    if applied & skipped:
        errors.append(f"FM-15: frames_applied and frames_skipped overlap on {sorted(applied & skipped)}")

    if output_type in SUCCESS_OUTPUT_TYPES:
        universe = set(range(1, 11))
        covered = applied | skipped
        missing = universe - covered
        if missing:
            errors.append(
                f"FM-15: non-failure output requires frames_applied ∪ frames_skipped == {{1..10}}; missing {sorted(missing)}"
            )

    for f in skipped:
        if str(f) not in reasons:
            errors.append(f"FM-15: frame {f} is skipped but has no entry in frames_skipped_reasons")

    if output_type == "brief" and coverage != "complete":
        errors.append(
            f"FM-15: output_type=brief requires coverage_score=complete; got {coverage!r}"
        )
    if coverage == "skipped" and output_type in SUCCESS_OUTPUT_TYPES:
        errors.append(
            f"FM-15: coverage_score=skipped is only valid for failure shapes; got output_type={output_type!r}"
        )

    return errors


def render_glossary(data: Dict[str, Any]) -> str:
    items = data.get("glossary", []) or []
    lines = [emit_frontmatter(minimal_fields(data, "ba-glossary"))]
    lines += [f"# {t('Glossary')}", ""]
    if not items:
        lines += ["_No glossary terms recorded._", ""]
        return "\n".join(lines)
    lines += [
        f"| {t('Canonical Form')} | {t('Surface Forms')} | {t('Definition')} | {t('PII Sensitivity')} | {t('Regulatory Tie')} |",
        "|---|---|---|---|---|",
    ]
    for g in items:
        surface = ", ".join(g.get("surface_form", []) or [])
        definition = (g.get("definition") or "").replace("\n", " ").replace("|", "\\|")
        lines.append(
            f"| {g.get('canonical_form', g.get('term', ''))} | {surface} | "
            f"{definition} | {g.get('pii_sensitivity', '—')} | {g.get('regulatory_tie') or '—'} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_pii_inventory(data: Dict[str, Any]) -> str:
    items = data.get("pii_inventory", []) or []
    lines = [emit_frontmatter(minimal_fields(data, "ba-pii"))]
    lines += [f"# {t('PII Inventory')}", ""]
    if not items:
        lines += [f"_{t('No PII identified')}._", ""]
        return "\n".join(lines)
    lines += [
        f"| {t('Field')} | {t('Category')} | {t('Treatment')} | {t('Retention')} | {t('Masking')} | {t('Access Audit')} |",
        "|---|---|---|---|---|---|",
    ]
    for p in items:
        treatment = (p.get("treatment") or "—").replace("\n", " ").replace("|", "\\|")
        lines.append(
            f"| `{p.get('field', '')}` | {p.get('category', '—')} | "
            f"{treatment} | {p.get('retention_rule', '—')} | "
            f"{p.get('masking_rule', '—')} | {p.get('access_audit', '—')} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_regulatory_deps(data: Dict[str, Any]) -> str:
    items = data.get("regulatory_dependencies", []) or []
    lines = [emit_frontmatter(minimal_fields(data, "ba-reg-deps"))]
    lines += [f"# {t('Regulatory Dependencies')}", ""]
    if not items:
        lines += [f"_{t('No regulatory dependencies')}._", ""]
        return "\n".join(lines)
    lines += [
        f"| {t('Regulator')} | {t('Code')} | {t('Revision')} | {t('Citation Status')} | {t('Promisor')} | {t('Due Date')} |",
        "|---|---|---|---|---|---|",
    ]
    for r in items:
        lines.append(
            f"| {r.get('regulator', '—')} | {r.get('code', '—')} | "
            f"{r.get('revision', '—')} | {r.get('citation_status', '—')} | "
            f"{r.get('promisor', '—')} | {r.get('due_date', '—')} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_processing_metadata(data: Dict[str, Any]) -> str:
    pm = data.get("processing_metadata", {}) or {}
    lines = [emit_frontmatter(minimal_fields(data, "ba-metadata"))]
    lines += [f"# {t('Processing Metadata')}", ""]

    td = pm.get("tier_decisions", []) or []
    if td:
        lines += [f"## {t('Tier Decisions')}", "", f"| {t('Epic')} | {t('Workload tier')} | {t('Tier Signals')} |", "|---|---|---|"]
        for entry in td:
            signals = "; ".join(entry.get("signals", []) or [])
            lines.append(
                f"| `{entry.get('epic_id', '')}` | "
                f"{entry.get('inferred_tier', '')} | {signals} |"
            )
        lines.append("")

    lines += [
        f"## {t('Parsing')}",
        "",
        f"- **Mode**: `{pm.get('parsing_mode', '—')}`",
        f"- **{t('Reason')}**: {pm.get('parsing_reason', '—')}",
        f"- **Chunking**: {pm.get('chunking') or 'none'}",
        f"- **Ground-truth stripped**: {bool(pm.get('ground_truth_stripped', False))}",
        f"- **Tipping-off scan clean**: {bool(pm.get('tipping_off_scan_clean', False))}",
        "",
    ]

    lang = pm.get("language_inventory", []) or []
    if lang:
        lines += [f"## {t('Language Inventory')}", "", "| Script | Frequency | Sample |", "|---|---|---|"]
        for lang_entry in lang:
            sample = (lang_entry.get("sample") or "").replace("\n", " ").replace("|", "\\|")
            lines.append(f"| {lang_entry.get('script', '—')} | {lang_entry.get('frequency', '—')} | {sample} |")
        lines.append("")

    ext = pm.get("external_dependencies", []) or []
    if ext:
        lines += [f"## {t('External Dependencies')}", ""]
        for e in ext:
            lines.append(f"- {e}")
        lines.append("")

    sweep = pm.get("hidden_requirements_sweep")
    if sweep:
        lines += [
            "## Hidden-Requirements Sweep (Step 9.5)",
            "",
            f"- **Coverage score**: `{sweep.get('coverage_score', '—')}`",
            f"- **{t('Total findings')}**: {sweep.get('total_findings', 0)}",
            f"- **Frames applied**: {', '.join(str(f) for f in sweep.get('frames_applied', []))}",
        ]
        skipped = sweep.get("frames_skipped") or []
        if skipped:
            lines.append(f"- **Frames skipped**: {', '.join(str(f) for f in skipped)}")
        if sweep.get("deferred_findings_count"):
            lines.append(f"- **{t('Deferred (beyond per-frame cap)')}**: {sweep['deferred_findings_count']}")
        lines.append("")
        lines.append("Full per-finding detail at [09-hidden-requirements.md](09-hidden-requirements.md).")
        lines.append("")

    return "\n".join(lines)


def render_audit_trace(data: Dict[str, Any]) -> str:
    lines = [emit_frontmatter(minimal_fields(data, "ba-audit-trace"))]
    lines += [f"# {t('Audit Trace')}", ""]

    brt = data.get("ba_reasoning_trace")
    if brt:
        lines += [f"## {t('BA Reasoning Trace')}", ""]
        if isinstance(brt, dict):
            for k in sorted(brt.keys()):
                v = brt[k]
                lines += [f"### {k}", "", str(v), ""]
        elif isinstance(brt, list):
            for i, item in enumerate(brt, 1):
                lines.append(f"### Trace {i}")
                lines.append("")
                if isinstance(item, dict):
                    for k, v in item.items():
                        lines.append(f"- **{k}**: {v}")
                else:
                    lines.append(str(item))
                lines.append("")
        else:
            lines += [str(brt), ""]

    cc = data.get("ba_compliance_checklist") or {}
    if cc:
        lines += [f"## {t('BA Compliance Checklist')}", ""]
        for k in COMPLIANCE_KEYS:
            mark = "✅" if bool(cc.get(k)) else "❌"
            lines.append(f"- {mark} `{k}`")
        # any extras not in canonical list
        extras = [k for k in cc.keys() if k not in COMPLIANCE_KEYS]
        for k in sorted(extras):
            mark = "✅" if bool(cc.get(k)) else "❌"
            lines.append(f"- {mark} `{k}`")
        lines.append("")

    return "\n".join(lines)


def render_failure(data: Dict[str, Any]) -> str:
    fm = data.get("frontmatter", {}) or {}
    failure = data.get("failure_state", {}) or {}
    output_type = data.get("output_type", "")

    fields = [
        ("artifact_type", "ba-failure"),
        ("brief_id", fm.get("id")),
        ("idempotency_key", fm.get("idempotency_key")),
        ("output_type", output_type),
        ("created_at", fm.get("created_at")),
        ("created_by", CREATED_BY),
    ]
    lines = [emit_frontmatter(fields)]
    lines += [
        f"# {t('Failure')} — `{output_type}`",
        "",
    ]
    if failure.get("reason"):
        lines += [f"**{t('Reason')}:** {failure['reason']}", ""]
    if failure.get("failure_code"):
        lines += [f"**{t('Failure code')}:** `{failure['failure_code']}`", ""]
    if failure.get("detected_by"):
        lines += [f"**Detected by:** {failure['detected_by']}", ""]
    if failure.get("do_not_proceed"):
        lines += [f"> **`do_not_proceed: true`** — {t('Do not proceed')}.", ""]
    rec = failure.get("recommended_action") or failure.get("unblock_actions")
    if rec:
        lines += [f"## {t('Recommended questions')}", ""]
        if isinstance(rec, list):
            for r in rec:
                lines.append(f"- {r}")
        else:
            lines.append(rec)
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Top-level renderer
# ---------------------------------------------------------------------------


def write_file(path: Path, content: str) -> None:
    if not content.endswith("\n"):
        content = content + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def validate_schema(data: Dict[str, Any], schema_path: Optional[Path]) -> List[str]:
    if not schema_path or not schema_path.exists():
        return ["schema-file-not-found (skipping validation)"]
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return ["jsonschema-not-installed (skipping validation)"]
    with schema_path.open("r", encoding="utf-8") as fh:
        schema = json.load(fh)
    validator = jsonschema.Draft7Validator(schema)
    errors = [e.message for e in validator.iter_errors(data)]
    return errors


def find_schema_path(start: Path) -> Optional[Path]:
    """Walk up from the script location to find schemas/output.json."""
    here = start.resolve()
    for parent in [here] + list(here.parents):
        cand = parent / "schemas" / "output.json"
        if cand.exists():
            return cand
    return None


def _apply_translations_in_place(node: Any, lang: str) -> None:
    """v1.4.0+. Walk a JSON-like structure; for any dict that has a
    `translations[lang]` sub-object, overwrite its sibling string fields with
    the translated values, then remove the `translations` key from the
    localized copy. Fields missing in `translations[lang]` keep their English
    source values (graceful fallback).
    """
    if isinstance(node, dict):
        trans = node.get("translations")
        if isinstance(trans, dict):
            lang_block = trans.get(lang)
            if isinstance(lang_block, dict):
                for k, v in lang_block.items():
                    if k != "translations" and isinstance(v, str):
                        node[k] = v
            del node["translations"]
        for value in node.values():
            _apply_translations_in_place(value, lang)
    elif isinstance(node, list):
        for item in node:
            _apply_translations_in_place(item, lang)


def _strip_translations_in_place(node: Any) -> None:
    """v1.4.0+. Remove all `translations` keys from a JSON-like structure.
    Used for emitting the English (canonical) tree, where the source fields
    are already in English and the translations sub-objects are presentation-
    layer cruft."""
    if isinstance(node, dict):
        node.pop("translations", None)
        for value in node.values():
            _strip_translations_in_place(value)
    elif isinstance(node, list):
        for item in node:
            _strip_translations_in_place(item)


def localize_data(data: Dict[str, Any], lang: str) -> Dict[str, Any]:
    """v1.4.0+. Return a deep-copied view of `data` localized for `lang`.

    For `lang == "en"`, returns the data with `translations` sub-objects
    stripped (English is canonical; translations sub-objects are not needed
    in the EN tree). For any other language, walks the tree applying per-
    object `translations[lang]` substitutions, then strips the `translations`
    sub-objects from the localized result. Missing per-field translations
    fall back to the English source value.

    Pure function; does not mutate the input."""
    import copy as _copy
    out = _copy.deepcopy(data)
    if lang == "en":
        _strip_translations_in_place(out)
    else:
        _apply_translations_in_place(out, lang)
    return out


def _render_language_tree(
    lang_data: Dict[str, Any],
    lang_target: Path,
    output_type: str,
    lang: str = "en",
) -> List[Path]:
    """v1.4.0+. Render a single language's tree under `lang_target`. Returns
    the list of files written. Called once per language by `render_tree()`.
    The caller is responsible for creating/cleaning `lang_target`.

    v1.4.1+: sets the module-level `_CURRENT_LANG` for the duration of this
    render pass so that `t(key)` resolves UI-string translations against the
    active language. Reset to "en" on exit so monolingual EN tests/callers
    don't see a stale TH context."""
    global _CURRENT_LANG
    _CURRENT_LANG = lang
    try:
        return _render_language_tree_inner(lang_data, lang_target, output_type)
    finally:
        _CURRENT_LANG = "en"


def _render_language_tree_inner(
    lang_data: Dict[str, Any],
    lang_target: Path,
    output_type: str,
) -> List[Path]:
    """Inner implementation called with `_CURRENT_LANG` already set. Split
    from `_render_language_tree()` so the language context is reliably
    cleared even when a render_* function raises."""
    files_written: List[Path] = []

    if output_type in FAILURE_OUTPUT_TYPES:
        readme = lang_target / "README.md"
        write_file(readme, render_readme(lang_data))
        failure = lang_target / "FAILURE.md"
        write_file(failure, render_failure(lang_data))
        files_written += [readme, failure]
        return files_written

    path_map = find_story_path_map(lang_data)

    write_file(lang_target / "README.md", render_readme(lang_data))
    files_written.append(lang_target / "README.md")

    write_file(lang_target / "00-BRIEF.md", render_brief_summary(lang_data))
    files_written.append(lang_target / "00-BRIEF.md")

    cross = [
        ("01-governance-gaps.md", render_governance_gaps(lang_data, path_map)),
        ("02-open-questions.md", render_open_questions(lang_data, path_map)),
        ("03-assumptions.md", render_assumptions(lang_data, path_map)),
        ("04-glossary.md", render_glossary(lang_data)),
        ("05-pii-inventory.md", render_pii_inventory(lang_data)),
        ("06-regulatory-dependencies.md", render_regulatory_deps(lang_data)),
        ("07-processing-metadata.md", render_processing_metadata(lang_data)),
        ("08-audit-trace.md", render_audit_trace(lang_data)),
    ]
    if has_hidden_requirements(lang_data):
        cross.append(("09-hidden-requirements.md", render_hidden_requirements(lang_data, path_map)))
    for name, content in cross:
        write_file(lang_target / name, content)
        files_written.append(lang_target / name)

    epics = lang_data.get("epics") or ([lang_data["epic"]] if lang_data.get("epic") else [])
    for epic in epics:
        eid = epic.get("id", "")
        epic_dir = lang_target / "epics" / epic_dir_name(eid)
        write_file(epic_dir / "EPIC.md", render_epic(lang_data, epic))
        files_written.append(epic_dir / "EPIC.md")
        stories = stories_for_epic(lang_data.get("stories", []), eid)
        for s in stories:
            rel_path = path_map.get(s["id"])
            if not rel_path:
                continue
            story_path = lang_target / rel_path
            write_file(story_path, render_story(lang_data, s, epic))
            files_written.append(story_path)
    return files_written


def render_tree(input_path: Path, output_dir: Path, schema_path: Optional[Path] = None) -> Dict[str, Any]:
    with input_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    if schema_path is None:
        schema_path = find_schema_path(Path(__file__).parent)

    schema_errors = validate_schema(data, schema_path)
    hard_errors = [e for e in schema_errors if not e.startswith(("schema-file-not-found", "jsonschema-not-installed"))]
    sweep_errors = validate_sweep_invariants(data)
    idempotency_errors = validate_idempotency_replay(data)
    frame4_errors = validate_frame4_subtopics(data)
    # v1.3.1+ warning-grade check (F-8). Does NOT block emission.
    cap_warnings = validate_cap_exceptions(data)
    if hard_errors or sweep_errors or idempotency_errors or frame4_errors:
        return {
            "ok": False,
            "errors": hard_errors + sweep_errors + idempotency_errors + frame4_errors,
            "warnings": cap_warnings,
            "files_written": [],
        }

    fm = data.get("frontmatter", {}) or {}
    idem = (fm.get("idempotency_key") or "").lower()
    idem8 = idem[:8] if idem else "unknown0"

    # If output_dir already ends with the canonical name, use it directly;
    # otherwise treat output_dir as the parent and create output-{idem8} inside.
    if output_dir.name == f"output-{idem8}":
        target = output_dir
    else:
        target = output_dir / f"output-{idem8}"

    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    files_written: List[Path] = []

    # 1. Canonical JSON at the tree root (v1.4.0+: lives once, contains both
    # English source + translation maps; the language subdirs derive from it).
    json_target = target / "output.json"
    json_target.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    files_written.append(json_target)

    output_type = data.get("output_type", "")

    # v1.4.0+: read bilingual_output flag; default ["en"] for backward
    # compatibility with pre-v1.4.0 briefs that don't carry the field.
    pm = data.get("processing_metadata") or {}
    languages = pm.get("bilingual_output") or ["en"]
    if not isinstance(languages, list) or not languages:
        languages = ["en"]

    for lang in languages:
        lang_dir_name = lang.upper()
        lang_target = target / lang_dir_name
        if lang_target.exists():
            shutil.rmtree(lang_target)
        lang_target.mkdir(parents=True, exist_ok=True)
        lang_data = localize_data(data, lang)
        files_written += _render_language_tree(lang_data, lang_target, output_type, lang)

    return _finalize(target, files_written, schema_errors, cap_warnings)


def _finalize(
    target: Path,
    files_written: List[Path],
    schema_errors: List[str],
    cap_warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    # Cross-link validation: scan every emitted .md file for ](relative.md...) refs
    link_errors: List[str] = []
    link_pattern = re.compile(r"\]\((?!https?:)([^)]+\.md)(#[^)]*)?\)")
    for f in files_written:
        if not f.name.endswith(".md"):
            continue
        text = f.read_text(encoding="utf-8")
        for m in link_pattern.finditer(text):
            rel = m.group(1)
            resolved = (f.parent / rel).resolve()
            if not resolved.exists():
                link_errors.append(f"{f.relative_to(target)} → broken link `{rel}`")
    return {
        "ok": not link_errors,
        "target": str(target),
        "files_written": sorted(str(p.relative_to(target)) for p in files_written),
        "schema_errors": schema_errors,
        "link_errors": link_errors,
        "warnings": cap_warnings or [],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Path to output.json")
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="Parent dir for output-{idem8}/ (or the canonical dir itself)")
    parser.add_argument("--schema", type=Path, default=None,
                        help="Optional path to schemas/output.json for defense-in-depth validation")
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"error: input file not found: {args.input}", file=sys.stderr)
        return 2

    result = render_tree(args.input, args.output_dir, args.schema)
    if not result.get("ok"):
        print("RENDER FAILED:", file=sys.stderr)
        for e in result.get("errors", []):
            print(f"  schema: {e}", file=sys.stderr)
        for e in result.get("link_errors", []):
            print(f"  link: {e}", file=sys.stderr)
        return 1

    print(f"rendered tree at: {result['target']}")
    print(f"  files written: {len(result['files_written'])}")
    for note in result.get("schema_errors", []):
        if note.startswith(("schema-file-not-found", "jsonschema-not-installed")):
            print(f"  note: {note}")
    for w in result.get("warnings", []) or []:
        print(f"  warning: {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
