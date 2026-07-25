# Edge Case + Failure Mode Catalog

> 18 edge cases + 17 failure modes + EC×FM trigger matrix. Loaded by `SKILL.md` Steps 1, 4, 5, 12 conditionally.

## Purpose & Loading Conditions

Load only when: (a) source confidence < 0.5 at Step 1; (b) PII detected at Step 4; (c) stakeholder absence / leave at Step 5; (d) ground-truth block detected (loads EC-17/FM-12 section); (e) Step 12 in `audit` mode. Happy-path runs skip this file. **Adapt, don't fabricate** — every edge case has a useful partial output.

Sources: C3 Part 1 (EC-01..EC-18); C3 Part 2 (FM-01..FM-13); C3 Part 3 (matrix); FM-14..FM-17 added v1.2+ (count/sweep/idempotency/Frame-4 enforcement).

## Edge Case Groups

### Group 1 — Input Quality

- **EC-01 Empty / minimal-signal.** *Detection*: non-whitespace < 200 chars OR no source-type metadata OR composite quality < 2.0/10. *Behavior*: refuse brief; emit needs-clarification packet with required minimums. *Output*: `output_type: needs_clarification`, `failure_state.failure_code: empty_or_minimal_input`, `failure_state.suggested_next_action: prompt_requester`, `ba_confidence: refused`.
- **EC-04 Very long input.** *Detection*: tokens >25k OR speakers >20 OR comments >50 OR file >250 KB. *Behavior*: chunk by semantic boundary (Jira by comment-thread; Slack by topic-shift; Meeting by numbered-agenda); run source-detect + ground-truth-strip on full input first; maintain global `entity_registry`; reduce confidence one tier. *Output*: `processing_metadata.chunking: {strategy, num_chunks, semantic_boundaries, cross_chunk_references_resolved}`.
- **EC-05 Very short input.** *Detection*: source detected AND body < 500 chars AND stakeholders < 2 AND composite quality < 4.0. *Behavior*: emit `output_type: partial_brief`, one stub story, no fabricated ACs; structured "Information Needed Before TL Handoff". *Output*: `completeness: partial`, `missing_fields`, `min_clarifications_needed`.
- **EC-07 Broken structure / paraphrase.** *Detection*: source-type passes but section-marker count < baseline (Jira <4 of 8; Meeting <5 of 8; Slack speaker-turn fails >20%) OR explicit note-taker paraphrase disclaimer. *Behavior*: fall back to prose parser, retain source-type tag; every statement → `attribution_confidence: paraphrase`; verbatim verification required for P1/P2. *Output*: `parsing_mode: degraded`, `parsing_reason: structure_broken`, per-finding `attribution_confidence`.
- **EC-10 Multi-epic.** *Detection*: distinct workstreams ≥3 each with ≥2 ACs; phase-language `phase 1/2`/`Q3/Q4`/`web first / mobile follow-on`; vendor-integration cluster; migration / legacy-data references. *Behavior*: emit `scope_kind: multi_epic`; one output file per epic; **tier inference per epic** (B5 §6 decision 1); stakeholder/banking-grade/dependency passes run per epic. *Output*: top-level `initiative.md` wrapper with `epic_files[]` + `per_epic_tier`.

### Group 2 — Input Structure

- **EC-11 Sub-ticket / linked-issue chain.** *Detection*: Jira `Blocks:`/`Relates to:` blocks OR inline `📎 Linked: <KEY>` OR "parent"/"child of"/"subtask" language. *Behavior*: extract typed dependency edges (`blocks`, `blocked_by`, `relates_to`, `historical`, `subtask_of`); mark closed/historical as context-only; linked ticket → `dependencies[]` with `resolution: external_reference_required` if content not embedded. *Output*: `linked_tickets: [{key, relation, status, content_embedded}]`.
- **EC-12 Conversational-only (Slack worst case).** *Detection*: source-type = Slack AND no structured summary AND >4 interleaved topics AND >5 cross-message pronoun refs. *Behavior*: Slack parser; resolve pronouns in 5-message sliding window; emoji 👍/✅/+1/🙏 = soft acceptance, **never** formal sign-off (emit `formal_signoff_pending: true` + OQ per compliance-topic emoji); synthesize ACs from longest decision chain; refuse handoff below 5.0; reduce confidence one tier. *Output*: `parsing_mode: synthesized_from_chat`, per-AC `synthesis_path: [msg_refs]`.
- **EC-13 Email-thread hold-out (quoted-reply inversion).** *Detection*: `From:`/`To:`/`Subject:`/`Date:` quartet OR `>` quote line-prefix OR `On <date>, <name> wrote:` markers OR `.eml` extension. *Behavior*: reverse to oldest-first; parse signature blocks for role metadata; each "wrote:" = speaker turn; boost `attribution_confidence: high` (email more formal than Slack); strip quoted-reply duplication. *Output*: `parsing_inversion_applied: true`, `quoted_replies_deduplicated: N`.

