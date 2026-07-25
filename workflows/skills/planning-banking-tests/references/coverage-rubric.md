# Coverage Rubric — `planning-banking-tests` v1.0.0

> Loaded by `SKILL.md` at **Step 11 (always)**. Sibling docs: `anti-patterns.md`, `markdown-rendering-spec.md`, `test-case-id-rules.md`, `tier-aware-test-policy.md`, `pyramid-allocation-rules.md`.

---

## 1. Purpose

This rubric defines **what counts as covered** for a QA test plan emitted by `planning-banking-tests`. It is the only authority on coverage thresholds; SKILL.md Step 11 evaluates the proposed plan against this rubric and emits `coverage_gaps[]` for every threshold that is not met. The rubric is the contract between the BA brief (scenarios, banking-grade rows, NFR criteria, regulators, PII inventory) and the QA artifact (test cases, NFR tests, compliance tests, test data specs). It deliberately excludes implementation metrics (line %, branch %) — see Section 6.

This rubric must be applied **per workload tier** (T1 / T2 / T3) because the cost of a missed test is non-linear in tier. T1 is banking-core; T2 is customer-facing PII or money-adjacent; T3 is internal or read-only.

---

## 2. Coverage dimensions

The rubric measures five orthogonal dimensions. Every test plan must score every dimension; a dimension that does not apply on a given brief is recorded as `n/a` with justification in `processing_metadata.audit_trace`.

