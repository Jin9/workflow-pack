# S2 · TL Design — ShopPilot

| | |
|---|---|
| **Stage** | S2 · TL Design |
| **Skill** | `designing-tech-lead-handoff 0.2.0` |
| **Owner / Gate** | Tech Lead + governance · **sync NAMED (L3)** — no auto-retry → queue `tl-design-pending` |
| **Input** | `ba.brief` (S1, `ready-for-tl`) + `ux.pack` (S1.5) |
| **Output contract** | `output.json` (`output_type: design`) + the `design/architecture/` tree |
| **Human-view** | markdown + draw.io house style (HTML viewer planned) |
| **State** | ✅ produced (2026-06-04) · re-scoped to the **system-design blueprint** (2026-06-07, skill `0.2.0`) · `output_type: design` · skill-schema **+ boundary** PASS |

System-design **blueprint** produced by `designing-tech-lead-handoff 0.2.0` from the S1 brief (4 epics / 8
stories) + the S1.5 UX pack: bounded contexts, integration contracts (`api_contracts`), `component_map`,
the 4 infra docs, 8 ADRs, and the consolidated offline L1–L4 architecture `.drawio`.

> **Re-scope note (2026-06-07).** The skill was narrowed to system/architecture design only. The former
> **detailed-design** outputs — per-service API specs, per-story L4 specs, and the event catalog — are no
> longer S2's responsibility (separate detailed-design concern, e.g. S3 contract-design). The earlier
> demo's detailed-design files were moved verbatim to **`_deferred-detailed-design/`** (preserved, not
> deleted); the `output.json` `l4_specs` / `api_specs` / `event_catalog` / `orchestrators` blocks were
> dropped. The architecture `.drawio` was regenerated offline-clean by `scripts/spec_to_drawio.py`
> (the previous demo file carried CDN icon URLs — an offline-rule violation now removed).

## Documents

```
output.json                         the machine contract (component_map · api_contracts ·
                                     infra/observability MdArtifacts · adrs · diagrams ·
                                     architecture_smells · coverage_gaps · open_questions · audit_id)
design/architecture/
  03-infra-summary.md  04-infra-topology.md  05-connectivity.md  06-observability-spec.md
  ADRs/ADR-001..ADR-008-*.md        8 accepted ADRs
architecture-overview.md            human-readable mirror (bounded contexts, NFR map)
project-structure.md                polyrepo Go + React layout
diagrams/shoppilot-architecture.drawio    consolidated offline L1–L4 + Legend (regenerated, vector-only)
diagrams/*.sql, *.spec.json               schema DDL + the generator's source spec

_deferred-detailed-design/          split-off (detailed-design concern; preserved, not part of S2 output):
  design/architecture/02-event-catalog.md
  design/architecture/contexts/<ctx>/api-spec.md          per-service API spec
  design/architecture/contexts/<ctx>/stories/EPIC-*-L4-spec.md   8 per-story L4 specs
```

## S2.5 loop-back (cap 1) — recorded

The round-1 `plan-review` (S2.5) returned **REVISE** on finding **RT-2** (sync orchestration per ADR-007
had a dual-write / partial-failure window). The one allowed loop-back added **ADR-008** (transactional
outbox + idempotent `order.create`/capture retry, TTL backstop). Round-2 `plan-review` → **PROCEED**.
See `../S2.5-plan-review/`.

## Caveats

- **Boundary-schema validated.** `output.json` validates against both the skill's own narrowed `schemas/output.json` (the `design` branch) **and** the node boundary `workflows/schemas/tl-design.json` (which now exists; requires `[component_map, api_contracts, audit_id]`).
- **One ADR-justified deviation.** `architecture_smells` records the no-standalone-Orchestrator decision as `fail → resolution: adr (ADR-007)`, mitigated by ADR-008.
- **Carried gaps (non-blocking):** UX `coverage_gaps` from S1.5 (admin stories without UX route; catalog/cart routes without a BA story) and 3 open questions (delivery-confirm, abandoned-cart, numeric SLO thresholds).

## Sign-off (Tech Lead + governance — sync named L3)

- **Approver(s):** `<named human(s)>` · **Verdict:** ☐ Approve ☐ Approve-with-caveats ☐ Reject
- **Date:** `<YYYY-MM-DD>` · **audit_id:** `a7d3e9f1-5b24-4c80-9e16-3f8a2b5c1d09` · **Notes:** `<…>`

> Gate is **pending** — an AI agent cannot sign the L3 named-human approval. The artifact is ready for that review.
