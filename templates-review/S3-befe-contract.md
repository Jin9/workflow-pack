<!-- TEMPLATE · stage S3a/3b Contracts (BE/FE) · owner: dev-squad · produced-by: befe-contract-design · audit_id: <audit_id:UUID> -->
# S3 Contracts (BE/FE) — Typed Contract Spec

> **⚖ Advisory — JSON-only stage.** Per the Codex GPT-5.5 (xHigh) brainstorm, Claude final decision (2026-05-31), this **autonomous** stage is **JSON-only**: the JSON/OpenAPI contract is the handoff and this readable doc is **optional**. Human-inspectable evidence surfaces at the adjacent S2 design + S4*-review gates. Template kept for optional use. See [`LEAN_DECISION.md`](LEAN_DECISION.md).

> **Dual output.** This stage emits **two** artifacts:
> 1. **JSON contract → next node** (machine handoff): the **typed contract itself** — OpenAPI / typed JSON, one per boundary; consumed directly by S4a/S4b implementation.
> 2. **This human-readable spec** (rendered from this template) — for review. *Autonomous stage* (AUTO gate) — no mandatory human sign-off, but the spec is the reviewable surface.
>
> **Mirrors** `agentic-delivery-pipeline/reference/squad-flow-v0.7/docs/templates/api-spec.md`; composes
> `api-contract-design` (shape) + `universal-spec-validator` (breaking-change gate). One file per API boundary.

## Endpoint
- **`<METHOD> <path>`** — e.g. `POST /api/v1/<svc>/<action>`
- **Story refs:** `<STORY_SLUG/AC-N>`  ·  **Contract ref:** `<contracts.json#<name>>`
- **Semantics:** `<sync | async-event | system-internal>`  ·  **Auth tier:** `<none | customer | admin>`

## Request (JSON Schema)
```json
{ "<field>": "<type · constraints>" }
```

## Response
- **Success:** `<HTTP 2xx · body schema>`
- **Errors:** `<HTTP 4xx/5xx · code · message (locked strings)>`

## Contract rules
- **Idempotency:** `<key / rule>`  ·  **Ordering:** `<guarantee>`  ·  **Versioning:** `<v1; backward-compat policy>`
- **Failure modes:** `<timeout / partial / retry semantics>`

## BE ↔ FE split
- **Backend owns:** `<…>`  ·  **Frontend consumes:** `<…>`  ·  **Shared types:** `<…>`

## Validation (universal-spec-validator)
- **Breaking-change vs baseline:** ☐ none ☐ `<list>`  ·  **audit_id:** `<audit_id:UUID>`
