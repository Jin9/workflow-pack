# Frame Coverage Completeness Assertions (v1.2.2+, refined v1.3.1)

> Validates the FM-16 (idempotency-replay enforcement) and FM-17 (Frame 4 sub-topic coverage) rules introduced in v1.2.2. Run after schema validation and before tree-shape assertions.

## Purpose

The v1.2.0/v1.2.1 holdout runs revealed two enforcement gaps in the procedure:

1. **FM-16**: BAs missed the AP-4.3 auto-emit rule on state-change stories — 16/29 v4 stories and 6/16 v5 stories declared `banking_grade_concerns.idempotency.status: "applies"` but never produced the corresponding `banking_grade_idempotency` AC scenario. The skill prose mandated it; the validation didn't enforce it.

2. **FM-17**: The v5 run dropped Frame 4 (Regulatory) findings from 10 to 6 — same input, same skill version, but lost cross-border PDPA, right-to-erasure-vs-retention, PCI scope, cookie consent. The skill listed required sub-topics in the reference but had no programmatic check.

v1.2.2 closes both gaps with schema if/then constraints + renderer runtime checks. These assertions verify both pathways.

## Severity Semantics

- **must-pass** = test case fails on violation. Counts toward `must_pass_failures`.
- **should-pass** = warning logged; case status becomes `pass-with-warnings`.

## Rule Table

| # | Rule | Severity | Source |
|---|---|---|---|
| F-1 | **Idempotency-replay AC present when applies** (FM-16). For every story where `banking_grade_concerns.idempotency.status == "applies"`, `acceptance_criteria[]` MUST contain ≥1 entry with `scenario_type == "banking_grade_idempotency"`. Schema if/then enforces; renderer's `validate_idempotency_replay()` provides per-story error messages. | must-pass | SKILL.md FM-16; `references/anti-patterns.md` AP-4.3; schema Story `allOf` |
| F-2 | **Frame 4 sub-topic coverage for activated triggers** (FM-17). When Frame 4 is in `processing_metadata.hidden_requirements_sweep.frames_applied` AND any of the 5 trigger conditions fires (pii_collection / jurisdiction_thailand / payment_processing / audit_logging / consumer_facing), each required sub-topic for the activated trigger MUST have ≥1 covering OQ or assumption (keyword match against `question + why_matters` and `assumption + why_made`). Renderer's `validate_frame4_subtopics()` enforces. | must-pass | SKILL.md FM-17; `references/hidden-requirements-frames.md` § "Required sub-topics when activated" |
| F-3 | **Skip declarations honored**. A required Frame 4 sub-topic may be explicitly skipped by adding `4:{sub_topic_id}` as a key in `processing_metadata.hidden_requirements_sweep.frames_skipped_reasons` with a non-empty (≥8 char) reason. When this key exists, F-2 does NOT fire for that sub-topic. | must-pass | `references/edge-case-catalog.md` FM-17 escalation; SKILL.md FM-17 trigger map |
| F-4 | **Schema if/then matches renderer runtime check**. The schema-level `Story.allOf` constraint and the renderer's `validate_idempotency_replay()` must produce equivalent verdicts: any brief that passes one must pass the other. (Tests run both and assert agreement.) | must-pass | redundant-defense pattern; if they diverge, one is wrong |
| F-5 | **Trigger detection is deterministic**. Running the renderer twice on the same brief must produce the same `_detect_frame4_triggers()` set, hence the same FM-17 verdict. (Idempotency narrowed to FM-17 outputs.) | must-pass | renderer determinism contract |
| F-6 | **FM-16 + FM-17 do not block failure-shape outputs**. For `output_type ∈ {needs_clarification, preprocessing_failure, pii_echo_blocked, schema_validation_failure, meta_response}`, FM-16 and FM-17 are skipped (the brief has no stories or no sweep). | must-pass | failure-shape contract per SKILL.md §Output Contract |
| F-7 | **Data-doc drift check** (v1.3.0+). The contents of `references/frame-rule-data.json#triggers` MUST agree with the table at `references/hidden-requirements-frames.md` lines 183-207. For each row in the markdown table, the JSON MUST contain a matching `{sub_topic_id, coverage_keywords (set-equal after split on ';' + lowercase/strip), jurisdiction_note (exact string)}` entry under the same trigger; trigger-set, sub-topic-set, and row-count MUST match. Dev-time check, runnable: `python3 scripts/check_frame_rule_data_drift.py`. Not part of per-render flow; runs once per CI invocation. | must-pass | v1.3.0 backlog item #1: rule data lifted to `references/frame-rule-data.json` (loaded by renderer); markdown table is the human-readable mirror |
| F-8 | **Cap-exception declaration** (v1.3.1+, warning-grade). When `processing_metadata.hidden_requirements_sweep.findings_per_frame[F]` exceeds `FRAME_CAPS[F]` (the per-frame soft cap declared in `references/hidden-requirements-frames.md` Cap-line for that frame: F1=5, F2=5, F3=5, F4=10, F5=5, F6=7, F7=5, F8=5, F9=5, F10=5), `cap_exceptions[str(F)]` MUST exist with `{cap, observed_count, reason (minLength 8)}`. Most common driver: FM-17 mandatory sub-topic coverage on Frame 4 with multiple active triggers (v6 elicitation emitted 22 vs cap 10). Renderer's `validate_cap_exceptions()` emits a warning when violated (warning-grade in v1.3.1; **promotion to `must-pass` is scheduled for v1.3.2** after one or two real-world inputs have been observed). | should-pass | v1.3 backlog item #6 (`frame_4_cap_exception` protocol) |

