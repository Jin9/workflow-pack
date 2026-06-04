---
name: authoring-e2e-test-suite
version: 0.1.0
description: >
  Derive end-to-end scenarios from user journeys or stories AND execute them
  against a running system in a sandbox via the CI/test runner, surface flaky
  scenarios by bounded re-run, and emit a runner-backed PASS, FAIL, or ERROR gate
  that feeds a human verification layer. Use when asked to build and run the e2e
  suite, turn user journeys or stories into end-to-end scenarios and execute them
  for SIT or UAT, produce the e2e pass/fail gate with scenario results, or measure
  the flaky rate. Routes failures to a fixer rather than fixing them. Do NOT use to
  design the QA plan (use planning-banking-tests). Do NOT use to run other levels —
  backend units (use executing-backend-unit-tests), frontend units (use
  executing-frontend-unit-tests), or integration (use executing-integration-tests).
  Do NOT use to write or fix production code.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: detailed, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
expected_duration_p95_seconds: 900
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Authoring the E2E Test Suite

## Purpose

Derive **end-to-end** scenarios from user journeys or stories and execute them
against a running system, then emit a runner-backed sign-off gate. This is the
e2e-level execution stage (SIT/UAT): it turns journeys into browser-driven
scenarios, runs them in a sandbox via the CI/test runner, surfaces flaky scenarios
by bounded re-run, and hands the verdict to a human verification layer. It derives
and executes scenario tests; it never writes or fixes production code, and a flaky
pass is not a pass.

## When to use this skill

- Use when: user journeys/stories exist and end-to-end scenarios must be derived
  and executed for SIT/UAT to produce a pass/fail gate with scenario results.
- Use when: asked to "build and run the e2e suite", "turn journeys into e2e
  tests", or "produce the e2e gate with the flaky rate".
- Do NOT use: to design the QA plan (`planning-banking-tests`), to run unit levels
  (`executing-backend-unit-tests` / `executing-frontend-unit-tests`), to run
  integration (`executing-integration-tests`), or to fix code.

## Input contract

Validate against `schemas/input.json`. Required: `journeys` (the user journeys or
stories to derive scenarios from), `target_env` (the running system/sandbox to
test), `idempotency_key`. Optional: `tier`. Stop with `needs-input` if there are
no journeys or no reachable target.

## Procedure

1. **Derive scenarios** (`references/e2e-suite.md`): from each journey/story,
   derive an executable end-to-end scenario with explicit steps and assertions.
   Entry: journeys + a reachable target. Exit: a runnable scenario set.
2. **Execute via the runner.** Run each scenario against `target_env` through the
   CI/test runner (e2e/browser driver) — never an LLM-asserted pass. Capture
   per-scenario result, `steps_total`, and `steps_failed`.
3. **Surface flaky scenarios** by bounded re-run; compute a `flaky_rate` and mark
   non-deterministic scenarios rather than passing them by luck.
4. **Apply the gate:** `PASS` only when there are 0 journey/assertion failures AND
   no scenario is flaky; `FAIL` on any failed scenario, any surfaced flaky
   scenario, or a masked/uncertain result; `ERROR` if the suite could not run.
5. **Emit** the verdict (Output contract). Stop — failures route to a fixer; the
   gate feeds a **human verification layer**, never auto-approves.

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR),
`scenarios[]{name,result,steps_total,steps_failed}`, `flaky_rate` (a number from 0
to 1), and `audit_id`.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| EE-01 | no journeys / unreachable target | no verdict | needs-input → human-queue |
| EE-02 | suite cannot execute | `ERROR` | human-queue |
| EE-03 | a journey/assertion fails | `FAIL` + scenarios[] | route to progressive-bug-hunter |
| EE-04 | flaky scenario surfaced | `FAIL` + flaky_rate | flag for human verification |
| EE-05 | masked/uncertain result | `FAIL` | flag for human verification |

## Constraints

- DO NOT write, edit, or fix production code — derive, execute, and report only.
- DO NOT emit a pass not backed by runner results; uncertain is a fail (banking).
- DO NOT pass a flaky scenario; surface it explicitly in `flaky_rate`.
- DO NOT auto-approve; the gate feeds a named human verification layer.
- DO NOT run outside the sandbox or reach the network beyond the target env.
- DO NOT echo real PII in scenarios or logs; redact as [PII:REDACTED:CLASS=...].

## References

| Need | Reference |
|------|-----------|
| Deriving scenarios from journeys, e2e runner integration, flaky-rate handling, gate, human layer | `references/e2e-suite.md` |
