# S5 · QA Validation

| | |
|---|---|
| **Owner** | qa-squad |
| **Skill** | `qa-squad (execute)` |
| **Tier / Gate** | T1 · `sync` |
| **Consumes → Emits** | `qa.plan` → `qa.evidence` |
| **Input** | `test_roster` |
| **Output contract** | qa-evidence (pass/fail) |
| **Human-view** | markdown + CSV today (HTML viewer planned) |
| **SDLC phase** | SIT → UAT |
| **Status** | ⏸ **deferred** — execution node missing (OI-003 / GAP-05); only test *design* (S4c) exists today |

Executes the test roster and produces pass/fail **evidence** that gates the release.

_Reference template: `.archive/.../templates/S5-qa-evidence-report.md`._
