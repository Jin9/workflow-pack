---
name: eliciting-banking-brief
description: >
  Convert raw BA input (Jira, Slack, meeting notes, email, mixed prose)
  into a structured epic-plus-stories brief with banking-grade fields
  force-evaluated, ambiguities surfaced as open questions, and governance
  gaps (Legal-absent, tipping-off, missing PII inventory, unresolved
  regulator citations) escalated as P1 blockers.

  Use when a user submits a Jira ticket, Slack export, meeting transcript,
  email thread, or mixed-source brief for BA elicitation. Use when raw
  input describes a banking workflow (KYC, EDD, AML, wires, sanctions)
  needing an epic-and-stories.md for TL handoff. Use when stakeholders
  produced semi-structured notes needing INVEST stories with Gherkin AC.

  Do NOT use for TL-stage design (use design-review), code generation
  from a finished spec (use implement-from-spec), domain-glossary lookups
  with no work request, inputs containing actual PII values, inputs
  carrying the training ground-truth annotation block, or for the decomposed
  pipeline (use extract-brief-structure).
compatibility: [claude-code, codex, opencode]
metadata:
  version: 1.5.0
  stage_type: analyze
  input_schema: schemas/input.json
  output_schema: schemas/output.json
  banking_grade: {idempotent: true, reversible: n/a, audit_level: enhanced, tier_default: T2, tier_adaptable: [T1, T2, T3]}
  expected_duration_p95_seconds: 120
  max_retries_recommended: 2
  recommended_temperature: {T1: 0.1, T2: 0.3, T3: 0.5}
  tier_review_levels: {T1: [L0, L1, L2], T2: [L0, L1, L2], T3: [L0, L1]}
---

# Skill: Eliciting Banking Brief

## Purpose

Convert heterogeneous raw BA input (Jira / Slack / meeting notes / email / mixed prose) into a structured brief — epic + stories conforming to `epic-and-stories.template.md` — with banking-grade fields force-evaluated, ambiguities surfaced as Open Questions, and governance gaps escalated as P1 blockers. **The skill surfaces defects; it does NOT silently repair them** — detection plus structural enforcement only; repair is the BA's downstream responsibility (silent repair launders ambiguity into shipped requirements and breaks audit reconstruction).

## Input

Accepts one of: **Jira ticket**, **Slack thread**, **Meeting notes**, **Email**, or **mixed/doc prose** (no canonical markers — generic fallback at reduced confidence). Per-type detection markers: `references/procedure-detail.md` Step 1. Optional hints: `source_type`, `tier_hint`, `domain_glossary_ref`, `project_context_ref`, `audit_mode` ∈ {standard, enhanced, strict, training}. Required: `raw_content` (≥200 chars) + `idempotency_key` (UUID v4). Refuse inputs containing actual PII values (NRIC, account numbers, credit cards) — request secure-channel resubmission. **Optional typed `discovery` handoff** (S1 composite chain, from `researching-ba-problem-space` after its human gate): an **advisory** object that may *raise* a tier floor, *seed* the absent-stakeholder enumeration, and *pre-populate* `regulatory_dependencies` rows for verification — it can NEVER suppress a detector, lower a tier, satisfy a citation, or replace `raw_content`. Idempotency extends to `(raw_content, discovery)`. How it threads into Steps 1 / 3 / 5–6 / 11 / 12: `references/procedure-detail.md`.

## Procedure

Twelve ordered steps, executed in order. Each line is the imperative action + load-bearing markers; binding sub-rules, thresholds, and field names live per-step in **`references/procedure-detail.md`**, with per-FM detection/output/escalation in **`references/edge-case-catalog.md`**.

