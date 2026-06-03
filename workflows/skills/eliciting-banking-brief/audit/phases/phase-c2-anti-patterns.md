# Phase C2 — Anti-Pattern Catalog

> **Role**: Anti-Pattern Catalog Builder for BA Skill Factory
> **Inputs**: All Phase A (A1-A5) and Phase B (B1-B5) outputs; `references/ba-best-practices.md`
> **Mission**: Identify ANTI-PATTERNS — behaviors the `ba-elicit-from-raw` atomic skill must NEVER do, or warning signs that BA work is going wrong. Each anti-pattern is enforceable as a skill guard or assertion.
> **Method**: Evidence-anchored — every anti-pattern is grounded in 2+ phase analyses or direct quote from raw inputs.

---

## 0. Orientation

Across the five A-phases and five B-phases, a consistent picture of failure modes emerges. The skill's greatest risks are not the things it cannot do but the things it **silently does wrong**: collapsing ambiguity into invented certainty, accepting weak attribution as binding policy, flattening compliance constraints into convenient summaries, and producing artifacts whose surface neatness masks unresolved governance gaps.

This catalog enumerates 22 anti-patterns across 8 buckets, each with detection signal, evidence-anchored rationale, correct alternative behavior, and source-phase trace. They are intended to populate the skill's guards/assertions layer and to serve as a checklist for any reviewer auditing skill output.

---

## 1. Wrong Inferences (Dangerous Leaps)

The skill must never trade an explicit quote for an unstated conclusion of its own — even when domain priors suggest one. The three patterns below are the most consequential leaps observed in the corpus.

### AP-1.1 — Inferring lifecycle policy from process labels

| Field | Detail |
|---|---|
| **Detection signal** | The skill writes "documents are auto-deleted after N days" / "abandoned applications are purged" / any retention claim that is not a verbatim quote from a compliance speaker, attached policy doc, or regulator citation. |
| **Why dangerous** | Input 001 explicitly says "if applicant abandons their application, what happens to the docs?" (001:82-83). Priya defers the answer to "separate ticket". A skill that fills in "docs are deleted after 30 days" because input 003 mentions that elsewhere has invented a policy across domains. Phase A5 G1-13 marks abandoned-app retention as P2 with a *live obligation today*. Inferring deletion silently exposes the firm to retention-policy breach. |
| **Correct behavior** | Treat any lifecycle claim without a Compliance-rule-mode utterance + policy reference as P2 open question. Emit `retention.status: unknown_p2` and force a `dependency: policy_doc_attachment` edge. Never copy a retention number from one input into another. |
| **Sources** | A1 §4.3, A5 G1-13/G3-2, B1 HCP-3, B5 T4 |

### AP-1.2 — Inferring priority from label vocabulary

| Field | Detail |
|---|---|
| **Detection signal** | Input includes the literal label `urgent` (e.g., 001:28) and the skill outputs `priority: P1`, or marks the work as MoSCoW Must, without an SLA, deadline, or business-pain quote backing it. |
| **Why dangerous** | A2 §5 item 1 explicitly downgrades the `urgent` label to P3 because nothing in the Jira metadata ties it to an SLA. B2 contradiction C1 demotes it to a metadata assumption, not a lexical ambiguity. The skill that treats label-vocabulary as severity has confused **labels** with **decisions**. Severity must be derived from quantified pain + deadline + stakeholder authority, not single-word tags. |
| **Correct behavior** | Surface label vocabulary as an assumption-to-document (`labels: [urgent]; severity_inference: unanchored`); compute working priority from quantified evidence (call volume, regulator deadline, named sponsor authority). |
| **Sources** | A2 §5 #1, B2 C1, references/ba-best-practices.md §MoSCoW |

### AP-1.3 — Inferring tier from explicit label while ignoring content signals

| Field | Detail |
|---|---|
| **Detection signal** | The skill outputs `tier: T2` because the meeting metadata says "working session" or the raw input was labelled T2 by the originator, while the content stack contains regulator name + dual approval + Compliance directive + tipping-off + Legal absent. |
| **Why dangerous** | A5 §5 explicitly assigns input 003 as "**T1 by content** (manual label T2)" and B5 §4.3 supports T1 escalation. Failing to escalate means LLM temperature stays too high, governance gaps go unflagged, and a regulator-cited initiative ships under T2 rigor. This is a *silent compliance risk*. |
| **Correct behavior** | Run tier inference (A5 §5 rule) over **content signals** before honoring the manual label. When inferred tier exceeds manual label by 1 step, emit `tier.inferred > tier.manual` with firing signals listed and require explicit human override. For multi-epic inputs, emit tier per epic, not per file (B5 conclusion §6 decision 1). |
| **Sources** | A5 §5+R2, B5 §4.3, B3 C4 |

---

## 2. Common Skill Failures (How BA Work Typically Goes Wrong)

These three are the most frequent "this looks like a BA brief but it's silently broken" patterns observed in the corpus.

