# Phase D1 — SKILL.md Design (`ba-elicit-from-raw`)

> **Role**: SKILL.md Architect, BA Skill Factory
> **Mission**: Design the frontmatter + body outline + rationale for `skills/ba-elicit-from-raw/SKILL.md`. E1 will author the live SKILL.md by following this design.
> **Inputs**: phase-c1 (30 patterns), phase-c2 (26 anti-patterns), phase-c3 (18 edge cases + 13 failure modes), epic-and-stories.template.md, references/ba-best-practices.md, COGNITIVE_OS_PROJECT.md §7 + §3.

---

## 0. Design Orientation

Atomic skill: one `stage_type: analyze`, one responsibility — convert heterogeneous raw input (Jira/Slack/meeting-notes/email/mixed prose) into a structured BA brief conforming to `epic-and-stories.template.md`, consumed downstream by the TL stage.

Three architectural pillars (C1 §10) drive design:

1. **Tier inference runs per emitted epic, not per raw file** — multi-epic inputs carry heterogeneous tiers.
2. **A single phrase can carry multiple flag types** — banking-grade + linguistic ambiguity + stakeholder-mode. Detectors must not deduplicate.
3. **Banking-grade detection is half pattern-matching, half forcing function** — surface invisible defects, don't repair them.

Highest-leverage rule (5-way triangulated, fires 100% of pilot inputs): **Legal-absent + regulatory content = P1 governance gap** (C14, AP-5.1, FM-05).

---

## 1. Frontmatter Design (Full YAML)

```yaml
---
# === Identity ============================================================
name: ba-elicit-from-raw
version: 1.0.0
description: >
  Analyze raw, heterogeneous BA input — Jira tickets, Slack threads,
  meeting notes, emails, or mixed prose — and emit a structured BA brief
  (epic + stories) conforming to epic-and-stories.template.md, with
  banking-grade fields force-evaluated, ambiguities surfaced (not
  resolved), and governance gaps (Legal-absent on regulatory content,
  tipping-off-risky language, missing PII inventory, unresolved regulator
  citations) escalated as P1 blockers.

  Use when a user submits a Jira ticket, Slack export, meeting transcript,
  email thread, or mixed-source brief for BA elicitation. Use when the
  raw input describes a banking workflow (KYC, EDD, AML, wire transfers,
  document re-upload, sanctions screening) and an epic-and-stories.md is
  required for TL handoff. Use when stakeholders have produced
  semi-structured notes that need conversion into INVEST-compliant
  stories with Gherkin acceptance criteria.

  Do NOT use for: TL-stage design work (use design-review workflow);
  generating code from a finished spec (use implement-from-spec);
  domain-glossary lookups with no work request (return meta-response);
  inputs that include actual PII values (refuse and request secure-channel
  resubmission); inputs containing the literal ground-truth annotation
  block "## Intentional Issues for R6 to Catch" (training-set marker —
  refuse in production).

# === Workflow contract (Section 7, v2 schema) ===========================
stage_type: analyze
input_schema: schemas/input.json
output_schema: schemas/output.json

# === Banking-grade metadata =============================================
banking_grade:
  idempotent: true
  reversible: n/a
  audit_level: enhanced
  tier_default: T2
  tier_adaptable: [T1, T2, T3]

# === SLA hints (workflow may override) ==================================
expected_duration_p95_seconds: 120
max_retries_recommended: 2

# === Compatibility ======================================================
compatibility: [claude-code, codex, opencode]
---
```

### 1.1 Frontmatter Rationale

