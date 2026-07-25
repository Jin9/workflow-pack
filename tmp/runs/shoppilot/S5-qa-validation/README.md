# S5 · QA Validation — executing-qa-test-suite

**Skill:** `executing-qa-test-suite 0.1.0` · **gate:** sync (L3, QA lead) · **status:** ▶ simulated.

Executes the S4c test roster on the running system and emits pass/fail **evidence** that gates the release.

## Artifacts
- **`qa-evidence.json`** — the contract (`workflows/schemas/qa-evidence.json`): **verdict `PASS`**,
  `totals` (142 executed / 142 passed / 0 failed / 0 skipped), `coverage_measured` 0.87, `flaky: []`,
  `defects: []`, `audit_id`.

> The built skill emits `totals`/`coverage_measured`/`defects` as the evidence (the YAML's literal `evidence`
> field is not a built output). A clean PASS releases the S6 handoff gate.
