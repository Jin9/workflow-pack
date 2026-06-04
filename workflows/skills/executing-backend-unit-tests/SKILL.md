---
name: executing-backend-unit-tests
version: 0.1.0
description: >
  Execute backend unit tests against built backend artifacts in a sandbox via the
  CI/test runner, measure real line coverage, surface flaky tests, catch unit-level
  defects, and emit a runner-backed PASS, FAIL, or ERROR gate that feeds a human
  verification layer. Use when asked to run the backend unit suite, execute Go unit
  tests pre-merge in CI, produce the backend unit pass/fail gate with coverage
  evidence, or check that backend units meet the coverage threshold. Routes failures
  to a fixer rather than fixing them. Do NOT use to design the test plan (use
  planning-banking-tests). Do NOT use to run other levels — frontend units (use
  executing-frontend-unit-tests), integration (use executing-integration-tests), or
  e2e (use authoring-e2e-test-suite). Do NOT use to write or fix tests or
  production code.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: detailed, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
expected_duration_p95_seconds: 420
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Executing Backend Unit Tests

## Purpose

Run the backend **unit** suite against built backend artifacts and emit a
runner-backed sign-off gate. This is the unit-level execution stage: it executes
Go (and equivalent backend) unit tests in a sandbox via the CI/test runner,
reads real line coverage from the runner report, surfaces flaky tests, and hands
the verdict to a human verification layer. It never writes or fixes code, and it
never claims a coverage number the runner did not measure.

## When to use this skill

- Use when: built backend artifacts exist and the backend unit suite must run
  pre-merge in CI to produce a pass/fail gate with coverage evidence.
- Use when: asked to "run the backend unit tests", "execute Go unit tests", or
  "produce the backend unit gate with coverage".
- Do NOT use: to design the plan (`planning-banking-tests`), to run frontend
  units (`executing-frontend-unit-tests`), integration
  (`executing-integration-tests`), or e2e (`authoring-e2e-test-suite`), or to fix
  code.

## Input contract

Validate against `schemas/input.json`. Required: `backend_artifacts` (the Go/test
file manifest of the built backend), `target_env` (the sandbox to run in),
`idempotency_key`. Optional: `coverage_threshold` (default 0.80), `tier`. Stop
with `needs-input` if there are no backend artifacts or no reachable sandbox.

## Procedure

1. **Resolve and stage** (`references/backend-unit-exec.md`): load
   `backend_artifacts`, set up the sandbox `target_env`. Entry: artifacts + a
   reachable sandbox. Exit: a runnable backend test set.
2. **Execute via the runner.** Run the backend unit suite through the CI/test
   runner — never an LLM-asserted pass. Capture per-test results with repro.
3. **Measure coverage from the runner report** (line), not a self-declared
   figure. If coverage cannot be measured, say so and do not infer a pass.
4. **Surface flaky tests** by bounded re-run; mark non-deterministic items rather
   than passing them by luck.
5. **Apply the gate:** `PASS` only when `failed` is 0 AND measured coverage is at
   least `coverage_threshold` (default 0.80); `FAIL` on any failed test, an unmet
   threshold, or a masked/uncertain result; `ERROR` if the suite could not run.
6. **Emit** the verdict (Output contract). Stop — failures route to a fixer; the
   gate feeds a **human verification layer**, never auto-approves.

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR),
`totals{executed,passed,failed,skipped}`, `coverage_measured` (a number from 0 to
1, or null), `failures[]{test,summary,repro}`, and `audit_id`.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| BU-01 | no artifacts / unreachable sandbox | no verdict | needs-input → human-queue |
| BU-02 | suite cannot execute | `ERROR` | human-queue |
| BU-03 | a unit test fails | `FAIL` + failures[] | route to progressive-bug-hunter |
| BU-04 | coverage under threshold or unmeasurable | `FAIL` | flag for human verification |
| BU-05 | flaky/non-deterministic results | verdict + flaky in failures[] | flag for human verification |

## Constraints

- DO NOT write, edit, or fix tests or production code — execute and report only.
- DO NOT emit a pass not backed by runner results; uncertain is a fail (banking).
- DO NOT report a self-declared coverage number; read it from the runner.
- DO NOT auto-approve; the gate feeds a named human verification layer.
- DO NOT run outside the sandbox or reach the network beyond the target env.
- DO NOT echo real PII in failures or logs; redact as [PII:REDACTED:CLASS=...].

## References

| Need | Reference |
|------|-----------|
| Backend unit runner integration, line coverage, flaky handling, threshold gate, human layer | `references/backend-unit-exec.md` |
