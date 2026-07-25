# Phase C1 — Recurring Pattern Distillation

> **Role**: Recurring Pattern Distiller, BA Skill Factory
> **Mission**: Extract patterns triangulated by ≥2 analyses across Phase A (deep extractions A1-A5) and Phase B (cross-validations B1-B5). These will become the **DEFAULT BEHAVIORS** of the `ba-elicit-from-raw` atomic skill.
> **Method**: For each pattern, capture name, trigger conditions, action, confidence (high ≥3 analyses, medium = 2 analyses), and source analyses (A/B IDs).
> **Inputs**: phase-a1..a5, phase-b1..b5 (10 documents).

---

## 0. Confidence Legend

| Tag | Meaning |
|---|---|
| **HIGH** | Triangulated by ≥3 analyses (A or B). These are non-negotiable defaults. |
| MED | Triangulated by exactly 2 analyses. Strong defaults, but call out adjacent considerations. |
| (Cross-cat) | Pattern appears in multiple categories — captured once in the most-fitting category. |

Patterns are numbered `C{n}` for cross-reference. Total: **30 patterns** across 8 categories.

---

## 1. Input Parsing Patterns

How the skill extracts information from each source type — before any semantic interpretation.

### C1. Detect source type before parsing (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Any raw input arrives. |
| **Action** | Classify into `{jira, slack, meeting-notes, doc-fallback}` using deterministic header markers BEFORE any other pass. Markers — Jira: bracketed key `[A-Z]+-\d+` in title; key:value header (`Project:`, `Type:`, `Priority:`, `Reporter:`); ASCII rules `────`; sections `## Description / Acceptance Criteria / Comments / Linked Issues`. Slack: `#channel — Slack channel` banner; `Name (Role) — Today HH:MM`; emoji reactions; `📎 Linked:`; chat register. Meeting notes: `========` banner; metadata block (`Meeting:`, `Date:`, `Time:`, `Note-taker:`, `Attendees:`, `[Apologies: …]`); numbered agenda `## 1. … ## 8.`; time-boxed `(Speaker, N min)`; bracketed `[Owner] task — due`. Fallback to `doc` parser if no marker matches; emit `ba_confidence: low`. |
| **Confidence** | HIGH (A2 reports 0.96-0.98 confidence per type) |
| **Sources** | A1 §3.3, A2 §1, A3 §1+§7, A5 §5, B1 row 1, B2 rows 1-3, B3 §5 |

### C2. Route to source-specific parser (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | After C1 source-type classifier emits a label. |
| **Action** | Dispatch parser branches: **Jira** → parse key:value header; treat `## Description` as problem+trigger; treat declared `## Acceptance Criteria` as DRAFT (low testability — see C25); read `## Comments` chronologically with role tagging; parse `## Linked Issues` as typed dependency edges. **Slack** → first message = trigger; mid-thread enumeration (`ok let me draft. so the asks are roughly: 1…`) = story spine; final exchange = ownership handoff; preserve emoji as decision acts; resolve pronouns within ≤5-message window. **Meeting notes** → parse attendees+apologies; numbered agenda sections = candidate epics; `### 3X.` sub-sections = candidate stories; `## Action Items` → `[Owner] task — due` extraction; `## Parking Lot` → deferred items; tag all statements `attribution_confidence: paraphrase`. **Fallback doc** → stakeholder-concern heuristic only; require human checkpoint. |
| **Confidence** | HIGH |
| **Sources** | A2 §1+§7, A3 §7+§8 R1, A4 §1+§5, B2 §5, B3 §5 |

### C3. Strip ground-truth annotation block before parsing (HIGH — unique safety rule)

| Field | Detail |
|---|---|
| **Trigger** | Raw input contains the literal heading `## Intentional Issues for R6 to Catch` (or any close variant `### Intentional Issues`, `Hidden from BA Workflow`). |
| **Action** | **Hard preprocessing rule**: detect the heading, strip everything from that line to end-of-file. This is training-set ground truth, not user input. Production inputs will not contain it; if it appears in production, refuse to consume it. Optionally retain for `audit/` mode only (skill self-evaluation), never for the main BA brief. Absence of this guard causes silent contamination of the output. |
| **Confidence** | HIGH (A3 unique; B3 elevates to "hard preprocessing rule"; appears in all 3 training inputs at predictable line ranges) |
| **Sources** | A3 §1.13+§8 R2, B3 row 12+C5 |

### C4. Resolve relative dates against the input's metadata date (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Any time expression appears that is not absolute ISO-8601 — `EOW`, `today`, `tomorrow`, `next sprint`, `next session`, `Q3`, `Q4`, `by next week`, `in 3 weeks ideally`, `next available`. |
| **Action** | Normalize against input's Created/Date metadata (Jira `Created`, meeting `Date`, Slack `Today HH:MM` anchored to thread start date). Compute absolute ISO-8601. When ambiguous (e.g., EOW mid-week could be this Friday or next), **emit an open question instead of guessing**. Note-taker self-flag `[unconfirmed if EOW = this or next week]` (003:43) is the canonical "do not silently resolve" cue. |
| **Confidence** | HIGH |
| **Sources** | A1 §3.2, A2 §7 R2, A3 §5.2+§8 R14, A5 I3-14, B1 row 8, B2 rows 9+HC9 |