### Group 3 — Stakeholder Issues

- **EC-02 Conflicting commenters / speakers.** *Detection*: two attributed speakers reference same entity/policy with incompatible predicates (replace-vs-archive, retention-yes-vs-defer, mobile-scope, threshold-vs-calibration, ETA-bucket-merge). *Behavior*: surface both quotes in `open_questions[]` with P2 severity; apply authority-mode arbitration (compliance rule-mode beats PM AC; compliance proposal-mode does NOT auto-beat data/eng feasibility); tag `conflict_class`; never silently pick. *Output*: `open_questions[].conflict_evidence: [{speaker, quote, line_ref, authority_mode}]`, working answer = latest claim. P1 if compliance.
- **EC-14 Anonymous / weak attribution.** *Detection*: speaker `Anonymous`, `Unknown`, `(group, N min)`, or `(likely <Name>)`. *Behavior*: `attribution: anonymous`, `attribution_confidence: low`; **refuse to bind** numeric policy params, thresholds, retention values, compliance assertions; convert proposal → OQ `requires_named_owner: true`; anonymous on compliance/PII/audit → P2 (B5 C1 promotion). *Output*: per-utterance `attribution_block`; anonymous-sourced AC → `open_questions[].proposed_value`.
- **EC-15 Note-taker-mediated content (paraphrase).** *Detection*: `Note-taker:` metadata OR paraphrase disclaimer ("paraphrase, not verbatim") OR first-person bracketed asides matching note-taker name OR `(me!)` self-reference. *Behavior*: every statement → `attribution_confidence: paraphrase`; preserve note-taker asides in `meta_asides` verbatim but not as decisions; P1/P2 findings → "verbatim verification required" action item; note-taker = tracked `meta_stakeholder`. *Output*: global `mediation: {note_taker, paraphrase_mode: true}`, per-utterance `attribution_confidence`.
- **EC-16 Stakeholder going on leave / handoff.** *Detection*: phrases `on leave / out of office / OOO / handing over to / handoff to / cover for / acting <role>` OR `Apologies:` in meeting metadata. *Behavior*: emit `stakeholder_continuity_risk` for P1/P2 unavailable stakeholder; detect named cover (else P2 OQ); **Legal on leave + regulatory scope → P1**; cross-reference action-item dates with absence window. *Output*: `stakeholder_availability: [{name, role, status, cover, return_date}]`.

### Group 4 — Hidden Ground Truth

- **EC-17 Ground-truth annotation block (training-set hidden).** *Detection*: literal headers `## Intentional Issues for R6 to Catch`, `## Hidden from BA Workflow`, `^## (Intentional|Hidden|Ground[- ]Truth|Audit Annotation)`. *Behavior*: **strip before any parsing** — first preprocessing pass; `audit_mode: training` may consume for self-evaluation; production **never reads** (would contaminate output); strip failure → fail closed (FM-12). *Output*: `processing_metadata.ground_truth_stripped: {found, byte_range, strip_method}`. **Unique safety guard** — only EC that triggers FM-12. *Discovery firewall (v1.5.0)*: the strip runs on `raw_content` ONLY; the optional `discovery` handoff object is structured input — never scanned for the ground-truth heading and never stripped.

### Group 5 — Scope & Language

