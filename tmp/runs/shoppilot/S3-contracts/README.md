# S3a/3b · Contracts (BE/FE)

| | |
|---|---|
| **Owner** | dev-squad |
| **Skill** | `dev-squad` |
| **Tier / Gate** | T2 · `auto` |
| **Consumes → Emits** | `tl.design` → `contracts.published` |
| **Input** | `api_contracts` (from S2) |
| **Output contract** | OpenAPI / typed JSON (JSON-only stage) |
| **Human-view** | OpenAPI · API-Path · event · request/response (native) |
| **SDLC phase** | Requirements & Design |
| **Status** | ⏸ **deferred** (OI-003) |

Splits the S2 `api_contracts` into typed **backend** (`be/`) and **frontend** (`fe/`) boundaries.

- `be/` — backend API + event contracts.
- `fe/` — frontend-facing request/response contracts.

_Reference template: `.archive/.../templates/S3-befe-contract.md`._
