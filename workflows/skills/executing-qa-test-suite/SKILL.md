---
name: executing-qa-test-suite
version: 0.2.0
description: Execute a planned QA test roster against a running system, measure run-system coverage, surface flaky tests, catch live defects, and emit a results-backed PASS, FAIL, or ERROR QA gate with honest execution provenance for the sync QA-lead layer. Use when asked to execute the QA test suite, run the planned test roster on the running system, produce the QA pass/fail gate with evidence, or measure run-system coverage. Runs in a sandbox via a CI/test runner and routes failures to a fixer rather than fixing them. Do NOT use to design the test plan (use planning-banking-tests). Do NOT use to run a single test level in isolation (use the unit/integration/e2e execution skills). Do NOT use to write or fix tests or production code.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: detailed, pii_handling: none, tier_default: T1, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
expected_duration_p95_seconds: 900
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Executing the QA Test Suite

## Purpose

Run the QA roster produced by `planning-banking-tests` against a running system
and emit a results-backed sign-off gate — the **execution** stage that the design
stage deliberately leaves out (it "produces test plans, not test code; never
measures coverage on running systems"). Measures real coverage, surfaces flaky
tests, catches live defects, and hands the verdict to the SYNC qa-lead gate (a named human always reviews this stage's verdict; failures go straight to the qa-validation-pending queue — no retry budget).
Never writes or fixes code.

## When to use this skill

- Use when: a `qa-plan` / test roster exists and must be executed on a running
  system to produce a pass/fail QA gate with evidence.
- Use when: asked to "execute the QA suite", "run the roster", or "produce the QA
  sign-off with coverage".
- Do NOT use: to design the plan (`planning-banking-tests`), to run one level in
  isolation (the unit/integration/e2e execution skills), or to fix code.

## Input contract

ADVISORY — documents the assembled stage input; the engine validates workflow input
and stage OUTPUTS only (engine/validation.py). Validate against `schemas/input.json`.
Required: `output_type` (const `test_plan`) + `blocks_qa_execution` (const `false`)
— the qa-plan discriminator: blocked, partial, and failure plans stop BEFORE
execution — plus `test_cases[]` (the executable roster, TC-… ids),
`signoff_criteria`, and `idempotency_key` (engine-injected). Optional
engine-injected: `upstream_artifacts`, `loop_back_feedback`. The execution target
is an execution-binding capability (runtime-binding.yaml), not a JSON field. Stop
with `needs-input` if the plan carries no executable test cases.

**Example (validates against schemas/input.json):**
```json
{
  "output_type": "test_plan",
  "blocks_qa_execution": false,
  "test_cases": [{ "id": "TC-CHECKOUT-01", "title": "Happy-path checkout" }],
  "signoff_criteria": { "coverage_floor": 0.8 },
  "idempotency_key": "3f6c0b2e-7a41-4d9b-9c2a-8e5b1f0a4d22"
}
```

## Procedure

1. **Plan-Act-Verify** (`references/qa-execution-loop.md`): for each roster item,
   execute against `target_env` via the CI/test runner, capturing real results —
   never an LLM-asserted pass. Entry: a roster + target. Exit: per-item results.
2. **Measure run-system coverage** from the runner report (line/branch), not a
   self-declared figure.
3. **Surface flaky tests** by bounded re-run; mark non-deterministic items rather
   than passing them by luck.
4. **Collect live defects** with reproduction evidence; classify by severity.
5. **Apply the gate:** `FAIL` on any failed required item or unmet
   `signoff_criteria`; `ERROR` if the suite could not run; else `PASS`. Banking
   default: a masked/uncertain result is a fail, not a pass.
6. **Emit** the verdict (Output contract). Stop — failures route to a fixer; the
   stage has a SYNC qa-lead gate (gates.yaml L3): a named human reviews the
   verdict; on failure there is no retry budget — straight to the
   `qa-validation-pending` queue.

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR),
`totals{executed,passed,failed,skipped}` (executed = passed + failed + skipped;
derived from `test_results[]` when records exist), `coverage_measured`, `flaky[]`,
`defects[]` (all three required; every defect carries P1|P2|P3 severity, summary,
non-empty repro), `execution{mode: runner|replay, target_source}` (required —
the GAP-05 honesty marker: replay means corpus evidence replayed, NEVER a
fabricated live execution), optional `test_results[]{test_case_id, result,
attempts?, evidence_ref?}` per-case traceability (live runs SHOULD emit it;
requiring it against the frozen corpus would fabricate per-case evidence —
ledgered), optional `errors[]` (required non-empty under ERROR) and
`unmet_signoff_criteria[]` (FAIL evidence), and `audit_id` — producer-stamped,
deterministic: UUIDv5(HOUSE_NS, "qa-validate:{idempotency_key}") with HOUSE_NS =
uuid5(NAMESPACE_URL, "https://squad-delivery/audit"). Schema-enforced: PASS ⇒
≥1 executed, zero failed, empty flaky/defects, numeric coverage.

**Example (validates against schemas/output.json):**
```json
{
  "verdict": "PASS",
  "totals": { "executed": 142, "passed": 142, "failed": 0, "skipped": 0 },
  "coverage_measured": 0.87,
  "flaky": [],
  "defects": [],
  "execution": { "mode": "replay", "target_source": "reference-corpus" },
  "audit_id": "fee17909-4709-5047-8b62-9e5ccf76e2bb"
}
```

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| QE-01 | no roster / unreachable target | no verdict | needs-input → human-queue |
| QE-02 | suite cannot execute | `ERROR` | human-queue |
| QE-03 | required item fails | `FAIL` + defects[] | qa-validation-pending queue (no retry budget; diagnosis is an optional human-triggered follow-on) |
| QE-04 | flaky/non-deterministic results | verdict + flaky[] | qa-validation-pending queue |

## Constraints

- DO NOT write, edit, or fix tests or production code — execute and report only.
- DO NOT emit a pass not backed by runner results; uncertain → fail (banking).
- DO NOT fabricate execution evidence (GAP-05) — execution.mode must say replay
  when replaying corpus material; the sync qa-lead gate always names its human.
- DO NOT run outside the sandbox or reach the network beyond the target env.

## References

| Need | Reference |
|------|-----------|
| Plan-Act-Verify loop, runner integration, run-system coverage, flaky handling, human layer | `references/qa-execution-loop.md` |
