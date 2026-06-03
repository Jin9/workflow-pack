# S4b · Frontend Impl (+ S4b-r Review)

| | |
|---|---|
| **Owner** | dev-squad |
| **Skill** | `implement-frontend-feature ^1.0.0` |
| **Tier / Gate** | T2 · `auto` (sandboxed) |
| **Consumes → Emits** | `tl.design · ux.pack` → `fe.artifacts` |
| **Input** | `api_contracts · ux pack` |
| **Output contract** | `frontend-artifacts.json` + TSX code (JSON manifest) |
| **Human-view** | code-skeleton + manifest (native) |
| **SDLC phase** | Development |
| **Status** | ⬜ pending |

Generates the React/TS (Next.js / TSX) storefront + admin code + tests in a sandbox, per the `web/` layout in
[`../S2-tl-design/project-structure.md`](../S2-tl-design/project-structure.md) and the S1.5 UX pack.

### `review/` — S4b-r · Frontend Review
`review-frontend-code ^1.0.0` · T2 · `async` · `fe.artifacts · tl.design` → `fe.review` (`frontend-review.json`).
Quality + security review; high/medium loop back to Dev (cap 2), low → advisory; human async-confirms the verdict.
Reference template: `.archive/.../templates/S4b_r-frontend-review-report.md`.
