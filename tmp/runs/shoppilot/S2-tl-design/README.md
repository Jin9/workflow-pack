<!-- TEMPLATE basis: .archive/agentic-delivery-pipeline/reference/integration/templates/S2-tl-design-index.md -->
# S2 · TL Design — ShopPilot (project-structure draft)

> **Stage:** S2 TL Design · owner **Tech Lead + governance** · skill `tl-design-from-brief ^0.1.0` · gate **sync (L3)**.
> **Input:** `ba.brief` (S1) + `ux.pack` (S1.5). **Emits:** `tl.design`. **Output contract:** `tl-design.json`
> (`component_map`, `api_contracts`, `audit_id`) + ADR docs. **Human-view:** draw.io (house style) + markdown.

This folder is the **project-structure design** for ShopPilot, drafted ahead of S1.5/the rest of the run. It is
**design intent, not code** — the actual Go/TSX is emitted at S4a/S4b from these decisions.

> ⚠️ This is a partial S2: it covers the **structure** (component map + repo layout + data model). The full
> `tl-design.json` machine contract, per-API specs, per-story L4 specs, and the split event catalog (what the
> `designing-tech-lead-handoff` skill emits) are **not** produced here — see the overview's S2 for the complete shape.

## Documents

| Concern | Doc |
|---|---|
| Repository / directory layout (polyrepo Go + React) | [`project-structure.md`](project-structure.md) |
| Bounded contexts · component map · events · tech stack · NFR mapping · decisions | [`architecture-overview.md`](architecture-overview.md) |
| High-level architecture diagram (HLD) | [`diagrams/shoppilot-architecture.drawio`](diagrams/shoppilot-architecture.drawio) |
| Entity-relationship diagram (ERD) | [`diagrams/shoppilot-erd.drawio`](diagrams/shoppilot-erd.drawio) |

## Sign-off (Tech Lead + governance — sync named L3)

- **Approver(s):** `<named human(s)>` · **Verdict:** ☐ Approve ☐ Approve-with-caveats ☐ Reject
- **Date:** `<YYYY-MM-DD>` · **audit_id:** `<audit_id:UUID>` · **Notes:** `<…>`
