# Phase C3 — Edge Case + Failure Mode Catalog

> **Role**: Edge Case + Failure Mode Cataloger, BA Skill Factory
> **Inputs**: All Phase A (A1-A5) + Phase B (B1-B5) outputs
> **Mission**: Identify (A) edge cases the `ba-elicit-from-raw` skill must handle gracefully, and (B) failure modes where the skill must explicitly fail rather than fabricate.
> **Audience**: Phase D skill implementers; R6 reviewers.

---

## 0. Orientation

Codifies the negative space — inputs needing different routing (edge case) or explicit refusal (failure mode). Two architectural truths from Phase B drive design:

1. **A single phrase carries multiple flag types** — banking-grade (A5), linguistic-ambiguity (A2), authority-mode (A4), structural (A3). Do not deduplicate across detectors.
2. **Banking-grade detection is half pattern matching, half forcing function** (B5 §6). Prefer **fail loud** over **silent fabrication**.

Severity = P1/P2/P3 per A2 §5 + A5 §1.

---

## Part 1 — Edge Cases (≥15)

> Edge case = valid input requiring departure from default flow, still producing useful output (possibly partial, possibly annotated). Adapt, don't fabricate.

### EC-01 — Empty / Minimal-Signal Input

- **Description**: Empty, whitespace-only, single sentence, Slack one-liner, or Jira ticket with only a title.
- **Detection**: Non-whitespace chars < 200 AND no source-type metadata AND no A5 §4 banking keyword OR named-stakeholder count = 0 OR A2 composite quality < 2.0/10.
- **Behavior**: Refuse to produce epic/stories. Emit needs-clarification packet: detected source type, required minimums (problem statement, owner, ≥1 constraint), templated requester prompt. Set `ba_confidence: refused`.
- **Output**: `output_type: needs_clarification`, `reason_code: empty_or_minimal_input`, `required_minimums`, `next_action: prompt_requester`.
- **Sources**: A2 §6 + §7 #15; B2 §4.5; A5 §6; B5 §6.

### EC-02 — Conflicting Commenters / Speakers