---

## 2. Domain Interpretation Patterns

How the skill interprets recurring domain terms once parsed.

### C5. Construct a structured Domain Glossary alongside the brief (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Every input — always. |
| **Action** | Emit a `glossary` object alongside the brief with one entry per domain term encountered. Each entry carries: `canonical_form` (e.g., `enhanced_due_diligence`), `surface_form` as quoted (e.g., `EDD`, `Enhanced Due Diligence`), `inferred_definition` with confidence, `pii_sensitivity` flag, `regulatory_tie` (regulator name + citation if any). Seed with the 32-term catalog from A1 §1. Without this, every downstream reviewer (TL, R6, risk reviewer) re-parses the dialect from scratch. |
| **Confidence** | HIGH |
| **Sources** | A1 §1+§5.1+§8 (glossary table), B1 §5 HCP-4, A4 §2 (domain references), A5 §4 (patterns) |

### C6. Recognize regulator citation patterns and resolve vs unresolved (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Regex `[A-Z]+-[A-Z]+-[A-Z0-9-]+` matches (e.g., `MAS-AML-1A`); or named regulators `MAS, OFAC, FATF, FinCEN, PDPA, GDPR, PCI` appear in prose. |
| **Action** | Extract the citation candidate; classify as `resolved` (citation document attached/linked) or `unresolved` (named but no document). For unresolved on T1/T2 inputs, **automatically emit P1 open question** with `dependency: regulatory_citation` and identify a citation_fetcher action item (e.g., 003:43 "David — share regulator citation by EOW"). Block TL handoff until resolved on T1. |
| **Confidence** | HIGH |
| **Sources** | A1 §3.1+§5.2, A2 §5 #13, A3 §5.4, A5 R4+E3-1+P-02, B1 HCP-4, B2 HC4, B4 HCP-15, B5 T6+P-02 |

### C7. Auto-classify PII terms by direct/indirect/regulatory sensitivity (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Any of these terms appear: **Direct identifiers** — `NRIC, passport, national ID, biometric, liveness, face match, fingerprint`; **Indirect identifiers in workflow context** — `source of funds, PEP classification, adverse media results, sanctions match, DOB, account number, applicant ID`; **Regulatory-confidential events** — `SAR filing, sanctions hold, tipping-off communications, suspicious activity`; **Financial PII** — `bank statement, transaction data, wire transfer`. |
| **Action** | Auto-tag each match into `pii_inventory` with fields `{category, term, retention_rule, residency_rule, masking_rule, access_audit}`. **T1**: refuse to proceed without full enumeration (name/address/photo/applicant-ID added even when not explicitly mentioned). **T2**: enumerate named PII + flag inferred gaps as P2. **T3**: allow "prototype, no real data" justification. Drive a downstream handling-requirements section. |
| **Confidence** | HIGH |
| **Sources** | A1 §1.1+§5.3, A2 §3.1 #2, A3 §6.1+§8 R6, A4 Priya rows, A5 E1-4+E1-13+I1-8/9+I3-3+P-04, B1 HCP-4, B5 T3+P-04 |

---

## 3. Structure Mapping Patterns

How raw inputs map to the epic/story output shape.

### C8. Classify scope kind — single-story / multi-story / single-epic / multi-epic (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | After C1+C2, before story emission. |
| **Action** | Emit a top-level `scope_kind: {single-story, multi-story, single-epic, multi-epic}` using these signals: (a) number of distinct workflows touched (>3 → suspect multi-epic); (b) presence of `phase 1 / phase 2`, `Q3 / Q4` language; (c) vendor-integration cluster as self-contained block (its own epic); (d) migration / legacy-data references = separate workstream; (e) Type-field self-questioning (`Story (but might need to be Epic — too big?)` — 001:23) = epic-promotion signal; (f) explicit author hint ("we may need to split into multiple stories" — 001:108). Refined rule per B3 C4: multi-epic ONLY when ≥3 distinct workstreams each introduce ≥2 ACs. r1 → single-epic; r2 → single-epic; r3 → multi-epic (5-6 epics). |
| **Confidence** | HIGH |
| **Sources** | A1 §0, A2 §6.3, A3 §3+§8 R8, A5 §5, B1 G4, B2 C3, B3 §1 row 8+§4+§5, B5 C2 |

