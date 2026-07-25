---
name: authoring-e2e-test-suite
version: 0.2.0
description: Derive end-to-end scenarios from hydrated stories AND execute them against a running system in a sandbox via the CI/test runner, surface flaky scenarios by bounded re-run, and emit a PASS, FAIL, or ERROR gate with honest execution provenance (runner vs replay). Use when asked to build and run the e2e suite, turn user journeys or stories into end-to-end scenarios and execute them for SIT or UAT, produce the e2e pass/fail gate with scenario results, or measure the flaky rate. On failure the stage retries once, then parks in the e2e-test-exceptions human queue. Do NOT use to design the QA plan (use planning-banking-tests). Do NOT use to run other levels — backend units (use executing-backend-unit-tests), frontend units (use executing-frontend-unit-tests), or integration (use executing-integration-tests). Do NOT use to write or fix production code.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: detailed, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
expected_duration_p95_seconds: 900
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Authoring the E2E Test Suite

## Purpose

Derive **end-to-end** scenarios from the hydrated stories and execute them
against a running system, then emit the T8 gate with honest execution provenance.
This is the e2e-level execution stage (SIT/UAT): it turns stories into
browser-driven scenarios, runs them in a sandbox via the CI/test runner, surfaces
flaky scenarios by bounded re-run, and emits the verdict for the gate policy
(auto+exception). It derives and executes scenario tests; it never writes or
fixes production code, and a flaky pass is not a pass. When no live runner is
bound (replay), the artifact proves the contract — not a runner-backed
execution — and says so via `execution.mode`.

## When to use this skill

- Use when: user journeys/stories exist and end-to-end scenarios must be derived
  and executed for SIT/UAT to produce a pass/fail gate with scenario results.
- Use when: asked to "build and run the e2e suite", "turn journeys into e2e
  tests", or "produce the e2e gate with the flaky rate".
- Do NOT use: to design the QA plan (`planning-banking-tests`), to run unit levels
  (`executing-backend-unit-tests` / `executing-frontend-unit-tests`), to run
  integration (`executing-integration-tests`), or to fix code.

## Input contract

ADVISORY — documents the assembled stage input; the engine validates workflow input
and stage OUTPUTS only (engine/validation.py). Validate against `schemas/input.json`.
Required: `epics` + `stories` (engine-hydrated from the ba-brief ref-chain;
`story_files` refs retained alongside), `verdict` (qa-validate's suite verdict),
`idempotency_key` (engine-injected). Optional engine-injected: `upstream_artifacts`,
`loop_back_feedback`. The execution target is an **execution-binding capability**
(runtime-binding.yaml), not a JSON field: a missing live runner/target is an
execution `ERROR` routed through retry → human queue, not a contract field. Stop
with `needs-input` if there are no stories to derive from.

**Example (validates against schemas/input.json):**
```json
{
  "epics": [{ "id": "EPIC-AUTH", "title": "Customer authentication" }],
  "story_files": [{ "epic": "EPIC-AUTH", "file": "EPIC-AUTH/STORY-AUTH-01.json" }],
  "stories": [{ "id": "STORY-AUTH-01", "epic_id": "EPIC-AUTH", "title": "Customer logs in" }],
  "verdict": "PASS",
  "idempotency_key": "3f6c0b2e-7a41-4d9b-9c2a-8e5b1f0a4d22"
}
```

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR),
`scenarios[]{name,result,steps_total,steps_failed}` (optional `source_story_ids`
traceability and `evidence_ref` — live runs SHOULD emit them), `flaky_rate`
(= flaky scenarios / executed scenarios; null ONLY for ERROR), `execution{mode:
runner|replay, runner?, evidence_ref?}` (honest provenance — runner mode must name
its runner), and `audit_id`. Schema-enforced invariants: PASS requires an all-pass
scenario set and zero flakiness; FAIL requires at least one failing or flaky
scenario. Procedural invariant: `steps_failed <= steps_total`. `audit_id` is
producer-stamped and deterministic — UUIDv5(HOUSE_NS, "e2e-tests:{idempotency_key}")
with HOUSE_NS = uuid5(NAMESPACE_URL, "https://squad-delivery/audit") — distinct
from the engine's per-attempt execution audit id.

**Example (validates against schemas/output.json):**
```json
{
  "verdict": "PASS",
  "scenarios": [
    { "name": "register-login-checkout", "result": "pass", "steps_total": 12, "steps_failed": 0 }
  ],
  "flaky_rate": 0.0,
  "execution": { "mode": "replay" },
  "audit_id": "84def0d2-df9b-5d04-a02d-ffd9662336b2"
}
```

## Procedure

1. **Derive scenarios** (`references/e2e-suite.md`): from each hydrated story,
   derive an executable end-to-end scenario with explicit steps and assertions,
   recording `source_story_ids`. Entry: stories + a bound execution target. Exit:
   a runnable scenario set.
2. **Execute via the runner.** Run each scenario against the bound target through
   the CI/test runner (e2e/browser driver) — never an LLM-asserted pass. Capture
   per-scenario result, `steps_total`, `steps_failed`, and evidence refs; set
   `execution.mode` honestly (`replay` when no runner is bound).
3. **Surface flaky scenarios** by bounded re-run; compute `flaky_rate` =
   flaky / executed and mark non-deterministic scenarios rather than passing them
   by luck.
4. **Apply the gate:** `PASS` only when there are 0 journey/assertion failures AND
   no scenario is flaky; `FAIL` on any failed scenario, any surfaced flaky
   scenario, or a masked/uncertain result; `ERROR` if the suite could not run
   (flaky_rate null).
5. **Emit** the verdict (Output contract). Stop — per the configured gate
   (auto+exception): `PASS` completes automatically; failures exhaust one retry
   and park in the `e2e-test-exceptions` queue for named-human resolution.
   Optional human-triggered diagnosis may follow; it is not an orchestrated stage.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| EE-01 | no stories to derive from | no verdict | needs-input → human-queue |
| EE-02 | suite cannot execute (no runner bound / target down) | `ERROR`, flaky_rate null | retry ×1 → e2e-test-exceptions queue |
| EE-03 | a journey/assertion fails | `FAIL` + scenarios[] | retry ×1 → e2e-test-exceptions queue |
| EE-04 | flaky scenario surfaced | `FAIL` + flaky_rate | retry ×1 → e2e-test-exceptions queue |
| EE-05 | masked/uncertain result | `FAIL` | retry ×1 → e2e-test-exceptions queue |

## Constraints

- DO NOT write, edit, or fix production code — derive, execute, and report only.
- DO NOT emit a pass not backed by runner results; uncertain is a fail (banking).
- DO NOT pass a flaky scenario; surface it explicitly in `flaky_rate`.
- DO NOT claim runner-backed execution without a bound runner — `execution.mode`
  must say `replay` when replaying corpus evidence; failures need a named human
  in the exceptions queue, PASS completes automatically (auto+exception gate).
- DO NOT run outside the sandbox or reach the network beyond the target env.
- DO NOT echo real PII in scenarios or logs; redact as [PII:REDACTED:CLASS=...].

## References

| Need | Reference |
|------|-----------|
| Deriving scenarios from journeys, e2e runner integration, flaky-rate handling, gate, human layer | `references/e2e-suite.md` |
