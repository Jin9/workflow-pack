# SAGA compensation — reverse the handoff, append to the audit trail

`handoff-revoke` is the **compensating action** for the S6 forward step
`handoff-to-deploy`. In a SAGA, a step that cannot be undone in place is paired
with an explicit compensation that reverses its effect; the orchestrator fires the
compensation when the forward step (or a later step) fails.

## What "reverse the handoff" means

The skill reverses the *handoff mechanics*, not the business outcome:

1. **Revoke the issued credentials.** The short-lived OIDC tokens minted for the
   handoff are revoked / allowed to expire so they cannot be reused.
2. **Signal the control plane to halt or roll back** the promotion tied to the
   `receipt_id` (halt a progressing rollout, or roll back to the prior known-good
   revision — a planned reverse path, not an ad-hoc edit).
3. **Record the compensation** as an append-only revoke record alongside the
   original receipt.

This is rollback-by-design: a deliberate reverse path defined up front.

- Vault: [[literature/deployment-delivery/deployment-rollback-design|Deployment rollback design]]
- Vault: [[literature/deployment-delivery/blue-green-deployment|Blue-green deployment]]

## The compensation window and the forward-fix fallback

Compensation is bounded by a window (600s in the pipeline). Inside the window, the
reversal is automatic-after-confirmation. If the window has elapsed or the control
plane refuses (e.g. the release has already taken irreversible downstream effect),
the skill returns `partial` and escalates to a **human forward-fix** path rather
than forcing an unsafe reversal — some effects are corrected forward, not undone.

- Vault: [[literature/observability-reliability/incident-response-playbook|Incident response playbook]]
- Vault: [[literature/agent-orchestration/agentic-software-delivery-lifecycle|Agentic software delivery lifecycle]]

## Idempotent and append-only

Replays are safe: a revoke for an already-revoked `receipt_id` returns the existing
record and performs no second rollback. The original handoff receipt is never
deleted or rewritten — the revoke record is appended, so the audit trail shows both
the handoff and its compensation. Audit history is evidence; it is never erased.

## Named confirmation

Reversing a control-plane action is itself a control-plane action, so a named human
confirms the revoke. The confirmer is accountable and logged under `audit_id`.

- Vault: [[literature/agent-orchestration/human-in-the-loop-gates|Human-in-the-loop gates]]

## Sources

- [[literature/deployment-delivery/deployment-rollback-design|Deployment rollback design]]
- [[literature/deployment-delivery/blue-green-deployment|Blue-green deployment]]
- [[literature/observability-reliability/incident-response-playbook|Incident response playbook]]
- [[literature/agent-orchestration/human-in-the-loop-gates|Human-in-the-loop gates]]
- [[literature/agent-orchestration/agentic-software-delivery-lifecycle|Agentic software delivery lifecycle]]
