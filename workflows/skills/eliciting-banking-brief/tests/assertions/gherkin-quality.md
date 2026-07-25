# Gherkin Quality Assertions

> Per-rule checklist that every Gherkin acceptance criterion in `stories[].acceptance_criteria[]` meets BDD / testability rules per `references/ba-best-practices.md` §2 and C29-C30.

## Purpose

Schema validation (`schemas/output.json`) checks structural shape: `scenario_name`, `scenario_type`, `given[]` ≥1, `when` string, `then[]` ≥1. This file enforces **content quality**: concrete values, single-action `When`, observable `Then`, scenario-type coverage, banking-grade scenario emission.

## Severity Semantics

- **must-pass** = test case fails on violation.
- **should-pass** = warning logged; case passes-with-warnings.
- **conditional must-pass** = depends on banking-grade row status; only triggers must-pass when condition holds.

## Rule Table

| # | Rule | Severity | Source |
|---|---|---|---|
| G-1 | **Format**: every AC has `scenario_name`, `given[]` (≥1), `when` (string), `then[]` (≥1). | must-pass | Gherkin §; schema |
| G-2 | **Single-action `When` (AP-8.2)**: `when` has no `\band\b` joining two verb phrases. Reject regex `\b(and\|&)\b\s+\w+(s\|es\|ed\|ing)?\b` followed by second verb phrase. | must-pass | AP-8.2; C30 |
| G-3 | **Concrete values**: each AC has ≥1 concrete value (integer/decimal, quoted string, proper noun, ISO date, regex pattern) across `given + when + then`. | must-pass | AP-8.1, AP-8.3, C30 |
| G-4 | **Observable `Then` (AP-8.3)**: every `then` matches observable-outcome pattern. Reject `is happy`, `is satisfied`, `is improved`, `handles correctly`, `is compliant`, `is fast`. | must-pass | AP-8.3 |
| G-5 | **No vague `Given` (AP-8.1)**: no bare `Given the system`, `Given a user`, `Given the application`. Must reference concrete role + state. | must-pass | AP-8.1 |
| G-6 | **Scenario-type coverage (C29)**: per story, multiset has ≥1 `happy`, ≥1 `error` OR `edge_case`, ≥1 `banking_grade_*`. | must-pass when any banking-grade row `applies`; should-pass otherwise | C29; AP-8.4 |
| G-7 | **Tipping-off scenario**: when `banking_grade_concerns.tipping_off.status == "applies"`, ≥1 AC with `scenario_type: banking_grade_tipping_off` whose `then[]` includes deny-list scan. | conditional must-pass | C20, AP-4.4, FM-06 |
| G-8 | **Idempotency replay**: when `banking_grade_concerns.idempotency.status == "applies"`, ≥1 AC with `scenario_type: banking_grade_idempotency`: `given` previous identical request + key; `when` replayed; `then` no duplicate effect + no duplicate audit. | conditional must-pass | C18, AP-4.3 |
| G-9 | **Testability**: every `then` references concrete observable AND no soft-language tokens (`happy`, `satisfied`, `fast`, `improved`, `compliant`, `consistent`) within 30 chars of unmeasurable predicate. | must-pass | quality heuristic; AP-8.3, AP-4.2 |

## Per-Rule Pseudo-Check

### G-1 Format
For each AC: assert keys `scenario_name`, `scenario_type`, `given`, `when`, `then` all present and well-typed per schema. Schema-validated; this is a redundant guard.

### G-2 Single-action `When`
For each AC's `when`:
- Tokenize on whitespace.
- Apply regex `\b(and|&)\b\s+(?:the\s+)?\w+\s+(?:is|are|was|were|gets?|performs?|sends?|clicks?|submits?|validates?|fires?|processes?)`.
- On match → G-2 fails with `{story_id, scenario_name, when, evidence: "multi-action"}`.

