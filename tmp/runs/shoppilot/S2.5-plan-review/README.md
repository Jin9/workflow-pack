# S2.5 · Plan-Review gate

| | |
|---|---|
| **Owner** | Tech Lead |
| **Skill** | `Plan-Reviewer` (adversarial red-team) |
| **Tier / Gate** | T1 · `gate` |
| **Consumes → Emits** | `ba.brief · tl.design` → `plan.reviewed` |
| **Input** | BA + TL outputs |
| **Output contract** | `plan-review.json` — `pass / reroute / HardFail` + findings |
| **Human-view** | markdown today (HTML viewer planned) |
| **SDLC phase** | Design gate |
| **Status** | ⬜ pending |

Red-teams the BA+TL plan **before** the expensive S3/S4 fan-out (cheap to reverse, high blast radius → it gates).
Caps at 1 per diagnosis; `reroute` high findings to BA/TL; cap exceeded → `HardFail` (no fan-out), human reviews.

_Reference template: `.archive/.../templates/S2_5-plan-review-findings.md`._
