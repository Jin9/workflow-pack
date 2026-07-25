# RATIONALE — designing-tech-lead-handoff

> **Audience**: humans reviewing the skill before merge / promotion.
> **Not loaded into LLM context.** Skills load `SKILL.md` + `references/`;
> this file lives at `audit/` specifically because the loader does not pull it
> (mirrors `dev-squad/skills/implement-backend-feature/RATIONALE.md`).
>
> **Authoritative sources**: `integration/stages/2-tl-design/tl-design-scaffold-v1.1.md`
> (the procedure spec), `reference/squad-flow-snapshot/docs/roles.md`
> (Tech-Lead emission order), and the templates under
> `reference/squad-flow-snapshot/docs/templates/`.
>
> **Rename note (2026-05-28).** Renamed `tl-design-from-brief` →
> `designing-tech-lead-handoff`; pipeline stage `tl-design` →
> `designing-tech-lead-handoff` and failure queue `tl-design-pending` →
> `designing-tech-lead-handoff-pending`. The external `integration/` wiring
> (`delivery-pipeline.yaml` stage id + skill path, `integration/schemas/tl-design.json`,
> the `tl-design.skill_version` pin) lives outside this repo and must be updated
> there for the rename to take effect end-to-end. Old tokens and external
> scaffold/pipeline paths below are preserved as authoring-time provenance.

## 0. Narrowing to the system-design blueprint (v0.2.0, 2026-06-07)

The skill was **narrowed** from the full Tech-Lead handoff to the
**system-design blueprint** only. Rationale: the v0.1.0 skill owned eight
unrelated concerns in one pass (contracts, components, infra, ADRs, per-service
API specs, per-story L4 specs, event catalog, architecture diagram), violating
the "one responsibility per skill / black-box to its IO contract" principle.

**KEPT (this skill):** bounded contexts + layer-presence, `component_map`,
`api_contracts` (the cross-component *interface* contracts), the 4 infra docs,
ADRs, the consolidated L1–L4 architecture `.drawio` (+ its `.spec.json` and the
`scripts/spec_to_drawio.py` generator), the consolidated ER / `data_model`
boundaries, smells/coverage/open-questions, and the *architectural
identification* of orchestrators (which context needs a process manager + the
ADR).

**SPLIT OUT (trimmed, not built here) — target home:**

| Removed concern | Was | Moves to |
|---|---|---|
| Per-service API endpoint specs | `api_specs[]`, `templates/api-spec.md` | S3 `contract-design` stage |
| Event catalog (domain/process events) | `event_catalog`, `references/event-catalog-split.md`, `tests/assertions/event-split-discipline.md` | S3 `contract-design` stage |
| Per-story L4 implementation specs (+ `spec` mode) | `l4_specs[]`, `templates/l4-spec.md`, input `mode`/`story_id`/`prior_design_ref` | a future detailed-design skill |
| Detailed orchestrator state-machine spec | `orchestrators[]`, `templates/orchestrator.md`, `references/orchestrator-scaffold.md`, `references/mermaid-conventions.md` | a future detailed-design skill |

The detailed-design skills are **deliberately NOT authored** in this change
(scope stayed on the one system-design skill). Until they exist, those concerns
are simply not produced by S2.

**Boundary impact:** `workflows/schemas/tl-design.json` is permissive and only
requires `component_map`/`api_contracts`/`audit_id`, so the narrowed output still
satisfies it — no boundary-schema edit was needed. The downstream `from_stage`
mappings (S2.5/S3/S4a/S4b) already consume only `component_map`/`api_contracts`,
so wiring is unaffected.

**Version + ripple:** bumped `0.1.0 → 0.2.0` (the output contract narrowed — a
breaking change; one version = one immutable artifact). The exact pins in
`workflows/delivery-pipeline.yaml`, `dashboard-data.json`, and
`delivery-pipeline-flow.drawio` were synced. (This supersedes the stale §6 R1
note below, written when the YAML used a `^0.1.0` caret range — the pipeline is
now exact-pinned, so a `0.2.0` bump is a one-line pin update, not an unresolve.)

