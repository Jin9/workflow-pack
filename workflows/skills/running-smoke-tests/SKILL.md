---
name: running-smoke-tests
version: 0.1.0
description: >
  Run a small set of critical-path smoke probes against a freshly deployed live
  release and emit a PASS, FAIL, or ERROR sanity gate from real probe results —
  each probe green or red with its measured latency, never an agent assertion.
  Use when asked to run smoke or sanity tests, probe critical paths after a
  deploy, confirm a live release is up on its golden paths, or produce the
  post-deploy smoke gate. Runs in a sandbox via probe runners and reports only; it
  never shifts traffic or changes config. Do NOT use for the full QA suite (use
  executing-qa-test-suite). Do NOT use for post-deploy SLO burn-rate validation
  (use validating-production-slo). Do NOT use for canary-vs-baseline rollout
  analysis (use analyzing-canary-rollout) or to fix a failing release.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: detailed, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
expected_duration_p95_seconds: 120
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Running Smoke Tests

## Purpose

Confirm a freshly deployed **live release** is up and healthy on its
**critical paths** with a small, fast set of smoke probes — a sanity gate, not a
full QA pass. Each probe runs against the live target and is recorded green/red
with its measured latency from a real probe runner, never an agent claim. It
reports only; it never shifts traffic or changes config. A red probe is a fail,
which a release controller can use to hold or roll back.

## When to use this skill

- Use when: a release just deployed and its golden paths must be quickly sanity-
  probed before wider exposure.
- Use when: asked to "run smoke tests", "probe the critical paths post-deploy", or
  "produce the smoke gate with evidence".
- Do NOT use: for the full QA suite (`executing-qa-test-suite`), for post-deploy
  SLO burn-rate validation (`validating-production-slo`), for the canary-vs-
  baseline comparison (`analyzing-canary-rollout`), or to fix a failing release.

## Input contract

Validate against `schemas/input.json`. Required: `probes` (the critical-path
probes/endpoints), `target_env` (the live release to probe), `idempotency_key`.
Optional: `tier`. Stop with `needs-input` if there are no probes or no reachable
live target.

## Procedure

1. **Bind the probes** (`references/smoke.md`): take the supplied critical-path
   probes as the golden set; do not invent paths. Entry: probes + live target.
   Exit: a runnable probe spec.
2. **Run each probe** against `target_env` via the probe runner, capturing the
   observed end-state (not merely HTTP 200 — the expected response) and the
   measured `latency_ms`. Results are read from the runner — **never an
   LLM-asserted green**. If no probe could run, that is an `ERROR`.
3. **Record per-probe results** into `probes[]` with `name`, `green` (bool), and
   `latency_ms`. A probe whose end-state does not match expectation is red.
4. **Apply the gate:** `ERROR` if the probe set could not execute against the
   target; `FAIL` if any probe is red OR the run was too sparse to be a
   meaningful sanity check (banking default: uncertain is not a clean pass); else
   `PASS` with `all_green` true.
5. **Emit** the verdict (Output contract). Stop — a controller or human decides
   on a red gate (hold/roll back); this skill does not shift traffic or change
   config.

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR),
`probes[]{name,green,latency_ms}`, `all_green` (bool), and `audit_id`.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| SM-01 | no probes / unreachable live target | no verdict | needs-input → human-queue |
| SM-02 | probe set could not execute | `ERROR` | human-queue |
| SM-03 | one or more probes red | `FAIL` + probes[] | route to controller (hold/rollback) |
| SM-04 | run too sparse to be a meaningful sanity check | `FAIL` + note | human review |

## Constraints

- DO NOT treat smoke as a full QA pass — it is a fast critical-path sanity gate.
- DO NOT emit a green not backed by a probe result; uncertain → fail (banking).
- DO NOT shift traffic, hold, or roll back — recommend/gate only.
- DO NOT auto-approve; a red gate feeds a named human / release controller.
- DO NOT echo real PII captured in probe responses; redact as
  [PII:REDACTED:CLASS=...].

## References

| Need | Reference |
|------|-----------|
| Critical-path probes, end-state checks, latency capture, gate policy, boundary | `references/smoke.md` |