- **EC-03 Multi-language (English + Thai / SG-localized).** *Detection*: non-Latin Unicode in body (Thai U+0E00-U+0E7F, Chinese U+4E00-U+9FFF) OR code-switched sentences OR non-Latin filenames. *Behavior*: preserve original tokens verbatim (never silent-transliterate); emit `language_inventory`; translate only when English gloss accompanies else `translation_required: true` (P3); compliance/legal text in non-English is P2. *Output*: `language_inventory: [{script, sample, frequency}]`, per-quote `language_tag`.
- **EC-09 Meta-request (asks clarification, not work).** *Detection*: interrogative form (`?`, `what`/`why`/`how`/`should`/`can you explain`) AND no problem-statement structure AND stakeholders ≤1. *Behavior*: do not produce brief; route to `meta_response` using glossary + best-practices ref; cite canonical passage; suggest requester resubmit work request. *Output*: `output_type: meta_response`, `meta_response_body`, `citations`, `suggested_next_action`.
- **EC-18 Regulator named without full citation.** *Detection*: regex `[A-Z]{2,}-[A-Z]{2,}-[A-Z0-9-]+` AND no attached doc AND no URL AND no quoted regulation text. Soft form: regulator name + promise-to-forward language. *Behavior*: P1 finding (always); generate action `[<promisor>] forward exact citation for <regulation_id>`; T1 block TL handoff until citation produced; T2 flag `pending_regulatory_citation: true`; maintain `regulatory_dependencies[]` separate from generic OQs. *Output*: `regulatory_dependencies: [{regulator, code, revision, citation_status, promisor, due_date}]`. *Discovery (v1.5.0)*: `discovery.regulatory_regimes[]` may seed `regulatory_dependencies[]` rows at `citation_status: pending` — leads, not citations; an unresolved citation still blocks T1 (discovery never clears FM-04).

### Group 6 — PII & Sensitive Data

- **EC-06 Input citing documents not provided.** *Detection*: regex `.pdf|.xlsx|.docx|.pptx|.csv` filenames OR regulator-citation regex OR phrases "slides not attached", "policy doc separately", "I'll send it". *Behavior*: each ref → `open_dependencies[]` with `resolution: missing_attachment`; regulatory/PII-policy refs escalate to P1; auto-action `[<author>] provide <filename>`; T1 block TL handoff until citation produced. *Output*: `open_dependencies: [{ref_type, ref_value, source_quote, line_ref, severity, action_item_generated}]`.
- **EC-08 PII clearly present in input body.** *Detection*: SG NRIC `[STFG]\d{7}[A-Z]`, credit card `\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}`, 10+-digit account numbers, personal-domain emails, DOB in identifying context, base64 image blocks. *Behavior*: **never echo PII** — replace with `<PII:REDACTED:CLASS=NRIC>`; emit `pii_detected_in_input: true`; P1 governance alert (channel may be non-compliant for PII transport); recommend secure-channel resubmit if T1. *Output*: auto-redact all strings; `pii_redaction_log`; P1 finding `governance: input_channel_pii_exposure_risk`.

## Failure Mode Table

