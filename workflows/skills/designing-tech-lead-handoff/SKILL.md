---
name: designing-tech-lead-handoff
version: 0.3.0
description: "Convert an approved BA epic-and-stories brief plus a UX design pack into the system-design blueprint: bounded contexts, integration contracts, component map, infrastructure topology, ADRs, and a consolidated offline L1-L4 architecture diagram. Canonical 4-layer DDD+CQRS house style, failure-not-rollback discipline. Use when a BA brief is ready-for-tl and architecture, contracts, and component boundaries must be locked before backend/frontend fan-out. Use when a UX pack must be reconciled against BA stories for coverage gaps. Do NOT use for BA elicitation (breaking-down-ba-scope or elaborating-user-stories), code generation, code or architecture review, QA test design, greenfield architecture chat (architecting-fintech-systems), or inputs not past the BA ready-for-tl gate. Do NOT use for detailed design — per-service API endpoint specs, per-story L4 implementation specs, or the event catalog (a separate detailed-design concern)."
stage_type: design
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: enhanced, pii_handling: redact, tier_default: T2, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 300
max_retries_recommended: 0
fallback: human-queue
recommended_temperature: {T1: 0.1, T2: 0.2, T3: 0.4}
tier_review_levels: {T1: [L0, L1, L2], T2: [L0, L1, L2], T3: [L0, L1]}
compatibility: claude-code, codex, opencode
---

# Skill: Designing Tech-Lead Handoff

## Purpose

Consume the ready-for-tl BA brief plus the UX pack and emit the **system-design
blueprint** — the load-bearing architecture the Tech-Lead owns before
backend/frontend fan-out: bounded contexts, integration contracts, component
map, infrastructure topology, ADRs, and the consolidated L1–L4 architecture
diagram. Structured by the TL Design Scaffold Pack v1.1 (distilled into
`references/`). The TL **surfaces architecture risk and locks load-bearing
decisions as ADRs; it does not implement and does not let downstream consumers
renegotiate boundaries.** Detailed design — per-service API endpoint specs,
per-story L4 implementation specs, and the event catalog — is a **separate
concern, out of this skill's scope** (see `audit/RATIONALE.md`). Output is a
single JSON document conforming to `schemas/output.json`; the architecture
directory tree is carried as `path`+`content` entries inside that JSON so the
caller can persist it and downstream consumers can address artifacts per
context.

## When to use this skill

- Use: a BA `elaborating-user-stories` manifest with `state: ready-for-tl` and a
  `generate-ux-pack` pack are available; the `designing-tech-lead-handoff`
  pipeline stage (S2) fires.
- Use: architecture, contracts, and component boundaries must be locked before
  backend/frontend fan-out, or a UX pack must be reconciled against BA stories
  for coverage gaps.
- Do NOT use: BA elicitation, code generation, review, QA test design, or
  exploratory architecture (route those to the skills named in the frontmatter
  `description`).
- Do NOT use for **detailed design** — per-service API endpoint specs,
  per-story L4 implementation specs, or the event catalog (a separate
  detailed-design concern, e.g. the S3 contract-design stage).

## Input contract

ADVISORY — documents the assembled stage input; the engine validates workflow input
and stage OUTPUTS only (engine/validation.py). Validate against `schemas/input.json`.
Required: `epics` + `stories` (engine-hydrated from the ba-brief ref-chain;
`story_files` refs retained; hydrated shapes owned by elaborating-user-stories'
`epic-sidecar.json` / `story-sidecar.json`), `governance_gaps`, the ux-intake
paths `pack_dir` + `tokens_path` + `route_map_path` + `component_inventory_path`
(pack-relative POSIX — resolve via `dirname(upstream_artifacts["ux-intake"])`,
verify containment in `pack_dir`, reject absolute paths and `..` traversal), and
`idempotency_key` (engine-injected; same key + inputs ⇒ same design). Optional
engine-injected: `upstream_artifacts`, `loop_back_feedback` (plan-review findings
the re-run must address). The legacy singular `epic`/`initiative`/`tier_hint`
fields are gone — nothing assembles them.

