---
name: handoff-revoke
version: 0.2.0
description: Reverse a previously emitted deploy handoff as a SAGA compensating action — revoke the issued short-lived deploy credentials, signal the release control plane to halt or roll back the promotion tied to a handoff receipt, and emit an idempotent revoke record. Use when a release-handoff failed or must be undone, when the delivery pipeline S6 SAGA compensation fires, or when you need to safely reverse a deploy handoff as the SAGA compensation. It reverses the handoff, not the business outcome, runs behind a named-human confirmation, and appends to the audit trail rather than deleting it. Do NOT use to perform the forward handoff (use handoff-to-deploy), to validate production health (use validating-production-slo), to respond to a live incident, or to delete audit history.
stage_type: notify
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: reversible, audit_level: enhanced, pii_handling: redact, tier_default: T1, tier_adaptable: [T1]}
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
  compensation fires (600s is the execution budget, not an eligibility window).
- Use when: you need to safely reverse a deploy handoff tied to a known receipt.
- Do NOT use: to perform the forward handoff (`handoff-to-deploy`), to validate
  production health (`validating-production-slo`), to respond to a firing incident,
  or to delete audit history.

## Input contract

ADVISORY — documents the assembled compensation input; the engine validates
workflow input and stage OUTPUTS only (engine/validation.py). Validate against
`schemas/input.json`. This is EXACTLY what the SAGA trigger sends
(engine/orchestrator.py): required `reason`, `original_receipt` (the handoff
receipt being reversed, or null; the revoke target derives from
`original_receipt.receipt_id` — stop `blocked` on null or a non-`handed_off`
status), `idempotency_key` (engine-injected: invocation identity; the BUSINESS
dedupe key is `original_receipt.receipt_id` — same key + same normalized input
⇒ byte-identical receipt; an already-compensated receipt never triggers a
second rollback). Optional: `confirmation{actor_ref, role, decision:
approve-revoke}` — the engine's trigger supplies none today; the named decision
lives in the typed HITL resolution record (threading it into this payload is a
ledgered engine follow-up). NEVER reuse the forward handoff's approver as the
revoke confirmer. Optional engine-injected: `upstream_artifacts`.

**Example (validates against schemas/input.json):**
```json
{
  "reason": "SAGA compensation: prod-validate hard-failed after handoff.",
  "original_receipt": { "receipt_id": "RCPT-shoppilot-20260607-0001", "status": "handed_off" },
  "idempotency_key": "3f6c0b2e-7a41-4d9b-9c2a-8e5b1f0a4d22"
}
```

## Procedure

1. **Resolve the original handoff** by `receipt_id` (`references/saga-compensation.md`).
   No matching receipt is a refusal, not a no-op success. Entry: receipt_id. Exit:
   the receipt to reverse.
2. **Require named-human confirmation.** Reversing a control-plane action is itself
   a control-plane action; a named human confirms the revoke. Capture the confirmer.
3. **Compensate.** Revoke the
   short-lived OIDC credentials and signal the control plane to halt/roll back the
   promotion tied to the receipt.
4. **Enforce idempotency.** A replay for an already-revoked receipt returns the
   existing revoke record — never double-rolls-back.
5. **Emit the revoke record** (Output contract) with `audit_id`. Stop. Preserve the
   original receipt and this record in the audit trail; if the budget is exceeded,
   escalate to a human forward-fix path rather than forcing a reversal.

## Output contract

Validate against `schemas/output.json`: `revoke_id`, `original_receipt_id` (must
equal the input receipt id), `status` (`revoked` = credentials revoked AND
promotion withheld; `partial` = mixed; `blocked` = no effect performed —
partial/blocked require `failure_code`), `reason` (echoed, audit-visible),
`effects{credentials, promotion}`, optional `confirmation` echo, and `audit_id`
— LIVE derivations use UUIDv5(HOUSE_NS,
"release-handoff::compensation:{idempotency_key}"); fixture/corpus ids are
grandfathered. The record is append-only; the original receipt remains intact
alongside it. The 600-second value is the execution budget only — no contract
supplies a compensation deadline, so no expiry is enforced.

**Example (validates against schemas/output.json):**
```json
{
  "revoke_id": "RVK-shoppilot-20260607-0001",
  "original_receipt_id": "RCPT-shoppilot-20260607-0001",
  "status": "revoked",
  "reason": "SAGA compensation fixture: downstream stage failure after release handoff (deterministic corpus material).",
  "effects": { "credentials": "revoked", "promotion": "withheld" },
  "audit_id": "4b679039-81ee-5f81-b374-0986d2ebf120"
}
```

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| HR-01 | no matching receipt_id | no revoke | refuse → human-queue |
| HR-02 | confirmation withheld | `blocked` | block → delivery-handoff-failures |
| HR-03 | execution budget exceeded (600s is the executor timeout, not an eligibility window) | `partial` | escalate → human forward-fix |
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