| FM | Detection | Severity | Skill output | Escalation |
|---|---|---|---|---|
| **FM-01** Input quality below threshold | Linguistic composite <5.0 after parsing + ambiguity | P1 blocking | `output_type: needs_clarification`, gap_analysis, recommended_questions | Return to requester; do not route to TL |
| **FM-02** Critical info missing (P1 blocks) | P1 finding in {compliance, tipping_off, retention, audit_schema, pii_inventory, regulatory_citation, dual_approval_named_owner} AND `resolution_provided: false` | P1 blocking | `output_type: blocked_partial_brief`, `failure_state.blocking_items`, `<MISSING:P1:reason>`, `failure_state.suggested_next_action` | Surface to BA/TL; TL resolves P1s or accepts risk in writing |
| **FM-03** Stakeholder conflicts unresolvable | EC-02 + no authority-mode override resolves + no Sponsor-grade speech act | P2 surface | Brief + `unresolved_conflicts: [...]` | Identify resolver (Compliance-vs-Compliance → Legal; PM-vs-Eng on scope → Sponsor; PM-vs-Eng on feasibility → Eng lead); follow-up request |
| **FM-04** Regulatory ref unclear / unresolvable | Regulator not in known dict OR no fetcher named OR buried in paraphrase | P1 T1 / P2 T2 | `output_type: blocked_partial_brief` (T1) or brief-with-flag (T2); `unresolved_citations: [...]` | T1 refuse handoff; T2 produce brief with flag |
| **FM-05** Legal absent on regulatory content | `legal_status ∈ {absent, mentioned_only}` AND `scope_touches_regulatory: true`. **Fires 3/3 pilots — highest-leverage rule** | P1 T1 / P1 T2 | Brief + `governance_gap.type: legal_absent_on_regulatory`, `blocks_tl_handoff: true` | T1 refuse handoff; T2 Sponsor risk-acceptance in writing |
| **FM-06** Tipping-off risk in customer comms | Customer-facing string contains forbidden terms (`sanctions / AML / flagged / suspicious / regulated / SAR / PEP / adverse media / EDD`). Internal-only fields exempt | P1 blocking unless mitigated | `tipping_off_scan.violations`, safe-phrase mitigations, `legal_signoff_required: true` | Replace with safe phrases; if none exists, Legal sign-off required; block TL handoff |
| **FM-07** Tier classification ambiguous | All overrides run AND no tier with confidence ≥0.8, OR two rules at distinct tiers equal weight | P2 | `tier_inference.recommended_tier` = higher choice; OQ `confirm_tier_assignment` (P2) | Higher tier default (fail-safe over-strict); human BA/TL confirms |
| **FM-08** Stakeholder authority unclear | Cannot determine authority mode for utterance that would bind AC | P2 | Per-utterance `authority_mode: {primary, confidence, alternate}`; OQ `clarify_authority` | More-restrictive default (rule-mode) for banking-grade; ask speaker or role owner |
| **FM-09** Scope unclear (story vs epic vs multi-epic) | Author self-signal `(but might need to be|too big\?|may need to split)` OR 3-4 workstreams at boundary OR signals balanced | P2 | `scope_kind: ambiguous`, `scope_signals`, `recommended_scope_kind`, OQ `confirm_scope_kind` | Clarifying question; may emit draft with `pending_scope_confirmation: true` |
| **FM-10** Source type undetectable | All source-type fingerprints < 0.5 confidence OR mixed signals without dominance | P3 short / P2 long | `source_type: doc`, `parsing_mode: generic_prose_fallback`, `confidence: low`; standard brief at reduced confidence | Generic prose fallback; if subsequent passes cannot anchor, escalate to FM-01 |
| **FM-11** Schema validation failure | `banking_grade` row `status: null`; story without ACs and without `insufficient_information`; P1 without `required_resolution`; stakeholder ref not in registry | P1 blocking | `output_type: schema_validation_failure`, `validation_errors`, `partial_output_available` | Never emit malformed brief; retry with gap-fill; if fail, human implementer |
| **FM-12** Ground-truth annotation strip failed | Block detected AND strip errored / boundary overlap / multi-block / substring survives | P1 blocking — fail safe | `output_type: preprocessing_failure`, `failure_code: ground_truth_strip_failed`, `do_not_proceed: true` | Refuse to produce any brief; escalate to human implementer; never proceed to AC generation |
| **FM-13** PII detected in output path (echo risk) | Post-generation scan finds unredacted PII regex hit | P1 blocking | `output_type: pii_echo_blocked`, `detected_pii`, `auto_redaction_attempted`, `manual_review_required` | Auto-redact; if clean emit redacted brief; if redaction fails, escalate human BA |
| **FM-14** Count consistency | OQ-table header N ≠ row count; `stakeholders[]` missing an `absent` row referenced by a `governance_gap`; `epics[].story_ids[]` cardinality ≠ `stories[]` per epic | P1 blocking | Schema-validation error with cell-level diff; refuse emit | Re-run Step 5 (stakeholder enumeration) + Step 12 (assembly counts) |
| **FM-15** Sweep coverage insufficient | `hidden_requirements_sweep.coverage_score` is `partial`/`skipped` on a `brief`; OR `frames_applied ∪ frames_skipped ≠ {1..10}`; OR a `frames_skipped` entry has no matching `frames_skipped_reasons` key | P2 | Refuse `output_type: brief`; downgrade to `blocked_partial_brief` + P2 OQ recording the gap; `skipped` valid only for failure shapes | Re-run Step 9.5 with the missing frames; populate `frames_skipped_reasons`. **Precedence:** FM-02 (P1 governance) takes priority when both apply |
| **FM-16** Idempotency-replay AC missing on state-change story | Story with `banking_grade_concerns.idempotency.status == "applies"` lacks an `acceptance_criteria[]` entry of `scenario_type` `banking_grade_idempotency`/`idempotency_replay` (schema if/then + renderer `validate_idempotency_replay()`) | P1 blocking | Hard schema-validation failure; refuse to write tree until each offending story carries the replay AC | Add a `banking_grade_idempotency` scenario per `gherkin-templates.md §6.1`; or downgrade `idempotency.status` to `not_applicable` with workflow-class justification (AP-4.1) |
| **FM-17** Frame 4 sub-topic coverage incomplete | Frame 4 active (PII / payment / named jurisdiction / consumer-facing / regulated activity) but a required sub-topic per `hidden-requirements-frames.md` has zero matching OQ/assumption (renderer `validate_frame4_subtopics()`) | P2 | Downgrades `coverage_score` `complete`→`partial`; emits P2 OQ per missing sub-topic OR requires a `frames_skipped_reasons` entry keyed by sub-topic | Re-run Frame 4 so each active-trigger sub-topic produces ≥1 OQ; or document the skip with evidence in `frames_skipped_reasons` |