1. **Pre-flight — strip ground-truth + detect source type.** Fail closed on strip failure → FM-12.
2. **Route to parser + extract structural skeleton.** Classify `scope_kind`; never tech-layer split (AP-7.1).
3. **Build Domain Glossary + normalize dates + recognize regulator citations.** Ambiguous date → P3 OQ (never silent-resolve); unresolved citation blocks T1 handoff (FM-04).
4. **Auto-classify PII + redact PII in input body.** Never echo actual values (`<PII:REDACTED:CLASS=NRIC>` + P1 alert); force a `pii_inventory` table per story (empty without justification = handoff block, AP-4.1).
5. **Extract stakeholders with authority weighting.** Never collapse roles; down-weight anonymous/paraphrased input (AP-2.3); enumerate absent-but-implied stakeholders into `stakeholders[]` with `status: absent` + `engagement_required_for`.
6. **Surface missing stakeholders — Legal-absence is the highest-leverage gate.** Always emit `legal_status`; when ≠ `present` on regulatory scope → P1 `legal_absent_on_regulatory`, `blocks_tl_handoff: true` (fires 100% of pilots). Compliance ≠ Legal (AP-3.2). Every absent-implied stakeholder dual-writes to `stakeholders[]` (Step 5) and `governance_gaps[]`.
7. **Map structure to scope + emit stories.** Split only on legitimate value axes; never tech-layer (AP-7.1); one epic per workstream for multi-epic.
8. **Per-story banking-grade evaluation (force-fill 7 fields).** Emit `banking_grade_concerns` with all 7 rows non-null (`{pii_fields, audit_events, idempotency, reversibility, authn_authz, regulatory, tipping_off}`), each `status` + `justification` (≥10 chars); empty row → FM-11 hard fail.
9. **Detect ambiguities (8 types) with severity + tipping-off scan.** Per `references/ambiguity-patterns.md`; `tipping_off_scan` hit → P1 + safe phrase from `references/non-tipping-vocabulary.md` + `legal_signoff_required: true` + block handoff. Anti-patterns compose — never deduplicate.
9.5. **Hidden-requirements sweep — frame-driven elicitation-gap detection.** Apply the 10 frames in `references/hidden-requirements-frames.md` (Step 9 catches what prose says ambiguously; this catches what prose omits); emit into `open_questions[]`/`assumptions_made[]` with `provenance: hidden_frame_sweep` + `frame: N`; FM-17 Frame-4 sub-topic coverage may override the per-frame cap; record `processing_metadata.hidden_requirements_sweep` coverage.
10. **Compose Gherkin acceptance criteria with testability check.** `Given/When/Then` with concrete values; mandatory per story ≥1 happy + ≥1 error/edge + ≥1 banking_grade_*; composite linguistic quality < 5.0 → refuse handoff (FM-01).
11. **MoSCoW prioritization + tier inference (per epic).** Tier per epic (not per file); inferred tier > `tier_hint` by ≥1 step → require human override (AP-1.3); flag `>70% Must`.
12. **Failure-mode evaluation + output assembly.** Run the final gates (FM-01, FM-02, FM-05, FM-06, FM-11, FM-12, FM-13, FM-14 count consistency, FM-15 sweep-coverage, FM-16 idempotency-replay enforcement, FM-17 Frame-4 sub-topic coverage), apply bilingual emission when required, emit JSON conforming to `schemas/output.json` as the canonical artifact, then invoke `scripts/render_markdown_tree.py` per `references/markdown-rendering-spec.md`.

## Output Contract

**Dual emission — JSON is canonical, Markdown directory tree is mechanically derived.** The authoritative output is a JSON document conforming to `schemas/output.json` (the contract the downstream TL-handoff step consumes and the caller validates). Alongside it, `scripts/render_markdown_tree.py` deterministically renders a per-epic/per-story Markdown tree per `references/markdown-rendering-spec.md` for human review and fan-out routing; the tree is presentation-only and re-derivable, and the JSON is authoritative on any conflict.