## Per-Rule Pseudo-Check

### F-1 Idempotency-replay AC present when applies

```python
for story in data.get("stories", []):
    bgc = story.get("banking_grade_concerns", {}) or {}
    idem = bgc.get("idempotency", {}) or {}
    if idem.get("status") != "applies":
        continue
    acs = story.get("acceptance_criteria") or []
    has_replay = any(
        (ac or {}).get("scenario_type") == "banking_grade_idempotency"
        for ac in acs
    )
    assert has_replay, (
        f"FM-16: story {story.get('id')} declares idempotency.status='applies' "
        f"but lacks banking_grade_idempotency AC"
    )
```

### F-2 Frame 4 sub-topic coverage

```python
FRAME4_SUBTOPIC_RULES = {  # mirror of renderer constant
    "pii_collection": [
        ("dsar_workflow", ["dsar", "data subject access", ...]),
        ("right_to_erasure", ["right to erasure", "right to be forgotten", ...]),
        # ...
    ],
    # ...
}

sweep = data.get("processing_metadata", {}).get("hidden_requirements_sweep", {}) or {}
if 4 not in (sweep.get("frames_applied") or []):
    return  # F-2 doesn't fire when Frame 4 not active

active_triggers = detect_frame4_triggers(data)
skip_keys = set((sweep.get("frames_skipped_reasons") or {}).keys())
haystack = build_haystack(data)  # all OQs + assumptions text

for trigger in active_triggers:
    for sub_id, keywords in FRAME4_SUBTOPIC_RULES.get(trigger, []):
        if f"4:{sub_id}" in skip_keys:
            continue  # explicit skip with reason
        covered = any(kw.lower() in haystack.lower() for kw in keywords)
        assert covered, f"FM-17: trigger={trigger}, sub-topic={sub_id} uncovered"
```

### F-3 Skip declarations honored

```python
# Synthesize a brief with: Frame 4 active, pii_collection trigger, AND
# a frames_skipped_reasons entry "4:dsar_workflow": "Out of scope; system is
# read-only and doesn't store subject-identifiable records."
# Even though no OQ covers dsar_workflow, F-2 must not fire for this sub-topic.
assert renderer_runs_clean(synthesized_brief)
```

### F-4 Schema if/then matches renderer runtime check

```python
schema_errors = run_jsonschema_validation(data, schema_path)
runtime_errors = validate_idempotency_replay(data)
# Both should agree on story-level passes/fails. Convert to sets of story_ids and assert equality.
schema_fail_ids = extract_story_ids_from_schema_errors(schema_errors)
runtime_fail_ids = extract_story_ids_from_runtime_errors(runtime_errors)
assert schema_fail_ids == runtime_fail_ids
```

### F-5 Trigger detection deterministic

```python
triggers_a = _detect_frame4_triggers(data)
triggers_b = _detect_frame4_triggers(data)
assert triggers_a == triggers_b  # set equality
```

### F-6 Failure shapes skip F-1 and F-2

```python
data["output_type"] = "preprocessing_failure"
data["failure_state"] = {"failure_code": "ground_truth_strip_failed", "do_not_proceed": True}
# Remove stories array (failure shapes have no stories)
data.pop("stories", None)
result = render(data)
assert result["ok"], "FM-16/FM-17 must not fire on failure shapes"
```

### F-7 Data-doc drift check (v1.3.0+)

```python
# Runnable: python3 scripts/check_frame_rule_data_drift.py
# (Implementation lives in scripts/check_frame_rule_data_drift.py.)
# Exits 0 on agreement, 1 on drift (with a structured diff to stderr).
#
# Comparison key per row:
#   (trigger, sub_topic_id, frozenset(lowercased+stripped keywords), jurisdiction_note)
#
# Markdown keyword cells are semicolon-separated; JSON keyword lists are
# explicit. Both sides normalize via lowercase + strip before set comparison.
import subprocess
proc = subprocess.run(["python3", "scripts/check_frame_rule_data_drift.py"], capture_output=True)
assert proc.returncode == 0, f"F-7: {proc.stderr.decode()}"
```

### F-8 Cap-exception declaration (v1.3.1+, warning-grade)