## EC × FM Decision Matrix

| Edge Case | FM-01 quality | FM-02 P1 info | FM-03 conflict | FM-04 citation | FM-05 Legal | FM-06 tipping | FM-07 tier | FM-08 authority | FM-09 scope | FM-10 source | FM-11 schema | FM-12 strip | FM-13 PII echo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EC-01 Empty / minimal | **Y** | | | | | | | | | Y? | | | |
| EC-02 Conflicting | | Y? P1 topic | **Y** | | Y? Legal | Y? comms | | Y? auth-mode | | | | | |
| EC-03 Multi-language | | | | Y? non-EN reg | | Y? non-EN comms | | | | | | | |
| EC-04 Very long | Y? chunk degrades | | | | | | | | | | Y? cross-chunk | | |
| EC-05 Very short | **Y** | | | | | | | | Y? | Y? | | | |
| EC-06 Missing citations | | Y? P1 doc | | **Y** for T1 | Y? Legal doc | | | | | | | | |
| EC-07 Broken structure | Y? degrades | | | | | | | | | Y? type drops | | | |
| EC-08 PII in input | | | | | Y? no Privacy/Legal | | | | | | | | **Y** if echo |
| EC-09 Meta-request | | | | | | | | | | | | | |
| EC-10 Multi-epic | | Y? epic P1 | | | Y? Legal scope | Y? comms | Y? tier varies | | | | | | |
| EC-11 Sub-ticket chain | Y? linked unembedded | | | | | | | | Y? parent unknown | | | | |
| EC-12 Conversational only | **Y** (002=3.5) | | Y? pronouns | | | Y? 👍 sole signoff | | Y? emoji=decision | | | | | |
| EC-13 Email hold-out | | | | | | | | | | Y? headers ambig | | | |
| EC-14 Anonymous | | Y? sets P1 value | | | | | | Y? policy speaker | | | | | |
| EC-15 Note-taker paraphrase | | Y? P1 paraphrased | | Y? citation paraphrased | | Y? tipping paraphrased | | Y? auth paraphrased | | | | | |
| EC-16 Stakeholder on leave | | Y? P1 owner unavail | | Y? fetcher on leave | Y? Legal on leave | | | | | | | | |
| EC-17 Ground-truth present | | | | | | | | | | | | **Y** if strip fails | |
| EC-18 Incomplete citation | | **Y** for T1 | | **Y** | Y? Legal needs it | | | | | | | | |

**Reading the matrix**:

- **EC-12 (conversational-only)** is the multi-FM generator — Slack inputs reliably trip quality + conflicts + tipping-off + authority.
- **EC-17 (ground-truth)** is the only EC that triggers **FM-12**, and FM-12 fires only via EC-17 — unique safety guard.
- **FM-05 (Legal absent)** can be triggered by 8 distinct edge cases — most reliably firing governance gap.
- **EC-01, EC-17** are preprocessing-stage emergencies — must fire before normal flow.

## Cross-References

- `anti-patterns.md` (AP-1.3 ↔ EC-17; AP-2.3 ↔ EC-14; AP-3.2 ↔ EC-15; AP-3.3 ↔ EC-10; AP-5.1 ↔ FM-05; AP-5.3 ↔ EC-15)
- `ambiguity-patterns.md` §5 + §6 (EC-02, EC-14)
- `SKILL.md` keeps a compact FM trigger map (Step 12 enforces the gates); full per-FM detection/output/escalation for FM-01..FM-17 lives here
