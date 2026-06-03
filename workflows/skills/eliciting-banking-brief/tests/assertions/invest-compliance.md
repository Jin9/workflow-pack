# INVEST Compliance Assertions

> Per-rule checklist that every story in `stories[]` satisfies INVEST per `references/ba-best-practices.md` §1 and `references/invest-checklist.md`. Run after schema validation passes.

## Purpose

Schema validation (`schemas/output.json`) enforces structural shape. This assertion file enforces **semantic INVEST compliance** — each story is testable as an independently valuable unit of delivery. Failures route per severity below.

## Severity Semantics

- **must-pass** = test case fails on violation. Counts toward `must_pass_failures`.
- **should-pass** = warning logged; test case status becomes `pass-with-warnings`. Counts toward `should_pass_warnings`.

## Rule Table

| # | Rule | Severity | Source |
|---|---|---|---|
| I-1 | **Independent**: each `depends_on[]` entry resolves to an in-brief story id OR appears in `processing_metadata.external_dependencies[]`. No phantom dependencies. | must-pass | INVEST §I; AP-7.1 |
| I-2 | **Negotiable**: no tech-layer prescription in `title` or `card`. Forbidden tokens (case-insensitive): `API`, `endpoint`, `DB schema`, `frontend component`, `backend service`, `microservice`, `lambda`, `webhook handler`. Spike stories (`scenario_type` set includes only banking-grade-spike) whitelisted. | must-pass | INVEST §N; AP-7.1 |
| I-3 | **Valuable**: `card.so_i_can` (or `card.so_that`) length ≥ 12 chars AND contains ≥1 value-word from set: `complete`, `verify`, `track`, `comply`, `resolve`, `submit`, `receive`, `approve`, `understand`, `recover`, `audit`, `protect`, `reduce`, `prevent`, `enable`. | must-pass | INVEST §V |
| I-4 | **Estimable**: `sizing.story_points ∈ {1,2,3,5,8,13}` OR `sizing.story_points == "TBD_by_TL"` AND `sizing.split_required: true`. | must-pass | INVEST §E |
| I-5 | **Small**: `sizing.story_points ≤ 8` OR `sizing.split_required: true`. 13-SP stories without `split_required: true` fail. | must-pass | INVEST §S; AP-7.3 |
| I-6 | **Testable** (structural): `acceptance_criteria.length ≥ 3` AND every AC well-formed (deeper checks in `gherkin-quality.md`). Stories with `priority: "Could"` / `"Won't"` may have `assessment: insufficient_information` instead — log as should-pass warning. | must-pass M/S; should-pass C/W | INVEST §T |
| I-7 | **DoR completeness**: all 8 `dor_checklist` fields = `true` for Must/Should stories. Could/Won't stories may have `sizing_done: false` AND `dependencies_identified: false`. | must-pass M/S; should-pass C/W | DoR §4 |

## Per-Rule Pseudo-Check

### I-1 Independent
For each `story.dependencies.depends_on[]` entry `dep`:
- If `dep` matches `^EPIC-[A-Z0-9-]+-\\d+$` → must exist in `stories[].id` registry.
- Else → must exist in `processing_metadata.external_dependencies[]`.
- Otherwise → I-1 fails with evidence `{story_id, dep, reason: "phantom_dependency"}`.

### I-2 Negotiable
For each story:
- Concatenate `title + JSON.stringify(card)`; lowercase.
- For each forbidden token, run word-boundary regex; if match → I-2 fails unless story has `scenario_type: spike` only.

### I-3 Valuable
For each story:
- Get `outcome = card.so_i_can ?? card.so_that`.
- Assert `outcome.length >= 12`.
- Assert `outcome` (lowercased) contains ≥1 value-word from set above.
- Otherwise → I-3 fails with `{story_id, outcome, reason: "no_value_word"}`.

### I-4 Estimable
For each story:
- If `sizing.story_points` is integer → assert ∈ Fibonacci set above.
- If string → assert equals `"TBD_by_TL"` AND `sizing.split_required === true`.
- Otherwise → I-4 fails.

### I-5 Small
For each story:
- If `typeof sizing.story_points === "number"` AND `sizing.story_points > 8` AND `sizing.split_required !== true` → I-5 fails.
- 13-SP boundary: allowed only when `split_required: true` AND story's `acceptance_criteria.length ≤ 7`.

### I-6 Testable (structural)
For each story:
- Assert `acceptance_criteria.length >= 3` for Must/Should.
- For Could/Won't, allow `length === 0` only if story has a dedicated assessment field — log warning.

### I-7 DoR completeness
For each story:
- Get `priority`. If Must/Should → all 8 booleans must be `true`.
- If Could/Won't → may have `sizing_done: false`, `dependencies_identified: false`; all others `true`.

## Pass/Fail Interpretation

- **All must-pass rules pass** → case status = `pass`.
- **All must-pass rules pass AND ≥1 should-pass warning** → case status = `pass-with-warnings`.
- **≥1 must-pass rule fails** → case status = `fail`. Accumulate `must_pass_failures: [{rule_id, story_id, evidence}]`.

## Per-Story Report Format

```json
{
  "assertion_file": "invest-compliance.md",
  "story_id": "EPIC-LOAN-2847-1",
  "rule_results": [
    { "rule_id": "I-1", "status": "pass" },
    { "rule_id": "I-2", "status": "pass" },
    { "rule_id": "I-3", "status": "pass" },
    { "rule_id": "I-4", "status": "pass" },
    { "rule_id": "I-5", "status": "pass" },
    { "rule_id": "I-6", "status": "pass" },
    { "rule_id": "I-7", "status": "pass" }
  ]
}
```

## Cross-References

- `references/invest-checklist.md` (canonical INVEST rules + split patterns)
- `references/anti-patterns.md` §7 (AP-7.1 tech-layer split, AP-7.3 AC > 7 unsplit)
- `gherkin-quality.md` (deeper AC quality checks beyond I-6 structural)
- `banking-grade-fields.md` (banking-grade compliance separate from INVEST)