```python
# Implementation lives in scripts/render_markdown_tree.py: validate_cap_exceptions()
# Returns a list of warning strings (empty = pass). Warnings are surfaced via
# the renderer's `warnings` channel but do NOT block emission in v1.3.1.
# Promotion to must-pass (hard error) scheduled for v1.3.2.
FRAME_CAPS = {1: 5, 2: 5, 3: 5, 4: 10, 5: 5, 6: 7, 7: 5, 8: 5, 9: 5, 10: 5}

sweep = (data.get("processing_metadata") or {}).get("hidden_requirements_sweep") or {}
findings = sweep.get("findings_per_frame") or {}
exceptions = sweep.get("cap_exceptions") or {}

for frame_key, count in findings.items():
    frame_int = int(frame_key)
    cap = FRAME_CAPS[frame_int]
    if count <= cap:
        continue  # F-8 doesn't fire when within cap
    exc = exceptions.get(str(frame_int))
    assert exc is not None, (
        f"F-8 (warning-grade): Frame {frame_int} findings={count} > cap {cap}; "
        f"declare cap_exceptions['{frame_int}'] = {{'cap': {cap}, "
        f"'observed_count': {count}, 'reason': '...' (>=8 chars)}}."
    )
    assert exc["cap"] == cap and exc["observed_count"] == count
    assert len(exc["reason"]) >= 8
```

## Pass/Fail Interpretation

- **All must-pass rules pass** → case status = `pass`.
- **All must-pass rules pass AND ≥1 should-pass warning** → case status = `pass-with-warnings`.
- **≥1 must-pass rule fails** → case status = `fail`. Accumulate `must_pass_failures: [{rule_id, file_path, evidence}]`.

## Per-Tree Report Format

```json
{
  "assertion_file": "frame-coverage-completeness.md",
  "tree_root": "output-{idem8}/",
  "rule_results": [
    { "rule_id": "F-1", "status": "pass" },
    { "rule_id": "F-2", "status": "pass" },
    { "rule_id": "F-3", "status": "pass" },
    { "rule_id": "F-4", "status": "pass" },
    { "rule_id": "F-5", "status": "pass" },
    { "rule_id": "F-6", "status": "pass" },
    { "rule_id": "F-7", "status": "pass" },
    { "rule_id": "F-8", "status": "pass-with-warnings" }
  ]
}
```

## Historical regressions caught

When this assertion is run retroactively against the v4 and v5 holdout JSONs:

- **`/tmp/ba-brief-v4.json`** (10 epics, 29 stories): F-1 fails on 16 stories (CATALOG-3, CATALOG-4, AUTH-PROFILE-2, AUTH-PROFILE-3, CART-CHECKOUT-1, ORDER-LIFECYCLE-3, FULFILL-ADMIN-1, FULFILL-ADMIN-3, INVENTORY-1, INVENTORY-2, COUPON-1, COUPON-2, REVIEW-1, REVIEW-2, AUDIT-OBSERVE-1, AUDIT-OBSERVE-2). F-2 fails on 4 sub-topics (log_pii_redaction, cookie_consent, merchant_identity_disclosure, chargeback_workflow). These matches confirm the audit-identified misses.

- **`/tmp/ba-brief-v5.json`** (5 epics, 16 stories): F-1 fails on 6 stories (IDENTITY-1, IDENTITY-2, IDENTITY-3, ORDER-FULFILL-2, GOVERNANCE-OBS-1, GOVERNANCE-OBS-2). F-2 fails on 4 sub-topics (log_pii_redaction, privacy_policy_authoring, terms_of_service, cookie_consent). The v5 sub-topic gaps reveal exactly the "Frame 4 dropped from 10 to 6" thinning Phase D flagged.

If the renderer were rerun on these JSONs after applying the appropriate fixes (adding the missing AC scenarios, adding the missing OQs or sub-topic skip reasons), F-1 and F-2 would both pass.

## Cross-References

- `references/frame-rule-data.json` (v1.3.0+) — runtime source-of-truth for FM-17; loaded by the renderer at import time
- `references/hidden-requirements-frames.md` § "Required sub-topic detection table" — human-readable mirror of `frame-rule-data.json`; drift caught by F-7
- `references/anti-patterns.md` AP-4.3 — the auto-emit rule FM-16 enforces
- `scripts/render_markdown_tree.py` — `validate_idempotency_replay()`, `validate_frame4_subtopics()`, `validate_cap_exceptions()` (v1.3.1+), `_detect_frame4_triggers()`, `_load_frame4_subtopic_rules()`, `FRAME4_SUBTOPIC_RULES`, `FRAME_CAPS` (v1.3.1+)
- `scripts/check_frame_rule_data_drift.py` (v1.3.0+) — F-7 dev-time drift assertion
- `tests/assertions/banking-grade-fields.md` — sibling assertion covering structural force-fill (not coverage)
- `tests/assertions/markdown-tree-shape.md` — sibling assertion covering tree structure
- `tests/assertions/surfacing-completeness.md` — sibling assertion covering v1.2.1 surfacing