## 1. Why this skill exists

The `tl-design` stage in `integration/delivery-pipeline.yaml` pointed at a
non-existent `skills/tl-design-from-brief` (WORKFLOW_GAP_ANALYSIS GAP-01 /
OI-002). Without it the pipeline could not resolve past `ux-intake`, and the
four downstream stages that consume `tl-design.{api_contracts, component_map}`
broke. This skill fills the Design stage so `ba-analyze → … → qa-plan` runs.

## 2. What was extracted from the source

| Source | Target in this skill | Notes |
|---|---|---|
| `roles.md` Tech-Lead row (6 artifacts + ADRs, emitted in order) | `SKILL.md` Procedure emission order | contracts → components → infra-summary → infra-topology → connectivity → observability-spec → ADRs. |
| `tl-design-scaffold-v1.1.md` §2/§3/§4/§5/§6/§8/§9 | `references/*` (distilled) + `templates/layer-presence-table.md` (transcribed) | Scaffold is the upstream spec; not loaded at runtime. (§7 orchestrator + the `l4-spec` transcription were removed at v0.2.0 — see §0.) |
| `templates/tech-lead-contracts.md`, `tech-lead-components.md`, `infra-summary.md`, `infra-topology.md`, `connectivity.md`, `observability-spec.md`, `adr.md`, `erd.md` | `templates/` — **copied verbatim** (`cp`) | Faithful, no transcription risk. |
| `templates/api-spec.md` | (removed at v0.2.0 — see §0) | Per-service API specs split out to the detailed-design concern. |
| `tech-lead-contracts.md` / `tech-lead-components.md` embedded JSON Schemas | `schemas/output.json` `api_contracts` / `component_map` | Lifted byte-faithful so backend/frontend implement+review consume them unchanged. |
| `eliciting-banking-brief/schemas/output.json` `definitions` | `schemas/input.json` `definitions` (Epic/Story/Stakeholder/AcceptanceCriterion/BankingGradeRow/GovernanceGap/Translations) | Inline-copied (value-handoff; no cross-file `$ref` — no artifact-handoff skill yet). |
| `eliciting-banking-brief/SKILL.md` frontmatter | `SKILL.md` frontmatter shape | Mirrors the house exemplar (single-line `banking_grade`, tier_* keys). |

## 3. What was added (v0.1-specific)

- `oneOf` discriminator `design | partial_design | blocked_design` with
  pre-architecture gates (BA ready-for-tl, P1 governance, UX contract).
- Schema-level naming discipline: `command.name` negative-lookahead bans
  `Submit*/Process*/Handle*/Manage*`; event-name triple-segment pattern;
  disjoint `domain_events`/`process_events` arrays encode the §7 split.
- `architecture_smells[]` machine-checkable: every `fail` carries `revised`
  or an `adr_ref`.
- `references/consuming-ba-brief.md` — the only genuinely new analysis prose
  (how BA `governance_gaps`/`banking_grade_concerns`/epic-workstreams map to
  contexts/ADRs/L3/L4).

## 4. What was intentionally dropped

- The scaffold §11 "refactor `fintech-systems-architect`" path — superseded
  by the net-new decision (see §5).
- Per-service API specs, per-story L4 specs, and the event catalog — split out
  to the detailed-design concern at v0.2.0 (see §0).

> Superseded since v0.1: draw.io is no longer a deferred concern and `scripts/`
> is no longer empty. The consolidated offline L1–L4 `.drawio` is now generated
> deterministically by `scripts/spec_to_drawio.py` at step 7 (see
> `references/drawio-architecture-conventions.md`); the ASCII `infra-topology.md`
> remains the one-screen deployment view.

## 5. Deviations from the plan (flagged)

