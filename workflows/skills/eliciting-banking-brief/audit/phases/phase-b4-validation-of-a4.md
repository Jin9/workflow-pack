# Phase B4 — Cross-Validation of A4 (Stakeholder Topology)

> **Role**: Cross-Validation Specialist (B4)
> **Validates**: `phase-a4-stakeholder-analysis.md`
> **Cross-refs**: A1 (domain), A2 (linguistic), A3 (structural), A5 (banking-grade)
> **Ground truth**: hidden R6 annotations in `raw-request-{001,002,003}.md`

---

## 1. Triangulated Findings (cross-confirmed)

| # | Claim | A4 evidence | Corroborated by | Confidence |
|---|---|---|---|---|
| T1 | **Legal absent in 3/3** — single most reliably missing role | A4 §4.2 "P1 — 100%"; §8 row "Legal MISSING…" | A1 §3.4 "Legal absent but cited"; A2 §7 R8; A3 §8 R9; A5 R5; ground truth 001:162, 002:194, 003:170-172 | **High** |
| T2 | **Compliance ≠ Legal** — compliance owns policy, only Legal blesses customer-facing language | A4 §3.7 "Compliance presence ≠ Legal sign-off" | A1 §4.2 "Priya defers to Legal multiple times"; A5 R5; raw 002:65, 003:115 | **High** |
| T3 | Compliance directive uppercase modals ("MUST NOT", "can't", "regulated") signal binding rule-mode | A4 §3.3, §5.3 | A2 §4.2 (002:65); A5 §1b E2-5 | **High** |
| T4 | **Owner ≠ Sponsor ≠ Approver** — merged in 001, separate in 002, chair-merged in 003 | A4 §2.1-§2.2, §8 | A1 §3.4; A3 §8 R7 | **High** |
| T5 | Engineering leads pose constraints as questions ("file size?", "those are different states fwiw") | A4 §5.2 | A2 §4.1 Raj's 4 bullets (001:88-95); A2 §4.2 Tom 002:29-30 | **High** |
| T6 | PMs hedge ("probably/maybe/let's") and defer technical & compliance specifics | A4 §5.1 | A1 §3.4; A2 §3.1 + R1 modal detector | **High** |
| T7 | Note-taker is a meta-stakeholder with interpretive authority (Aisha, 003) | A4 §2.6, §5.7, R9 | A2 §1.3; A3 §7.3; raw 003:8-11 | **High** |
| T8 | Anonymous attribution must be down-weighted ("Anonymous (likely Raj) — N could be 3") | A4 §3.6, R5 | A2 §3.1; A3 §7.1; ground truth 001 P3 #2 | **High** |
| T9 | Compliance officers cite specific retention numbers (7y / 30d / archive-not-delete) without policy doc attached | A4 §5.3 | A1 §1.1 row 11; A5 §1a E1-3, E1-6; raw 001:115 | **High** |
| T10 | Customer/applicant has zero voice across 3/3 — mediated by Ops/Support/UX | A4 §2.4, R12 | A1 §2.3 final actor; A2 §3.1; A5 R6 | **High** |
| T11 | Mobile owner/lead missing in all 3; deferred without confirmed owner | A4 §4.2 | A1 §4.1; A3 §5.6; ground truth 001:164, 002:196, 003 Q4 | **High** |
| T12 | Authority by deference — `@X` and "Y would know better" mark Y as answer-owner | A4 §3.2, R8 | A2 §4.1 (Sarah→Priya 001:80); A3 §7.1; raw 002:35-36 | **High** |
| T13 | Compliance **proposal-mode** is negotiable — Jamie overrides Priya's 0.75 on calibration grounds | A4 §3.5, §6 | A1 §3.4 last bullet; A2 §4.3; A5 §2c I3-2; raw 003:91-93 | **High** |
| T14 | Sarah Khoo (Product 002) is explicit Sponsor distinct from drafter (Tom) — "Sarah can you sponsor?" → "yes go ahead" | A4 §1.2, §2.2 | A1 §1.3 row 31; A2 §4.2; ground truth 002:191 | **High** |
| T15 | Emoji-as-decision is real but soft — `👍 with caveats` from compliance carries signal but not formal sign-off | A4 §1.2, §3.4 | A2 §1.2; A3 §1.12, R12 | **High** |
| T16 | Vendor liaison ≠ vendor entity — Hua speaks for Acuant; entity owns SLA/contract | A4 §1.3, §2.5, R11 | A1 §2.3; A5 §1c E3-12/13 | **High** |
| T17 | Internal affected-users (support agents, EDD analysts) voiced via proxy, rarely co-designed with | A4 §2.4, §4.2 | A2 §3.1; A5 §3b G2-9; ground truth 002:195, 003:198 | **High** |
| T18 | Regulator references are cited-only, never produced in-meeting — "MAS-AML-1A" is a name, not a citation | A4 §2.5, §6 | A1 §3.1; A5 R4; raw 003:39 | **High** |