**Example (validates against schemas/input.json):**
```json
{
  "epics": [{ "id": "EPIC-CHECKOUT", "title": "Checkout" }],
  "story_files": [{ "epic": "EPIC-CHECKOUT", "file": "EPIC-CHECKOUT/STORY-CHECKOUT-01.json" }],
  "stories": [{ "id": "STORY-CHECKOUT-01", "epic_id": "EPIC-CHECKOUT", "title": "Customer pays" }],
  "governance_gaps": [],
  "pack_dir": "ux-design-c3f8a1d2",
  "tokens_path": "ux-design-c3f8a1d2/tokens.json",
  "route_map_path": "ux-design-c3f8a1d2/route-map.md",
  "component_inventory_path": "ux-design-c3f8a1d2/component-inventory.md",
  "idempotency_key": "d4b8c2a0-7e31-4f95-8a6d-2c9e1b0f3a47"
}
```

**Pre-flight gates (step 1 below):**

- Read the ba-brief INDEX manifest via `upstream_artifacts["ba-research"]` and
  require manifest `state == ready-for-tl`; any `governance_gaps[]` entry with
  `blocks_tl_handoff: true` → emit `output_type: blocked_design` with a
  `BLOCK-BA-NOT-READY` / `BLOCK-P1-GOVERNANCE` blocker. Do not architect on a
  governance-blocked brief. (The old checks on `output_type`,
  `blocks_tl_handoff`, and `frontmatter.status` read fields the assembled
  payload never carries — the manifest `state` is the readiness signal.)
- Missing `tokens_path` or `route_map_path` → `blocked_design` with
  `BLOCK-UX-CONTRACT`.

## Procedure

Emission order is contracts → components → infra-summary → infra-topology →
connectivity → observability-spec → ADRs → architecture diagram, interleaved
with the scaffold-v1.1 structural requirements. This skill produces the
**system-design blueprint only**; per-service API specs, per-story L4 specs, and
the event catalog are a separate detailed-design concern (see
`audit/RATIONALE.md`).

1. **Pre-flight — brief + UX gate.** Validate input against
   `schemas/input.json`. Apply the two gates above. Read
   `references/consuming-ba-brief.md`. Collect every story's
   `banking_grade_concerns` row with `status: applies` into a working list that
   the L3 §6.5 failure/connectivity content and the ADRs MUST honor.
   Non-blocking `governance_gaps` become candidate ADRs.
2. **Context discovery + layer-presence declaration.** Derive bounded contexts
   from epic workstreams (never a tech-layer split — mirrors the BA AP-7.1).
   Load `references/canonical-architecture-layers.md`. Emit the per-context
   layer-presence table (`templates/layer-presence-table.md`) with a mandatory
   non-"following the pattern" rationale; instantiate an Orchestrator **as an
   architectural component** only when ≥1 of the 3 signals (multi-Aggregate /
   compensation / temporal) fires, and cite the signal. **Begin the
   architecture spec**: record the derived `contexts[]`, `actors[]`,
   `externals[]`, `aggregates[]` (each with its `root` table + owned
   `tables[]`), and `process_aggregates[]` into the in-progress
   `diagrams/{system}-architecture.spec.json` (schema in
   `references/drawio-architecture-conventions.md`).
3. **Emit integration contracts (artifact 1 → `api_contracts`).** Per
   `templates/tech-lead-contracts.md`. Every cross-component HTTP action and
   every async event gets one contract with non-vague `idempotency_rules`
   (key shape + scope + TTL + collision), enumerated `failure_modes`, explicit
   `ordering_guarantees` (async MUST name the partition key), `contract_version`.
   These are the component **interfaces** (the architecture's connective
   tissue) — NOT per-service endpoint specs (a detailed-design concern).
4. **Emit component map (artifact 2 → `component_map`).** Per
   `templates/tech-lead-components.md`. `dependencies[]` reference ONLY
   `contract_name`s emitted in step 3 — an orphan dependency is a structural
   failure (`partial_design`, FM-TL-03). **Mirror into the architecture spec**:
   each component + its datastore → `services[]`/`datastores[]`, and each
   cross-component HTTP / event edge (from the step-3 contracts) →
   `topology[]` with `kind: sync|async` — no new analysis, these derive from
   artifacts already emitted.