**Bilingual emission.** When `processing_metadata.bilingual_output` lists more than one ISO-639-1 code (lowercase, e.g., `["en", "th"]`; default `["en"]`), the renderer emits one Markdown subtree per language under `output-{idem8}/<LANG_UPPER>/...`; the canonical JSON lives once at `output-{idem8}/output.json` with per-object `translations` maps (`schemas/output.json#/definitions/Translations`), missing entries falling back to English. Full contract (which fields need translations, UI-string localization via `references/ui-strings.json`, version history): `references/bilingual-emission.md`, `references/version-notes.md`.

Three top-level JSON shapes by `output_type`:

- **`brief`** — happy path. Contains all template sections: `frontmatter`, `scope_kind`, `epic` (single) or `epics[]` + `initiative` (multi), `stories[]`, `open_questions[]`, `assumptions_made[]`, `glossary[]`, `governance_gaps[]`, `ba_compliance_checklist`, `ba_reasoning_trace`, `processing_metadata`.
- **`blocked_partial_brief`** — P1 gap unresolved (FM-02/05/06). Same shape as `brief` plus `frontmatter.status: "blocked"`, `blocks_tl_handoff: true`, at least one P1 OQ or `governance_gap`.
- **`partial_brief`** — emit when the input contains enough signal to produce some stories but the BA cannot complete all epics within the per-brief scope (e.g., one workstream needs additional input that the source did not include). Same shape as `brief` plus `failure_state` describing which epic(s) are partial and what input would unblock the rest. Distinct from `blocked_partial_brief` (which is content-complete but governance-blocked).
- **Failure shapes** — `needs_clarification` (FM-01), `preprocessing_failure` (FM-12), `pii_echo_blocked` (FM-13), `schema_validation_failure` (FM-11), `meta_response` (EC-09). `failure_state` block describes refusal; `stories` absent.

**Governance extensions beyond `epic-and-stories.template.md`** (full field shapes in `schemas/output.json`): `governance_gaps[]` (legal_absent_on_regulatory / tipping_off_violation / pii_inventory_missing / regulatory_citation_unresolved / dual_approval_named_owner_missing / compensating_action_missing / retention_policy_unstated); `regulatory_dependencies[]`; `pii_inventory[]` (one row per field with treatment); `processing_metadata` including **`hidden_requirements_sweep` recording frame coverage and finding counts per Step 9.5**. When a `discovery` handoff was consumed, `frontmatter.upstream_refs.discovery_audit_id` carries its `audit_id` (provenance only — proves the discovery→brief chain without altering brief content).

**Elicitation-gap provenance tagging (optional fields; older outputs validate without them):** `open_questions[]` / `assumptions_made[]` may carry `provenance` (`prose_ambiguity` from Step 9 or `hidden_frame_sweep` from Step 9.5) and `frame` (1–10, indexed to `references/hidden-requirements-frames.md`); `assumptions_made[]` may carry `default_revisit_trigger` (the date, telemetry signal, or event when the assumed default must be re-evaluated).

**Key invariants enforced by schema:** `frontmatter.status: "ready-for-tl"` ⟹ no P1 OQs AND no `blocks_tl_handoff: true` gaps. Every `banking_grade_concerns` row has `justification.minLength ≥ 10`. `scope_kind: multi-epic` ⇔ `epics[]` + `initiative` present, `epic` absent.

## Failure Modes

Enforcement gates fire at **Step 12**. Full per-FM detection logic, output shape, and escalation live in `references/edge-case-catalog.md` (FM-01…FM-17 + EC×FM matrix). Quick trigger map:

- **FM-01** quality composite < 5.0 → `needs_clarification`.
- **FM-02** unresolved P1 in {compliance, tipping_off, retention, audit_schema, pii_inventory, regulatory_citation, dual_approval} → `blocked_partial_brief`.
- **FM-05** Legal absent/mentioned-only on regulatory scope → P1 governance block (`blocks_tl_handoff`); fires 3/3 pilots.
- **FM-06** forbidden tipping-off term in a customer-facing string → P1 + safe-phrase + `legal_signoff_required`.
- **FM-07** tier ambiguous → higher-tier fail-safe + P2 OQ.
- **FM-09** story/epic/multi-epic undecidable → `scope_kind: ambiguous` + P2 OQ.
- **FM-11** schema validation failure → `schema_validation_failure`; never emit malformed.
- **FM-12** ground-truth strip failed → `preprocessing_failure`, `do_not_proceed: true`.
- **FM-13** PII echo in output path → `pii_echo_blocked`, auto-redact.
- **FM-14** count consistency (OQ header N ≠ rows; absent-stakeholder row missing; epic↔story cardinality) → schema error.
- **FM-15** sweep coverage `partial`/`skipped` on a `brief` → downgrade to `blocked_partial_brief` + P2 OQ (FM-02 precedes).
- **FM-16** state-change story missing idempotency-replay AC → hard schema failure.
- **FM-17** Frame 4 active, required sub-topic uncovered → `coverage_score: partial` + P2 OQ.

## Anti-Patterns

Five handoff blockers (**AP-1.3** tier-from-label, **AP-4.1** PII-none-unjustified, **AP-4.4** tipping-off unflagged, **AP-5.1** Legal-absence undetected, **AP-8.4** missing banking-grade scenarios) override quality scores — any one prevents TL handoff. The **full 26-entry catalog** (detection + correct alternative + severity per AP) plus the top-5 quick-reference table live in `references/anti-patterns.md` (Steps 9, 12).

## References

Progressive disclosure — load only what each step needs (load point in parentheses):

- `references/procedure-detail.md` — per-step expanded rules: thresholds, field names, AP/FM cross-refs for all 12 steps (every step).
- `references/version-notes.md` — behavior maturity timeline (which FMs/behaviors landed in which version); provenance only, no behavior change (Steps 9.5, 12).
- `references/invest-checklist.md` — INVEST per-letter rules + split-pattern table (Steps 7, 10).
- `references/gherkin-templates.md` — Gherkin format + banking-grade scenario templates (idempotency / audit / tipping-off / authz) (Steps 8, 10).
- `references/ambiguity-patterns.md` — the 8 ambiguity types + P1/P2/P3 severity + conflict-resolution (Step 9).
- `references/anti-patterns.md` — full 26-entry catalog + top-5 handoff blockers (Steps 9, 12).
- `references/job-story-decision-tree.md` — Job Story vs Classic User Story choice (Step 7, format ambiguous).
- `references/edge-case-catalog.md` — 18 edge cases + 17 failure modes (FM-01…FM-17, full detection/output/escalation) + EC×FM matrix (Steps 1, 4, 5, 12).
- `references/non-tipping-vocabulary.md` — approved phrases + forbidden terms (Step 9, on forbidden-term hit).
- `references/markdown-rendering-spec.md` — directory tree structure, per-file-type frontmatter, slug rules, cross-link conventions (Step 12).
- `references/hidden-requirements-frames.md` — the 10 elicitation-gap frames with activation triggers, severity floors, caps, output pattern (Step 9.5).
- `references/frame-rule-data.json` (v1.3.0+) — runtime source-of-truth for FM-17 Frame-4 sub-topic coverage; loaded by `scripts/render_markdown_tree.py` at import, mirrored in `hidden-requirements-frames.md` (drift caught by `scripts/check_frame_rule_data_drift.py` F-7).
- `references/bilingual-emission.md` (v1.4.0+) — multilingual-brief contract: which fields require `translations[<lang>]`, fallback, sub-agent prompt guidance, verification checklist (Step 12, multi-language).
- `references/ui-strings.json` (v1.4.1+) — renderer UI-string translations per language; consulted by the renderer's `t(key)` helper, English-source fallback for missing keys.

Project-context resources (BA best practices, epic-and-stories.template.md) live at the parent project root, are not loaded by the skill, and are consumed directly by the downstream TL-design step.