---

## 2. Contradicted Findings (A4 vs others)

**C1 — Sarah Lim "Owner+Approver merged" (001) overstates approver scope.** A4 §1.1 implies Sarah is Approver, but A1 §3.4 says "PM is reporter / sponsor, **not decider** on compliance", A5 §1a E1-3 makes Priya the binding voice on retention, and ground-truth P3 #4 explicitly notes "Compliance officer Priya is the approver (implicit — not stated)". *Refinement*: A4 row should read "Owner; partial Approver (priority/scope only)"; Priya = de-facto Approver on compliance subset.

**C2 — Internal contradiction inside A4 on engineering authority.** §6 says eng is "**low** on prioritization" but §1.2 credits Tom Becker as "**de-facto owner**" who drafts scope (002:85-92). *Resolution*: engineering becomes de-facto owner when Product is absent or late; Tom yields once Sarah Khoo joins at 11:02. Heuristic: engineering prioritization-authority is provisional, scoped to Product-absence windows.

**C3 — Senior analyst mis-classed as Affected User (003).** A4 §2.4 lists "Senior analyst — tier-2 approver" with "no voice". A5 §1c E3-8 makes this a P1 authn/authz Approver role. Ground truth 003:199 lists "Senior management approval owner" as a stakeholder gap. *Refinement*: senior analyst belongs in §2.2 as "named role — name TBD" approver, not as voiceless affected.

**C4 — "honestly i don't know, Mei would know better" is dual-mapped.** A4 §5.4 reads this as ops-manager competence-modesty; A2 §4.2 reads it as a question/deference edge. Both true; A4 should fold it into §3.2 (deference) rather than §5.4 — the deference reading is the more actionable pattern.

**C5 — David's "highest in-room authority" (003) is bounded by Legal absence.** A4 §1.3 calls David the highest authority because he made scope cuts. A5 R5 + ground truth 003:170-172 P1 say David made compliance-touching decisions *without Legal*, which the banking-grade view says he did not have authority to do. *Refinement*: distinguish organizational authority (A4) from governance authority (A5) for regulatory-touching decision classes.

**C6 — A4 P2 on agent-UI access is too lenient.** A4 §1.2 lists "Customer support team … not consulted on agent UI design" as a P2 co-design gap. A5 §3b G2-9 elevates: agent UI shows back-office data (002:99 "agent UI = same as back-office"), making this a P1 access-control + audit gap, not just co-design.

**C7 — Risk-Analyst override (Jamie) hides a separate dependency.** A4 §6 "Risk/Data — can override compliance proposals" is correct, but A5 §2c I3-2 reframes the same exchange as a standing P1 (uncalibrated engine = non-deterministic routing). The override is provisional pending calibration debt. *Refinement*: record both authority-resolution and the dependency.

---

## 3. Gaps in A4 Noticed by Other Phases

**3.1 From A1 (domain).** A1 §1.1 row 13 implies SG PDPA via NRIC; no A-phase names a Data Protection Officer / Privacy stakeholder. A4 lists Security as absent but not Privacy/DPO. **Gap**: add Privacy/DPO to required-role checks alongside Legal and Security.

**3.2 From A2 (linguistic).**
- **Hedge density as role-mismatch signal** — A2 §7 R14 proposes a count-based hedge penalty (>5 per input). A4's fingerprints (§5) treat hedging as a PM trait but don't use density to detect *delegated decisions*. Gap: when PM hedges and an SME commits within ≤5 messages on the same topic, bind AC to SME.
- **Speech-act granularity** — A2 §4 tags request/assertion/promise/question/pushback; A4's authority modes (rule/proposal/preference/estimate/pain) operate at a different layer. Gap: stamp each utterance with both axes for the deference graph.
- **Hybrid acceptance** — A4 §3.4 captures explicit "yes go ahead" but understates `👍 with caveats` (002:64) as acceptance+constraint. A2 §4.2 catches both halves.

