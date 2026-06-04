---
name: handoff-to-deploy
version: 0.1.0
description: >
  Hand a QA-signed-off release off to the deploy/release control plane behind a
  mandatory synchronous named-human approval, mint short-lived OIDC deploy
  credentials, and emit an immutable handoff receipt that ties the live release
  to its named approver and audit trail. Use when a release is QA-signed-off and
  must be promoted to a live environment, when you need a gated deploy handoff
  with a named approver and a receipt, or when wiring the S6 release stage of the
  delivery pipeline. This is an irreversible control-plane boundary: it requires
  approval, never retries, and is SAGA-compensated by handoff-revoke. Do NOT use
  to author CI/CD config or pipelines, to run tests or validate production SLOs
  (use validating-production-slo), to design the release runbook, or to reverse a
  completed handoff (use handoff-revoke).
stage_type: notify
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: false, audit_level: enhanced, pii_handling: none, tier_default: T1, tier_adaptable: [T1]}
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

Validate against `schemas/input.json`. Required: `verdict` (the QA sign-off
verdict), `evidence` (the QA evidence backing it), `idempotency_key`. Optional:
`release_ref`, `approver`, `target_env`, `tier`. Stop with `needs-input` if there
is no passing verdict or no evidence to approve against.

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

Validate against `schemas/output.json`: `receipt_id`, `status`
(handed_off|blocked|failed), `release_ref`, `approver{name,role}`, and `audit_id`.
The receipt is immutable — downstream stages reference it; they do not edit it.

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
