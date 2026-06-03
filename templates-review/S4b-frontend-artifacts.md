<!-- TEMPLATE · stage S4b Frontend Impl · owner: dev-squad · produced-by: implement-frontend-feature ^1.0.0 · audit_id: <audit_id:UUID> -->
# S4b Frontend Impl — Artifacts Manifest

> **⚖ Advisory — JSON-only stage.** Per the Codex GPT-5.5 (xHigh) brainstorm, Claude final decision (2026-05-31), this **autonomous, sandboxed** stage is **JSON-only**: the JSON manifest is the handoff and this readable summary is **optional**. Human review of the UI happens at the adjacent S4b-r gate. Template kept for optional use. See [`LEAN_DECISION.md`](LEAN_DECISION.md).

> **Dual output.** This stage emits **two** artifacts:
> 1. **JSON manifest → next node** (machine handoff, schema-validated): [`../schemas/frontend-artifacts.json`](../schemas/frontend-artifacts.json) — the TSX + test file lists + `audit_id`. *The manifest is the machine contract; the code files are the payload.*
> 2. **This human-readable manifest summary** (rendered from this template). *Autonomous stage* (AUTO, sandboxed) — no mandatory human sign-off; this is the conformance surface for the S4b-r review.
>
> **Reuse, do not duplicate.** The Next.js/TSX layout follows `implement-frontend-feature`'s mandatory structure
> (`package.json`, `tsconfig.json`, `app/`, `lib/`, `components/`) — reference it; do not copy a skeleton here.

## Generated artifacts
- **TSX files (N):** `<list / link>`  ·  **Test files (N):** `<list / link>`  ·  **UX pack consumed:** `<pack_dir>`

## Structure conformance
| Required element | Present? |
|---|---|
| `package.json` · `tsconfig.json` | `<yes/no>` |
| `app/` · `lib/` · `components/` | `<yes/no>` |
| Test siblings (component/unit) | `<yes/no>` |
| No `dangerouslySetInnerHTML` (unless justified) | `<yes/no>` |
| Tokens / route-map from S1.5 UX pack honored | `<yes/no>` |

## Notes
- **Sandbox:** built/tested in sandbox.  ·  **audit_id:** `<audit_id:UUID>`  ·  Routes to **S4b-r Frontend Review**.
