---
name: executing-integration-tests
version: 0.2.0
description: Execute integration tests (post-implementation SIT) against a wired-up system in a sandbox via the CI/test runner, verify clean teardown, catch integration defects, and emit a PASS, FAIL, or ERROR gate with honest execution provenance (runner vs replay). Use when asked to run the integration suite, execute SIT after implementation, produce the integration pass/fail gate with evidence, or confirm cross-service flows and clean teardown. On failure the stage retries once, then parks in its named human queue. Do NOT use to design the test plan (use planning-banking-tests). Do NOT use to run other levels — backend units (use executing-backend-unit-tests), frontend units (use executing-frontend-unit-tests), or e2e journeys (use authoring-e2e-test-suite). Do NOT use to write or fix tests or production code.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: detailed, pii_handling: redact, tier_default: T2, tier_adaptable: [T1, T2, T3]}
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
integration defects, and hands the verdict to the gate policy (auto: PASS completes; failures retry once, then park in the integration-test-exceptions queue for named-human resolution). It never
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

ADVISORY — documents the assembled stage input; the engine validates workflow input
and stage OUTPUTS only (engine/validation.py). Validate against `schemas/input.json`.
Required: `files_generated`, `idempotency_key` (engine-injected). FLAT-MERGE
COLLISION: both implementation stages supply `files_generated` and the engine
merges last-writer-wins — **the top-level field is the frontend manifest only**;
load both manifests via `upstream_artifacts["backend-implement"]` and
`upstream_artifacts["frontend-implement"]`. Optional: `integration_test_context`
(workflow-supplied runner context: suite_ref, target_env, runner_profile_ref,
teardown_probe_ref — non-secret). In live runner mode with no context, stop
`needs-input` — file manifests do not identify a runnable SIT environment.

**Example (validates against schemas/input.json):**
```json
{
  "files_generated": [{ "path": "src/api/types.gen.ts" }],
  "idempotency_key": "3f6c0b2e-7a41-4d9b-9c2a-8e5b1f0a4d22",
  "upstream_artifacts": {
    "backend-implement": "../S4a-backend/backend-artifacts.json",
    "frontend-implement": "../S4b-frontend/frontend-artifacts.json"
  }
}
```

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
   gate is auto: PASS completes; failures exhaust one retry and park in the `integration-test-exceptions` queue for named-human resolution. Evidence, not release authorization.

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR),
`totals{executed,passed,failed,skipped}` (executed = passed + failed + skipped),
`teardown_ok` (boolean; null ONLY under ERROR when teardown was not attempted),
`defects[]` (required; [] when none; each carries severity/summary/non-empty
repro, optional test_case_id), `execution{mode: runner|replay}` (required —
runner mode must carry suite_ref/environment/result_ref; replay = corpus
evidence replayed), optional `errors[]` (required non-empty under ERROR), and
`audit_id` — producer-stamped, deterministic: UUIDv5(HOUSE_NS,
"integration-tests:{idempotency_key}") with HOUSE_NS = uuid5(NAMESPACE_URL,
"https://squad-delivery/audit"). Schema-enforced: PASS ⇒ zero failed, ≥1
executed, clean teardown, no defects; ERROR ⇒ errors[] says why.

**Example (validates against schemas/output.json):**
```json
{
  "verdict": "PASS",
  "totals": { "executed": 38, "passed": 38, "failed": 0, "skipped": 0 },
  "teardown_ok": true,
  "defects": [],
  "execution": { "mode": "replay" },
  "audit_id": "37c0ae17-1504-5904-b16f-a5ad2220edcf"
}
```

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| IT-01 | no roster/artifacts or unreachable sandbox | no verdict | needs-input → human-queue |
| IT-02 | suite cannot execute | `ERROR` | human-queue |
| IT-03 | an integration flow fails | `FAIL` + defects[] | retry ×1 → integration-test-exceptions queue (diagnosis is an optional human-triggered follow-on) |
| IT-04 | dirty teardown (leaked state) | `FAIL` + teardown_ok=false | exception → human-queue |
| IT-05 | flaky/non-deterministic results | verdict + defects[] | retry ×1 → integration-test-exceptions queue |

## Constraints

- DO NOT write, edit, or fix tests or production code — execute and report only.
- DO NOT emit a pass not backed by runner results; uncertain is a fail (banking).
- DO NOT pass on a dirty teardown; a leaked environment escalates as an exception.
- DO NOT claim runner-backed execution without a bound runner — the artifact's execution provenance must say replay when replaying corpus evidence; failures need a named human in the queue, PASS completes automatically.
- DO NOT run outside the sandbox or reach the network beyond the target env.
- DO NOT echo real PII in defects or logs; redact as [PII:REDACTED:CLASS=...].

## References

| Need | Reference |
|------|-----------|
| Integration/SIT runner integration, teardown verification, defect capture, gate, human layer | `references/integration-exec.md` |
