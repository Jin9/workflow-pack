---
name: executing-integration-tests
version: 0.1.0
description: >
  Execute integration tests (post-implementation SIT) against a wired-up system in
  a sandbox via the CI/test runner, verify clean teardown, catch integration
  defects, and emit a runner-backed PASS, FAIL, or ERROR gate that feeds a human
  verification layer. Use when asked to run the integration suite, execute SIT after
  implementation, produce the integration pass/fail gate with evidence, or confirm
  cross-service flows and clean teardown. Routes failures to a fixer rather than
  fixing them. Do NOT use to design the test plan (use planning-banking-tests). Do
  NOT use to run other levels — backend units (use executing-backend-unit-tests),
  frontend units (use executing-frontend-unit-tests), or e2e journeys (use
  authoring-e2e-test-suite). Do NOT use to write or fix tests or production code.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: detailed, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
expected_duration_p95_seconds: 600
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Executing Integration Tests

## Purpose

Run the **integration** suite (post-implementation system integration testing,
SIT) against a wired-up system and emit a runner-backed sign-off gate. This is the
integration-level execution stage: it executes cross-service flows in a sandbox
via the CI/test runner, verifies clean teardown of the test environment, catches
integration defects, and hands the verdict to a human verification layer. It never
writes or fixes code, and a dirty teardown is an exception, not a pass.

## When to use this skill

- Use when: implementation is complete and the integration suite must run as SIT
  to produce a pass/fail gate with defect evidence and a teardown check.
- Use when: asked to "run the integration tests", "execute SIT", or "confirm
  cross-service flows with clean teardown".
- Do NOT use: to design the plan (`planning-banking-tests`), to run unit levels
  (`executing-backend-unit-tests` / `executing-frontend-unit-tests`), to run e2e
  journeys (`authoring-e2e-test-suite`), or to fix code.

## Input contract

Validate against `schemas/input.json`. Required: either `test_roster` (the planned
integration suite) OR `artifacts` (the built system to derive runs from),
`target_env` (the sandbox to run in), `idempotency_key`. Optional: `tier`. Stop
with `needs-input` if there is neither a roster nor artifacts, or no reachable
sandbox.

## Procedure

1. **Resolve and stage** (`references/integration-exec.md`): load `test_roster`
   or `artifacts`, set up the sandbox `target_env` with its dependencies. Entry:
   a roster/artifacts + a reachable sandbox. Exit: a runnable integration set.
2. **Execute via the runner.** Run the integration suite through the CI/test
   runner — never an LLM-asserted pass. Capture per-flow results with repro.
3. **Verify teardown.** After the run, confirm the sandbox environment tears down
   cleanly (no leaked state, fixtures, or connections). Record `teardown_ok`.
4. **Collect defects** with reproduction evidence; classify by severity.
5. **Apply the gate:** `PASS` only when `failed` is 0 AND `teardown_ok` is true;
   `FAIL` on any failed flow or a masked/uncertain result; a dirty teardown is an
   exception that escalates; `ERROR` if the suite could not run.
6. **Emit** the verdict (Output contract). Stop — failures route to a fixer; the
   gate feeds a **human verification layer**, never auto-approves.

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR),
`totals{executed,passed,failed,skipped}`, `teardown_ok` (boolean),
`defects[]{severity,summary,repro}`, and `audit_id`.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| IT-01 | no roster/artifacts or unreachable sandbox | no verdict | needs-input → human-queue |
| IT-02 | suite cannot execute | `ERROR` | human-queue |
| IT-03 | an integration flow fails | `FAIL` + defects[] | route to progressive-bug-hunter |
| IT-04 | dirty teardown (leaked state) | `FAIL` + teardown_ok=false | exception → human-queue |
| IT-05 | flaky/non-deterministic results | verdict + defects[] | flag for human verification |

## Constraints

- DO NOT write, edit, or fix tests or production code — execute and report only.
- DO NOT emit a pass not backed by runner results; uncertain is a fail (banking).
- DO NOT pass on a dirty teardown; a leaked environment escalates as an exception.
- DO NOT auto-approve; the gate feeds a named human verification layer.
- DO NOT run outside the sandbox or reach the network beyond the target env.
- DO NOT echo real PII in defects or logs; redact as [PII:REDACTED:CLASS=...].

## References

| Need | Reference |
|------|-----------|
| Integration/SIT runner integration, teardown verification, defect capture, gate, human layer | `references/integration-exec.md` |
