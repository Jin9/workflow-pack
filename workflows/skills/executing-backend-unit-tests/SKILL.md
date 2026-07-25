---
name: executing-backend-unit-tests
version: 0.2.0
description: Execute backend unit tests against built backend artifacts in a sandbox via the CI/test runner, measure real line coverage, surface flaky tests, catch unit-level defects, and emit a PASS, FAIL, or ERROR gate with honest execution provenance (runner vs replay). Use when asked to run the backend unit suite, execute Go unit tests pre-merge in CI, produce the backend unit pass/fail gate with coverage evidence, or check that backend units meet the coverage threshold. On failure the stage retries once, then parks in its named human queue. Do NOT use to design the test plan (use planning-banking-tests). Do NOT use to run other levels — frontend units (use executing-frontend-unit-tests), integration (use executing-integration-tests), or e2e (use authoring-e2e-test-suite). Do NOT use to write or fix tests or production code.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: detailed, pii_handling: redact, tier_default: T2, tier_adaptable: [T1, T2, T3]}
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
the verdict to the gate policy (auto: PASS completes; failures retry once, then park in the backend-unit-test-failures queue for named-human resolution). It never writes or fixes code, and it
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

ADVISORY — documents the assembled stage input; the engine validates workflow input
and stage OUTPUTS only (engine/validation.py). Validate against `schemas/input.json`.
Required: `files_generated` + `tests_generated` (backend-implement's manifests;
upstream `coverage_pct` is generation-time metadata, never gate evidence),
`idempotency_key` (engine-injected). Optional engine-injected: `upstream_artifacts`,
`loop_back_feedback`. The runner target and the 0.80 coverage floor are
execution-binding configuration (gate-runners.yaml), not JSON inputs. Stop with
`needs-input` if the manifests carry no Go test files.

**Example (validates against schemas/input.json):**
```json
{
  "files_generated": [{ "path": "services/auth/app/handlers/login.go" }],
  "tests_generated": [{ "path": "services/auth/app/handlers/login_test.go" }],
  "idempotency_key": "3f6c0b2e-7a41-4d9b-9c2a-8e5b1f0a4d22"
}
```

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
   gate is auto: PASS completes; failures exhaust one retry and park in the `backend-unit-test-failures` queue for named-human resolution. Evidence, not release authorization.

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR),
`totals{executed,passed,failed,skipped}` (executed = passed + failed + skipped),
`failures[]` (required; [] on PASS; items are runner-emitted strings — what the
live script executor emits today — or canonical `{test,summary,repro}` objects),
and `audit_id`. Optional until the ledgered runner enrichment lands:
`coverage_measured` (when present, PASS requires ≥ 0.80), `flaky[]` (when
present, PASS requires []), `execution{mode: runner|replay, target_source:
current-run|reference-corpus}` — the replay corpus carries
`{replay, reference-corpus}`: the gate tests the REFERENCE CORPUS code, not
freshly generated output. Schema-enforced: PASS ⇒ zero failed, ≥1 executed,
empty failures. `audit_id` is producer-stamped, deterministic —
UUIDv5(HOUSE_NS, "backend-unit-tests:{idempotency_key}") with HOUSE_NS =
uuid5(NAMESPACE_URL, "https://squad-delivery/audit") — distinct from the
engine's per-attempt execution audit id (the live executor currently stamps the
attempt id; the correction is ledgered).

**Example (validates against schemas/output.json):**
```json
{
  "verdict": "PASS",
  "totals": { "executed": 96, "passed": 96, "failed": 0, "skipped": 0 },
  "failures": [],
  "audit_id": "15d966fa-68b1-5ea7-aefa-b3ef30ab0a76"
}
```

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| BU-01 | no artifacts / unreachable sandbox | no verdict | needs-input → human-queue |
| BU-02 | suite cannot execute | `ERROR` | human-queue |
| BU-03 | a unit test fails | `FAIL` + failures[] | retry ×1 → backend-unit-test-failures queue (diagnosis is an optional human-triggered follow-on) |
| BU-04 | coverage under threshold or unmeasurable | `FAIL` | retry ×1 → backend-unit-test-failures queue |
| BU-05 | flaky/non-deterministic results | verdict + flaky in failures[] | retry ×1 → backend-unit-test-failures queue |

## Constraints

- DO NOT write, edit, or fix tests or production code — execute and report only.
- DO NOT emit a pass not backed by runner results; uncertain is a fail (banking).
- DO NOT report a self-declared coverage number; read it from the runner.
- DO NOT claim runner-backed execution without a bound runner — the artifact's execution provenance must say replay when replaying corpus evidence; failures need a named human in the queue, PASS completes automatically.
- DO NOT run outside the sandbox or reach the network beyond the target env.
- DO NOT echo real PII in failures or logs; redact as [PII:REDACTED:CLASS=...].

## References

| Need | Reference |
|------|-----------|
| Backend unit runner integration, line coverage, flaky handling, threshold gate, human layer | `references/backend-unit-exec.md` |
