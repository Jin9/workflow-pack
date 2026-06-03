# S4a · Backend Impl (+ S4a-r Review)

| | |
|---|---|
| **Owner** | dev-squad |
| **Skill** | `implement-backend-feature ^1.0.0` |
| **Tier / Gate** | T2 · `auto` (sandboxed) |
| **Consumes → Emits** | `tl.design` → `be.artifacts` |
| **Input** | `api_contracts · component_map` (from S2) |
| **Output contract** | `backend-artifacts.json` + Go code (JSON manifest) |
| **Human-view** | code-skeleton + manifest (native) |
| **SDLC phase** | Development |
| **Status** | ⬜ pending |

Generates the Go service code + tests **in a sandbox**, conforming to the
[`repo-generator`](../../../../repo-generator/) skeleton and the layout in
[`../S2-tl-design/project-structure.md`](../S2-tl-design/project-structure.md). Reversible → auto-gated.

### `review/` — S4a-r · Backend Review
`review-backend-code ^1.0.0` · T2 · `async` · `be.artifacts · tl.design` → `be.review` (`backend-review.json`).
Severity-graded; **an agent never reviews its own code** (separate identity); high/medium loop back to Dev (cap 2),
low → advisory. Reference template: `.archive/.../templates/S4a_r-backend-review-report.md`.
