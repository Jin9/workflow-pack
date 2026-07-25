# S4c · QA Test Design — planning-banking-tests

**Skill:** `planning-banking-tests 1.0.0` · **gate:** sync conditional-go (L3, QA lead) · **status:** ▶ simulated.

Converts the S1b brief (banking-grade concerns — idempotency, last-item race, audit, PII) into a structured
**test plan**: pyramid allocation, per-story test cases, NFR + compliance tests, a smoke subset, and sign-off
criteria.

## Artifacts
- **`qa-plan.json`** — the `test_plan` contract (boundary `workflows/schemas/qa-plan.json`; skill
  `planning-banking-tests/schemas/output.json`): `output_type: test_plan`, `blocks_qa_execution: false`,
  `frontmatter` (status `ready-for-execution`, tier T2), `strategy` (55/25/12/8 pyramid), `epics` (4),
  `stories` (8, all `complete`), `test_cases` (8, `TC-<EPIC>-NNN`), `smoke_subset` (3), `coverage_matrix`,
  `nfr_tests`, `compliance_tests` (PDPA · PCI_DSS · CPA), `execution_dag`, `environments`, `test_data_specs`,
  `signoff_criteria` (go / conditional-go / no-go), `qa_readiness_checklist`, `processing_metadata`.

> The plan carries no top-level `audit_id` (the skill uses `frontmatter.test_plan_id` = `TP-shoppilot-mvp`).
> The YAML's `[test_roster, signoff_criteria]` map to the skill's `test_cases[]` + `signoff_criteria`.
> The one open NFR target (order-confirm p95, `OQ-3`) is tracked as a conditional-go condition, not a blocker.
