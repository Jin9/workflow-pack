# S7 · Prod Validation

| | |
|---|---|
| **Owner** | On-call / Release Manager |
| **Skill** | `ops + observability` |
| **Tier / Gate** | T2 · `sync` |
| **Consumes → Emits** | `deploy.receipt` → `prod.validated` |
| **Input** | live release |
| **Output contract** | smoke/SLO metrics + rollback record |
| **Human-view** | markdown today (HTML viewer planned) |
| **SDLC phase** | Operate |
| **Status** | ⏸ **deferred** (OI-003) |

Smoke + SLO check on the live release, with a **named human rollback decision**.

_Reference template: `.archive/.../templates/S7-smoke-slo-rollback.md`._