### C9. Detect story boundaries by stakeholder concern + enumerated lists (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | After C8 emits `scope_kind`. |
| **Action** | Each named compliance/risk/security/UX/eng participant who introduces ≥1 distinct AC = candidate story (filter per B3 C3: stakeholder-as-boundary AND topic-introduces-≥1-AC). Additionally: enumerated `1. 2. 3. 4.` lists in chat summaries (e.g., Tom's r2:84-92 enumeration) = spine of story inventory. Each `### 3X.` sub-section in meeting notes = at least one story. Each `Blocks:` / `Relates to:` link is a dependency edge, not a story. Stakeholders that introduce **no AC** (Marketing as deadline-setter, BA team as consumer) are NOT stories. |
| **Confidence** | HIGH |
| **Sources** | A1 §2.3, A3 §2+§8 R7, A4 §1, B1 row 11, B3 §1 rows 6-7+C3, B4 T4 |

### C10. Detect epic boundaries by workstream and self-questioning (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | When scope shows multiple workstreams. |
| **Action** | Promote a candidate cluster to **epic** when any of: (a) `### 3X.` sub-section bundles vendor + migration + security spike; (b) Type-field carries self-questioning ("Story but might need to be Epic"); (c) ≥4 workstreams or ≥6 P2 open questions; (d) cross-team dependency cluster (mobile + legal + vendor present together); (e) vendor-integration cluster is self-contained. r3 promotes 3a (doc portal + Acuant) and 3d (tiered approval) to epic-shaped. |
| **Confidence** | HIGH |
| **Sources** | A2 §7 R12, A3 §3+§8 R8, A5 R9, B1 G4, B3 §1 row 15, B5 C2 |

### C11. Extract out-of-scope and deferred items into Parking Lot section (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | (a) Explicit `## Parking Lot` section. (b) Phrases `separate ticket`, `out of scope`, `different concern`, `Q4 follow-on`, `phase 2`, `defer to migration plan`, `next sprint not this one`, `web first / mobile follow-on`. (c) Compliance scope-cuts ("Abandoned applications — separate ticket, that's a different concern" — 001:86). (d) Chair scope-cuts ("Skipped, out of scope for this phase per David" — 003:117). |
| **Action** | Always emit `out_of_scope_deferred` section in the brief. For each deferred item record `{topic, deferral_reason, owner_for_future, banking_grade_obligation_today?}`. If deferred item carries a LIVE banking-grade obligation (retention rule applies today, SAR workflow undefined, tipping-off rule applies on every channel), flag `deferred_compliance_risk: P2` with explicit risk-acceptance owner (per C18). |
| **Confidence** | HIGH |
| **Sources** | A1 §4.1+§5.5, A3 §1.10+§8 R15, A5 R10+P-17, B1 G13, B3 §1 row 18+§5, B5 T18+P-17 |

---

## 4. Stakeholder Extraction Patterns

### C12. Distinguish Owner / Sponsor / Approver / SME / Affected / External / Meta (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Every input. |
| **Action** | Never collapse stakeholders into one list. Emit schema per person: `{name, role_title, function, type ∈ {owner, sponsor, approver, sme, affected, external, meta}, authority_mode, evidence, attribution_confidence}`. Owner = drafts/opens (Jira reporter, Slack thread starter, meeting chair). Sponsor = grants priority/budget ("yes go ahead. priority is high" — 002:148). Approver = signs off per change-class (Compliance for retention; Legal for customer language). Note that 001 merges Owner+partial-Approver (Sarah Lim is Owner; Priya is de-facto Approver on compliance subset per B4 C1); 002 separates Owner (Tom drafts) from Sponsor (Sarah Khoo); 003 has chair-style merged Owner+Approver (David, bounded by Legal absence per B4 C5). |
| **Confidence** | HIGH |
| **Sources** | A1 §1.3+§2.3, A2 §3.1+§4, A4 §1+§2.1-§2.2+R1, A5 §5 stakeholder rules, B1 row 10, B4 T4+HCP-6 |

### C13. Identify SMEs by domain (compliance / engineering / risk / UX / ops / vendor) (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | A speaker with a recognizable role title or speech-pattern signature. |
| **Action** | Classify SMEs into a fixed set: **Compliance** (Priya, Mei — keywords: tipping off, retention, sanctions, MUST NOT, regulated, MAS, AML, PEP, SAR, EDD). **Engineering** (Raj P., Tom B., Karim — keywords: rate limit, schema change, P95 latency, file size, idempotency, throughput, spike, integration estimate). **Risk/Data** (Jamie — keywords: model, calibration, structured fields, score). **UX/CX** (Ben — keywords: NPS, status page, wireframes). **Ops/Frontline** (Mike, Jenny — keywords: cases/week, ↑40%, hours per agent, escalations). **Vendor liaison** (Hua — speaks for the vendor entity but distinct from it — see C19). Each utterance is then weighted by SME role on its topic axis. |
| **Confidence** | HIGH |
| **Sources** | A1 §2.3, A2 §1+§4, A4 §2.3+§5+§6, A5 §1+§4, B4 T5+T6+T7+T13+T16 |

### C14. Detect missing stakeholders — especially Legal on regulatory content (HIGH — strongest convergence)

| Field | Detail |
|---|---|
| **Trigger** | Always run on every input. Check explicit attendees, commenters, @mentions, and `[Apologies: …]` list. |
| **Action** | Maintain required-role checklist per scope (per A4 R3 + B5 G-3.3): **Legal** if scope touches customer-facing language, retention, regulator citation, tipping-off, sanctions, biometric. **Security** if PII, biometric, file upload, vendor integration. **Privacy/DPO** if PII inventory non-empty (added per B4 §3.3 + B5 G-3.3 — third absent role behind Legal and Security). **Customer Support** if internal tooling redesign or customer comms. **Mobile owner** if cross-platform mention. **Data/Analytics** if declared metrics (CSAT, NPS, call volume). **Senior management approver** if tiered/dual approval. **Migration workstream owner** if cutover. **SAR liaison** if any SAR mention. **Model Owner** distinct from Risk SME if score-threshold drives routing. **Security Reviewer** distinct from Eng if biometric spike. For each missing required role, emit gap with severity: **P1** for Legal-absent on regulatory scope (canonical — fires in 100% of 3 banking inputs). |
| **Confidence** | HIGH (most-corroborated finding across all 10 analyses) |
| **Sources** | A1 §3.4+§6, A2 §7 R8, A3 §1.1+§8 R9, A4 §4+R3+R10+§8, A5 R5+P-14, B1 row 5+HCP-1, B2 row 13+HC12, B3 row 2, B4 T1+T2+§3.3+HCP-2+HCP-12, B5 T7+P-14 ("single highest-leverage rule") |

### C15. Weight authority by speech act and authority mode (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Each utterance/statement. |
| **Action** | Stamp each utterance with `authority_mode ∈ {rule, proposal, preference, estimate, pain}`. **Rule mode** (compliance MUST NOT / can't / regulated / uppercase modals; explicit prohibition or directive) → binding, fixed AC. **Proposal mode** (compliance "I suggest 0.75 threshold") → negotiable, AC + open question for affected SME. **Preference** (PM "probably yes", "let's") → soft assumption. **Estimate** (eng "2-3 weeks") → range to validate. **Pain** (ops "142 cases / 4 hours / ↑40%") → problem-framing evidence. Cross-role override rule: data/eng can override compliance proposal mode on data-feasibility grounds (Jamie overrides Priya 0.75); compliance rule mode overrides eng/PM preference on customer comms (Mei overrides Tom on 5-day bucket). |
| **Confidence** | HIGH |
| **Sources** | A1 §3.4, A2 §4, A4 §3+§5+§6+R2, A5 §4, B1 row 5+HCP-5, B2 C4, B4 HCP-1+T3+T13, B5 P-03 |

### C16. Down-weight anonymous and paraphrased/mediated content (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | (a) Comment author = `Anonymous` or `Anonymous (likely X)` (e.g., 001:103 "Anonymous (likely Raj) — N could be 3"). (b) Group-labels `(group, 20 min)`. (c) Note-taker explicit declaration ("paraphrase, not verbatim" — 003:11). (d) First-person editorial asides (`Aisha (me!)`). |
| **Action** | Down-weight: tag `attribution_confidence ∈ {high, paraphrase, anonymous, group}`. Anonymous + numeric policy parameter (N=3, retention days, score threshold) = automatic P2 (promoted from P3 per B2 C1 and B5 C1). Mediated-by-note-taker → all statements default `attribution_confidence: paraphrase`; P1/P2 items require verbatim follow-up before AC binding. Refuse to treat anonymous statements as policy decisions. |
| **Confidence** | HIGH |
| **Sources** | A1 §3.4+§4.4, A2 §3.1+§7 R5, A3 §7.1+§7.3+§8 R11, A4 §3.6+§5.7+R5+R9, A5 I1-11, B1 row 7+HCP-8, B2 HC2, B4 T7+T8+HCP-4+HCP-5, B5 G-B+G-C+C1+P-16 |

### C17. Detect mentioned-but-not-engaged stakeholders (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Same name appears as `count_mentions(person) ≥ 2 AND count_utterances(person) == 0`. Canonical case: Legal mentioned 3× in 002, 0 utterances. |
| **Action** | Distinct from "absent" — these stakeholders are referenced by participants but never speak. Tag `engaged: false, mentioned: N` per person; severity scales with N and topic regulatory weight. For Legal: any mention-not-engaged on regulatory content = P1 (consistent with C14). Use deference graph (per A4 R8 + B4 HCP-3) to identify answer-owners: `@X`, "Y would know better", "need X to confirm" → Y is answer-owner; if Y absent → escalate. |
| **Confidence** | HIGH |
| **Sources** | A4 R4+R8+§3.2, A5 R5, B4 HCP-3+HCP-13, B1 row 5 |

---

## 5. Banking-Grade Detection Patterns

### C18. Force evaluation of 7 banking-grade fields per story (HIGH — central forcing function)

| Field | Detail |
|---|---|
| **Trigger** | Every story emitted. |
| **Action** | For every story, force-emit a `banking_grade_concerns` block. Empty rows = schema-validation failure. The 7 mandatory fields: **(1) pii_fields** `{status: applies\|not_applicable\|unknown_p2, fields: [...], justification}`; **(2) audit** `{status: standard\|enhanced\|none_pure_read, events: [event/actor/ts/before/after/reason/idem_key]}`; **(3) idempotency** `{status: required\|not_applicable_pure_function, key_strategy}`; **(4) reversibility** `{status: reversible\|soft_reversible\|irreversible_human_queue, compensating_action}`; **(5) authn_authz** `{actors, role_matrix}`; **(6) regulatory** `{citations}` (at least one for T1); **(7) tipping_off** `{risk_level: none\|low\|medium\|high, mitigation}`. **This is the forcing function** — pattern matching alone is insufficient. T1 refuses to proceed without all fields. T2 baseline = default-fill with `unknown_p2` if silent. T3 allows skip with justification. |
| **Confidence** | HIGH |
| **Sources** | A5 §6+R1, B1 G1, B3 §4+§5, B5 §4.1+P-04 through P-11 |

### C19. Infer Tier (T1/T2/T3) per epic, not per file (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Before story extraction. |
| **Action** | Run tier inference per emitted epic (per B5 C2 — multi-epic 003 may have heterogeneous tiers). Rule (compact, from A5 §5): `IF (regulator_named AND citation_provided) → T1`; `ELIF (compliance_officer_present AND (sanctions|aml|kyc|edd|sar|pep|tipping_off)) → T1 candidate, confirm`; `ELIF (compliance_officer_present AND PII_high_grade) → T2 with T1-shadow on retention+PII`; `ELIF (customer_facing AND PII_any) → T2`; `ELIF (no_regulator AND no_compliance_officer AND prototype_language) → T3`; `ELSE → T2 default + P2 "tier ambiguous"`. Override rules: ≥3 T1 indicators OR (regulator-cited + compliance-officer-directive) = auto-T1. Emit `inferred_tier` with firing signals for audit traceability. r1 = T2 (T1-shadow on retention+PII); r2 = T2 borderline T1 (recommend escalate — sanctions+SAR+tipping-off); r3 = T1 by content (per epic: EDD+biometric T1; mobile follow-on T2). |
| **Confidence** | HIGH |
| **Sources** | A5 §5+R2, B1 G2, B3 §1 row 8, B4 C5, B5 C2+§4.3 |

### C20. Detect tipping-off risk on every customer-facing communication change (HIGH — highest-stakes pattern)

| Field | Detail |
|---|---|
| **Trigger** | Any AC, decision, or story touches email/push/SMS/status/error message/agent script/rejection text/customer notification. Keywords: `tipping off`, `tipping-off`, `regulated comms`, `MUST NOT`, `can't tell the customer`, `generic message`, `vague but helpful`, `non-tipping`, `standard line`, plus implicit when speaker = Compliance + customer-facing comm change. |
| **Action** | Run `tipping_off_scan`; emit risk level `{none, low, medium, high}` and mitigation. Convert prose constraints into testable AC: `Given a wire is rejected for sanctions reason, When the customer is notified, Then the message uses the standard non-tipping phrase and does NOT contain 'sanctions', 'AML', 'flagged', 'suspicious', or specific compliance terminology`. Treat any AML-related rejection (PEP, AM, fraud, SAR) as tipping-off-class (per B5 G-E — A5 originally only handled sanctions). Block TL handoff until Legal sign-off captured. Ship a non-tipping vocabulary reference (`references/non-tipping-vocabulary.md`) with approved phrases ("the transfer could not be completed. please contact the sender."), forbidden terms ("sanctions hold", "AML review", "flagged"), and detection patterns. |
| **Confidence** | HIGH |
| **Sources** | A1 §4.3, A2 §5 #12, A4 §3.3, A5 E2-3/5/6+E3-9+R3+R12+P-01, B1 HCP-2, B2 HC3, B4 T3+HCP-1, B5 T1+T17+G-E+P-01 |

### C21. Require compensating action / human-queue policy for irreversible operations (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Any external write — funds movement, document replacement, retention deletion, screening re-run, notification dispatch, vendor call. Keywords: `undo, revert, abandon, rollback, delete, archive, return funds, replace, in-flight when we cut over`. |
| **Action** | For every mutation/state transition/replace/notification, force a `reversibility` decision: `{reversible, soft_reversible, irreversible_human_queue}` with explicit `compensating_action`. Examples: rejected wire → return funds to originator bank (002:74); document replace → archive old version 7y (001:77); EDD cutover → in-flight case migration plan (003:112). If irreversible, emit `human_queue` policy AC + named escalation owner. Idempotency complement (per C18 field 3): every side-effect op requires `idempotency_key` strategy + Gherkin replay test. T1: replay test mandatory. |
| **Confidence** | HIGH |
| **Sources** | A1 §0+§5.5, A3 §6.4+§8 R5, A5 E1-7+E2-7+I2-5+I3-7+P-09+P-10, B1 G7, B3 row 11, B5 T12+T15+P-09+P-10 |

---

## 6. Ambiguity Detection Patterns (R6 logic)

### C22. Detect 6 ambiguity types with severity assignment (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Every text segment during ambiguity pass. |
| **Action** | Run detection across **6 types** (per A2 §5 catalog of 30+ items). **(1) Lexical** — vague words `urgent, reasonable, appropriate, piecemeal, happy` without testable predicate → P2/P3 (P2 if in AC). **(2) Syntactic** — parenthetical aside negates main clause (`replaced (or maybe kept as version? unclear)` — 001:54) → P2 self-contradicting AC. **(3) Pragmatic** — context-dependent reference requiring domain knowledge (`that's regulated comms` — 002:46) → P2/P3. **(4) Pronominal** — `this, it, they, that, those, same thing` referring across >1 sentence boundary → P3 default, P2 if in AC. **(5) Quantifier** — `a LOT, some, several, multiple, most, rare, typically` without adjacent numeric → P3 default; cluster >5 → completeness penalty. **(6) Modal** — closed-class `may, might, could, should, would, probably, maybe, possibly, perhaps, ideally, tentatively, hopefully` in prescriptive sections → P2 per occurrence; compliance-speaker rule-mode override (per C15) elevates "should" to "must" in regulatory contexts. Additional class: **placeholder tokens** `(?), X req/min, $Xk, N attempts, TBD, ???, single capital in numeric slot` → P2 default, P1 if attached to regulator/PII-vendor. |
| **Confidence** | HIGH |
| **Sources** | A2 §5+§7, A3 §8 R6+R18, A4 §5.1, A5 §4, B1 HCP-13, B2 HC1+HC5+HC6+HC7+HC11+§5, B3 row 13, B5 G-F |

### C23. Severity assignment — P1 blocker / P2 must-address / P3 assumption-to-document (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Each ambiguity flagged by C22 or banking-grade detector. |
| **Action** | Map onto 3-tier severity: **P1** (blocker — must resolve before TL handoff) — Legal absent on regulatory; regulator named without citation; tipping-off violation; missing PII inventory on T1; missing compensating action on funds movement; calibration debt on risk routing. **P2** (must-address — should resolve before sprint planning) — self-contradicting AC; anonymous policy parameter; modal hedge in commitment; placeholder token unattached to regulator; notification matrix gap; AC vs comment-thread conflict; mobile parity deferral on regulated workflow; emoji-only decision on compliance topic. **P3** (assumption-to-document — document and move on) — pronoun across sentence boundary in non-AC context; quantifier without quantity (unless cluster); urgent-label-without-SLA; pragmatic shorthand in non-regulatory context. Context lifts severity (relative-date attached to regulator citation = P2, not P3 — per B5 C6). |
| **Confidence** | HIGH |
| **Sources** | A2 §5+§8, A5 §1-§3, B1 §5 + HCPs, B2 §5, B5 §1+§5 |

### C24. Down-weight anonymous comments and surface conflicting commenters (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Same field/decision receives incompatible claims across speakers (e.g., AC says "replaced" 001:54; Priya says "archived not deleted" 001:77 — never reconciled). Or anonymous comment makes a policy claim (001:103-104 "N could be 3"). |
| **Action** | Maintain per-entity decision ledger; if two speakers make incompatible claims on the same field (mobile scope, retention duration, replace-vs-archive, ETA timing, NPS as primary vs secondary, document version policy), surface a P2 conflict and **accept the latest claim as working answer** but log the conflict. For anonymous: refuse to treat as decision; flag for explicit attribution before AC binding. Resolution rule (per B3 C6): when AC and compliance rule-mode comment conflict, **comment wins**; original AC becomes "Assumption Overridden" with both `source_quote`s. |
| **Confidence** | HIGH |
| **Sources** | A2 §3.3+§7 R9, A3 §8 R6+C6, A4 R5, A5 P-16, B1 row 7, B2 HC2+HC13, B3 §1 row 16, B4 HCP-4 |

---

## 7. Splitting Patterns

### C25. Split by workflow steps / state transitions (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Raw input describes a state machine with ≥2 named states (`on hold`, `additional review`, `approved`, `rejected`, `escalated`, `pending second-level review`, `submitted`, `verified`). |
| **Action** | Emit each meaningful workflow step as a story candidate if it carries ≥1 distinct AC. For r2's wire-status flow: customer-facing status story; rejection messaging story; back-office state machine story; agent script story; notification policy story; audit emission story. For r3's EDD flow: doc capture (3a); upfront screening (3b); risk-engine ingestion (3c); tiered approval (3d); applicant status page (3e). **For every state**: auto-emit notification AC + audit-emission AC + tipping-off check AC (per A3 R17 + B1 HCP-10). Use customer-vs-internal dual-state model (per C8) when compliance constraints force divergence. |
| **Confidence** | HIGH |
| **Sources** | A1 §2.2, A3 §6.2+§8 R7+R17, A5 E2-10+I2-1+R7+P-07, B1 HCP-6, B3 §1 row 7+§5 |

### C26. Split by business rule variations (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Same operation differs by data class, customer tier, or risk class. Examples: re-upload of "regular" doc vs "sensitive" doc (NRIC/bank-stmt requires archive vs delete — 001); tiered approval by risk (low/medium/high — 003:87-89); ETA bucket by hold type (compliance 24-72h vs ops same-day — 002:54-55). |
| **Action** | Emit separate story when business rules diverge meaningfully across data/risk class. For r1: re-upload happy path story + audit-on-replacement story + archive-vs-delete-for-sensitive-docs story + retry-limit-and-escalation story. For r3 tiered approval: low-risk analyst-sole-decider story + high-risk dual-approval story (with named senior approver — see C14). When one customer-facing rule covers multiple internal SLAs, surface the flattening as P2 OQ (per B1 HCP-15). |
| **Confidence** | HIGH |
| **Sources** | A1 §2.2+§4.1+§5.5, A3 §2+§3+§6.5, A5 §1+§4+R9, B1 HCP-15, B3 C2, B5 P-06 |

### C27. Split by data variations (PII / non-PII / financial / biometric) (MED)

| Field | Detail |
|---|---|
| **Trigger** | Story handles multiple data classes with different governance: PII (high retention, residency, masking) vs non-PII; biometric (security review required) vs identity-doc (standard); financial PII (bank statement) vs general identity. |
| **Action** | If a single story handles a sensitive class AND a non-sensitive class with materially different governance, propose a split (or at minimum a per-class AC variation block). Aligned with A5 R9 — split along banking-grade concern boundaries (audit/PII/idempotency/reversibility shift), not by tech layer. Example: 001 has re-upload of generic docs + re-upload of NRIC (PII) — same workflow but archive-vs-delete diverges. |
| **Confidence** | MED |
| **Sources** | A5 R9, B5 P-04+§4.1, A3 §6.1 |

### C28. Split by stakeholder/role boundary (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Same operation has different actors with different authority/access. Examples: customer UI vs agent UI (002:99 "agent UI = same as back-office. customer UI = sanitized"); analyst sole decider vs dual approval (003:87-89); vendor liaison vs vendor entity (003 — Hua vs Acuant). |
| **Action** | Emit separate stories per role boundary when role determines AC. For r2: customer-facing status story + agent-UI status story. For r3: vendor integration story (Acuant SLA owned by entity) + vendor security review story (owned by Karim) — vendor liaison feasibility separate from contract owner. Force AuthZ role matrix on every story with multiple actors (per A5 P-08). |
| **Confidence** | HIGH |
| **Sources** | A4 §1+§2, A5 E2-9+I2-4+P-08, B3 §3.2, B4 HCP-7 |

---

## 8. Acceptance Criteria Patterns

### C29. Mandatory scenario types — happy / error / banking-grade (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Every story. |
| **Action** | Each story must carry at minimum three Gherkin scenario types: **(1) Happy path** — primary success criterion (testable, concrete values). **(2) Error/failure** — `What happens if X fails?` (loop, escalate, retry, timeout, rate-limit). **(3) Banking-grade scenarios** — per state transition: (a) notification AC ("When state changes from X to Y, Then customer receives email/in-app within Z minutes"); (b) audit-emission AC ("Then audit event emitted with {event, actor, ts, before, after, reason, idem_key}"); (c) tipping-off check AC ("Then message does NOT contain regulated terminology"); (d) idempotency replay scenario; (e) reversibility / compensating action scenario. |
| **Confidence** | HIGH |
| **Sources** | A2 §4, A3 §4+§8 R17, A5 P-01+P-05+P-07+P-08+P-09+P-10, B1 HCP-10, B3 §5, B5 P-01 through P-13 |

### C30. Gherkin rewrite + concrete-value enforcement + testability check (HIGH)

| Field | Detail |
|---|---|
| **Trigger** | Every prose AC from raw input. |
| **Action** | **Rewrite** every existing AC line into Gherkin `Given/When/Then` with concrete values. **Flag embedded ambiguities** — when source ACs contain words like "maybe", "unclear", "probably", "or version?" (001:54), split into a Gherkin scenario AND an Open Question. Never silently drop the ambiguity. **Concrete-value enforcement**: replace vague placeholders with calculated values from input metadata (resolve `EOW` via C4, resolve `N=3` from anonymous via C16, resolve `$Xk` to TBD-with-owner). **Testability check**: refuse non-testable predicates like `Compliance is happy` (001:57) — rewrite as `Given a document replacement event, When the audit event is emitted, Then it contains {actor, timestamp, doc_id, before_hash, after_hash, reason} AND Compliance Officer can retrieve the trail via the audit dashboard within 5 seconds`. Apply Gherkin rewrite across ALL source types: Jira declared ACs become drafts; Slack decisions are synthesized from longest decision chain; Meeting compound clauses (decision+dependency+caveat) are split into AC + open question + dependency edge (per A3 §4.3). Linguistic-quality scorecard (per A2 §6) below composite 5.0 requires human checkpoint before silent handoff. |
| **Confidence** | HIGH |
| **Sources** | A2 §6+§7 R15, A3 §4+§8 R6, A5 R3+R7, B1 G3, B2 §4+§5 HC1, B3 §1 row 3+§5, B5 C3+P-01 |

---

## 9. Cross-Cutting Defaults (Summary Index)

These 30 patterns yield the skill's **DEFAULT BEHAVIORS**:

| Pattern | Category | Conf | Trigger summary |
|---|---|---|---|
| C1 — Detect source type | Input parsing | HIGH | Any raw input |
| C2 — Route to source-specific parser | Input parsing | HIGH | After C1 |
| C3 — Strip ground-truth annotation block | Input parsing | HIGH | `## Intentional Issues for R6 to Catch` present |
| C4 — Resolve relative dates | Input parsing | HIGH | Non-ISO-8601 time expressions |
| C5 — Construct Domain Glossary | Domain interpretation | HIGH | Every input |
| C6 — Recognize regulator citations | Domain interpretation | HIGH | `[A-Z]+-[A-Z]+-[A-Z0-9-]+` regex match |
| C7 — Auto-classify PII | Domain interpretation | HIGH | PII terms in text |
| C8 — Classify scope kind | Structure mapping | HIGH | Before story emission |
| C9 — Detect story boundaries | Structure mapping | HIGH | After scope_kind |
| C10 — Detect epic boundaries | Structure mapping | HIGH | Multi-workstream scope |
| C11 — Extract Parking Lot / Out-of-Scope | Structure mapping | HIGH | Explicit or implicit deferrals |
| C12 — Distinguish Owner/Sponsor/Approver | Stakeholder | HIGH | Every input |
| C13 — Identify SMEs by domain | Stakeholder | HIGH | Speaker with role title/signature |
| C14 — Detect missing stakeholders (Legal P1) | Stakeholder | HIGH | Every input — strongest convergence |
| C15 — Weight authority by speech act | Stakeholder | HIGH | Each utterance |
| C16 — Down-weight anonymous/paraphrased | Stakeholder | HIGH | Anonymous/group/paraphrase markers |
| C17 — Detect mentioned-but-not-engaged | Stakeholder | HIGH | ≥2 mentions, 0 utterances |
| C18 — Force 7 banking-grade fields | Banking-grade | HIGH | Every story (forcing function) |
| C19 — Infer tier per epic | Banking-grade | HIGH | Before story extraction |
| C20 — Tipping-off scan | Banking-grade | HIGH | Customer-facing comm change |
| C21 — Compensating action / reversibility | Banking-grade | HIGH | Any external write |
| C22 — Detect 6 ambiguity types | Ambiguity | HIGH | Every text segment |
| C23 — P1/P2/P3 severity assignment | Ambiguity | HIGH | Each flagged ambiguity |
| C24 — Anonymous downgrade + conflict resolution | Ambiguity | HIGH | Conflicting/anonymous claims |
| C25 — Split by workflow steps | Splitting | HIGH | State machine with ≥2 states |
| C26 — Split by business rule variations | Splitting | HIGH | Rules differ by class/tier |
| C27 — Split by data variations | Splitting | MED | Multiple data classes |
| C28 — Split by stakeholder/role boundary | Splitting | HIGH | Different actors / authority |
| C29 — Mandatory scenario types | Acceptance Criteria | HIGH | Every story |
| C30 — Gherkin rewrite + testability | Acceptance Criteria | HIGH | Every prose AC |

**29 patterns at HIGH confidence (≥3 analyses) + 1 at MED confidence (2 analyses) = 30 patterns total.**

---

## 10. Architectural Pillars (extracted from triangulation)

Three meta-principles emerge from the cross-validation that no single analysis stated alone:

1. **Tier inference runs per emitted epic, not per raw file** (forced by A3's multi-epic framing of r3; confirmed B3 §3.3 + B5 C2). The tier loop boundary changes when scope_kind = multi-epic.

2. **A single phrase can carry multiple flag types** — banking-grade + linguistic ambiguity + stakeholder-mode. The skill **must not deduplicate** across detectors. Each phase contributes a different facet: A5 = regulatory force, A2 = linguistic shape, A4 = speaker authority mode. Example: "regulated comms" (002:47) fires P-01 (tipping-off), HC11 (pragmatic ambiguity), and rule-mode authority (compliance directive) simultaneously.

3. **Banking-grade detection is half pattern-matching, half forcing function** (A5 §6 + A3 §6.4 "idempotency/reversibility rarely stated, always required" + A4 R3 stakeholder-gap forcing). The skill's primary value is **forcing fields to be filled or explicitly declared n/a**, not keyword matching alone.

**Highest-leverage rule across the entire analysis**: `Legal absent + regulatory content = P1 governance gap` — triangulated by A1, A2, A3, A4, A5 independently, with raw evidence in 100% of inputs. Canonical always-fires detector (C14).

---

*End of Phase C1 Recurring Pattern Distillation. These 30 patterns become the default procedures of the `ba-elicit-from-raw` atomic skill.*