1. **Scenario coverage** — the fraction of BA `acceptance_criteria[]` Gherkin scenarios that have at least one corresponding entry in `test_cases[]`. A test case "covers" a scenario when `test_cases[i].scenario_ref` literally equals the BA `scenario_name` (or matches the scenario's stable id when present).
2. **Banking-grade coverage** — the fraction of BA `banking_grade_applies[]` rows (idempotency, audit, authz, PII, evidence-of-consent, irreversibility, monetary-correctness, ...) that have at least one test case tagged with the corresponding `banking_grade_*` tag in `test_cases[i].tags`.
3. **NFR coverage** — the fraction of BA `success_criteria[]` entries that have at least one NFR test in `nfr_tests[]` carrying the same metric name and an explicit numeric or boolean target.
4. **Compliance coverage** — the fraction of BA `regulatory_dependencies[]` entries that have at least one compliance test in `compliance_tests[]` whose `regulator_code` matches the regulator. For regulators carrying DSAR / retention / breach-notification sub-requirements, each sub-requirement must have its own test.
5. **PII coverage** — the fraction of BA `pii_inventory[]` entries whose protective controls (authz, access-audit, retention, masking) each have at least one corresponding test case.

---

## 3. Rubric thresholds per tier

| Dimension | T1 target | T2 target | T3 target |
|---|---|---|---|
| Scenario | 100% (hard) | 100% (hard) | 90% |
| Banking-grade | 100% (hard) | 100% (hard) | 100% if applicable, else n/a |
| NFR | every `success_criterion` has a numeric or boolean target **and** a test | every numeric `success_criterion` has a test | perf smoke only (one p95 latency + one error-rate test) |
| Compliance | every regulator covered **and** every regulator's DSAR / retention / breach sub-requirement covered where applicable | every regulator covered | if a regulator is named on the brief then it must be covered, else n/a |
| PII | every PII field has authz + access-audit + retention tests | every PII field has authz + retention tests | if PII present then a masking-only test, else n/a |

"Hard" targets cannot be waived by conditional-go. A T1 plan that misses a single banking-grade row produces a P1 gap and `blocks_qa_execution: true`.

T3 thresholds are deliberately lower because T3 workloads are read-only or internal; the cost of a marginal missed scenario is bounded.

---

## 4. Per-story coverage rules

The rubric also applies **per story**, not only in aggregate. A story-level plan passes only if all of the following hold simultaneously:

1. Every BA `acceptance_criteria[i]` scenario for the story has at least one entry in `test_cases[]` with matching `story_id` and `scenario_ref`.
2. Every `banking_grade_applies[]` row that the story inherits has a corresponding tagged test case.
3. The story has at least **one** happy-path test (`scenario_type == "happy"`), at least **one** error-path test (`scenario_type == "error"`), and at least **one** banking-grade test (`tags` contains any `banking_grade_*`).
4. If the story carries any open question (`open_questions[]` referenced in its scenarios), the affected test case sets `target: "TBD pending OQ-N"` and lists `blocking_oqs[]` (see `anti-patterns.md` AP-Q9).
5. If the story touches PII, at least one test asserts masking in logs / responses and at least one asserts access-audit emission.

Story-level rule (3) is enforced even on stories whose BA scenarios are all happy-path: SKILL.md Step 6 generates the missing error and banking-grade tests from the brief's banking_grade_applies rows.

---

## 5. Coverage gap severity assignment

Every dimension threshold that fails produces an entry in `coverage_gaps[]`. Severity is assigned by the table below; the renderer (`scripts/render_test_plan_tree.py`) writes the gap list to `08-coverage-gaps.md` and surfaces P1 gaps in `README.md` and `00-STRATEGY.md`.

| Severity | Meaning | Effect on sign-off |
|---|---|---|
| P1 | Blocks sign-off. `blocks_qa_execution: true`. Examples: scenario coverage <100% on T1/T2; banking-grade <100% on T1/T2; PII field without authz test on T1/T2; regulator without test on T1; cannot ship. | Hard block. Invariant 1 (see `schemas/output.json`) prohibits `status: ready-for-execution`. |
| P2 | Conditional-go acceptable with documented exception. Examples: NFR numeric target deferred to next iteration on T2; T3 scenario coverage 88% vs 90%. | Soft block. Requires Sign-off authority approval recorded in `signoff_criteria.exceptions[]`. |
| P3 | Informational. Examples: T3 PII masking-only test missing on a single internal field; non-numeric NFR criterion lacks a boolean target. | No block. Surfaced for transparency. |

A single dimension can produce multiple gap entries (one per missing item). The severity is computed **per item**, not per dimension.

---

## 6. What's NOT in the rubric

The following metrics are explicitly **out of scope** for this rubric. SKILL.md Step 11 must not consume them and the renderer must not surface them:

1. **Line coverage %, branch coverage %, statement coverage %** — these are runtime metrics from a test execution platform, not a property of the test plan. Treating them as targets is **AP-Q5 (coverage-target obsession)** in `anti-patterns.md`. The plan can recommend instrumenting them but must not assign thresholds.
2. **Implementation-detail assertions** — tests that assert a private function was called by name, or that a specific database query ran. These are **AP-Q2** anti-patterns. The rubric measures observable-behavior coverage only (state change, response, audit event, notification, side-effect).
3. **Test code authoring** — code-block output is forbidden. See **AP-Q1**.
4. **Defect counts / pass rates from prior runs** — those belong to the QA execution stage, not test design.

---

## 7. Auditing the rubric

Every rubric evaluation must record its result in `processing_metadata.audit_trace`. The audit entry has fixed shape:

```
{
  "step": "11-coverage-rubric",
  "dimension": "scenario" | "banking-grade" | "nfr" | "compliance" | "pii",
  "tier": "T1" | "T2" | "T3",
  "threshold": "<from Section 3>",
  "observed": "<measured fraction or count>",
  "passed": true | false,
  "gaps_emitted": ["GAP-001", "GAP-002", ...]
}
```

One entry per dimension per tier scope (top-level + per-epic if epics carry distinct tiers). This makes the rubric application reproducible: re-running the skill on the same brief with the same idempotency key produces byte-identical audit entries (see `markdown-rendering-spec.md` Section 7 on determinism).

The audit trace is the **only** authoritative record of which thresholds were applied; downstream auditors (Stage 5 sign-off, regulator inspection) must read this trace rather than re-derive thresholds from the rubric document.

---

## 8. Cross-references

- SKILL.md Step 11 — calls into this rubric and writes `coverage_gaps[]`.
- `anti-patterns.md` — AP-Q5 (coverage-target obsession), AP-Q2 (implementation-detail tests), AP-Q9 (unresolved OQs).
- `tier-aware-test-policy.md` — defines T1/T2/T3 semantics that drive the thresholds in Section 3.
- `pyramid-allocation-rules.md` — defines the unit / integration / e2e split used when scenario coverage is measured.
- `markdown-rendering-spec.md` — renderer for `08-coverage-gaps.md` and audit trace serialization.