5. **Emit infra summary, topology, connectivity, observability spec
   (artifacts 3–6).** In that exact order, per the four copied templates. Load
   `references/failure-retry-strategy.md` for the L3 §6.5 failure≠rollback
   content woven into connectivity/observability. infra-topology is one single
   ASCII fenced block (one-screen rule).
6. **Emit ADRs.** One ADR per load-bearing decision (sole-writer, outbox,
   lock-order pin, Orchestrator instantiation when contested, every
   non-blocking governance gap that drove a trade-off) per `templates/adr.md`.
   IDs `ADR-NNN` zero-padded sequential.
7. **Emit the architecture spec + consolidated diagram.** Finalize
   `diagrams/{system}-architecture.spec.json` per
   `references/drawio-architecture-conventions.md`: complete the `tables{}` map
   (one entry per table, `rows: [[flag, "col : TYPE"], …]`, lifting the schema
   detail from the data model — see `templates/erd.md`) and the `fks[]`
   (classed `intra|composition|cross`). Then **invoke the deterministic
   generator — never hand-write `.drawio`**:
   `python3 scripts/spec_to_drawio.py --input diagrams/{system}-architecture.spec.json --output diagrams/{system}-architecture.drawio`.
   This renders ONE offline file with five tabs (L1 System Context · L2
   High-Level Design · L3 Components & Aggregates · L4 ER & Aggregate→Table
   Boundaries · Legend / Standard Template), in the hivemind house style
   (New/Enhanced/Existing/External component colours, Sync/Async/Authorization
   connections) with edges anchored + gutter-routed so no arrow crosses a box.
   Record `diagrams.{architecture_drawio, architecture_spec,
   erd_consolidated, offline:true}` in the output. Emit the optional
   `data_model` block **only** once the per-service split ER pack exists (its
   `index` is mandatory, mirroring the boundary); until then the consolidated
   ER is carried by `diagrams.erd_consolidated`. Both blocks are
   present-or-absent, **never `null`**. The generator fails closed if any table
   is unowned or doubly-claimed by an aggregate.
8. **Architecture-smells self-audit (gate).** Run the 10-item L3 checklist in
   `references/architecture-smells.md`. Every failing item → revise the design
   OR file an ADR (step 6) naming the smell as a knowing trade-off. Record
   each as an `architecture_smells[]` entry; an unresolved `fail` downgrades
   `output_type` to `partial_design`.
9. **UX reconciliation.** Run the manual UX acceptance checklist
   (`references/ux-input-contract.md`) against the three UX paths. Every
   customer-facing BA story maps to ≥1 UX route and vice-versa; mismatches →
   `coverage_gaps[]` (non-blocking, FM-TL-08).
10. **Assemble + self-validate.** Emit JSON conforming to
    `schemas/output.json`; set `output_type`; compute `audit_id`; populate
    `processing_metadata`. Re-run the four `tests/assertions/*` gates before
    returning. **Diagram determinism gate:** re-run `scripts/spec_to_drawio.py`
    a second time and assert byte-identical output; assert the source
    `.drawio` is offline-clean (no `image=http`, `src=`, `@import`,
    `@font-face`). Any diff or external reference is a build failure.

## Output contract

`schemas/output.json`, `oneOf` discriminated by `output_type`:

- **`design`** — requires `component_map`, `api_contracts`, `infra_summary`,
  `infra_topology`, `connectivity`, `observability_spec`, `adrs`, `audit_id`,
  `processing_metadata` (plus optional `coverage_gaps`, `architecture_smells`,
  `open_questions`, and the step-7 `diagrams` + `data_model` blocks). The
  pipeline-mandated required fields are exactly `component_map`, `api_contracts`,
  `audit_id`. Contract entries SHOULD name `provider_component` /
  `consumer_components` (resolving against `component_map`) and structured
  `async_channel` data — optional for compatibility with frozen artifacts.
- **`partial_design`** — a contract/dependency gate failed, but the blueprint
  still ships: requires `component_map`, `api_contracts`, AND non-empty
  `blocking_findings[]`, so it reaches the mandatory named-human gate for
  adjudication.
- **`blocked_design`** — pre-architecture stop; carries non-empty `blockers[]`,
  no artifacts. **Intentionally fails the stage boundary** (which requires
  `component_map` + `api_contracts`) and routes to the
  `designing-tech-lead-handoff-pending` human queue — the boundary is a
  superset of the success branch only, not of the failure branches.

