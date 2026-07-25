---
name: running-smoke-tests
version: 0.2.0
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
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: detailed, pii_handling: redact, tier_default: T2, tier_adaptable: [T1, T2, T3]}
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

`schemas/input.json` is **ENFORCED** — the engine validates the ASSEMBLED payload
against it before this stage runs (fail-closed, exactly like output validation);
it documents the POST-adapter payload assembled at stage `smoke-tests`. Required: `receipt_id` (picked from release-handoff — the S6
deployment receipt) and the engine-injected `idempotency_key`. Optional
engine-injected: `upstream_artifacts`, `loop_back_feedback`.

**Receipt resolution:** resolve `receipt_id` through the read-only deployment
registry into its deployment target and the receipt's APPROVED smoke manifest —
the probe set and endpoints come from the receipt, never invented, and any
endpoint outside the receipt's approved target is rejected. An unknown receipt
or a missing approved manifest is a preflight `needs-input` (distinct from a
runner-time ERROR).

**Example (validates against schemas/input.json):**

```json
{
  "receipt_id": "RCPT-shoppilot-20260607-0001",
  "idempotency_key": "req-2026-07-12-shoppilot-001"
}
```

## Procedure

1. **Bind the probes** (`references/smoke.md`): resolve the receipt into its
   target + approved smoke manifest and take that as the golden set; do not
   invent paths. Entry: a resolved receipt. Exit: a runnable probe spec.
2. **Run each probe** against `target_env` via the probe runner, capturing the
   observed end-state (not merely HTTP 200 — the expected response) and the
   measured `latency_ms`. Results are read from the runner — **never an
   LLM-asserted green**. If no probe could run, that is an `ERROR`.
3. **Record per-probe results** into `probes[]` with `name`, `executed`,
   `green`, optional `latency_ms`, and a redacted `reason` for every non-green
   row. Rows carry only normalized, redacted end-state summaries or offline
   evidence references — never response bodies, credentials, or captured
   identifiers. A probe whose end-state does not match expectation is red.
4. **Apply the gate:** `ERROR` if the probe set could not execute against the
   target; `FAIL` if any probe is red OR the run was too sparse to be a
   meaningful sanity check (banking default: uncertain is not a clean pass); else
   `PASS` with `all_green` true.
5. **Emit** the verdict with the receipt binding and execution provenance
   (Output contract): `receipt_id` echoes the input unchanged, and `execution`
   records `runner` (real probes: runner + evidence_ref + report_sha256) vs
   `replay` (byte-verbatim reference corpus — no probe ran). Stop — a named
   human / release controller decides on a red gate (hold/roll back); this
   skill does not shift traffic or change config.

## Output contract

Validate against `schemas/output.json`. Required: `verdict` (PASS|FAIL|ERROR),
`receipt_id` (echoed unchanged), `probes[]` (every manifest probe; items require
`name`/`executed`/`green`; non-green rows require a redacted `reason`;
`latency_ms` optional-nullable), `all_green`, `execution`, and `audit_id`;
`errors[]` required non-empty on ERROR. Conditionals: PASS ⇒ every probe
executed AND green ∧ all_green true; FAIL ⇒ ≥1 executed ∧ (≥1 non-green ∨
unexecuted) ∧ all_green false; ERROR ⇒ no probe executed ∧ all_green false.

`audit_id` (live): `UUIDv5(HOUSE_NS, "smoke-tests:{idempotency_key}")`,
`HOUSE_NS = uuid5(NAMESPACE_URL, "https://squad-delivery/audit")` — distinct
from the engine's per-attempt audit id; corpus ids grandfathered.

**Example (validates against schemas/output.json):**

```json
{
  "verdict": "PASS",
  "receipt_id": "RCPT-shoppilot-20260607-0001",
  "probes": [{"name": "GET /health", "executed": true, "green": true}],
  "all_green": true,
  "execution": {"mode": "replay", "target_source": "reference-corpus"},
  "audit_id": "2b9bdffa-d5fb-5f4b-823c-80d65889e47a"
}
```

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| SM-01 | unknown receipt / missing approved manifest (preflight) | `needs-input` | human supplies/repairs the receipt |
| SM-02 | probe set could not execute (runner-time) | `ERROR` | retry once (exponential) → smoke-test-failures (named human) |
| SM-03 | one or more probes red | `FAIL` + probes[] | retry once → smoke-test-failures; hold/rollback is the named human's / release controller's decision |
| SM-04 | run too sparse to be a meaningful sanity check | `FAIL` + unexecuted probes visible | retry once → smoke-test-failures |

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
