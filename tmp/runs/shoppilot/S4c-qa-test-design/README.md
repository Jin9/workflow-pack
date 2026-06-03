# S4c · QA Test Design

| | |
|---|---|
| **Owner** | qa-squad |
| **Skill** | `planning-banking-tests ^1.0.0` |
| **Tier / Gate** | T2 · `sync` (on conditional-go) |
| **Consumes → Emits** | `ba.brief · be.review · fe.review` → `qa.plan` |
| **Input** | `epic · stories · review verdicts` |
| **Output contract** | `qa-plan.json` — test_roster · signoff_criteria |
| **Human-view** | markdown today (HTML viewer planned) |
| **SDLC phase** | SIT → UAT |
| **Status** | ⬜ pending |

Maps business logic (the S1 stories' banking-grade concerns — idempotency, last-item race, audit, PII) to a **test
roster** + **sign-off criteria**. A conditional-go verdict requires **L3 sync named approval**.

_Reference template: `.archive/.../templates/S4c-test-plan-and-signoff.md`._