- **`name`** verb-noun per Section 12. **`version: 1.0.0`** first atomic skill.
- **`description`**: 3 paragraphs satisfy Section 12 ("3+ trigger phrases + 1+ negative trigger"). Negative triggers cover meta-requests (EC-09), PII echo (EC-08/FM-13), ground-truth leak (EC-17/FM-12), wrong-stage routing.
- **`stage_type: analyze`** (not `generate`): brief is structured *analysis* of raw input — the skill extracts and classifies, does not invent. Section 5 taxonomy: idempotent + retry-safe + no compensation.
- **`input_schema` / `output_schema`**: separate files per Section 7. Input = raw body + optional source-type hint + tier override + audit-mode flag. Output = epic-and-stories.template.md plus governance extensions (open_questions, governance_gaps, blocks_tl_handoff, regulatory_dependencies, pii_inventory, processing_metadata, glossary).
- **`idempotent: true`**: pure analysis; same input → same output. C18 banking-grade idempotency applies to output stories' replay-test scenarios, not skill-call idempotency.
- **`reversible: n/a`**: no external state change.
- **`audit_level: enhanced`** (not `standard`): governance traceability is the skill's primary value — every ambiguity, authority-mode, PII inference, Legal-absent check must land in audit with source quote + line reference. C18 forcing function requires richer `decision_metadata` than default. Token cost marginal.
- **`tier_default: T2`** + **`tier_adaptable: [T1, T2, T3]`**: Section 3 banking-grade default. C19 + AP-1.3 require adapting across all tiers — T1 hard-blocks missing PII / regulator citation / Legal sign-off; T2 surfaces with `blocks_tl_handoff`; T3 allows justified skips.
- **`expected_duration_p95_seconds: 120`**: pilot r1-r3 each carry 6-8 stakeholders, 5-8 stories, 12-25 ambiguity flags. Two minutes covers 9-pass parsing at ~15s/pass. EC-04 long inputs may override.
- **`max_retries_recommended: 2`**: Section 8 Generate-pattern (LLM tokens expensive). Reserve retries for transient rate-limit; after 2, route to FM-01.
- **`compatibility`**: Section 12 convention; no IDE-specific logic.

---

## 2. Body Structure Design (Outline + Budgets)

Total body budget: **≤ 220 lines** (Section 7).