### AP-2.1 — Silently resolving ambiguity instead of surfacing it

| Field | Detail |
|---|---|
| **Detection signal** | An AC text was reported by the source with an embedded contradiction (e.g., "Old document is replaced (or maybe kept as version? unclear)" 001:54-55) and the skill output picks one branch as the AC without an Open Question entry referring to the original ambiguity. |
| **Why dangerous** | The self-contradiction is the *most actionable* signal in the source. The author flagged uncertainty for the BA precisely because they could not resolve it. A skill that silently chooses replace-vs-version commits a downstream policy decision the source explicitly disowned. B2 HC1 catalogues this as a 4-way-confirmed anti-pattern. |
| **Correct behavior** | When a parenthetical, "unclear", "(?)", or self-questioning aside negates the main clause, split into (a) one Gherkin AC for the most-evidenced reading, (b) an Open Question (P2) referencing both alternatives by quote, (c) suggested resolution owner per the deference graph. Never drop either branch silently. |
| **Sources** | A2 §5 #9, A3 §4.1, A5 I1-4, B2 HC1 |

### AP-2.2 — Burying ambiguity in an "Assumptions" section

| Field | Detail |
|---|---|
| **Detection signal** | The skill emits an Open Questions list with 0-2 P2 items and an Assumptions list containing 5+ entries that each look like "We assume X" / "Assuming Y" where X/Y is a decision a Compliance/Legal/Risk authority would need to make. |
| **Why dangerous** | The reference doc (ba-best-practices §Ambiguity Detection) explicitly says "**P2 = open question (surface), P3 = assumption (document)**". Burying P2 items as assumptions makes them invisible to downstream reviewers (TL, R6) and to compliance review. The ground truth in all three inputs treats stakeholder-blocking unknowns as P1/P2; misclassifying them as assumptions launders ambiguity into shipped requirements. |
| **Correct behavior** | Any item whose resolution requires a named authority decision (Compliance for retention, Legal for customer-facing language, Eng for limits, PM for priority) belongs in Open Questions, not Assumptions. Apply the rule "if the question can be answered by data, it's an assumption-to-document; if it requires a person's authority, it's an open question". |
| **Sources** | references/ba-best-practices.md §Ambiguity Detection, A5 R8, B2 §4 |

### AP-2.3 — Treating anonymous commenter as if named

| Field | Detail |
|---|---|
| **Detection signal** | The skill encodes "N=3" (from 001:103-104 "Anonymous (likely Raj) — N could be 3") as a hard policy parameter in an AC without an `attribution: anonymous` flag and without an Open Question for explicit owner. |
| **Why dangerous** | A1 §3.4 flags "anonymous suggestions accepted as defaults" as a corpus-wide pattern. A4 §3.6 + R5 mandates down-weighting. A5 I1-11 makes it an AuthZ concern (missing identity binding on a policy decision). The risk is real: a retry-limit becomes a policy parameter that no named individual approved, which fails audit reconstruction. B1 HCP-8 promotes this to a 4-way default. |
| **Correct behavior** | Detect anonymous/`(likely X)`/`(group, N min)` attribution. When the utterance carries a numeric or policy default, refuse to encode it as AC; instead emit `proposed_value: 3, attribution: anonymous_guessed_raj, status: requires_named_owner_P2` and link to the deference graph for who should formally own. |
| **Sources** | A1 §3.4+§4.4, A4 §3.6+R5, A5 I1-11, B1 HCP-8 |

---

## 3. Forbidden Simplifications

The skill must resist convenient over-compression. Three patterns dominate.

### AP-3.1 — Collapsing internal SLA disparity into one customer-facing ETA bucket without flagging

| Field | Detail |
|---|---|
| **Detection signal** | A single customer-facing ETA appears in output (e.g., "up to 5 business days") and is not paired with an Open Question surfacing the underlying internal SLAs (e.g., 24-72h compliance vs same-day 95% ops). |
| **Why dangerous** | Input 002 explicitly merges two SLAs into one bucket (002:54-55 vs 002:113-114). B1 HCP-15 and A5 I2-3 both elevate this as a recurring pattern: customer-facing simplicity is bought by hiding internal granularity. The trade-off may be correct, but the *flattening must be visible* to TL review. Silent flattening means downstream eng cannot verify the SLA computation is conservative across both paths, and compliance cannot evaluate the customer-comms risk on the long tail. |
| **Correct behavior** | When ≥2 internal-state SLAs feed one customer-facing bucket, emit `eta_flattening_observed: true` with both internal SLAs listed as evidence, and generate an Open Question per the A1 §5.5 conflict library. Force the trade-off to be a decision recorded by a named authority. |
| **Sources** | A1 §4.1+§5.5, A2 §3.2 #2, A5 I2-3, B1 HCP-15 |

### AP-3.2 — Treating Compliance as Legal

