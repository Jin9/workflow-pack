<!-- TEMPLATE · stage S4a Backend Impl · owner: dev-squad · produced-by: implement-backend-feature ^1.0.0 · audit_id: <audit_id:UUID> -->
# S4a Backend Impl — Artifacts Manifest

> **⚖ Advisory — JSON-only stage.** Per the Codex GPT-5.5 (xHigh) brainstorm, Claude final decision (2026-05-31), this **autonomous, sandboxed** stage is **JSON-only**: the JSON manifest is the handoff and this readable summary is **optional**. Human review of the code happens at the adjacent S4a-r gate. Template kept for optional use. See [`LEAN_DECISION.md`](LEAN_DECISION.md).

> **Dual output.** This stage emits **two** artifacts:
> 1. **JSON manifest → next node** (machine handoff, schema-validated): [`../schemas/backend-artifacts.json`](../schemas/backend-artifacts.json) — required fields `go_files`, `test_files`, `audit_id`. *The manifest is the machine contract; the code files are the payload.*
> 2. **This human-readable manifest summary** (rendered from this template). *Autonomous stage* (AUTO, sandboxed) — no mandatory human sign-off; this is the conformance surface for the S4a-r review.
>
> **Reuse, do not duplicate.** The Go service layout is the canonical skeleton at `repo-generator/project-skeleton/`,
> stamped by `repo-generator/generate-repos.sh` (module-path rewrite). Reference it — do **not** copy the skeleton here.

## Generated artifacts
- **`go_files` (N):** `<list / link>`  ·  **`test_files` (N):** `<list / link>`
- **Module path:** `<gitlab.com/.../<service>>` (rewritten by generate-repos.sh from `project-skeleton`)

## Skeleton conformance (repo-generator/project-skeleton/)
| Required element | Present? |
|---|---|
| `main.go` · `go.mod` · `go.sum` (committed) | `<yes/no>` |
| `config/` · `router/` · `app/<domain>/` · `migrations/` | `<yes/no>` |
| `_test.go` siblings (table-driven, cov ≥ 0.80) | `<yes/no>` |
| `Dockerfile` · `Makefile` · `.golangci.yaml` (lint clean) | `<yes/no>` |

## Notes
- **Sandbox:** built/tested in sandbox (ALLOW: tests-in-sandbox).  ·  **audit_id:** `<audit_id:UUID>`
- Routes to **S4a-r Backend Review** (review identity ≠ impl identity).