| # | Section | Lines | Purpose | Phase C source |
|---|---|---|---|---|
| 1 | `# Skill: BA Elicit From Raw` | 1 | Heading | — |
| 2 | `## Purpose` | 6-8 | One paragraph: what skill does + does NOT do (surface, don't repair) | C1 §10; AP §9.5 |
| 3 | `## Input` | 10-14 | Supported sources (Jira/Slack/meeting/email/mixed/doc-fallback) + detection markers + audit_mode flag | C1-C4; EC-17 |
| 4 | `## Procedure` | 70-90 | 12 numbered steps — heart of the skill | C1 §1-§8; C2 guards; C3 branches |
| 5 | `## Output Contract` | 18-25 | Required sections matching epic-and-stories.template.md + governance extensions | template.md; C18-C20, C29; FM-11 |
| 6 | `## Failure Modes` | 18-22 | Table: 9 highest-impact failure modes | C3 Part 2 |
| 7 | `## Anti-Patterns` | 20-25 | Top 10 anti-patterns (handoff blockers + silent failures) | C2 §10 |
| 8 | `## References` | 8-12 | Progressive-disclosure load strategy | C1 cross-cut; FM-06 |
| **Total** | | **≤ 220** | | |

**Buffer**: ~180 lines core + ~20-40 headroom. If overflow, compress Anti-Patterns to top 6 and merge steps 11+12 into one assembly step. Failure Modes table is irreducible — every row is a handoff blocker or P1.

---

## 3. Procedure Steps — Detailed Outline

Each step maps to ≥1 C1 pattern, ≥1 C2 anti-pattern guard, and respects relevant C3 failure modes. E1 collapses each to ≤ 7 body lines.

### Step 1 — Pre-flight: strip ground-truth annotations + detect source type
- **C1**: C3 (strip ground-truth — hard preprocessing), C1 (detect source type).
- **C3**: FM-12 (strip failed → fail closed), FM-10 (source undetectable → prose fallback). EC-17 (ground-truth blocks), EC-13 (email inversion).
- **C2 avoided**: implicit — strip ordering prevents annotation answers leaking into AC generation.

### Step 2 — Route to source-specific parser + extract structural skeleton
- **C1**: C2 (parser routing), C8 (classify scope_kind), C11 (Parking Lot / Out-of-Scope).
- **C3**: EC-04 (long input chunking), EC-10 (multi-epic), EC-11 (sub-ticket chain), EC-12 (Slack-only signal). FM-09 (scope unclear).
- **C2 avoided**: AP-3.3 (squash multi-epic), AP-7.1 (tech-layer splitting).

### Step 3 — Build domain glossary + normalize dates + recognize regulator citations
- **C1**: C5 (Domain Glossary), C4 (relative-date resolution), C6 (regulator citations resolved vs unresolved).
- **C3**: EC-03 (multi-language preserve verbatim), EC-18 (regulatory citation incomplete = P1). FM-04 (regulatory ref unresolvable).
- **C2 avoided**: AP-1.1 (lifecycle policy from labels — never copy retention across inputs), AP-1.2 (`urgent` label as priority).

### Step 4 — Auto-classify PII + redact PII detected in input body
- **C1**: C7 (auto-classify PII).
- **C3**: EC-08 (PII present → never echo; `<PII:REDACTED:CLASS=NRIC>`; P1 governance). FM-13 (PII echo block).
- **C2 avoided**: AP-4.1 (PII = none without explicit reasoning).

### Step 5 — Extract stakeholders (Owner/Sponsor/Approver/SME/Affected/External/Meta) with authority weighting
- **C1**: C12 (distinguish roles), C13 (SMEs by domain), C15 (weight by speech act + authority_mode), C16 (down-weight anonymous + paraphrased), C17 (mentioned-but-not-engaged).
- **C3**: EC-02 (conflicting commenters), EC-14 (anonymous), EC-15 (note-taker paraphrase), EC-16 (stakeholder on leave). FM-03 (conflict unresolvable), FM-08 (authority unclear → more-restrictive default).
- **C2 avoided**: AP-2.3 (anonymous as named), AP-5.2 (over-weighting Owner without domain authority), AP-5.3 (paraphrase as authoritative).

### Step 6 — Surface missing stakeholders (Legal P1 on regulatory; Privacy/DPO, Security, SAR Liaison, Model Owner, Migration Owner per scope)
- **C1**: C14 (missing stakeholders — strongest convergence).
- **C3**: FM-05 (Legal absent + regulatory = P1; T1 blocks handoff; T2 requires Sponsor risk-acceptance).
- **C2 avoided**: AP-3.2 (Compliance ≠ Legal), AP-5.1 (canonical always-fires Legal-absence detector).
- **Rationale**: Highest-leverage rule in the entire skill (C1 §10). Standalone step for visibility.

### Step 7 — Map structure to scope + emit stories (split by workflow / business-rule / data / stakeholder boundaries)
- **C1**: C9 (story boundaries by stakeholder-concern + enumerated lists), C10 (epic boundaries by workstream + self-questioning), C25 (workflow steps), C26 (business-rule variations), C27 (data variations), C28 (role boundary).
- **C3**: EC-10 (multi-epic → per-epic tier and per-epic banking-grade). FM-09 (ambiguous scope).
- **C2 avoided**: AP-7.1 (tech-layer split), AP-7.2 (merge happy + error), AP-7.3 (AC > 7 unsplit).

### Step 8 — Per-story banking-grade evaluation (7 mandatory fields, force-fill)
- **C1**: C18 (force 7 banking-grade fields — central forcing function), C21 (compensating action / reversibility on irreversible ops).
- **C3**: FM-11 (empty banking_grade rows = schema validation hard fail).
- **C2 avoided**: AP-4.1 (PII none without reasoning), AP-4.3 (skip idempotency on state-change), AP-4.4 (tipping-off-risky unflagged — handoff block).

### Step 9 — Detect ambiguities (6 types) with P1/P2/P3 severity + run tipping-off scan
- **C1**: C22 (6 ambiguity types — lexical/syntactic/pragmatic/pronominal/quantifier/modal), C23 (P1/P2/P3 severity), C24 (anonymous downgrade + latest-claim conflict resolution), C20 (tipping-off scan).
- **C3**: FM-06 (tipping-off risk → P1 blocking unless mitigated; safe phrasing from non-tipping-vocabulary.md).
- **C2 avoided**: AP-2.1 (silent resolution), AP-2.2 (P2 buried in Assumptions), AP-6.1 (silent pick among disagreeing commenters), AP-6.2 (modal as binding), AP-6.3 (quantifier as quantified), AP-4.4 (tipping-off unflagged).

### Step 10 — Compose Gherkin acceptance criteria (happy + error + banking-grade) with testability check
- **C1**: C29 (mandatory scenario types), C30 (Gherkin rewrite + concrete-value enforcement + testability check).
- **C3**: FM-01 (composite linguistic quality < 5.0 → refuse handoff).
- **C2 avoided**: AP-4.2 (AC without testability), AP-8.1 (vague Given), AP-8.2 (multi-action When), AP-8.3 (Then without observable), AP-8.4 (missing banking-grade scenarios — handoff block).

### Step 11 — MoSCoW prioritization + tier inference (per epic) + override checks
- **C1**: C19 (infer tier per epic, not per file).
- **C3**: FM-07 (tier ambiguous → conservative default = higher tier).
- **C2 avoided**: AP-1.3 (label tier ignoring content — handoff block when content-tier > label-tier), AP-3.1 (collapse internal SLAs into one ETA without flag).
- **Inherits**: ba-best-practices.md §6 MoSCoW discipline (> 70% Must → re-evaluate).

### Step 12 — Failure-mode evaluation + output assembly (conform to schemas/output.json)
- **C3 gates**: FM-01, FM-02, FM-05, FM-06, FM-11 evaluated as final gates; FM-12 re-confirmed.
- **C1**: C30 (final testability), C18 (final banking-grade schema completeness).
- **C2 avoided**: AP-3.3 (squash multi-epic), AP-7.3 (AC > 7 unsplit).
- **Output assembly**: glossary, stakeholders, stories, open_questions[], assumptions[], governance_gaps, blocks_tl_handoff, regulatory_dependencies, pii_inventory, processing_metadata (tier_decisions, chunking, ground_truth_stripped, parsing_mode, language_inventory).
- **Validation**: empty banking-grade rows → FM-11; PII echo → FM-13.

---

## 4. References Loading Strategy (Progressive Disclosure)

Body references — does not inline — six supporting files. Progressive loading keeps body ≤ 220 lines and controls token budget.

| Reference file | When to load | Triggering pattern |
|---|---|---|
| `references/invest-checklist.md` | Step 7 (splitting) + Step 10 (testability) — always | C9, C29, C30 |
| `references/gherkin-templates.md` | Step 10 (AC composition) + Step 8 (banking-grade scenario templates) — always | C29, C18 |
| `references/job-story-decision-tree.md` | Step 7 (story format choice: context-drives vs role-drives) | ba-best-practices §3 |
| `references/ambiguity-patterns.md` | Step 9 (ambiguity detection) — always | C22, C23, C24 |
| `references/anti-patterns.md` | Step 9 (conflict arbitration) + Step 12 (final guardrails) — always | C2 §all |
| `references/edge-case-catalog.md` | Step 1-2 when source confidence < 0.5; Step 4 (PII present); Step 6 (stakeholder leave) | EC-01 to EC-18 |
| `references/non-tipping-vocabulary.md` | Step 9 only when tipping-off forbidden terms detected | C20, FM-06 |

**Rationale**: Always-loaded refs are the irreducible core (invest, gherkin, ambiguity, anti-patterns). `non-tipping-vocabulary.md` only fires on ~30% of stories with customer-facing comm changes; `edge-case-catalog.md` only on weak source-type signal (~20% inputs); `job-story-decision-tree.md` only when role-vs-context ambiguous. Saves ~1000-2000 tokens on long-tail invocations — matters for Section 3 P95 < 30s/stage target.

---

## 5. Failure Modes Table Design

Body's `## Failure Modes` section: 9-row table covering handoff blockers + always-fires governance gaps.

| Failure mode | Detection | Skill output | Escalation |
|---|---|---|---|
| FM-01 — Input quality below threshold | Linguistic composite < 5.0 after parsing + ambiguity (A2 §6) | `output_type: needs_clarification`, gap analysis, recommended questions | Return to requester. Do not route to TL. |
| FM-02 — Critical info missing (P1 blocks) | P1 finding in {compliance, tipping_off, retention, audit_schema, pii_inventory, regulatory_citation, dual_approval} with no resolution | `output_type: blocked_partial_brief`, blocking_findings, `<MISSING:P1:reason>`, unblock_actions | Surface to BA/TL. TL resolves P1s or accepts risk in writing. |
| FM-05 — Legal absent on regulatory content | `legal_status ∈ {absent, mentioned_only}` AND scope touches regulatory. Fires 3/3 pilots — highest-leverage rule | Standard brief + `governance_gap.type: legal_absent_on_regulatory`, P1, `blocks_tl_handoff: true` | T1: refuse handoff, escalate to Sponsor/Owner. T2: brief with handoff-block flag, Sponsor risk-acceptance in writing. |
| FM-06 — Tipping-off risk in customer comms | Customer-facing string contains forbidden terms (sanctions/AML/flagged/suspicious/regulated/SAR/PEP/adverse media/EDD). Internal-only fields exempt | `tipping_off_scan.violations[]`, safe-phrase mitigations from `non-tipping-vocabulary.md`, `legal_signoff_required: true` | Replace violations with safe phrases. If none exists, require Legal sign-off. Block TL handoff until mitigation or sign-off recorded. |
| FM-07 — Tier classification ambiguous | All overrides run AND no tier emerges with confidence ≥ 0.8, OR two rules at distinct tiers with equal weight | `tier_inference.recommended_tier` = higher choice (fail-safe over-strict), OQ `confirm_tier_assignment` (P2) | Higher-tier default. Human BA/TL confirms. Document in `processing_metadata.tier_decisions[]`. |
| FM-09 — Scope unclear (story vs epic vs multi-epic) | Cannot decide; phrases `(but might need to be|too big\?|may need to split)` OR 3-4 workstreams at boundary | `scope_kind: ambiguous`, scope_signals, recommended_scope_kind, OQ `confirm_scope_kind` | Clarifying question. May emit draft with `pending_scope_confirmation: true`. |
| FM-11 — Schema validation failure | banking_grade row `status: null`, story without ACs and without `assessment: insufficient_information`, P1 without `required_resolution`, stakeholder reference not in registry | `output_type: schema_validation_failure`, validation_errors, partial_output_available | Never emit malformed brief. Return errors to orchestrator. Retry with gap-fill prompt; on retry fail, human implementer. |
| FM-12 — Ground-truth annotation strip failed | Preprocessing detected block AND strip errored / boundary overlap / multiple blocks / substring survived | `output_type: preprocessing_failure`, `failure_code: ground_truth_strip_failed`, `do_not_proceed: true` | Refuse to produce any brief. Return failure code. Never proceed to AC generation — would constitute fabrication. |
| FM-13 — PII detected in output path | Post-generation scan finds unredacted PII regex hit; scrubbed tokens `<PII:REDACTED:CLASS=X>` allowed | `output_type: pii_echo_blocked`, detected_pii, auto_redaction_attempted, manual_review_required | Auto-redact; if clean, emit redacted brief. If redaction fails (token cannot be confidently classed), escalate to human BA. |

**Omitted from body** (covered in `references/edge-case-catalog.md`): FM-03 (P2 surface only), FM-04 (collapsed under FM-02+FM-05), FM-08 (P2 surface), FM-10 (low-confidence prose fallback).

**Selection criterion**: handoff blockers + always-fires governance gaps. P2-surface-only failure modes deferred to keep body within budget.

---

## 6. Anti-Patterns Section Design

Body's `## Anti-Patterns` section: top 10. Compressed to 2-3 lines per entry.

| # | Anti-pattern | Why dangerous | Correct alternative |
|---|---|---|---|
| 1 | **Inferring tier from explicit label, ignoring content signals** (AP-1.3) | Regulator-cited initiative ships under T2 rigor; governance gaps unflagged; silent compliance risk | Run tier inference over content (C19). When inferred > label by ≥1 step, emit `tier.inferred > tier.manual` + require human override. Multi-epic: tier per epic. |
| 2 | **Silently resolving ambiguity instead of surfacing it** (AP-2.1) | Author flagged uncertainty because they could not resolve it. Silent choice commits a policy decision the source disowned | Split into Gherkin AC + Open Question (P2) referencing both alternatives + suggested resolver. Never drop either branch. |
| 3 | **Treating Compliance as Legal** (AP-3.2) | Compliance describes regulation; Legal interprets language. Conflation makes the most reliable governance gap invisible | Maintain disjoint Compliance vs Legal slots. Emit `legal_status` independently. Compliance rule-mode binds implementation; does NOT discharge Legal-engagement. |
| 4 | **Squashing multi-epic initiative into one epic to fit template** (AP-3.3) | Per-epic tier inference (C19) hidden; INVEST `Small` violated; downstream prioritization distorted | Detect `scope_kind` first (C8 + EC-10). If ≥3 workstreams each with ≥2 ACs, emit `scope_kind: multi-epic` with one epic file per workstream. |
| 5 | **PII fields = none without explicit reasoning** (AP-4.1) | Documents/applicants/IDs/biometrics surfaced without full enumeration (name, address, photo, applicant-ID). Privacy compatibility check impossible | Produce `pii_inventory` table per field. If truly none, emit `pii.status: not_applicable, justification: <workflow class + reason>`. Schema rejects empty justification. |
| 6 | **Tipping-off-risky language in customer comms without flag** (AP-4.4) | Highest-stakes regulatory pattern (B5 P-01). Failure is NOT emitting something — forbidden terms pass through customer copy by default | Run `tipping_off_scan` over every customer-facing AC. On hit: P1 + non-tipping safe phrasing + `formal_signoff_pending: legal`. Block TL handoff until sign-off recorded. |
| 7 | **Missing Legal-absence detection on regulatory content** (AP-5.1) | Legal absent in 100% of pilot inputs — canonical always-fires detector. Skill without this auto-emit is structurally blind to most reliable defect | Always emit `legal_status`. When status ≠ `present` AND scope touches retention / customer-comms / tipping-off / sanctions / biometric / regulator citation / dual approval, emit P1 governance block. |
| 8 | **Treating anonymous commenter as if named** (AP-2.3) | Numeric policy params encoded with no named approver — fails audit reconstruction | Detect anonymous / `(likely X)` / `(group, N min)`. On numeric/policy default, refuse to encode as AC. Emit `proposed_value, attribution: anonymous, requires_named_owner: true` (P2). |
| 9 | **Splitting by tech layer (frontend/backend/DB) instead of user value** (AP-7.1) | Tech-layer splits violate INVEST `Independent` and `Valuable` — UI has no value without API; API has no value without UI | Split using workflow steps / business rules / happy-vs-error / data variations / CRUD / roles / spike. Never tech layer. If forced, flag for TL. |
| 10 | **Missing banking-grade scenarios on stateful / notification ops** (AP-8.4) | Empty banking rows fail schema validation (C18 + FM-11). Most common banking-grade defects never reach AC | For every state-change or notification story, auto-emit: idempotency-replay + audit-emission + (if customer-facing) tipping-off check scenarios. Templates in `gherkin-templates.md`. |

**Selection**: 5 are handoff blockers (AP-1.3, AP-4.1, AP-4.4, AP-5.1, AP-8.4) — must appear in body. Other 5 (AP-2.1, AP-3.2, AP-3.3, AP-2.3, AP-7.1) are most-evidenced silent failures (≥3 phase analyses each). Remaining 16 anti-patterns live in `references/anti-patterns.md`, loaded by Step 9 + Step 12.

---

## 7. Design Rationale (Major Choices)

**Why 12 procedure steps?** Maps to natural pass-boundaries (pre-flight / skeleton / domain / stakeholders / Legal-gate / scope-to-stories / banking-grade / ambiguity+tipping / AC / MoSCoW+tier / assembly). Each step maps to ≥1 C1 pattern and ≥1 C2 guard. Fewer steps would obscure FM-05 (highest-leverage rule); more would blow body budget. 12 fit in 70-90 lines.

**Why tier inference inside this atomic skill (not delegated)?** (1) C19 mandates per-epic tier inference, which requires scope-kind classification first — a workflow-level tier stage would force a candidate-epic round-trip violating "one stage, one responsibility". (2) AP-1.3 ties tier inference to content signals visible during parse; LLM context resets between stages. (3) `tier_adaptable: [T1, T2, T3]` presupposes this skill operates across tiers.

**Why progressive disclosure for references?** Body ≤ 220 lines hard constraint. Loading 7 refs unconditionally inflates context ~1500-3000 tokens/call. `non-tipping-vocabulary.md` fires on ~30% of stories; `edge-case-catalog.md` on ~20% of inputs. Always-loaded core (invest, gherkin, ambiguity, anti-patterns) is irreducible. Long-tail savings matter for Section 3 P95 < 30s/stage SLA.

**Why "surface, don't repair"?** C2 §9.5: repair-mode skills launder ambiguity into shipped requirements (AP-2.2 canonical failure). Banking-grade audit reconstruction depends on every decision being traceable to a named human — silent repair breaks that chain. The skill's job is detection + structural enforcement; repair is the BA's downstream.

**Why `audit_level: enhanced`?** Standard logs inputs/outputs only. Enhanced adds `decision_metadata.uncertainty_flags`, `complexity_classification`, `tier_decisions[]`, `governance_gaps_detected[]` — without these, R6 reviewers and TL cannot reconstruct *why* a P1 was raised, defeating C18's forcing function.

**Why `idempotent: true`?** Pure analysis; same input → same brief. Non-determinism bounded by procedural ordering. C18 banking-grade idempotency applies to output stories' replay scenarios, not skill-call idempotency.

**Why expose `audit_mode` flag?** EC-17 training mode consumes ground-truth blocks for self-evaluation; production strips them (FM-12 fail-closed). Default `false`; training harness sets explicitly. Keeps safety guard absolute in production while enabling Phase B validation.

**Why 10 anti-patterns in body?** 5 handoff blockers must appear (AP-1.3, AP-4.1, AP-4.4, AP-5.1, AP-8.4). 5 others are most-evidenced silent failures. Remaining 16 are P2/P3 rewrites — important but live in `references/anti-patterns.md`.

---

## 8. Open Design Questions for E1

Decisions E1 makes at write-time, not blockers to this design.

1. **Step 1 ordering: detect-then-strip or strip-then-detect?** Recommend detect-then-strip (source type informs strip heuristic). E1 chooses based on parser simplicity.
2. **PII redaction display format**: `<PII:REDACTED:CLASS=NRIC>` inline vs structured JSON token? E1 aligns with `schemas/output.json` PII field shape.
3. **Glossary inheritance across multi-epic**: per-epic copy or shared `initiative.glossary`? Recommend per-epic (smaller token cost, easier audit) unless workflow constraints require otherwise.

---

## 9. Validation Checklist for E1

Verify before marking SKILL.md ready:

- [ ] Frontmatter validates against `schemas/skill-v1.schema.json`.
- [ ] Description has ≥3 "Use when…" + ≥1 "Do NOT use for…".
- [ ] Banking-grade fields populated (`idempotent`, `reversible`, `audit_level`, `tier_default`, `tier_adaptable`).
- [ ] Body ≤ 220 lines.
- [ ] Body references (does not inline) 7 supporting files in `references/`.
- [ ] Failure Modes table has all 5 handoff blockers + governance gaps (FM-01, FM-02, FM-05, FM-06, FM-07, FM-09, FM-11, FM-12, FM-13).
- [ ] Anti-Patterns section has all 5 handoff blockers (AP-1.3, AP-4.1, AP-4.4, AP-5.1, AP-8.4).
- [ ] Step 1 strips ground-truth (EC-17 / FM-12) before any other pass — the only **fail-closed** preprocessing rule.
- [ ] Step 6 emits Legal-absence check as standalone gate (single highest-leverage rule).
- [ ] Step 8 force-emits all 7 banking-grade fields (C18 forcing function).
- [ ] Step 12 runs schema validation before output emission (FM-11).
- [ ] Output Contract references `schemas/output.json` and lists all governance extensions beyond `epic-and-stories.template.md`.

---

*End of Phase D1 SKILL.md Design. E1 writes the live SKILL.md by following this design and the validation checklist.*