`audit_id` is producer-stamped and deterministic —
UUIDv5(HOUSE_NS, "tl-design:{idempotency_key}") with HOUSE_NS =
uuid5(NAMESPACE_URL, "https://squad-delivery/audit") — distinct from the
engine's per-attempt execution audit id. `processing_metadata.skill_version`
equals the frontmatter version at production time (historical artifacts keep
their original producer version).

JSON is canonical; the architecture tree is described by `path`+`content`
entries (contracts.json, components.json, the 4 MD docs, `ADRs/`) plus the
consolidated `diagrams/` artifacts. **Out of scope** (separate detailed-design
concern): per-service API specs, per-story L4 specs, and the event catalog.

**Example (validates against schemas/output.json):**
```json
{
  "output_type": "blocked_design",
  "blockers": [
    { "code": "BLOCK-P1-GOVERNANCE", "description": "Legal-absent governance gap blocks TL handoff." }
  ],
  "audit_id": "82ca53e0-2bfd-56ef-bed1-dffa9ff88ba2",
  "processing_metadata": {
    "skill_name": "designing-tech-lead-handoff",
    "skill_version": "0.3.0",
    "started_at": "2026-07-12T00:00:00Z",
    "completed_at": "2026-07-12T00:00:00Z",
    "tier": "T2",
    "mode": "full"
  }
}
```

## Failure Modes

| ID | Trigger | Output | Route |
|---|---|---|---|
| FM-TL-01 | BA not ready-for-tl / P1 governance unresolved | `blocked_design` `BLOCK-BA-NOT-READY`/`BLOCK-P1-GOVERNANCE` | designing-tech-lead-handoff-pending |
| FM-TL-02 | UX contract incomplete (no tokens.json / route-map) | `blocked_design` `BLOCK-UX-CONTRACT` | designing-tech-lead-handoff-pending |
| FM-TL-03 | Orphan contract dependency (component cites non-existent contract_name) | `partial_design` + structural finding | designing-tech-lead-handoff-pending |
| FM-TL-04 | Vague contract (`idempotency_rules:"Idempotent"`, `failure_modes:["Various"]`, async w/o partition key) | `partial_design` + per-contract finding | designing-tech-lead-handoff-pending |
| FM-TL-06 | Unjustified Orchestrator (no signal) OR missing Orchestrator (signal present) | architecture-smell; revise or ADR | inline |
| FM-TL-07 | Output fails `schemas/output.json` | hard fail — `max_retries:0` → straight to human-queue | designing-tech-lead-handoff-pending |
| FM-TL-08 | UX route↔story coverage gap | non-blocking `coverage_gaps[]` | inline |

Note: this skill is configured with `max_retries: 0` / `on_failure:
human-queue` — there is no retry budget; any hard failure escalates to a
human (the caller's `designing-tech-lead-handoff-pending` queue or equivalent).

## Constraints

- Tech-layer context split → split by epic workstream.
- Orchestrator with business logic (`if cart.subtotal > X`) → Domain Processor
  owns correctness ("the Orchestrator answers 'what's next?' never 'is this
  correct?'").
- `failure = rollback` by default → failure≠rollback; compensation is the
  documented exception only.
- ADR with no Alternatives / fuzzy Decision (the adr.md negative examples).
- Fabricated external vendor/version in topology → mock-only unless the brief
  states the integration.
- Silently architecting past an unresolved BA P1 governance gap → block, do
  not launder.
- Hand-writing or raster-exporting the architecture `.drawio` → always run the
  deterministic `scripts/spec_to_drawio.py` generator (offline vector only).

## References

Progressive disclosure — load the file at the step that needs it:

- `references/consuming-ba-brief.md` — step 1
- `references/canonical-architecture-layers.md` — step 2
- `references/failure-retry-strategy.md` — step 5
- `references/architecture-smells.md` — step 8
- `references/ux-input-contract.md` — steps 1, 9
- `references/drawio-architecture-conventions.md` — steps 2, 7 (the consolidated
  L1–L4 `.drawio` spec + generator)

`audit/RATIONALE.md` is human-only and MUST NOT be loaded into LLM context.
The scaffold-v1.1 source has been distilled into these references; it is not
loaded at runtime.
