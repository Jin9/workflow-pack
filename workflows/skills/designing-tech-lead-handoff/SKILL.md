---
name: designing-tech-lead-handoff
description: >
  Convert an approved BA epic-and-stories brief plus a UX design pack into the
  full Tech-Lead architecture handoff: integration contracts, component map,
  infra spec, ADRs, per-service API specs, per-story L4 specs, and a
  Domain/Process-split event catalog. Canonical 4-layer DDD+CQRS house style,
  failure-not-rollback discipline.

  Use when a BA brief is ready-for-tl and architecture + contracts must precede
  backend/frontend fan-out. Use when stories carry banking_grade_concerns
  mapping to L3/L4 specs. Use when a UX pack (tokens.json + route-map +
  component-inventory) must be reconciled against BA stories for coverage gaps.

  Do NOT use for BA elicitation (eliciting-banking-brief), code generation
  (implement-backend-feature/implement-frontend-feature), code or architecture
  review (review-backend-code/review-frontend-code), QA test design
  (planning-banking-tests), greenfield architecture chat
  (architecting-fintech-systems), or inputs not past the BA ready-for-tl gate.
compatibility: [claude-code, codex, opencode]
metadata: {version: 0.1.0, stage_type: design, input_schema: schemas/input.json, output_schema: schemas/output.json, banking_grade: {idempotent: true, reversible: n/a, audit_level: enhanced, tier_default: T2, tier_adaptable: [T1, T2, T3]}, expected_duration_p95_seconds: 300, max_retries_recommended: 0, recommended_temperature: {T1: 0.1, T2: 0.2, T3: 0.4}, tier_review_levels: {T1: [L0, L1, L2], T2: [L0, L1, L2], T3: [L0, L1]}}
---

# Skill: Designing Tech-Lead Handoff

## Purpose

