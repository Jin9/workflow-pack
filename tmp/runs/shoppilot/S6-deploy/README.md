# S6 · Release Handoff — handoff-to-deploy

**Skill:** `handoff-to-deploy 0.1.0` · **gate:** sync NAMED (L3, Release Manager) — **MANDATORY, irreversible** ·
**status:** ▶ simulated.

Hands the QA-signed release to the deploy control plane behind a named-human approval; emits an immutable
receipt. SAGA-compensated by `handoff-revoke` (600s) if the boundary must be reversed.

## Artifacts
- **`handoff-receipt.json`** — the contract (`workflows/schemas/handoff-receipt.json`; skill
  `handoff-to-deploy/schemas/output.json`): `receipt_id` (`RCPT-shoppilot-20260607-0001`),
  `status: handed_off`, `release_ref`, `approver` (**named** Release Manager), `audit_id`.

> Irreversible control-plane boundary — no auto-retry; requires the synchronous named approval regardless of
> agent confidence (`requires_approval: true` in the YAML). This is the one gate the pipeline never auto-clears.