| Field | Detail |
|---|---|
| **Detection signal** | The skill records "Legal sign-off: complete" or omits Legal from required stakeholders because Compliance gave an opinion (e.g., Priya saying "Retention: 7 years"). Or, the skill encodes Compliance-officer policy assertions as final without flagging they lack a policy doc citation. |
| **Why dangerous** | A4 §3.7 declares "Compliance presence ≠ Legal sign-off". B4 T2 confirms 4-way. The corpus shows compliance officers describing the regulation but explicitly deferring legal interpretation ("need legal to bless the language" 002:65; "need to confirm with Legal" 003:115). Treating Compliance = Legal makes the most reliable governance gap — Legal absent in 100% of inputs — invisible. |
| **Correct behavior** | Maintain disjoint Compliance vs Legal stakeholder slots. Compliance-officer assertions in rule mode (MUST NOT, can't, regulated) bind the implementation; they do NOT discharge Legal-engagement requirements for customer-facing language, novel regulator citations, biometric/PII contracts, or retention-policy variances. Emit `legal_status ∈ {present, scheduled, mentioned_only, absent}` independently. |
| **Sources** | A4 §3.7, A1 §3.4+§4.2, A5 R5, B4 T2 |

### AP-3.3 — Squashing a multi-epic initiative into one epic to fit a template

| Field | Detail |
|---|---|
| **Detection signal** | The skill emits one `epic-and-stories.md` file for input 003 (the EDD redesign) where ground truth declares 5-6 epics, OR the skill silently fits 4+ workstreams (intake portal, automated screening, tiered routing, vendor integration, biometric, migration) under one epic header. |
| **Why dangerous** | A3 §3.3 + A5 §5 + B3 §1.8 all converge: 003 is "**multi-epic (5-6 epics)**". Forcing it into one epic violates INVEST `Small` (ref §1) and obscures the per-epic tier inference (B5 §6 decision 1) because biometric/EDD are T1 while mobile-Q4 is T2. The shape of the artifact dictates downstream prioritization, MoSCoW distribution, and dependency editing. |
| **Correct behavior** | Detect scope-kind first (A3 §8 #8 + B3 row 8): count distinct workstreams, presence of phased Q3/Q4 language, vendor-integration cluster, migration references. If ≥3 distinct workstreams each introduce ≥2 ACs (B3 C4 refinement), emit `scope_kind: multi-epic` and produce one epic file per workstream with per-epic tier inference. Never compress under template-fit pressure. |
| **Sources** | A3 §3.3+§8 #8, A5 §5, B3 row 8+C4, B5 §6 decision 1 |

---

## 4. Banking-Grade Violations

Banking-grade is a forcing function (A5 §6, B5 §6 decision 3). These four violations cost the most when they happen.

### AP-4.1 — Marking PII = none without explicit reasoning

| Field | Detail |
|---|---|
| **Detection signal** | The skill emits `pii_fields: []` or `pii.status: not_applicable` for a story involving documents, applicants, customers, IDs, or biometrics, without a justification field naming the workflow class and citing why PII is absent. |
| **Why dangerous** | A5 §6 mandates "Empty rows fail schema validation. Forced-evaluation contract." Inputs 001 and 003 surface NRIC + bank statements + biometric + source-of-funds; none of the inputs *list* the full PII inventory (name, address, photo, applicant-ID). G1-1 marks "PII inventory incomplete" as P2. A skill that silently outputs an empty inventory makes a privacy-policy compatibility check impossible. |
| **Correct behavior** | For any input mentioning identity docs, customers, applicants, or financial records, produce a `pii_inventory` table with one row per field — even if the row says "name: standard customer record, treatment: encrypted at rest, retention: per policy". If truly no PII, emit `pii.status: not_applicable, justification: <workflow class + reason>`. Schema validation rejects empty justification. |
| **Sources** | A5 §6+R6+G1-1, B5 P-04, references §Banking-Grade BA Field Reference |

### AP-4.2 — Producing acceptance criteria without testability check

| Field | Detail |
|---|---|
| **Detection signal** | The skill emits an AC whose `Then` clause contains words like "happy", "satisfied", "fast", "improved", "consistent", "compliant" without a measurable predicate; or `Given` clauses begin with "Given the system" or "Given a user" without specifying state. |
| **Why dangerous** | The reference doc's quality test is "Can a tester write an automated test from this scenario without asking questions?" Input 001 AC #4 says "Compliance is happy" (001:57) — A3 §4.1 + B2 HC5 declare this non-testable. A skill that propagates non-testable ACs violates INVEST `Testable` (ref §1) and ships work that R6 must catch but downstream reviewers may not. |
| **Correct behavior** | Pass every AC through a testability filter: (a) `Given` must reference a concrete state with at least one observable variable; (b) `When` must be a single discrete action; (c) `Then` must reference an observable outcome (state change, response payload, audit event, UI element). Replace soft language ("happy") with measurable predicates ("audit event emitted with required fields", "retention timer set to 7 years"); if no measurable predicate can be derived, emit Open Question rather than the AC. |
| **Sources** | A3 §4.1, B2 HC5, references §Gherkin Acceptance Criteria + §Quality Heuristics |

### AP-4.3 — Skipping idempotency evaluation on customer-notification or state-change operations

| Field | Detail |
|---|---|
| **Detection signal** | A story includes a state transition (review → approved/rejected; uploaded → verified), a notification (email/push/in-app), or a replace operation (document re-upload), and the output has no `idempotency` row, OR the row says `not_applicable` without justification. |
| **Why dangerous** | A5 G2-2 + I2-2 + G1-2 + I3-6 + G3-10 surface notification-idempotency and replay-idempotency gaps across all three inputs. None of the raw inputs *state* the requirement; A3 §6.4 + B3 row 11 + B5 P-10 converge: "idempotency rarely stated, always required". A re-upload double-click that fires two audit events, or a status-change that emails the customer twice, is a banking-grade defect. |
| **Correct behavior** | Default-fill the idempotency row for every story with side effects. Required: `idempotency_key_strategy` (request-id, business-key, hash), Gherkin replay scenario ("Given same request with key X, When replayed, Then no duplicate effect" per ref §Gherkin), and explicit `not_applicable` only for pure-read or pure-compute stages. |
| **Sources** | A3 §6.4, A5 G1-2/G2-2/I2-2/G3-10, B3 row 11, B5 P-10 |

### AP-4.4 — Allowing tipping-off-risky language in customer-facing comms without flag

| Field | Detail |
|---|---|
| **Detection signal** | A customer-facing AC contains terms like "sanctions", "AML", "flagged", "suspicious", "compliance hold", "fraud review", "PEP", or "adverse media", OR the skill encodes "compliance is reviewing your transfer" as customer copy without a `tipping_off_scan` block. |
| **Why dangerous** | B5 P-01 calls tipping-off the "**highest-stakes regulatory pattern**". A5 R3 + E2-3/5/6/11 + E3-9 establish the prohibition as binding. The penalty exposure is regulatory, not business. The skill's failure mode is in *not* emitting something — letting a forbidden term pass through customer copy by default. A2 §5 #4 ("vague-but-helpful") catalogues the regulator-mandated vagueness class. |
| **Correct behavior** | Run a `tipping_off_scan` over every customer-facing AC. Maintain a forbidden-terms list (sanctions, AML, flagged, suspicious activity, PEP, adverse media, regulated comms, hold-for-compliance). On any hit, emit P1 risk + force non-tipping safe phrasing (e.g., "transfer could not be completed; please contact the sender") + require `formal_signoff_pending: legal`. Block TL handoff until Legal sign-off is recorded. |
| **Sources** | A5 R3+R12+E2-3/5/6, B5 P-01, B2 C2 |

---

## 5. Stakeholder Neglect Patterns

These three errors come from listing only what is visible while ignoring what is structurally required.

### AP-5.1 — Listing only named stakeholders, not detecting Legal absence

| Field | Detail |
|---|---|
| **Detection signal** | The skill's Stakeholders block enumerates the present commenters/attendees and omits a `legal_status` field. Or, the skill detects `[Apologies: Legal — Sundar K.]` but treats it as informational metadata rather than as a P1 governance gap. |
| **Why dangerous** | A4 §4.2 quantifies Legal absent in 100% of banking inputs. B4 §3.4 verifies 13/13 missing-stakeholder predictions correct against ground truth. A5 R5 + B5 §6 ("the single highest-leverage rule") elevate Legal-absence + regulatory content to "always-fires" P1 governance gap. A skill that does not auto-emit this check is structurally blind to the most reliable defect. |
| **Correct behavior** | Always emit `legal_status ∈ {present, scheduled, mentioned_only, absent}`. When status is anything but `present` AND scope touches retention / customer-facing language / tipping-off / sanctions / biometric / regulator citation / dual approval, emit P1 governance block. For scope-implied missing roles (Privacy/DPO, Security Reviewer, SAR Liaison, Model Owner, Migration Owner per B4 §3.3), run the same check. |
| **Sources** | A4 §4.2+R10, A5 R5, B1 HCP-1, B4 §3.4, B5 §6 |

### AP-5.2 — Over-weighting Owner who lacks domain authority

| Field | Detail |
|---|---|
| **Detection signal** | The skill writes "approved by Sarah Lim" or "decided by David Lim" on a retention/PII/customer-comms item, treating the Owner/Chair as the deciding authority on a topic that requires Compliance, Legal, Security, or Data sign-off. |
| **Why dangerous** | B4 C1 explicitly refines: "Sarah Lim 'Owner+Approver merged' overstates approver scope. PM is reporter / sponsor, not decider on compliance." B4 C5 flags David's "highest in-room authority" as bounded by Legal absence on regulatory decisions. A4 §6 distinguishes organizational authority (broad) from governance authority (topic-specific). Conflating them lets a PM or Chair "approve" a topic they have no authority over, which fails audit reconstruction. |
| **Correct behavior** | Schema each authority as `{topic_class, named_authority, authority_mode}` with `authority_mode ∈ {rule, proposal, preference, estimate, pain}`. For each AC, attach the *topic-appropriate* approver: compliance topics → Compliance (rule mode); legal language → Legal; engineering feasibility → Eng Lead; priority → Sponsor. Owner is a structural role, not a substitute for SME sign-off. |
| **Sources** | A4 §2.1-§2.2+§3+R2, B4 C1+C5, B1 HCP-5 |

### AP-5.3 — Treating note-taker's paraphrase as authoritative as original speaker

| Field | Detail |
|---|---|
| **Detection signal** | The skill quotes Priya's compliance directive from input 003 (e.g., "30 days for abandoned") as a verbatim quote in an AC, without an `attribution_confidence: paraphrase, mediated_via: Aisha (note-taker)` flag. |
| **Why dangerous** | Input 003 explicitly states "Note-taker filtered some content (paraphrase, not verbatim)" (003:11+18). A4 §2.6 + §5.7 + R9 first-class the note-taker as a meta-stakeholder. B2 §3.2 and B3 §3.1 reinforce. A regulator-citation transmitted via a junior PM's paraphrase is not the same evidentiary weight as a Compliance-officer's verbatim utterance. Treating them equivalently means the audit trail records a higher confidence than the source supports. |
| **Correct behavior** | When the input source is a paraphrasing intermediary (note-taker, summarizer), tag every quoted statement with `attribution_confidence: paraphrase` and `mediated_via: <name>`. For P1/P2 items, emit an action "verbatim verification with <original speaker>" before treating as binding. The bracketed action-item owners (`[Priya]`, `[David]`) carry stronger weight because the format preserves owner+deliverable structure. |
| **Sources** | A4 §2.6+§5.7+R9, B2 §3.2, B3 §3.1, A1 §3.3 |

---

## 6. Ambiguity-Burying Patterns

The skill must surface ambiguity rather than resolve it silently. Three patterns dominate.

### AP-6.1 — Silently picking one stakeholder's answer when commenters disagree

| Field | Detail |
|---|---|
| **Detection signal** | The output records one resolution (e.g., "mobile is in scope") when two commenters made incompatible claims on the same topic (002:107 Jenny "both, web first" vs 002:161 Sarah Khoo "web, then agent, then mobile"). No Open Question references both quotes. |
| **Why dangerous** | A2 §3.3 lists six conflicting-claim cases across the three inputs. A3 §8 #9 mandates: "Maintain a per-entity decision ledger; if two speakers make incompatible claims on the same field, surface a P2. Accept the *latest* claim as the working answer but log the conflict." A skill that picks silently destroys the trail of the disagreement, making it impossible for downstream reviewers to verify the working answer is correct. |
| **Correct behavior** | Detect conflicts via per-entity decision ledger: same field, ≥2 speakers, incompatible content. Emit Open Question (P2) listing both quotes with attribution + timestamps. Accept the latest authoritative quote as working answer (with authority-mode weighting) but never drop the earlier conflicting one. |
| **Sources** | A2 §3.3, A3 §8 #9, B1 HCP-5 |

### AP-6.2 — Resolving modal ambiguity ("should/may") as binding requirement

| Field | Detail |
|---|---|
| **Detection signal** | The skill writes "the system MUST X" or "the workflow shall Y" where the source said "should NOT just be deleted" (001:77) or "we may need to split" (001:108) or "agent UI changes might slip a sprint" (002:155). |
| **Why dangerous** | A2 §5 #25-30 catalogues 6+ modal-ambiguity cases as P2. B2 HC5 promotes modal-hedged commitments to 4-way default. B2 C4 refines: when compliance speakers use "should" in regulatory context, the authority mode is rule (binding); otherwise, modals are non-binding hedges. Treating both alike either under-claims regulator force (when Compliance says "should NOT" = MUST NOT in domain) or over-claims weak commitment (when PM says "may need" = optionality). |
| **Correct behavior** | Tokenize modal verbs (`may, might, could, should, would, probably, maybe, possibly, perhaps, ideally`). Apply authority-mode override: Compliance speaker in regulatory context → rule mode → bind to MUST; PM/Eng with hedge → proposal/preference mode → emit Open Question. Never collapse modal force in either direction silently. |
| **Sources** | A2 §5+§7 #1, A2 §7 R1, A4 §3.3+§5.3, B2 HC5+C4 |

### AP-6.3 — Treating quantifier ambiguity ("many", "most", "a LOT") as quantified

| Field | Detail |
|---|---|
| **Detection signal** | The skill writes "approximately 142 cases/week affected" where the source said "getting a LOT of escalations" (002:21); or "most variable step" (003:54) becomes a definite SLA. |
| **Why dangerous** | A2 §5 #20-24 lists 5 unbound-quantifier cases. A5 §3.3 G-F escalates: "Unquantified banking-grade metric = P2 audit-defensibility gap" because an audit-replay needs the actual numbers. B2 HC6 promotes to 3-way default with the rule that >5 quantifier-without-quantity occurrences in a single input triggers a completeness penalty. |
| **Correct behavior** | Maintain quantifier word-list (`some, several, a few, many, most, lots of, a LOT, multiple, often, sometimes, frequently, rare, typically`). For each unbound occurrence on a banking-grade-relevant metric, emit assumption-to-document. Pair with adjacent numerics when present (e.g., "some up to 22" → quantify "22" but flag "some"). Count occurrences; if >5, emit completeness penalty on the input score. |
| **Sources** | A2 §5 #20-24+R4, A5 §3.3 G-F, B2 HC6 |

---

## 7. Story Granularity Errors

The skill must split by user value, not by tech layer; and at the right level.

### AP-7.1 — Splitting by frontend / backend / DB layer instead of by user value

| Field | Detail |
|---|---|
| **Detection signal** | The output contains stories named "Re-upload UI", "Re-upload API", "Re-upload DB schema" — one per technical layer for a single user behavior. |
| **Why dangerous** | The reference doc (ba-best-practices §Story Splitting) explicitly declares: "**Anti-pattern**: Splitting by technical layers (frontend / backend / DB). Each split must independently deliver user value." Tech-layer splits violate INVEST `Independent` (a UI story has no user value without the API; the API has no value without the UI) and `Valuable`. A skill that produces tech-layer splits has misunderstood the unit of delivery. |
| **Correct behavior** | When a story fails `Small` (>8 SP), split using the reference patterns: Workflow steps (submit/verify/approve), business-rule variations, happy vs error paths, data variations, CRUD operations, roles, optimize-later, or spike. Never split by tech layer. If splitting feels forced, flag for TL rather than fitting INVEST. |
| **Sources** | references/ba-best-practices.md §Story Splitting Patterns, A3 §8 #8 |

### AP-7.2 — Merging happy path + error path into one story / scenario

| Field | Detail |
|---|---|
| **Detection signal** | A single Gherkin scenario contains both `Then user sees success` and `Then user sees error if X` chained with `And`; or a single story contains the happy re-upload path AND the failed-verification-loop AND the escalate-to-support path. |
| **Why dangerous** | The reference doc (§Gherkin Acceptance Criteria) declares: "One scenario per behavior — don't combine happy + error in one scenario". Input 001 surfaces three distinct paths (re-upload, retry-limit, escalation per A3 §2.1). Merging them produces 7+ ACs for one story, which violates the AC density quality heuristic (>7 = split). |
| **Correct behavior** | For each user-facing behavior, produce one happy-path Gherkin scenario and one error/edge-case scenario as mandatory minimum (ref §Gherkin). Distinct error paths (timeout, validation failure, retry exhausted) become separate scenarios; if scenario count for one story exceeds 7, split the story along the happy-vs-error or business-rule-variation axis. |
| **Sources** | references/ba-best-practices.md §Gherkin + §Quality Heuristics, A3 §2.1, B3 row 6 |

### AP-7.3 — Not splitting when AC count exceeds 7

| Field | Detail |
|---|---|
| **Detection signal** | A story has 8+ Gherkin scenarios listed; or the story description includes 10+ bullet points each implying a distinct AC. |
| **Why dangerous** | The reference doc's quality heuristic: "AC density: 2-5 Gherkin scenarios per story (1 is too few; >7 = split)". B3 row 6 + A3 §2.1 confirm stakeholder-concern boundaries usually map 1:1 with stories — when one story covers Compliance + Eng + UX + Ops concerns, it's accumulating four stakeholders' AC sets. The result: a "story" too big for INVEST `Small`. |
| **Correct behavior** | When a story candidate has >7 scenarios or >5 distinct stakeholder concerns, emit a `split_recommendation` with proposed split axis (workflow step / business rule / role / data variation). The skill can split itself only on clear axes; for ambiguous splits, surface to TL via `split_pending_decision`. |
| **Sources** | references/ba-best-practices.md §Quality Heuristics, A3 §2.1+§8 #8, B3 row 6 |

---

## 8. AC Quality Failures

These three errors are the most common acceptance-criteria defects in the corpus.

### AP-8.1 — Vague `Given` clauses ("Given the system", "Given a user")

| Field | Detail |
|---|---|
| **Detection signal** | A Gherkin scenario begins with `Given the system`, `Given a user`, `Given the application`, or any precondition that does not specify which state, which actor identity, or which input data. |
| **Why dangerous** | The reference doc (§Gherkin Acceptance Criteria) declares: "Given = state/preconditions ONLY (no actions); concrete values > abstract". An automated test cannot set up a precondition that says "Given the system" — the test author must guess. Such ACs propagate ambiguity into test design. |
| **Correct behavior** | Each `Given` clause must reference (a) a concrete actor with role (applicant, compliance officer, support agent), (b) a concrete state (application status = "verification failed", wire status = "additional review"), and (c) concrete input data where relevant (NRIC re-upload, amount = 50000, retry attempt = 2). Soft preconditions trigger rewrite or Open Question. |
| **Sources** | references/ba-best-practices.md §Gherkin, A3 §4.1, B2 HC5 |

### AP-8.2 — Multiple actions in one `When`

| Field | Detail |
|---|---|
| **Detection signal** | A `When` clause uses `and` to chain actions: "When the user clicks submit and the system validates and the notification fires". |
| **Why dangerous** | The reference doc declares: "When = ONE trigger action per scenario (split if multiple)". Chaining actions hides which step failed when the scenario fails, breaks idempotency-replay tests (you can replay one action; you can't replay three), and obscures the cause-effect chain. |
| **Correct behavior** | Each `When` clause expresses exactly one trigger action. If two actions are co-occurring, split into two scenarios with different `Given` setups: one where action A occurs first, one where action B occurs first. Use `And` only to chain additional `Given` (precondition) or `Then` (outcome) clauses, never additional `When` actions. |
| **Sources** | references/ba-best-practices.md §Gherkin, A3 §4.1 |

### AP-8.3 — `Then` clauses without observable outcome

| Field | Detail |
|---|---|
| **Detection signal** | A `Then` clause says "Then the user is happy", "Then the system handles it correctly", "Then compliance is satisfied", or any subjective predicate without a measurable state change, response, log event, or UI element. |
| **Why dangerous** | The reference doc declares: "Then = observable outcome (state change, response, side effect)". Input 001 AC #4 ("Compliance is happy") is the canonical example. B2 HC5 + A3 §4.1 confirm. Such ACs fail INVEST `Testable` and the quality test "Can a tester write an automated test from this scenario without asking questions?" |
| **Correct behavior** | Each `Then` clause references one of: (a) UI element observable change, (b) database state change with concrete field/value, (c) outbound message (email/push/audit) with required payload fields, (d) downstream event emission with schema. Subjective predicates trigger rewrite or, when no measurable predicate exists, generate an Open Question and pull the scenario from binding ACs. |
| **Sources** | references/ba-best-practices.md §Gherkin, A3 §4.1, B2 HC5 |

### AP-8.4 — Missing banking-grade scenarios on stateful or notification operations

| Field | Detail |
|---|---|
| **Detection signal** | A story involves persistent state change (document replace, wire status update, EDD case escalation) or outbound notification (email/push/in-app on status change), and the AC set does NOT include an idempotency-replay scenario AND an audit-emission scenario. |
| **Why dangerous** | The reference doc (§Gherkin) declares: "If banking-grade applies: Idempotency replay AND Audit emission scenarios are mandatory". A5 §6 forced-evaluation contract: empty banking rows = schema failure. Inputs 001/002/003 surface state transitions and notifications across all three domains; none of the raw inputs explicitly write either scenario. Skipping them means the most common banking-grade defects never reach AC. |
| **Correct behavior** | For every state-change or notification story, auto-emit two banking-grade scenarios per the reference template: (a) Idempotency replay: "Given same request with key X, When replayed, Then no duplicate effect AND no duplicate audit event"; (b) Audit emission: "When state changes, Then audit event emitted with required fields {event, actor, ts, before, after, reason, idem_key}". For tipping-off-relevant comms, add a third: "When customer is notified of rejection, Then message does NOT contain {sanctions, AML, flagged, suspicious}". |
| **Sources** | references/ba-best-practices.md §Gherkin + §Banking-Grade BA Field Reference, A5 R1+R3+R7+§6, B5 P-05+P-10+P-01 |

---

## 9. Cross-Cutting Enforcement Notes

A small number of meta-rules govern how these anti-patterns interact in skill implementation.

1. **Anti-patterns compose**: a single source phrase can fire multiple anti-pattern guards. E.g., "we may need to split" by an anonymous commenter on a compliance topic fires AP-2.3 (anonymous), AP-6.2 (modal), and AP-5.1 (Legal-absence if compliance scope). The skill must not deduplicate — each fires independently (B5 §6 decision 2).
2. **Severity escalation by context**: P3 detectors escalate to P2 when topic is regulatory; P2 escalates to P1 when authority-mode is rule (B2 C4). The skill's severity computation must respect both axis (detector severity × topic class × authority mode).
3. **Block-on-handoff guards**: AP-1.3 (mis-tier), AP-4.1 (missing PII inventory), AP-4.4 (tipping-off-risky language), AP-5.1 (Legal absent on regulatory), and AP-8.4 (missing banking-grade scenarios) are *handoff blockers* — they must prevent TL handoff even if other quality scores are high.
4. **Pair-with-positive-test**: each anti-pattern guard should have at least one corresponding positive pattern that explicitly disables the alarm (e.g., AP-4.1 disabled by an explicit `pii.status: not_applicable, justification: <reason>` row). Without a disable-path, guards become noise.
5. **Surface, don't repair**: when an anti-pattern fires, the skill surfaces it as Open Question + risk flag rather than silently rewriting the input. Repair is the BA's job downstream; the skill's job is detection + structural enforcement.

---

## 10. Index of Anti-Patterns (Quick Reference)

| # | Anti-pattern | Bucket | Severity if fired |
|---|---|---|---|
| AP-1.1 | Inferring lifecycle policy from process labels | Wrong Inferences | P2 (P1 in T1) |
| AP-1.2 | Inferring priority from label vocabulary | Wrong Inferences | P3 |
| AP-1.3 | Inferring tier from label, ignoring content | Wrong Inferences | **Handoff block** |
| AP-2.1 | Silently resolving ambiguity instead of surfacing | Common Skill Failures | P2 |
| AP-2.2 | Burying ambiguity in Assumptions | Common Skill Failures | P2 |
| AP-2.3 | Treating anonymous commenter as named | Common Skill Failures | P2 |
| AP-3.1 | Collapsing internal SLAs into one customer-facing ETA | Forbidden Simplifications | P2 |
| AP-3.2 | Treating Compliance as Legal | Forbidden Simplifications | **P1 if regulatory** |
| AP-3.3 | Squashing multi-epic into one epic | Forbidden Simplifications | P2 (structural) |
| AP-4.1 | PII = none without explicit reasoning | Banking-Grade Violations | **Handoff block (T1/T2)** |
| AP-4.2 | AC without testability check | Banking-Grade Violations | P2 |
| AP-4.3 | Skipping idempotency on state-change ops | Banking-Grade Violations | P1 (T1/T2) |
| AP-4.4 | Tipping-off-risky language unflagged | Banking-Grade Violations | **P1 + handoff block** |
| AP-5.1 | Missing Legal-absence detection | Stakeholder Neglect | **P1 + handoff block** |
| AP-5.2 | Over-weighting Owner who lacks domain authority | Stakeholder Neglect | P2 |
| AP-5.3 | Note-taker paraphrase as authoritative | Stakeholder Neglect | P2 |
| AP-6.1 | Silently picking one stakeholder when commenters disagree | Ambiguity-Burying | P2 |
| AP-6.2 | Modal ambiguity resolved as binding | Ambiguity-Burying | P2 (P1 if compliance rule) |
| AP-6.3 | Quantifier ambiguity treated as quantified | Ambiguity-Burying | P3 (cluster → P2) |
| AP-7.1 | Splitting by tech layer | Story Granularity | P2 (re-split) |
| AP-7.2 | Merging happy + error in one scenario | Story Granularity | P2 (re-split) |
| AP-7.3 | Not splitting at AC count > 7 | Story Granularity | P2 (re-split) |
| AP-8.1 | Vague Given clauses | AC Quality | P2 (rewrite) |
| AP-8.2 | Multiple actions in one When | AC Quality | P2 (rewrite) |
| AP-8.3 | Then without observable outcome | AC Quality | P2 (rewrite) |
| AP-8.4 | Missing banking-grade scenarios on stateful ops | AC Quality | **Handoff block (T1/T2)** |

Total: **26 anti-patterns** across 8 buckets (target ≥15, stretch 18-22 exceeded — driven by the AC Quality bucket needing four entries to cover Given/When/Then/banking-grade scenarios coherently, and Wrong Inferences/Common Failures/Forbidden Simplifications each requiring three entries to hit the corpus's actual failure modes).

---

## 11. Summary

The catalog encodes 26 enforceable guards: 5 are handoff blockers (AP-1.3, AP-4.1, AP-4.4, AP-5.1, AP-8.4), 9 are P1/P2 when regulatory context fires, and 12 are P2/P3 quality assertions. The single highest-leverage guard, triangulated across all five phase pairs, is **AP-5.1 (Legal-absence on regulatory scope = P1)** — Legal is absent in 100% of corpus inputs and is the canonical always-fires detector. The bucket with the largest aggregate risk is **Banking-Grade Violations** (AP-4.1 through AP-4.4) because three of its four entries are handoff blockers or P1 regulatory issues.

The skill must treat anti-pattern detection as a *forcing function*, not pattern-matching: empty fields fail schema validation; missing justification fails the disable-path; conflicting claims are recorded with both quotes; modal/quantifier/anonymous markers are surfaced as Open Questions; banking-grade scenarios are auto-generated for stateful operations. The principle across all 26 entries: **surface, don't repair** — the skill's value is making invisible defects visible to downstream review, not silently fixing them.

---

*End of Phase C2 Anti-Pattern Catalog.*
