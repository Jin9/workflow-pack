<!-- TEMPLATE · stage S7 Prod Validation · owner: On-call / Release Mgr · produced-by: running-smoke-tests + validating-production-slo + analyzing-canary-rollout · audit_id: <audit_id:UUID> -->
# S7 Prod Validation — Smoke/SLO Report + Rollback Decision Record

> **Dual output.** This stage emits **two** artifacts:
> 1. **Machine handoff:** a JSON smoke/SLO metrics + rollback record object (`audit_id`). *S7 is **deferred (OI-003)**; no boundary schema file under `../schemas/` yet — the shape below is the contract.*
> 2. **This human-review document** — the **sync (L3)** gate with a **named rollback decision** (owner: On-call / Release Mgr).
>
> Validates the live release. Never declare healthy without evidence; a named human owns the rollback call.

## Smoke (post-deploy)
| Check | Verdict | Evidence |
|---|---|---|
| `<critical path / health>` | `<pass/fail>` | `<link>` |

## SLO multi-window burn-rate
| Window | Threshold | Observed | Breach? |
|---|---|---|---|
| 1h | 14.4× | `<…>` | `<no/yes>` |
| 6h | 6× | `<…>` | `<no/yes>` |
| 24h | 3× | `<…>` | `<no/yes>` |

## Canary analysis (progressive)
- **AnalysisTemplate metrics (latency / success SLI):** `<pass/fail>`  ·  **Promote / hold / abort:** `<…>`

## Rollback decision record (named — On-call / Release Mgr)
- **Decision:** ☐ Keep (healthy) ☐ Hold / investigate ☐ **Rollback** (forward-only reversal)
- **Rationale:** `<…>`  ·  **Decider (named):** `<name>`
- **Date/time:** `<YYYY-MM-DDThh:mm>`  ·  **audit_id:** `<audit_id:UUID>`  ·  **Notes:** `<…>`