### G-3 Concrete values
For each AC:
- Concatenate `given[].join(' ') + ' ' + when + ' ' + then[].join(' ')`.
- Test for ≥1 of: integer literal `\b\d+\b`, decimal `\b\d+\.\d+\b`, quoted string `"[^"]+"`, proper noun (capitalized non-sentence-start word), ISO date `\d{4}-\d{2}-\d{2}`, regex pattern.
- On no match → G-3 fails.

### G-4 Observable `Then`
For each AC, for each `then[i]`:
- Lowercase.
- Test against forbidden patterns: `\bis (happy|satisfied|improved|compliant|consistent|fast)\b`, `\bhandles correctly\b`, `\bworks (well|properly)\b`.
- On match → G-4 fails with `{story_id, scenario_name, then: then[i]}`.

### G-5 Vague `Given`
For each AC, for each `given[i]`:
- Lowercase, trim leading "Given ".
- Test against forbidden bare patterns: `^(the system|a user|the application|the user|some data)\s*$` AND no additional state-naming clause.
- On match → G-5 fails.

### G-6 Scenario-type coverage
For each story:
- Collect `scenario_type` multiset across `acceptance_criteria[]`.
- Assert `happy ∈ multiset` AND (`error ∈ multiset` OR `edge_case ∈ multiset`).
- If any `banking_grade_concerns.*.status == "applies"` → must-pass on banking-grade scenario presence.
- Else → should-pass (warning logged).

### G-7 Tipping-off scenario (conditional must-pass)
For each story where `banking_grade_concerns.tipping_off.status == "applies"`:
- Assert ≥1 AC has `scenario_type == "banking_grade_tipping_off"`.
- Assert that AC's `then[].join(' ')` (lowercased) includes ≥1 of: `forbidden terms`, `does not contain`, `non-tipping`, `safe phrase`, `deny-list scan`.
- Otherwise → G-7 fails. Cross-check with `banking-grade-fields.md` B-7.

### G-8 Idempotency replay (conditional must-pass)
For each story where `banking_grade_concerns.idempotency.status == "applies"`:
- Assert ≥1 AC has `scenario_type == "banking_grade_idempotency"`.
- Assert that AC's `given[].join(' ')` mentions `idempotency_key` OR `same request` OR `previous request`.
- Assert that AC's `when` mentions `replay` OR `replayed` OR `same key`.
- Assert that AC's `then[].join(' ')` mentions `no duplicate` AND (`audit` OR `effect` OR `side effect`).
- Otherwise → G-8 fails.

### G-9 Testability
For each AC, for each `then[i]`:
- Find positions of soft-language tokens (`happy`, `satisfied`, `fast`, `improved`, `compliant`, `consistent`).
- For each hit, look within ±30 chars for measurable predicate (number, ISO date, named entity, regex output, payload field, audit event name).
- If no measurable predicate found → G-9 fails.

## Pass/Fail Interpretation

- **>5% of ACs fail any must-pass rule** → case fails.
- **≤5% AC failure** OR only should-pass warnings → `pass-with-warnings`.
- **All must-pass pass + conditional must-pass conditions all satisfied** → `pass`.

## Anti-Pattern Detection (Summary)

| Rule | Catches | AP / FM |
|---|---|---|
| G-2 | Multi-action `When` | AP-8.2 |
| G-3 | Vague placeholders, missing concrete values | AP-8.1, AP-8.3, C30 |
| G-4 | Subjective `Then` | AP-8.3 |
| G-5 | Vague `Given` | AP-8.1 |
| G-6 | Missing scenario-type coverage | C29, AP-8.4 |
| G-7 | Missing tipping-off scenario | AP-4.4, FM-06 |
| G-8 | Missing idempotency-replay | AP-4.3 |
| G-9 | Non-testable predicates | AP-4.2 |

## Cross-References

- `references/gherkin-templates.md` (canonical templates for banking-grade scenarios)
- `references/anti-patterns.md` §8 (AC quality)
- `invest-compliance.md` I-6 (structural testability — this file is the content check)
- `banking-grade-fields.md` B-7, B-8 (cross-checks)