Consume the ready-for-tl BA brief plus the UX pack and emit the complete
Tech-Lead handoff (the Tech-Lead role's required artifacts), structured by the
TL Design Scaffold Pack v1.1 (distilled into `references/`). The TL **surfaces
architecture risk and locks load-bearing decisions as ADRs; it does not
implement and does not let downstream consumers renegotiate boundaries.**
Output is a single JSON document conforming to `schemas/output.json`; the
architecture directory tree is carried as `path`+`content` entries inside that
JSON so the caller can persist it and downstream consumers can address
artifacts per context.

## When to use this skill

- Use: a BA `eliciting-banking-brief` output with `frontmatter.status:
  ready-for-tl` and a `generate-ux-pack` pack is available; the `designing-tech-lead-handoff`
  pipeline stage fires.
- Use: per-story L4 fan-out after a master pass (`mode: spec`).
- Do NOT use: BA elicitation, code generation, review, QA test design, or
  exploratory architecture (route those to the skills named in the frontmatter
  `description`).

## Input

| Field | Source | Notes |
|---|---|---|
| `epic` or `epics`+`initiative` | ba-analyze | Single- vs multi-epic, mutex (mirrors BA `scope_kind`). |
| `stories` | ba-analyze | BA `Story[]`; carries `banking_grade_concerns` force-fill. |
| `governance_gaps` | ba-analyze | Drives ADRs / blocking stop. |
| `tokens_path`, `route_map_path` | ux-intake | REQUIRED (scaffold §8.1). |
| `component_inventory_path` | ux-intake | Optional (not in ux-intake stage required_fields). |
| `idempotency_key` | workflow input | UUID v1–5; same key + inputs ⇒ same design. |
| `mode`, `story_id`, `prior_design_ref`, `tier_hint` | caller | `mode: spec` requires `story_id`. |

Exact shapes are in `schemas/input.json` (BA definitions inlined byte-faithful
from `eliciting-banking-brief/schemas/output.json` — see `audit/RATIONALE.md`).

**Pre-flight gates (step 1 below):**

- BA brief `output_type != brief` OR `blocks_tl_handoff: true` OR
  `frontmatter.status != ready-for-tl` OR any `governance_gaps[]` with
  `blocks_tl_handoff: true` → emit `output_type: blocked_design` with a
  `BLOCK-BA-NOT-READY` / `BLOCK-P1-GOVERNANCE` blocker. Do not architect on a
  governance-blocked brief.
- Missing `tokens_path` or `route_map_path` → `blocked_design` with
  `BLOCK-UX-CONTRACT`.

## Procedure

Emission order is contracts → components → infra-summary →
infra-topology → connectivity → observability-spec → ADRs, interleaved with
the scaffold-v1.1 structural requirements.

1. **Pre-flight — brief + UX gate.** Validate input against
   `schemas/input.json`. Apply the two gates above. Read
   `references/consuming-ba-brief.md`. Collect every story's
   `banking_grade_concerns` row with `status: applies` into a working list
   that L3 §6.5 and every L4 spec MUST honor. Non-blocking `governance_gaps`
   become candidate ADRs.
2. **Context discovery + layer-presence declaration.** Derive bounded contexts
   from epic workstreams (never a tech-layer split — mirrors the BA AP-7.1).
   Load `references/canonical-architecture-layers.md`. Emit the per-context
   layer-presence table (`templates/layer-presence-table.md`) with a mandatory
   non-"following the pattern" rationale; instantiate an Orchestrator only when
   ≥1 of the 3 signals (multi-Aggregate / compensation / temporal) fires, and
   cite the signal.
3. **Emit integration contracts (artifact 1 → `api_contracts`).** Per
   `templates/tech-lead-contracts.md`. Every cross-component HTTP action and
   every async event gets one contract with non-vague `idempotency_rules`
   (key shape + scope + TTL + collision), enumerated `failure_modes`, explicit
   `ordering_guarantees` (async MUST name the partition key), `contract_version`.
4. **Emit component map (artifact 2 → `component_map`).** Per
   `templates/tech-lead-components.md`. `dependencies[]` reference ONLY
   `contract_name`s emitted in step 3 — an orphan dependency is a structural
   failure (`partial_design`, FM-TL-03).
5. **Emit infra summary, topology, connectivity, observability spec
   (artifacts 3–6).** In that exact order, per the four copied templates. Load
   `references/failure-retry-strategy.md` for the L3 §6.5 failure≠rollback
   content woven into connectivity/observability. infra-topology is one single
   ASCII fenced block (one-screen rule).
6. **Emit ADRs.** One ADR per load-bearing decision (sole-writer, outbox,
   lock-order pin, Orchestrator instantiation when contested, every
   non-blocking governance gap that drove a trade-off) per `templates/adr.md`.
   IDs `ADR-NNN` zero-padded sequential.
7. **Emit per-Orchestrator files.** For each Orchestrator from step 2, one file
   per `templates/orchestrator.md` (`references/orchestrator-scaffold.md`):
   frontmatter + 11 sections incl. the journey `stateDiagram-v2`, commands
   table, Process-Events table, compensation under failure≠rollback, and the
   5-item Orchestrator smells self-audit.
8. **Emit per-service API specs.** One `api-spec.md` per service per
   `templates/api-spec.md` (scaffold §6.2 frontmatter + §0 Changelog; on a
   first design emit a single `v1.0 — initial` changelog entry — do not
   fabricate prior versions).
9. **Emit per-story L4 specs.** One `{story-id}-L4-spec.md` per story per
   `templates/l4-spec.md`: structured `command` (imperative; MUST NOT match
   `Submit*/Process*/Handle*/Manage*`) + `events_emitted[]` (past-tense
   `{domain}.{subject}.{verb}`, `type: domain|process`) or `events_emitted: []`
   + `no_event_rationale`, `api_spec_endpoint_ref` to step 8. Quote the BA
   Gherkin happy-path verbatim in §1.
10. **Emit the split event catalog.** Per `references/event-catalog-split.md`:
    Section A Domain Events (only from Domain Processors), Section B Process
    Events (only from Orchestrators). Every event classifies into exactly one;
    bidirectional emitter/consumer links; orphan event flagged.
11. **Architecture-smells self-audit (gate).** Run the 10-item L3 checklist in
    `references/architecture-smells.md`. Every failing item → revise the design
    OR file an ADR (step 6) naming the smell as a knowing trade-off. Record
    each as an `architecture_smells[]` entry; an unresolved `fail` downgrades
    `output_type` to `partial_design`.
12. **Command/event naming validation (gate).** Check every L4 `command.name`
    and `events_emitted[].name` against the scaffold §6.4 rules. Any violation
    blocks that L4 from `spec_status: ready-for-implementation` and downgrades
    overall `output_type` to `partial_design` (FM-TL-05).
13. **UX reconciliation.** Run the manual UX acceptance checklist
    (`references/ux-input-contract.md`) against the three UX paths. Every
    customer-facing BA story maps to ≥1 UX route and vice-versa; mismatches →
    `coverage_gaps[]` (non-blocking, FM-TL-08).
14. **Assemble + self-validate.** Emit JSON conforming to
    `schemas/output.json`; set `output_type`; compute `audit_id`; populate
    `processing_metadata`. Re-run the four `tests/assertions/*` gates before
    returning.

## Modes

- **`full`** (default) — steps 1–14, the complete handoff.
- **`spec`** — steps 9 + 12 + 14 for a single `story_id` (per-story L4 fan-out
  after a master `full` pass); `prior_design_ref` supplies the prior output.

## Output Contract

`schemas/output.json`, `oneOf` discriminated by `output_type`:

- **`design`** — requires `component_map`, `api_contracts`, `infra_summary`,
  `infra_topology`, `connectivity`, `observability_spec`, `adrs`, `l4_specs`,
  `event_catalog`, `audit_id`, `processing_metadata` (plus optional
  `orchestrators`, `api_specs`, `coverage_gaps`, `architecture_smells`,
  `open_questions`). The required output fields are exactly
  `component_map`, `api_contracts`, `audit_id`.
- **`partial_design`** — artifacts produced but a contract/naming/dependency
  gate failed; carries `blocking_findings[]`.
- **`blocked_design`** — pre-architecture stop; carries `blockers[]`, no
  artifacts.

JSON is canonical; the architecture tree is described by `path`+`content`
entries (contracts.json, components.json, the 4 MD docs, `ADRs/`,
`contexts/{ctx}/{api-spec.md,orchestrators/,stories/}`, `02-event-catalog.md`).

## Failure Modes

| ID | Trigger | Output | Route |
|---|---|---|---|
| FM-TL-01 | BA not ready-for-tl / P1 governance unresolved | `blocked_design` `BLOCK-BA-NOT-READY`/`BLOCK-P1-GOVERNANCE` | designing-tech-lead-handoff-pending |
| FM-TL-02 | UX contract incomplete (no tokens.json / route-map) | `blocked_design` `BLOCK-UX-CONTRACT` | designing-tech-lead-handoff-pending |
| FM-TL-03 | Orphan contract dependency (component cites non-existent contract_name) | `partial_design` + structural finding | designing-tech-lead-handoff-pending |
| FM-TL-04 | Vague contract (`idempotency_rules:"Idempotent"`, `failure_modes:["Various"]`, async w/o partition key) | `partial_design` + per-contract finding | designing-tech-lead-handoff-pending |
| FM-TL-05 | Command/event naming violation | block offending L4; `partial_design` | designing-tech-lead-handoff-pending |
| FM-TL-06 | Unjustified Orchestrator (no signal) OR missing Orchestrator (signal present) | architecture-smell; revise or ADR | inline |
| FM-TL-07 | Output fails `schemas/output.json` | hard fail — `max_retries:0` → straight to human-queue | designing-tech-lead-handoff-pending |
| FM-TL-08 | UX route↔story coverage gap | non-blocking `coverage_gaps[]` | inline |

Note: this skill is configured with `max_retries: 0` / `on_failure:
human-queue` — there is no retry budget; any hard failure escalates to a
human (the caller's `designing-tech-lead-handoff-pending` queue or equivalent).

## Anti-Patterns

- Tech-layer context split → split by epic workstream.
- Orchestrator with business logic (`if cart.subtotal > X`) → Domain Processor
  owns correctness ("the Orchestrator answers 'what's next?' never 'is this
  correct?'").
- Process Events from Domain Processors, or Domain Events from Orchestrators →
  event-split discipline.
- `failure = rollback` by default → failure≠rollback; compensation is the
  documented exception only.
- L4 spec duplicating the API contract → reference it via
  `api_spec_endpoint_ref`.
- ADR with no Alternatives / fuzzy Decision (the adr.md negative examples).
- Fabricated external vendor/version in topology/api-spec → mock-only unless
  the brief states the integration.
- Silently architecting past an unresolved BA P1 governance gap → block, do
  not launder.

## References

Progressive disclosure — load the file at the step that needs it:

- `references/consuming-ba-brief.md` — step 1
- `references/canonical-architecture-layers.md` — step 2
- `references/failure-retry-strategy.md` — step 5
- `references/architecture-smells.md` — steps 11, 7
- `references/orchestrator-scaffold.md` — step 7
- `references/event-catalog-split.md` — steps 3, 9, 10, 12
- `references/ux-input-contract.md` — steps 1, 13
- `references/mermaid-conventions.md` — steps 5, 7, 9

`audit/RATIONALE.md` is human-only and MUST NOT be loaded into LLM context.
The scaffold-v1.1 source has been distilled into these references; it is not
loaded at runtime.