**3.3 From A5 (banking-grade).**
- **Privacy/DPO** (P1 wherever PII inventory non-empty — i.e., all 3 inputs).
- **Adverse-media vendor owner (unnamed)** — A4 §1.3 lists this P3; A5 §3c G3-8 says P1 (vendor processes PII without DPA owner).
- **SAR filer/liaison** — A5 §3b G2-5 P1; A4 omits this role entirely.
- **Model Owner vs Risk SME** — A5 §2c I3-2 demands a calibration-cycle/version-pinning owner distinct from Jamie's analyst role.
- **Vendor security reviewer (Karim's spike)** — A5 §3c G3-9 P1 dependency; A4 mentions Karim flagging but does not name a distinct Security Reviewer role.
- **Originator-bank ops / compensating-action owner** — A5 §3b G2-6 P1; A4 §1.2 lists as gap with no severity.
- **Migration workstream owner** — A4 P2; A5 §3c G3-12 P1.

**3.4 Predictions tested against ground truth.**

| A4 prediction | Ground truth | Verdict |
|---|---|---|
| 001 missing: Legal, Security, Mobile | 001:162-164 (exact) | **3/3 Match** |
| 002 missing: Legal, CS, Mobile PM, Data/Analytics, Originator-bank ops | 002:193-198 (exact) | **5/5 Match** |
| 003 missing: Legal, CS, Marketing, Senior approver, Migration owner | 003:195-200 (exact) | **5/5 Match** |
| Legal-as-P1 across all 3 (A4 §4.2) | Formally P1 only in 003; P3/gap in 001/002 | **Partial — A4 stricter than ground truth** (defensible) |
| R10 "always emit Legal-engagement check" | Aligned with 003 P1; arguably correct generalization | **Strong match** |

**13/13 named missing-stakeholder predictions correct.** Strongest empirical sub-skill in A4.

---

## 4. Quality Assessment of A4

**Strengths.** Comprehensive 30+ stakeholder inventory with quote-anchored evidence; authority-mode taxonomy (rule/proposal/preference/estimate/pain) is the most BA-actionable framing across A-phases; missing-stakeholder predictions empirically 100% correct against ground truth; communication-style fingerprints (§5) usable as a downstream classifier; deference-graph proposal (R8) is uniquely novel; note-taker as meta-stakeholder (R9) correctly first-classed.

**Weaknesses.** Approver mis-merge in 001 (C1); senior analyst mis-classed as Affected (C3); systematic severity under-call on several banking-grade gaps (C6 + §3.3 bullets — A5 elevates multiple A4 P2s to P1); no Privacy/DPO required-role; Model Owner not separated from Risk SME; §5 fingerprints would sharpen with A2 speech-act tagging; no quantitative `attribution_confidence` field per row; no stakeholder counterpart to A5 R4 (citation-fetcher when regulator named without citation).

**Verdict.** Strong on inventory and missing-stakeholder detection; moderate on severity calibration; weak on Privacy/DPO, Model Owner, and integration with A2 speech-acts. Recommended re-cut: keep §1-§4 as backbone; refactor §6 to absorb A2 speech acts; extend required-role checklists (Privacy/DPO, SAR liaison, Model Owner, Security Reviewer, Migration owner); upgrade P2→P1 on agent-UI access-control, vendor-PII processors, and migration ownership per A5.

---

## 5. High-Confidence Stakeholder Patterns (triangulated)

| # | Pattern | Detection rule | Skill action |
|---|---|---|---|
| HCP-1 | Compliance rule-mode = binding; proposal-mode = negotiable | Uppercase modals (MUST/MUST NOT/can't/regulated) → rule; hedges + thresholds/wording → proposal | Emit `authority_mode ∈ {rule, proposal}`; rule → fixed AC; proposal → AC + open question for affected SME |
| HCP-2 | Legal-engagement check mandatory for banking inputs | Input mentions any of: regulator name / "tipping off" / retention years / audit / PII / biometric / SAR AND no role=Legal in attendees | Emit `legal_status ∈ {present, scheduled, mentioned_only, absent}`; absent → P1 governance block |
| HCP-3 | Deference is authority | Regex `@\w+` + lemmas of "would know", "let me know", "need X to confirm" | Build deference graph; each edge → open question to Y on topic Z; if Y absent → escalate |
| HCP-4 | Anonymous attribution down-weights | String match `anonymous`, `(likely X)`, group labels `(group, 20 min)` | `attribution_confidence: low`; commitments/numerics inside require re-attribution before AC |
| HCP-5 | Note-taker = meta-stakeholder; paraphrase by default | Detect first-person aside, bracketed editorial, explicit "note-taker filtered" | All statements default `attribution_confidence: paraphrase`; P1/P2 items require verbatim follow-up |
| HCP-6 | Owner ≠ Sponsor ≠ Approver — never collapse | Owner = drafts/opens; Sponsor = grants priority/budget; Approver = signs off per change-class (Compliance for retention, Legal for customer language) | Schema `{name, role_title, function, type ∈ {owner, sponsor, approver, sme, affected, external, meta}, evidence}` |
| HCP-7 | Vendor liaison ≠ vendor entity | "Vendor liaison — <name>" in attendees, or "<Name>: <Vendor> API can…" | Record `vendor_liaison_person` AND `vendor_entity`; SLA/pricing attaches to entity; feasibility to liaison |
| HCP-8 | Engineering = de-facto owner when Product absent/late | Engineer drafts scope ("ok let me draft. the asks are roughly: 1…") before any PM speaks priority | Tag `provisional_owner`; once Sponsor speaks, transition to `drafter + sme` |
| HCP-9 | Hedge cluster on a topic = delegated decision | PM hedges + non-PM commits within ≤5 messages on same topic | Bind AC to non-PM; record PM utterance as `provisional_preference` |
| HCP-10 | Customer/applicant voice is always mediated in banking | `affected_user_type ∈ {customer, applicant}` and no proxy speaker or cited research artifact | P2 "no proxy for end user; cite NPS/CSAT/call-volume artifact" |
| HCP-11 | Senior approver named-by-role-only = P2 gap | "senior analyst", "compliance officer dual approval" without specific person | `approver_role: <role>, name: TBD, severity: P2`; auto-action "identify named senior approver" |
| HCP-12 | Privacy/DPO is the 3rd absent role behind Legal and Security | `pii_inventory` non-empty AND no role match `(privacy|dpo|data protection)` | P1 gap "Privacy/DPO not engaged — required for PII inventory sign-off" |
| HCP-13 | Mentioned-but-not-engaged ≠ absent | `count_mentions(role) ≥ 2 AND count_utterances(role) == 0` | `engaged: false, mentioned: N`; severity scales with N and topic regulatory weight |
| HCP-14 | Model Owner ≠ Risk SME when a score-threshold drives routing | "score >= X from engine" + "engine not calibrated" + named risk analyst | Split into `risk_sme` + `model_owner`; flag calibration debt as standing dependency |
| HCP-15 | Regulator-cited-but-not-produced needs a named citation-fetcher | Regex `[A-Z]+-[A-Z]+-[A-Z0-9-]+` (e.g., `MAS-AML-1A`) + no attached/linked source | Action item `citation_fetcher = <promisor> due <date>`; P1 if T1 |
| HCP-16 | Diffuse external pressure ("Marketing wants…", "the X team also asked…") needs a named contact | Phrases lacking individual attribution | P2 "diffuse stakeholder — name a single contact for sign-off before TL handoff" |

---

## 6. Conclusion

A4 is the most empirically validated A-phase output measured against ground truth (13/13 missing-stakeholder predictions correct across 3 inputs). Its inventory, authority-mode taxonomy, communication-style fingerprints, and Legal-engagement-check recommendation (R10) are load-bearing and should ship largely intact. Required refinements: (i) split Approver authority away from Sarah Lim in 001 (C1); (ii) reclassify "senior analyst" as Approver-pending-name in 003 (C3); (iii) elevate Privacy/DPO, Model Owner, SAR Liaison, and Security Reviewer to first-class required roles (§3.3); (iv) fold A2's speech-act taxonomy into A4 §6 for sharper role-by-utterance inference; (v) re-calibrate severity on agent-UI access-control, vendor-PII processors, and migration ownership from P2 to P1 per A5. With these refinements, A4's stakeholder schema `{name, role, function, type, authority_mode, evidence, attribution_confidence}` is the right backbone for the `ba-elicit-from-raw` stakeholder-extraction phase.
