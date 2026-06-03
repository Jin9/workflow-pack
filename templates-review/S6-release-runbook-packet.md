<!-- TEMPLATE · stage S6 Deploy · owner: Release Manager · produced-by: planning-release-handoff / handoff-to-deploy (OI-002) · audit_id: <audit_id:UUID> -->
# S6 Deploy — Release Runbook + KNOWN_ISSUES + Sign-off Packet

> **Dual output.** This stage emits **two** artifacts:
> 1. **JSON contract → next node** (machine handoff, schema-validated): [`../schemas/handoff-receipt.json`](../schemas/handoff-receipt.json) — required fields `receipt_id`, `audit_id`.
> 2. **This human-review packet** — the **mandatory sync named (L3) approval**, confidence-independent (owner: Release Manager).
>
> **IRREVERSIBLE / control-plane.** Requires a named human approval regardless of agent confidence. Deploy credentials
> must be **short-lived OIDC tokens** (no long-lived secrets). `handoff-to-deploy` / `handoff-revoke` skills are a GAP (OI-002).

## Release runbook
- **Release id / `receipt_id`:** `<…>`  ·  **Artifact / version:** `<immutable ref>`  ·  **Strategy:** `<canary | blue-green>`
- **Pre-flight checks:** `<migrations applied · feature flag default off · kill-switch wired · smoke target ready>`
- **Deploy steps (ordered):** 1. `<…>` 2. `<…>` 3. `<…>`
- **Rollback procedure (forward-only past pivot):** `<compensate via handoff-revoke / flag-off / redeploy previous>`  ·  **Pivot point:** `<…>`

## KNOWN_ISSUES (carried caveats → ShipWithCaveats)
| Issue | Severity | Mitigation / owner | Tracking ref |
|---|---|---|---|
| `<…>` | `<P1/P2/P3>` | `<…>` | `<…>` |

## Sign-off packet (Release Manager — sync named L3, mandatory, four-eyes)
- **QA evidence ref (S5):** `<link>`  ·  **Reviews clean (S4*-r):** `<yes/no>`  ·  **Credentials:** ☐ short-lived OIDC confirmed
- **Approver (named, accountable):** `<name>`  ·  **Second pair of eyes (maker ≠ checker):** `<name>`
- **Decision:** ☐ Approve deploy ☐ Approve-with-caveats (KNOWN_ISSUES) ☐ Reject
- **Date:** `<YYYY-MM-DD>`  ·  **audit_id:** `<audit_id:UUID>`  ·  **Notes:** `<…>`
