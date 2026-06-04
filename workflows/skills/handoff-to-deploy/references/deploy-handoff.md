# Deploy handoff — named approval, OIDC creds, idempotent receipt, SAGA boundary

The S6 handoff is the one stage in the pipeline that crosses an **irreversible
control-plane boundary**. Everything here exists to make that crossing safe,
accountable, and reversible-by-compensation (not by in-place retry).

## The mandatory named-human gate

A deploy handoff is a CONFIRM-tier action: it must never run on agent confidence
alone. A **named** individual with release authority approves synchronously, and
the approval is logged under the stage `audit_id`. This mirrors the vault's
human-in-the-loop guidance: gates belong at irreversible boundaries, and the
approver is accountable for the AI-assisted decision.

- Vault: [[literature/agent-orchestration/human-in-the-loop-gates|Human-in-the-loop gates]]
- Vault: [[literature/agent-orchestration/agentic-software-delivery-lifecycle|Agentic software delivery lifecycle]]

Concretely, hosted CI platforms model this as deployment environments with
required reviewers / approval gates before a sensitive job runs — a human approval
requirement in front of the deploy.

- Web: docs.github.com (environments and deployment protection rules)

## Short-lived OIDC credentials (keyless)

Do not use long-lived secrets to deploy. The handoff mints **short-lived OIDC
tokens** scoped to the target environment, obtained by exchanging a signed identity
JWT for temporary, environment-scoped credentials that expire when the job ends.
Even if leaked, they are useless outside the execution window. This also keeps the
skill clean against the secrets-leakage and supply-chain risks the vault catalogs.

- Vault: [[literature/platform-devops/secret-management|Secret management]]
- Vault: [[literature/ai-threats/secrets-leakage-ai-workflows|Secrets leakage in AI workflows]]
- Web: cycode.com (enhancing CI/CD security with OIDC tokens) · marzouk.io (keyless AWS deploys with OIDC)

## Idempotent, immutable receipt

The handoff is keyed on `(idempotency_key, release_ref)`. A replay with the same
key returns the **existing** receipt — it must never trigger a second deploy. The
receipt is immutable: downstream stages (e.g. `validating-production-slo`) reference
`receipt_id`; they never mutate it. This is the same content-addressed,
replay-safe discipline the pipeline uses elsewhere.

## SAGA boundary, not in-place retry

Because the action cannot be undone where it ran, a failed or bad handoff is
**compensated**, not retried: the forward action is `handoff-to-deploy`; its
compensating action is `handoff-revoke`, which reverses the handoff within the
600-second compensation window. Rollback-by-design (a planned reverse path) beats
hoping a retry converges.

- Vault: [[literature/deployment-delivery/deployment-rollback-design|Deployment rollback design]]
- Vault: [[literature/deployment-delivery/gitops-workflow|GitOps workflow]]

## Sources

- [[literature/agent-orchestration/human-in-the-loop-gates|Human-in-the-loop gates]]
- [[literature/agent-orchestration/agentic-software-delivery-lifecycle|Agentic software delivery lifecycle]]
- [[literature/platform-devops/secret-management|Secret management]]
- [[literature/ai-threats/secrets-leakage-ai-workflows|Secrets leakage in AI workflows]]
- [[literature/deployment-delivery/deployment-rollback-design|Deployment rollback design]]
- [[literature/deployment-delivery/gitops-workflow|GitOps workflow]]
- Web: cycode.com · marzouk.io · docs.github.com
