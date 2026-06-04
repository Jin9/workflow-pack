---
name: handoff-revoke
version: 0.1.0
description: >
  Reverse a previously emitted deploy handoff as a SAGA compensating action —
  revoke the issued short-lived deploy credentials, signal the release control
  plane to halt or roll back the promotion tied to a handoff receipt, and emit an
  idempotent revoke record. Use when a release-handoff failed or must be undone,
  when the delivery pipeline S6 SAGA compensation fires, or when you need to safely
  reverse a deploy handoff within its compensation window. It reverses the handoff,
  not the business outcome, runs behind a named-human confirmation, and appends to
  the audit trail rather than deleting it. Do NOT use to perform the forward
  handoff (use handoff-to-deploy), to validate production health (use
  validating-production-slo), to respond to a live incident, or to delete audit
  history.
stage_type: notify
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: true, audit_level: enhanced, pii_handling: none, tier_default: T1, tier_adaptable: [T1]}
requires_approval: true
requires_capabilities: [deploy_control_plane, network_egress_controlled]
expected_duration_p95_seconds: 600
max_retries_recommended: 0
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Handoff Revoke (SAGA compensation)

## Purpose

Reverse a previously emitted deploy handoff as the **SAGA compensating action** for
S6. Given a handoff `receipt_id`, the skill revokes the issued short-lived OIDC
credentials, signals the release control plane to halt or roll back the promotion,
and emits an **idempotent revoke record**. It reverses the *handoff*, not the
business outcome, runs behind a named-human confirmation, and **appends** to the
audit trail — it never deletes history.

## When to use this skill

- Use when: a `release-handoff` failed or must be undone, and the pipeline's S6
  compensation fires within the compensation window.
- Use when: you need to safely reverse a deploy handoff tied to a known receipt.
- Do NOT use: to perform the forward handoff (`handoff-to-deploy`), to validate
  production health (`validating-production-slo`), to respond to a firing incident,
  or to delete audit history.

## Input contract

Validate against `schemas/input.json`. Required: `receipt_id` (the handoff to
reverse), `reason`, `idempotency_key`. Optional: `confirmer`, `tier`. Stop with
`needs-input` if no receipt matches — there is nothing to revoke.

## Procedure

1. **Resolve the original handoff** by `receipt_id` (`references/saga-compensation.md`).
   No matching receipt is a refusal, not a no-op success. Entry: receipt_id. Exit:
   the receipt to reverse.
2. **Require named-human confirmation.** Reversing a control-plane action is itself
   a control-plane action; a named human confirms the revoke. Capture the confirmer.
3. **Compensate within the window.** Within the compensation window, revoke the
   short-lived OIDC credentials and signal the control plane to halt/roll back the
   promotion tied to the receipt.
4. **Enforce idempotency.** A replay for an already-revoked receipt returns the
   existing revoke record — never double-rolls-back.
5. **Emit the revoke record** (Output contract) with `audit_id`. Stop. Preserve the
   original receipt and this record in the audit trail; if the window has elapsed,
   escalate to a human forward-fix path rather than forcing a reversal.

## Output contract

Validate against `schemas/output.json`: `revoke_id`, `original_receipt_id`,
`status` (revoked|partial|blocked), and `audit_id`. The record is append-only; the
original receipt remains intact alongside it.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| HR-01 | no matching receipt_id | no revoke | refuse → human-queue |
| HR-02 | confirmation withheld | `blocked` | block → delivery-handoff-failures |
| HR-03 | window elapsed / control-plane refuses | `partial` | escalate → human forward-fix |
| HR-04 | duplicate revoke | existing record | idempotent replay (no double-rollback) |

## Constraints

- DO NOT revoke without a **named-human confirmation**.
- DO NOT delete or rewrite the original handoff receipt or audit history — append
  the revoke record.
- DO NOT double-rollback on replay; the skill is idempotent on `receipt_id`.
- DO NOT use long-lived secrets — revoke the short-lived OIDC credentials.
- DO NOT echo real PII or secrets; redact as [PII:REDACTED:CLASS=...].

## Human approval gate

The revoke is confirmed by a named human; the confirmer is accountable and logged
under `audit_id`. If confirmation is withheld, the skill blocks (`blocked`) and
routes to `delivery-handoff-failures` rather than reversing silently.

## References

| Need | Reference |
|------|-----------|
| SAGA compensation, compensation window, idempotent reversal, append-only audit, forward-fix fallback | `references/saga-compensation.md` |
