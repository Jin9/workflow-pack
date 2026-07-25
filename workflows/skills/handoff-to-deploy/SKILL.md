---
name: handoff-to-deploy
version: 0.2.0
description: "Hand a QA-signed-off release off to the deploy/release control plane behind a mandatory synchronous named-human approval, mint short-lived OIDC deploy credentials, and emit an immutable handoff receipt that ties the live release to its named approver and audit trail. Use when a release is QA-signed-off and must be promoted to a live environment, when you need a gated deploy handoff with a named approver and a receipt, or when wiring the S6 release stage of the delivery pipeline. This is an irreversible control-plane boundary: it requires approval, never retries, and is SAGA-compensated by handoff-revoke. Do NOT use to author CI/CD config or pipelines, to run tests or validate production SLOs (use validating-production-slo), to design the release runbook, or to reverse a completed handoff (use handoff-revoke)."
stage_type: notify
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: compensable, audit_level: enhanced, pii_handling: redact, tier_default: T1, tier_adaptable: [T1]}
requires_approval: true
requires_capabilities: [deploy_control_plane, network_egress_controlled]
expected_duration_p95_seconds: 60
max_retries_recommended: 0
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Handoff to Deploy

## Purpose

Promote a QA-signed-off release across the **irreversible control-plane boundary**
(S6) — but only behind a **mandatory synchronous named-human approval**. The skill
mints short-lived OIDC deploy credentials, hands the release to the deploy/release
control plane, and emits an immutable **handoff receipt** that binds the live
release to its approver and audit trail. It is a `notify`/release stage: it triggers
the deploy and records it; it does not write CI/CD config or validate prod health.
Because the action cannot be undone in place, it **never retries** and is
SAGA-compensated by `handoff-revoke`.

## When to use this skill

- Use when: a release is QA-signed-off (`qa-validate` verdict = pass) and must be
  promoted to a live environment with a named approver and a receipt.
- Use when: wiring the S6 `release-handoff` stage of the delivery pipeline.
- Do NOT use: to author CI/CD pipelines or runbooks, to run tests, to validate
  production SLOs (`validating-production-slo`), or to reverse a completed handoff
  (`handoff-revoke`).

## Input contract

ADVISORY — documents the assembled stage input; the engine validates workflow input
and stage OUTPUTS only (engine/validation.py). Validate against `schemas/input.json`.
Required: `verdict` (const `PASS` — release is permitted ONLY for a QA pass;
FAIL/ERROR is an explicit stop, and a human exception is a GATE decision, never an
input value), `totals` (the QA producer's shape; full evidence via
`upstream_artifacts["qa-validate"]`), `idempotency_key` (engine-injected).
Optional workflow inputs: `release_ref`, `target_env` — live mode stops
`needs-input` without them; handoff idempotency identity is
`(idempotency_key, release_ref, target_env)`. Optional engine-injected:
`upstream_artifacts`, `loop_back_feedback`.

**Example (validates against schemas/input.json):**
```json
{
  "verdict": "PASS",
  "totals": { "executed": 142, "passed": 142, "failed": 0, "skipped": 0 },
  "release_ref": "shoppilot@release-1.0.0+06d94543973d",
  "target_env": "production",
  "idempotency_key": "3f6c0b2e-7a41-4d9b-9c2a-8e5b1f0a4d22"
}
```

## Procedure

1. **Preflight** (`references/deploy-handoff.md`): confirm `verdict` = pass and
   `evidence` is present and complete. Entry: QA sign-off. Exit: preflight ok. A
   non-pass verdict or missing evidence is a refusal, not a handoff (banking
   default: uncertain = do not ship).
2. **Require synchronous named-human approval.** A named individual with release
   authority must approve; capture their identity. Block on the human queue until
   approval — **agent confidence never substitutes for the gate**, regardless of
   how strong the evidence looks.
3. **Mint short-lived OIDC credentials.** Use keyless, environment-scoped tokens
   that expire when the job ends; never long-lived secrets.
4. **Enforce idempotency.** Key the handoff on `(idempotency_key, release_ref)`. A
   replay with the same key returns the existing receipt — never double-deploys.
5. **Execute the handoff** to the release control plane; capture `receipt_id`,
   `status`, `release_ref`, and the `approver`.
6. **Emit the receipt** (Output contract) with `audit_id`. Stop. If the downstream
   release later fails, the SAGA compensation (`handoff-revoke`) reverses it within
   the compensation window.

## Output contract

Validate against `schemas/output.json`: `receipt_id`, `status` (const
`handed_off` — a receipt EXISTS only for a completed handoff; withheld approval
or a control-plane failure is a STAGE failure routed to
`delivery-handoff-failures`, never a schema-valid receipt), `release_ref`,
`target_env`, `approver{name,role}` (the accountable NAMED human — intentional
audit content, a design invariant; optional `approval_ref` links the gate
record), and `audit_id` — producer-stamped, deterministic:
UUIDv5(HOUSE_NS, "release-handoff:{idempotency_key}") with HOUSE_NS =
uuid5(NAMESPACE_URL, "https://squad-delivery/audit"); the human decision itself
is logged in the gate/HITL record, not under this artifact id. The receipt is
immutable — downstream stages reference it; they do not edit it.

**Example (validates against schemas/output.json):**
```json
{
  "receipt_id": "RCPT-shoppilot-20260607-0001",
  "status": "handed_off",
  "release_ref": "shoppilot@release-1.0.0+06d94543973d",
  "target_env": "production",
  "approver": { "name": "Khun Ratana", "role": "Release Manager" },
  "audit_id": "50012a63-945d-513f-b7eb-33edae948cba"
}
```

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| HD-01 | verdict not pass / evidence missing | no handoff | refuse → human-queue |
| HD-02 | no named approver / approval withheld | `blocked` | block → delivery-handoff-failures |
| HD-03 | control-plane error during handoff | `failed` | no retry → SAGA handoff-revoke |
| HD-04 | duplicate idempotency_key | existing receipt | idempotent replay (no double-deploy) |

## Constraints

- DO NOT proceed without a **synchronous named-human approval**; confidence never
  substitutes for the gate.
- DO NOT use long-lived secrets — mint short-lived OIDC tokens scoped to the target
  environment.
- DO NOT retry a failed handoff in place; reverse it via `handoff-revoke`.
- DO NOT double-deploy on replay; the same `idempotency_key` returns the existing
  receipt.
- DO NOT echo real PII or secrets in the receipt or logs; redact as
  [PII:REDACTED:CLASS=...].

## Human approval gate

This stage **always** ends in a human decision. The verdict the approver records is
authoritative: `approve` releases the handoff; `hold`/`reject` blocks it and routes
to `delivery-handoff-failures`. The approval is synchronous, named, and logged
under `audit_id`.

## References

| Need | Reference |
|------|-----------|
| Named-approval gate, OIDC short-lived creds, idempotent receipt, SAGA boundary, no-retry policy | `references/deploy-handoff.md` |