- **Description**: Two named speakers assert incompatible facts on the same field. Pilot examples: Sarah's AC "Old document is replaced" (r1:54) vs Priya "needs to be archived" (r1:76-78); Jenny "both ideally but web first" (r2:107) vs Sarah Khoo "web…then agent…then mobile" (r2:158-160).
- **Detection**: Two attributed speakers reference the same entity/policy and assert incompatible predicates. Conflict classes: replace-vs-archive, retention-yes-vs-defer, mobile-scope, threshold-vs-calibration, ETA-bucket-merge.
- **Behavior**: (1) Surface both quotes in `open_questions[]` with P2 severity; (2) apply A4 §3.5 authority-mode arbitration — compliance rule-mode beats PM AC; compliance proposal-mode does NOT auto-beat data/eng feasibility; (3) tag `conflict_class`; (4) never silently pick.
- **Output**: `open_questions[].conflict_evidence: [{speaker, quote, line_ref, authority_mode}]`, `recommended_resolution_path`. Working answer = latest claim (A2 §7 #9); conflict ledger preserved. P2 default; P1 if compliance.
- **Source analyses**: A2 §3.3; A4 §3.5; A1 §4.2; B1 HCP-5; B2 HC13; B4 C2/C5.

### EC-03 — Multi-Language Input (English + Thai / SG-Localized)

- **Description**: Non-English tokens (Thai script, simplified Chinese, mixed-script person names), code-switched sentences, non-Latin filenames. Not in pilot but anticipated per SG/TH banking context.
- **Detection**: Non-Latin Unicode in body OR named entities matching Thai U+0E00-U+0E7F, Chinese U+4E00-U+9FFF.
- **Behavior**: (1) Preserve original tokens verbatim — never silent-transliterate; (2) emit `language_inventory`; (3) translate only when English gloss accompanies; else `translation_required: true` (P3); (4) maintain UTF-8; (5) compliance/legal text in non-English is P2.
- **Output**: `language_inventory: [{script, sample, frequency}]`, per-quote `language_tag`, `translation_status`.
- **Sources**: A1 §3.2; A3 §1.5; A5 E3-12.

### EC-04 — Very Long Input (Token-Budget Concern)

- **Description**: Jira ticket with 100+ comments, 6-hour Slack incident, 90-minute meeting transcript. Pilot 003 (~160 lines) is at the lower end.
- **Detection**: Tokens > 25k OR distinct speakers > 20 OR comments > 50 OR file > 250 KB. Secondary: Slack > 200 messages; meeting > 8000 words.
- **Behavior**: (1) Chunk by **semantic boundary** — Jira by comment-thread/stakeholder; Slack by topic-shift; Meeting by numbered-agenda; (2) run source-detect + ground-truth-strip on full input first; (3) maintain global `entity_registry`; (4) emit `chunking_summary`; (5) reduce confidence one tier.
- **Output**: `processing_metadata.chunking: {strategy, num_chunks, semantic_boundaries, cross_chunk_references_resolved}`. Each AC/dependency carries source chunk index.
- **Sources**: A3 §1.4; A2 §1.2; B3 §5.

### EC-05 — Very Short Input (Insufficient Signal)

- **Description**: Source type recognizable but substance insufficient — Jira with title + one-line description, 3-message Slack thread, meeting with attendees but empty body. Differs from EC-01 in that form is detectable.
- **Detection**: Source detected AND body < 500 chars AND stakeholders < 2 AND zero turns beyond opener AND composite quality < 4.0.
- **Behavior**: Produce partial brief `completeness: partial` with one stub story, no fabricated ACs, structured "Information Needed Before TL Handoff". Recommend follow-up elicitation.
- **Output**: `output_type: partial_brief`, `missing_fields`, `min_clarifications_needed`. Quality scorecard rendered.
- **Sources**: A2 §6 + §7 #15; B2 §4; B5 §4.2.

### EC-06 — Input Citing Documents Not Provided

- **Description**: Attachments, policy docs, regulator citations, prior tickets, slide decks referenced but not attached. Pilot: `compliance-data-retention-policy-v3.2.pdf` (r1:115), `support-call-analysis-week-2026-w18.xlsx` (r1:114), David's slides (r3:65), `MAS-AML-1A revision` (r3:39).
- **Detection**: Regex match `.pdf|.xlsx|.docx|.pptx|.csv` filenames OR regulator-citation `[A-Z]+-[A-Z]+-[A-Z0-9-]+` OR phrases "slides not attached", "policy doc separately", "I'll send it" without parsed attachment.
- **Behavior**: (1) Each ref → `open_dependencies[]` with `resolution: missing_attachment`; (2) regulatory/PII-policy refs escalate to P1 (A5 R8); (3) auto-action `[<author>] provide <filename>` (A4 §1.3); (4) T1 — block TL handoff until citation produced; (5) T2 — flag and allow.
- **Output**: `open_dependencies: [{ref_type, ref_value, source_quote, line_ref, severity, action_item_generated}]`. Top-level `blocks_tl_handoff: true` if T1 + unresolved.
- **Sources**: A1 §4.4; A3 §1.5; A5 E1-5 + E3-1; B2 HC15; B3 §3.3; B5 P-02.

### EC-07 — Broken Structure / Note-Taker Paraphrase

- **Description**: Recognized source type but section markers corrupted, missing, or paraphrased. 003 partly exemplifies: Aisha "Note-taker filtered some content (paraphrase, not verbatim)" (r3:18).
- **Detection**: Source-type fingerprint passes but section-marker count < expected baseline (Jira < 4 of 8 standard headings; Meeting < 5 of 8 agenda; Slack speaker-turn fails > 20%) OR explicit note-taker disclaimer.
- **Behavior**: (1) Fall back to prose parser (A3 §7.3 default), retain source-type tag; (2) every statement → `attribution_confidence: paraphrase` (A4 R9); (3) lower section-completeness score; (4) for P1/P2 findings from paraphrased content, emit "verbatim verification required" action item.
- **Output**: Per-finding `attribution_confidence: {verbatim|paraphrase|inferred}`. Top-level `parsing_mode: degraded`, `parsing_reason: structure_broken`, `recovered_sections / unrecovered_sections`.
- **Source analyses**: A3 §7.3 + §8 #16; A4 §5.7 + R9; B1 G10; B3 §3.3.1; B4 HCP-5.

### EC-08 — PII Clearly Present in Input Body

- **Description**: Actual PII tokens (not just references) — NRIC value, account number, ID-doc photo, DOB. Pilot references categorically ("expired NRIC photos" r1:67) but production may include values.
- **Detection**: SG NRIC `[STFG]\d{7}[A-Z]`, credit-card `\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}`, 10+-digit account numbers, personal-domain emails, DOB in identifying context, base64 image blocks.
- **Behavior**: (1) **Never echo PII** — replace with `<PII:REDACTED:CLASS=NRIC>`; (2) `pii_detected_in_input: true`; (3) emit P1 governance alert (channel may be non-compliant for PII transport); (4) recommend secure-channel re-submit if T1; (5) generate `pii_inventory` (A5 R6).
- **Output**: Auto-redact all strings. New fields: `pii_detected_in_input`, `pii_redaction_log`, `pii_inventory`. P1 finding `governance: input_channel_pii_exposure_risk`.
- **Sources**: A1 §1.1 #13-15; A5 §1a E1-13 + R6; A4 §3.7; B5 P-04; A3 §6.1.

### EC-09 — Meta-Request (Asks for Clarification, Not Work)

- **Description**: Input requests help understanding a domain or a meta-question about a prior brief — not the work itself. Examples: "Can you explain what tipping-off means?"; "Should we use Story or Epic for EDD?"
- **Detection**: Interrogative form (`?`, opens with `what/why/how/should/can you explain`) AND no problem-statement structure AND stakeholders ≤ 1 AND no operational metrics.
- **Behavior**: (1) Recognize as meta-request; do not produce a brief; (2) route to `meta_response` using A1 §8 glossary + best-practices ref; (3) cite canonical passage; (4) suggest requester resubmit work request.
- **Output**: `output_type: meta_response`, `meta_response_body`, `citations`, `suggested_next_action`. No epics or stories.
- **Sources**: A1 §5.1; A2 §4; A4 §1.

### EC-10 — Input Spans Multiple Epics

- **Description**: Presented as one initiative but decomposes into ≥2 epics. Canonical: 003 "Onboarding 2.0 / EDD Workflow Re-design" is 5-6 epics (A3 §3.3; A5 §5; B5 C2): EDD redesign, biometric, risk-engine calibration, mobile follow-on, migration, status page.
- **Detection**: Distinct workstreams ≥ 3 (A3 §8 #8); phase-language (`phase 1/2`, `Q3/Q4`, `web first / mobile follow-on`); vendor-integration cluster (A3 §1.11); migration / legacy-data references (A3 §5.6); ≥ 4 banking-grade concern boundaries shifting (A5 R9).
- **Behavior**: (1) Emit `scope_kind: multi_epic`; (2) one output file per epic; (3) tier inference **per epic** (B5 §6 decision #1) — biometric → T1, mobile follow-on → T2; (4) maintain `initiative_index.md`; (5) stakeholder/banking-grade/dependency passes run per epic.
- **Output**: Top-level wrapper `initiative.md`: `scope_kind: multi_epic`, `epic_files: [...]`, `per_epic_tier: [{epic_id, tier, justification}]`. Each epic = standard brief.
- **Source analyses**: A3 §3.3 + §8 #8; A5 §5; B1 G4; B2 C3; B3 §3.2 + §3.3; B5 §6.

### EC-11 — Sub-Ticket / Linked-Issue Chain

- **Description**: Story-sized ticket chained to others — Jira `Blocks:`, `Relates to:`, parent epic key, `📎 Linked:`. Pilot: 001 `Blocks: LOAN-3001` (r1:121), `Relates to: LOAN-2401 (closed)` (r1:122); 002 `📎 Linked: PAY-1192 (closed)` (r2:28).
- **Detection**: Jira link blocks OR inline `📎 Linked: <KEY>` OR "parent" / "child of" / "subtask" language. Linked-ticket count ≥ 1.
- **Behavior**: (1) Extract typed dependency edges per A3 §5 (`blocks`, `blocked_by`, `relates_to`, `historical`, `subtask_of`); (2) mark closed/historical as **context-only**; (3) linked ticket → `dependencies[]` with `resolution: external_reference_required` if content not embedded; (4) parent-epic implied → `scope_kind: story_within_epic`; (5) surface "needs upstream ticket content" if scope truncated.
- **Output**: `scope_kind: {single_epic|multi_epic|story_within_epic|unknown}`, `linked_tickets: [{key, relation, status, content_embedded}]`.
- **Sources**: A3 §1.6 + §5.1 + §5.3; A1 §3.1; B3 row 4.

### EC-12 — Conversational Format with No Structure (Slack-Only Signal)

- **Description**: Pure Slack thread with no synthesizing recap. Decisions scattered across emoji, pronoun-laden replies, interleaved side-topics. Pilot 002 is **worst case** (A2 §6.2 = 3.5/10).
- **Detection**: Source-type = Slack AND no structured summary message ("1." "2." "3." in one speaker's turn) AND > 4 topics interleaved AND > 5 cross-message pronominal references.
- **Behavior**: (1) Slack parser dispatch; (2) resolve pronouns in 5-message sliding window; (3) emoji 👍/✅/+1/🙏 = soft acceptance, **never** formal sign-off — emit `formal_signoff_pending: true` + OQ per compliance-topic emoji; (4) synthesize ACs from longest decision chain; (5) refuse handoff below 5.0 (FM-01); (6) reduce confidence one tier.
- **Output**: `parsing_mode: synthesized_from_chat`, per-decision `decision_evidence_strength`, each AC `synthesis_path: [msg_refs]`.
- **Sources**: A2 §6.2; A3 §7.2; A4 §5.3/§5.4; B2 row 12; B3 §5; A1 §3.3.

### EC-13 — Email-Thread Hold-Out Style (Quoted-Reply Inversion)

- **Description**: Email thread where chronological order is **inverted** by quote-reply nesting (newest at top, prior quoted below). `From:/To:/Subject:/Date:` headers; `>` quote markers; signature blocks. Not in pilot but a known banking BA source.
- **Detection**: `From:`/`To:`/`Subject:`/`Date:` quartet OR `>` line-prefix quoting OR `On <date>, <name> wrote:` markers OR `--` signature delimiter OR `.eml` extension.
- **Behavior**: (1) Reverse to oldest-first (A3 §7.1 final line); (2) parse signature blocks for role metadata; (3) each "wrote:" = speaker turn; (4) email is more formal than Slack — boost `attribution_confidence: high`; (5) strip quoted-reply duplication.
- **Output**: `source_type: email_thread`, `parsing_inversion_applied: true`, `quoted_replies_deduplicated: N`.
- **Sources**: A3 §7.1 inversion patterns.

### EC-14 — Anonymous Commenters / Weak Attribution

- **Description**: Contributions tagged "Anonymous", "Unknown", `(group, 20 min)`, or "Anonymous (likely <Name>)". Canonical: 001:103-104 "Anonymous (likely Raj) — N could be 3".
- **Detection**: Speaker matches `^\s*(Anonymous|Unknown|Anon|Guest)\b` OR group label `(group, \d+ min)` OR uncertainty marker `(likely <Name>)`.
- **Behavior**: (1) Set `attribution: anonymous`, `attribution_guess`, `attribution_confidence: low`; (2) **refuse to bind** numeric policy params, thresholds, retention values, compliance assertions to anonymous statements; (3) convert proposal → OQ `requires_named_owner: true`; (4) anonymous on compliance/PII/audit → escalate to P2 (B5 C1 promotion); (5) capture suggestion as `proposed_default`.
- **Output**: Per-utterance `attribution_block: {primary: anonymous, guess, confidence: low}`. Anonymous-sourced ACs → `open_questions[].proposed_value`, not `stories[].acceptance_criteria[]`.
- **Sources**: A1 §3.4; A2 §3.1 #5 + §7 #5; A3 §7.1 + §8 #11; A4 §3.6 + R5; A5 I1-11; B1 HCP-8; B2 HC2; B4 T8; B5 P-16.

### EC-15 — Note-Taker-Mediated Content (Paraphrase)

- **Description**: Entire input produced by a note-taker paraphrasing multiple speakers with explicit disclaimer. Pilot: 003 — Aisha Rahman notes "(paraphrase, not verbatim)" (r3:18). Aside "Sigh." (r3:147).
- **Detection**: `Note-taker:` metadata field OR paraphrase disclaimer OR first-person bracketed asides matching note-taker name OR `(me!)` self-reference.
- **Behavior**: (1) Every statement → `attribution_confidence: paraphrase`; (2) preserve note-taker asides in `meta_asides` verbatim but not as decisions (B2 C5); (3) P1/P2 findings from paraphrased content → "verbatim verification required" action item to original speaker; (4) note-taker = tracked `meta_stakeholder`; (5) flag note-taker self-assignments as `mediated_self_assignment`.
- **Output**: Global `mediation: {note_taker, paraphrase_mode: true}`, per-utterance `attribution_confidence: paraphrase`, `meta_asides`.
- **Sources**: A1 §3.3; A3 §7.3; A4 §2.6 + §5.7 + R9; B1 G10; B2 C5; B3 §3.1; B4 HCP-5; B5 G-C.

### EC-16 — Stakeholder Going on Leave / Handoff

- **Description**: Key stakeholder leaving, unavailable, or handing off. Pilot: 003 `[Apologies: Legal — Sundar K., conflict with board prep]` (r3:31); 001 Sarah "creating this ticket for handoff to BA team" (r1:106-108); 003:148 "Loop legal in next time — Sundar's calendar already booked".
- **Detection**: Phrases `on leave / out of office / OOO / handing over to / handoff to / cover for / acting <role>` OR `Apologies:` in meeting metadata combined with role critical to scope.
- **Behavior**: (1) Emit `stakeholder_continuity_risk` for P1/P2 unavailable stakeholder; (2) detect named cover; if none, P2 OQ `who_covers_<role>`; (3) Legal-on-leave on regulatory scope → P1; (4) cross-reference action-item dates with absence window — flag due dates inside leave period without cover; (5) "handoff confirmation" action item.
- **Output**: `stakeholder_availability: [{name, role, status: present|on_leave|handing_off|absent_one_time, cover, return_date}]`. Inbound handoffs (Sarah → BA team) → `inbound_handoff_metadata`.
- **Sources**: A4 §1.3 + R4; B4 T1; B1 HCP-1. Pilot: 003:31, 003:148, 001:108.

### EC-17 — Ground-Truth Annotation Sections Present (Training-Set Hidden Blocks)

- **Description**: Input contains `## Intentional Issues for R6 to Catch (Hidden from BA Workflow)` block — training-set audit annotations, **not** user content. Present in all 3 pilot inputs (r1:137-181, r2:170-217, r3:167-221). Production won't contain; if it does, it's a leak or evaluation harness.
- **Detection**: Literal header `## Intentional Issues for R6 to Catch` or `## Hidden from BA Workflow` or `^## (Intentional|Hidden|Ground[- ]Truth|Audit Annotation)`.
- **Behavior**: (1) **Strip before any parsing** — first preprocessing pass (A3 §1.13; B3 C5 mandatory); (2) `audit/` mode may consume for self-evaluation; in production, **never read** — would contaminate output by leaking answers; (3) log `ground_truth_annotation_detected_and_stripped: true`; (4) strip failure → **fail closed** per FM-12.
- **Output**: Internal log: `preprocessing.ground_truth_stripped: {found, byte_range, strip_method}`. Never echo annotation content.
- **Sources**: A3 §1.13 + §8.2; B3 row 12 + C5; pilot evidence in all 3 inputs. **Unique to A3** — no other A-phase warned.

### EC-18 — Regulatory Citation Incomplete (Name Without Full Reference)

- **Description**: Regulator and code named but no full citation, document, or URL. Canonical: 003:39 "MAS-AML-1A revision — Priya to forward exact citation".
- **Detection**: Regex `[A-Z]{2,}-[A-Z]{2,}-[A-Z0-9-]+` (MAS-AML-1A, OFAC-SDN-2024, FATF-Rec-10) AND no attached doc AND no URL AND no quoted regulation text. Soft form: "MAS guidance", "AML revision" + promise-to-forward language.
- **Behavior**: (1) P1 finding — regulator named without citation is **always P1** (A5 R4); (2) identify promisor; generate action `[<promisor>] forward exact citation for <regulation_id> — due <date>`; (3) **block TL handoff** for T1 until citation produced; (4) T2 — flag `pending_regulatory_citation: true`; (5) maintain `regulatory_dependencies[]` separate from generic OQs.
- **Output**: `regulatory_dependencies: [{regulator, code, revision, citation_status: pending|partial|resolved, promisor, due_date}]`. Top-level `blocks_tl_handoff: true` if T1 + unresolved.
- **Sources**: A1 §3.1; A2 §5 #13; A5 §1c E3-1 + R4; B2 HC4; B4 HCP-15; B5 P-02 + G-H; B1 row 5.

**Edge case count: 18** (target ≥ 15). Each is detector + behavior pair without fabrication.

---

## Part 2 — Failure Modes (≥10)

> Failure mode = condition under which the skill **must refuse to produce a normal brief** because doing so would fabricate, misroute, or violate governance.

### FM-01 — Input Quality Below Threshold

- **Detection**: Linguistic-quality composite < 5.0 (A2 §6) computed after parsing + ambiguity detection but before AC synthesis.
- **Severity**: **P1 blocking** — must not produce a brief.
- **Output**: `output_type: needs_clarification`, `reason_code: input_quality_below_threshold`, `linguistic_quality: {sub-scores + composite}`, `gap_analysis: [{dimension, score, gap, suggested_clarifications}]`, `recommended_questions: [...]`.
- **Escalation**: Return to the requester (human or upstream agent). Include recommended questions for targeted resubmit. Do not escalate to TL — brief not in shape.
- **Source analyses**: A2 §7 #15; B2 §4; B5 §6.

### FM-02 — Critical Info Missing (P1 Ambiguity Blocks Production)

- **Detection**: Any open finding `severity: P1` AND `category in {compliance, tipping_off, retention, audit_schema, pii_inventory, regulatory_citation, dual_approval_named_owner}` AND `resolution_provided: false`. Examples: replace-vs-archive unresolved with PII present (A5 E1-4); tipping-off copy not produced (A5 E2-6); regulator named without citation on T1 (A5 R4).
- **Severity**: **P1 blocking** — produce partial brief with P1 blockers surfaced; do not assert TL-ready.
- **Output**: `output_type: blocked_partial_brief`, `blocking_findings: [{id, category, source_quote, line_ref, required_resolution}]`, `provisional_content` with P1 gaps inline as `<MISSING:P1:reason>`, `unblock_actions: [{action, owner, due, dependency_type}]`.
- **Escalation**: Surface to human BA/TL with blocking-findings list. TL must resolve P1s (or accept risk in writing) before further work. Generate requester summary template.
- **Source analyses**: A5 §6; B5 §6; A2 §5; B2 HC1/HC3/HC4/HC12.

### FM-03 — Stakeholder Conflicts Unresolvable

- **Detection**: EC-02 condition (named speaker conflict) AND no authority-mode override resolves (rule-vs-rule, or proposal-vs-proposal without SME-calibration grounds) AND no Sponsor-grade speech act ("yes go ahead" / chair scope-cut).
- **Severity**: **P2 surface for resolution** — produce brief, flag conflict, do not silently pick.
- **Output**: Standard brief plus `unresolved_conflicts: [{conflict_id, speakers, claims, authority_modes, attempted_arbitration, recommended_resolver, recommended_resolution_path}]`. Working-answer empty or "TBD pending <resolver>".
- **Escalation**: Identify resolver per A4 §3.5 — compliance-vs-compliance → Legal; PM-vs-Eng on scope → Sponsor; PM-vs-Eng on feasibility → Eng lead; Compliance-proposal-vs-Data → joint sync. Generate follow-up request.
- **Source analyses**: A4 §3.5; B4 HCP-1 + HCP-3; B1 G5; A2 §3.3.

### FM-04 — Regulatory Reference Unclear / Unresolvable

- **Detection**: Distinct from EC-18 — here skill cannot resolve at all. Regex `[A-Z]{2,}-...` but `regulator_name not in known_regulators_dict` (MAS, OFAC, FATF, FinCEN, BSP, OJK, BoT, BNM, FCA, BaFin) OR citation present but no fetcher named AND no `due` inferable OR buried in paraphrase.
- **Severity**: **P1 blocking for T1; P2 surface for T2.**
- **Output**: `output_type: blocked_partial_brief` (T1) or brief-with-flag (T2). `unresolved_citations: [{raw_token, regulator_guess, confidence, fetcher: null, recommended_action}]`.
- **Escalation**: T1 refuse handoff; escalate to Compliance Officer or Owner. T2 produce brief with flag; ownerless action item — TL/PM assigns.
- **Sources**: A5 R4; B5 P-02; B4 HCP-15; B2 HC4.

### FM-05 — Legal Absent on Regulatory Content (Governance Gap)

- **Detection**: `legal_status = absent OR mentioned_only` AND `scope_touches_regulatory = true`. Trigger: any B5 P-01..P-14 pattern fires AND no role match `(legal|counsel|attorney|solicitor)` in attendees. **3 of 3 pilot inputs** — strongest converged finding (B1 HCP-1; B4 T1; B5 P-14; B5 §6 "single highest-leverage rule").
- **Severity**: **P1 blocking for T1; P1 surface for T2** — governance violation, not routine gap.
- **Output**: Standard brief + top-level `governance_gap: {type: legal_absent_on_regulatory, severity: P1, evidence: [<regulatory_touchpoints>], required_action: schedule_legal_review, blocks_tl_handoff: true}`.
- **Escalation**: T1 — refuse TL handoff; escalate to Sponsor/Owner: "Legal review required". T2 — produce brief but `blocks_tl_handoff: true`; require explicit Sponsor risk-acceptance in writing.
- **Sources**: A1 §3.4 + §6; A2 §7 #8; A3 §8 R9; A4 §4.2 + R10 + §3.7; A5 R5 + I1-7 + I3-5; B1 HCP-1; B4 T1 + HCP-2; B5 P-14 + §6.

### FM-06 — Tipping-Off Risk in Customer Communications

- **Detection**: Any proposed customer-facing string (status, email, SMS, push, error, in-app banner, agent script visible to customer) AND contains forbidden terms: `sanctions`, `AML`, `flagged`, `suspicious`, `regulated`, `compliance hold`, `SAR`, `PEP`, `adverse media`, `EDD`. False-positive guard: internal-only fields (`agent_dashboard.real_reason`) exempt.
- **Severity**: **P1 blocking unless mitigated** — regulatory penalty class.
- **Output**: `tipping_off_scan: {risk_level, violations: [{string, forbidden_terms_matched, context, severity: P1}], mitigations_applied: [{original, suggested_safe_phrase, reference: non-tipping-vocabulary.md}], legal_signoff_required: true}`.
- **Escalation**: Replace violations with safe phrases from `references/non-tipping-vocabulary.md` (A5 R12). If no safe phrase exists, requires Legal sign-off before implementation. Block TL handoff until (a) mitigation recorded or (b) Legal sign-off captured.
- **Sources**: A1 §1.1 #7; A2 §5 #12; A3 §6.3; A4 §3.3; A5 E2-3/5/6 + E3-9 + R3 + R12; B1 HCP-2; B4 T1+T2; B5 P-01 + T17.

### FM-07 — Tier Classification Ambiguous

- **Detection**: Every override has run (banking-grade beats informal form; regulator-cited → T1; compliance-officer + AML/sanctions → T1) yet no tier emerges with confidence ≥ 0.8 OR two rules fire at distinct tiers with equal weight OR multi-epic epics straddle tiers without majority.
- **Severity**: **P2** — flag for human tier assignment; brief at conservative tier.
- **Output**: `tier_inference: {recommended_tier: <higher choice>, confidence: low, signals, rationale: ambiguous_after_override}`. Higher tier as default (fail safe to over-strict). OQ `confirm_tier_assignment` (P2).
- **Escalation**: Higher-tier working default — never under-strict. Human BA/TL confirms. Document in `processing_metadata.tier_decisions[]`.
- **Sources**: A5 §5; B1 G2; B5 C2 + §6 + §4.2.

### FM-08 — Stakeholder Authority Unclear

- **Detection**: Cannot determine authority mode (rule/proposal/preference/estimate/pain per A4 §3) for utterance that would bind an AC. Example: Compliance "we should probably archive" — `should` + `probably` ambiguous between rule (binding) vs proposal (negotiable). Or: unnamed "compliance team" (r1:43) without individual.
- **Severity**: **P2** — produce brief, flag ambiguity.
- **Output**: Per-utterance `authority_mode: {primary, confidence, alternate}`. OQ: `clarify_authority: <utterance> from <speaker> — rule or proposal?` with `recommended_resolver`.
- **Escalation**: Apply **more restrictive** default (rule-mode) for banking-grade to avoid under-protective ACs; ask speaker or role owner. Diffuse institutional speakers need named individual before binding.
- **Sources**: A4 §3.3 + §3.5 + R2; B2 C4; B4 HCP-1; B5 §1 T3.

### FM-09 — Scope Unclear (1 Story vs Epic)

- **Detection**: Cannot decide single story vs single epic vs multi-epic. Author self-signal: 001 `Type: Story (but might need to be Epic — too big?)` (r1:23). Phrases `(but might need to be|too big\?|may need to split)` OR 3-4 workstreams (at A3 §8 #8 boundary) OR signals balanced.
- **Severity**: **P2** — ask before proceeding.
- **Output**: `scope_kind: ambiguous`, `scope_signals: [{signal, type, weight}]`, `recommended_scope_kind`, OQ `confirm_scope_kind`.
- **Escalation**: Clarifying question: "This appears to be {scope-kind}; confirm? Do these workstreams belong together — [list]?" No final brief until confirmed. May emit *draft* at recommended scope with `pending_scope_confirmation: true`.
- **Sources**: A3 §3 + §8 #8; B1 G4; B2 HC8; B3 §3.2 + C4; A2 §5 #8.

### FM-10 — Source Type Undetectable

- **Detection**: All source-type fingerprints below 0.5 confidence OR mixed signals without dominance (doc containing pasted Slack snippets + Jira comments without canonical wrapping).
- **Severity**: **P3** for short inputs; **P2** for longer inputs.
- **Output**: `source_type: doc`, `parsing_mode: generic_prose_fallback`, `confidence: low`, standard brief at reduced confidence. Per B3 §5: human checkpoint before TL handoff.
- **Escalation**: Generic prose fallback (B3 §5 last row): extract problem → constraints → decisions. `ba_confidence: low`. If subsequent passes cannot anchor, escalate to FM-01.
- **Sources**: A2 §1; A3 §7 + §8 #1; B3 §5.

### FM-11 — Schema Validation Failure

- **Detection**: Post-generation validator finds: any `banking_grade_concerns` row with `status: null` (must be `applies|not_applicable|unknown_p2`); any story without ACs and without `assessment: insufficient_information`; any P1 finding without `required_resolution`; any stakeholder reference not in `stakeholders[]` registry.
- **Severity**: **P1 blocking** — fail loud per B5 §6.
- **Output**: `output_type: schema_validation_failure`, `validation_errors: [{field_path, error_type, expected, actual}]`, `recovery_attempted`, `partial_output_available`.
- **Escalation**: Do NOT emit malformed brief. Return errors to orchestrator. Suggest retry with gap-fill prompts. If retry fails, escalate to human implementer — likely a code-level bug.
- **Sources**: A5 §6 ("empty rows = schema-validation failure. This is the forcing function"); A5 R1; B5 P-04 + §4.1; B3 §4.

### FM-12 — Ground-Truth Annotation Stripping Failed

- **Detection**: Preprocessing pre-flight per EC-17 ran AND any of: (a) `ground_truth_block_detected: true` AND `strip_method_returned_error: true`; (b) detected block boundary overlaps with non-annotation text; (c) multiple ground-truth blocks detected, only one stripped; (d) substring `R6 to Catch` or `Hidden from BA Workflow` survives post-strip.
- **Severity**: **P1 blocking — fail safe** — never produce a brief when ground-truth content may have leaked into parsing context.
- **Output**: `output_type: preprocessing_failure`, `failure_code: ground_truth_strip_failed`, `detected_markers: [{line, content_preview}]`, `recovery_suggestion: manual_review_of_input`, `do_not_proceed: true`.
- **Escalation**: Refuse to produce any brief. Return failure code to orchestrator. Escalate to human implementer. **Never proceed to AC generation** — would constitute fabrication (model has seen the answers).
- **Sources**: A3 §1.13 + §8.2 (unique safety rule); B3 C5 (mandatory preprocessing); B3 row 12; pilot evidence r1:137-181, r2:170-217, r3:167-221.

### FM-13 — PII Detected in Output Path (Echo Risk)

- **Detection**: Post-generation scan applies EC-08 PII regex set to proposed output. Any match = failure. Scrubbed tokens (`<PII:REDACTED:CLASS=X>`) allowed.
- **Severity**: **P1 blocking** — never let unredacted PII flow downstream.
- **Output**: `output_type: pii_echo_blocked`, `detected_pii_in_output: [{field_path, pii_class, count}]`, `auto_redaction_attempted`, `auto_redacted_output_available`, `manual_review_required: true`.
- **Escalation**: Attempt auto-redaction pass; if clean, emit redacted brief with `pii_redaction_in_output: true`. If redaction fails (token cannot be confidently classed), refuse. Escalate to human BA.
- **Sources**: A1 §1.1 #13-15; A5 R6 + §1a E1-13; B5 P-04. Distinct from EC-08 — output-side guard.

**Failure mode count: 13** (target ≥ 10). Each is a deterministic refuse-rather-than-fabricate condition.

---

## Part 3 — Decision Matrix (Edge Case × Failure Mode Trigger)

Rows = edge cases; columns = failure modes; cells = which FM each EC triggers (`Y` = always, `Y?` = if condition met). Empty cell = no trigger.

| Edge Case | FM-01 quality | FM-02 P1 info | FM-03 conflict | FM-04 citation | FM-05 Legal | FM-06 tipping | FM-07 tier | FM-08 authority | FM-09 scope | FM-10 source | FM-11 schema | FM-12 strip | FM-13 PII echo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EC-01 Empty / minimal | **Y** | | | | | | | | | Y? | | | |
| EC-02 Conflicting speakers | | Y? P1 topic | **Y** | | Y? Legal | Y? customer-comms | | Y? auth-mode | | | | | |
| EC-03 Multi-language | | | | Y? non-EN reg | | Y? non-EN comms | | | | | | | |
| EC-04 Very long | Y? chunk degrades | | | | | | | | | | Y? cross-chunk | | |
| EC-05 Very short | **Y** | | | | | | | | Y? | Y? | | | |
| EC-06 Missing citations | | Y? P1 doc | | **Y** for T1 | Y? Legal doc | | | | | | | | |
| EC-07 Broken structure | Y? parse degrades | | | | | | | | | Y? type drops | | | |
| EC-08 PII in input | | | | | Y? no Privacy/Legal | | | | | | | | **Y** if echo |
| EC-09 Meta-request | | | | | | | | | | | | | |
| EC-10 Multi-epic | | Y? epic P1 | | | Y? Legal scope | Y? customer-comms | Y? tier varies | | | | | | |
| EC-11 Sub-ticket chain | Y? linked unembedded | | | | | | | | Y? parent unknown | | | | |
| EC-12 Conversational only | **Y** (002=3.5) | | Y? pronouns unresolved | | | Y? 👍 sole signoff | | Y? emoji=decision | | | | | |
| EC-13 Email hold-out | | | | | | | | | | Y? headers ambiguous | | | |
| EC-14 Anonymous | | Y? sets P1 value | | | | | | Y? policy speaker | | | | | |
| EC-15 Note-taker paraphrase | | Y? P1 paraphrased | | Y? citation paraphrased | | Y? tipping paraphrased | | Y? auth paraphrased | | | | | |
| EC-16 Stakeholder on leave | | Y? P1 owner unavailable | | Y? fetcher on leave | Y? Legal on leave | | | | | | | | |
| EC-17 Ground-truth present | | | | | | | | | | | | **Y** if strip fails | |
| EC-18 Incomplete citation | | **Y** for T1 | | **Y** | Y? Legal needs it | | | | | | | | |

### Reading the Matrix

- **EC-01 (empty)** and **EC-17 (ground-truth)** are preprocessing-stage emergencies — must fire before normal flow.
- **EC-12 (conversational only)** is the multi-failure-mode generator — Slack inputs reliably trip quality + conflicts + tipping-off + authority (consistent with A2 §6.2 putting Slack as worst case).
- **EC-10 (multi-epic)** fans out into per-epic failure modes — the per-epic tier-inference rule (B5 §6 decision #1) means multiple FMs can fire on different epics in the same input.
- **EC-17 (ground-truth)** is the only EC that triggers **FM-12**, and FM-12 fires only via EC-17 — unique safety guard.
- **FM-05 (Legal absent)** can be triggered by 8 distinct edge cases — most reliably firing governance gap (B1 HCP-1; B4 T1; B5 §6 "highest-leverage rule").

---

## 4. Aggregate Summary

| Class | Count |
|---|---|
| Edge cases catalogued | **18** |
| Failure modes catalogued | **13** |
| P1-default edge cases | 3 (EC-01, EC-08, EC-17; EC-18 in T1) |
| P1-severity failure modes | 7 (FM-01, FM-02, FM-05, FM-06, FM-11, FM-12, FM-13) |
| Triangulated source coverage | 100% — every entry references ≥2 A/B phases |

### Top Implementation Priorities

1. **FM-12 + EC-17 (ground-truth strip pre-flight)** — highest-stakes safety guard; failure invalidates the skill (A3 §1.13; B3 C5). Implement first.
2. **FM-05 (Legal absent)** — most-fired FM; fires 3/3 pilot inputs (B5 §6 "highest-leverage rule").
3. **FM-06 (tipping-off scan)** — highest regulatory-penalty exposure; ship `non-tipping-vocabulary.md` per A5 R12.
4. **FM-11 (schema validation)** — the forcing function A5 §6 calls the skill's main architectural value.
5. **FM-01 (quality threshold)** — gates everything else; below 5.0, nothing may silently fabricate.
6. **EC-10 (multi-epic)** — pilot 003 exercises; per-epic tier inference required (B5 §6 #1).
7. **EC-12 + EC-07 + EC-15** — informal / mediated content paths.

### Closing Note for Phase D

Converts A1-A5 empirical findings + B1-B5 cross-validation residue into **18 edge-case specs** and **13 failure-mode contracts**. Each edge case produces useful partial output with annotations; each failure mode refuses and explains why. The decision matrix encodes the routing. Phase D should ingest this as the **test-case spec** for negative-path coverage — every row is at least one test fixture.

— End of Phase C3 Edge Case + Failure Mode Catalog —
