# S2 · TL Design — ShopPilot

| | |
|---|---|
| **Stage** | S2 · TL Design |
| **Skill** | `designing-tech-lead-handoff 0.1.0` |
| **Owner / Gate** | Tech Lead + governance · **sync NAMED (L3)** — no auto-retry → queue `tl-design-pending` |
| **Input** | `ba.brief` (S1, `ready-for-tl`) + `ux.pack` (S1.5) |
| **Output contract** | `output.json` (`output_type: design`) + the `design/architecture/` tree |
| **Human-view** | markdown + draw.io house style (HTML viewer planned) |
| **State** | ✅ produced (2026-06-04) · `output_type: design` · skill-schema PASS |

Full Tech-Lead handoff produced by `designing-tech-lead-handoff 0.1.0` from the S1 brief (4 epics / 8
stories) + the S1.5 UX pack. This supersedes the earlier **partial** draft (which covered only the
structure); the machine contract, per-service API specs, per-story L4 specs, ADRs and the split event
catalog are now present.

## Documents

```
output.json                         the machine contract (component_map · api_contracts ·
                                     infra/observability MdArtifacts · adrs · l4_specs · event_catalog ·
                                     architecture_smells · coverage_gaps · open_questions · audit_id)
design/architecture/
  02-event-catalog.md               9 domain events (audit_id-keyed), 0 process events
  03-infra-summary.md  04-infra-topology.md  05-connectivity.md  06-observability-spec.md
  ADRs/ADR-001..ADR-008-*.md        8 accepted ADRs
  contexts/<auth|inventory|checkout|order>/api-spec.md        per-service API spec
  contexts/<ctx>/stories/EPIC-*-L4-spec.md                    8 per-story L4 specs
architecture-overview.md            human-readable mirror (bounded contexts, NFR map)
project-structure.md                polyrepo Go + React layout
diagrams/*.drawio, *.sql, *.spec.json   HLD + ERD (house style)
```

## S2.5 loop-back (cap 1) — recorded

The round-1 `plan-review` (S2.5) returned **REVISE** on finding **RT-2** (sync orchestration per ADR-007
had a dual-write / partial-failure window). The one allowed loop-back added **ADR-008** (transactional
outbox + idempotent `order.create`/capture retry, TTL backstop). Round-2 `plan-review` → **PROCEED**.
See `../S2.5-plan-review/`.

## Caveats

- **Boundary-schema gap.** `workflows/delivery-pipeline.yaml` names `schemas/tl-design.json` for this node, but that file does **not exist** in `workflows/schemas/`. Validated against the skill's own `schemas/output.json` (the `design` branch) + the node `required_fields` `[component_map, api_contracts, audit_id]`.
- **One ADR-justified deviation.** `architecture_smells` records the no-standalone-Orchestrator decision as `fail → resolution: adr (ADR-007)`, mitigated by ADR-008.
- **Carried gaps (non-blocking):** UX `coverage_gaps` from S1.5 (admin stories without UX route; catalog/cart routes without a BA story) and 3 open questions (delivery-confirm, abandoned-cart, numeric SLO thresholds).

## Sign-off (Tech Lead + governance — sync named L3)

- **Approver(s):** `<named human(s)>` · **Verdict:** ☐ Approve ☐ Approve-with-caveats ☐ Reject
- **Date:** `<YYYY-MM-DD>` · **audit_id:** `a7d3e9f1-5b24-4c80-9e16-3f8a2b5c1d09` · **Notes:** `<…>`

> Gate is **pending** — an AI agent cannot sign the L3 named-human approval. The artifact is ready for that review.
