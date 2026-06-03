<!-- TEMPLATE · stage S2 TL Design · owner: Tech Lead + governance · produced-by: designing-tech-lead-handoff ^0.1.0 · audit_id: <audit_id:UUID> -->
# S2 TL Design — Design Doc + ADRs (index)

> **Dual output.** This stage emits **two** artifacts:
> 1. **JSON contract → next node** (machine handoff, schema-validated): [`../schemas/tl-design.json`](../schemas/tl-design.json) — required fields `component_map`, `api_contracts`, `audit_id`.
> 2. **This human-review document** — the **sync named (L3)** governance gate (owner: Tech Lead + governance).
>
> **Reuse, do not duplicate.** The TL design doc is *composed from the 12 canonical sub-templates already in*
> `workflows/skills/designing-tech-lead-handoff/templates/`. This file is an **index**: fill the
> table with links to each filled sub-doc — do not re-author the sub-templates here. Architecture / component /
> ER diagrams are emitted as **raw draw.io XML** via the external **`drawio` skill** house style (never Mermaid).

## Composed sub-documents
| Concern | Sub-template (reference) | Filled doc |
|---|---|---|
| Component decomposition | `tech-lead-components.md` | `<link>` |
| Integration contracts | `tech-lead-contracts.md` | `<link>` |
| Infra summary | `infra-summary.md` | `<link>` |
| Infra topology | `infra-topology.md` | `<link>` |
| Request/event connectivity | `connectivity.md` | `<link>` |
| Per-API spec | `api-spec.md` | `<link>` |
| Data model / ERD | `erd.md` | `<link>` |
| L4 detail | `l4-spec.md` | `<link>` |
| Layer-presence table | `layer-presence-table.md` | `<link>` |
| Observability | `observability-spec.md` | `<link>` |
| Orchestration | `orchestrator.md` | `<link>` |
| Decisions | `adr.md` (one ADR per decision) | `<links>` |

## Diagrams (draw.io, house style)
- **Architecture / HLD:** `<path/to/*.drawio>` (raw draw.io XML via the external `drawio` skill house style)
- **Component:** `<…components.xml…>`  ·  **ER:** `<…database-er.xml…>`

## `component_map` / `api_contracts` summary (mirrors the JSON contract)
- **Components (N):** `<list>`  ·  **API contracts (N):** `<list>`

## Sign-off (Tech Lead + governance — sync named L3)
- **Approver(s):** `<named human(s)>`  ·  **Verdict:** ☐ Approve ☐ Approve-with-caveats ☐ Reject
- **Date:** `<YYYY-MM-DD>`  ·  **audit_id:** `<audit_id:UUID>`  ·  **Notes:** `<…>`