| Plan said | We did | Why |
|---|---|---|
| Scaffold §12 implies the skill follows the `fintech-systems-architect` refactor | Net-new skill; `architecting-fintech-systems` untouched (stays a manual persona reference) | In-place upgrade not viable (no skill-v1 frontmatter, prose output, 4-mode persona, wrong output contract). User-approved. |
| Scaffold example frontmatter shows `created_by: tl-design-from-brief-v1.0.0` | `version: 0.1.0` | Satisfies `delivery-pipeline.yaml` `tl-design.skill_version: "^0.1.0"` with **zero pipeline edits**. `v1.0.0` would fall out of `^0.1.0` range. The `created_by` literal in scaffold examples is cosmetic; the skill emits its actual version at runtime. |
| 4 dev skills use `audit_level: detailed` | `audit_level: enhanced` | `enhanced` is the design-weight semantic (matches `eliciting-banking-brief`) and is robust regardless of GAP-06 apply-order. GAP-06 widens the enum to include `detailed` but this skill does not depend on that. |
| `tests/README.md` | `tests/harness-guide.md` | `scripts/quick_validate.py` `BANNED_DOCS` refuses any skill folder containing `README.md` at any depth (per `implement-backend-feature/RATIONALE.md §5`). |
| Nested `banking_grade:` block | inline `banking_grade: {…}` one line | `quick_validate.py` is a flat-YAML parser that errors on indented frontmatter. Round-trips identically through real YAML. |
| Test case derived from real `ecommerce-v9` 208KB BA output | Compact hand-built single-epic case valid against `schemas/input.json` | A shape-assertion fixture does not need the full 208KB reshape; an `ecommerce-v9`-derived case is a follow-up. |
| `integration/schemas/tl-design.json` re-specifies the full output | Permissive superset enforcing only `required_fields` | Single source of truth = this skill's `schemas/output.json`. The pipeline pins a *version range*, so a permissive boundary is the only drift-free contract. Strict boundary validation should wait for GAP-03's `contract-validation`/`artifact-handoff`. |

## 6. What still needs human review

- **R3 — downstream `design_document` impedance (out of scope, GAP-03).**
  `implement-backend-feature/schemas/input.json` requires
  `design_document`(string)+`target_package`, but the pipeline wires
  `tl-design: [api_contracts, component_map]` (objects). This skill is correct
  against the *stage contract* (`required_fields: [api_contracts,
  component_map, audit_id]`); the per-context `l4_specs[].content` MD is
  precisely the `design_document` a future `artifact-handoff` (GAP-03) must
  map, with `l4_specs[].context_id` → `target_package`. `backend-review` /
  `frontend-review` consume `tl-design: [api_contracts]` directly and are
  lower-risk.
- **R1 — version pin (UPDATED v0.2.0).** The pipeline is now EXACT-pinned
  (`skill_version: "0.2.0"`, not a `^` caret range), so bumping the folder
  `version` requires the matching one-line pin update in
  `workflows/delivery-pipeline.yaml` (+ `dashboard-data.json` +
  `delivery-pipeline-flow.drawio`). The old "must stay 0.1.x to stay in the
  `^0.1.0` range" constraint no longer applies.
- **R4 — BA-def drift.** `schemas/input.json` inlines BA defs pinned to
  `eliciting-banking-brief` (pipeline allows `^1.4.0`, so `1.5.x` is allowed).
  `tests/assertions/ba-def-drift.md` formalizes the sync obligation.
- **Idempotency** (`banking_grade.idempotent: true`) is a behavioral contract
  the harness checks, not the schema — low temperature + explicit
  `idempotency_key` thread mitigate generative variance.

## 7. Recommended next step

GAP-03 — the shared `contract-validation` + `artifact-handoff` skills. Without
`artifact-handoff`, R3 remains an unbridged boundary between `tl-design` and
`backend-implement`. Build before relying on an automated end-to-end run past
the design stage.
