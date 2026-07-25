# Phase B1 — Cross-Validation of A1 (Domain Anthropology)

> **Role**: Cross-Validation Specialist for BA Skill Factory
> **Primary**: A1 Domain Anthropologist output
> **Triangulated against**: A2 Linguistic Forensics, A3 Structural Patterns, A4 Stakeholder Topology, A5 Banking-Grade Signals
> **Confidence rubric**: high = 3+ agree, medium = 2 agree, low = A1-only

---

## 1. Triangulated Findings (A1 finding confirmed by 1+ other analysis)

| # | A1 finding (quoted) | Confirming analyses | Conf. | Implication for skill |
|---|---|---|---|---|
| 1 | "Coherent **banking BA dialect**" across Jira/Slack/Meeting (A1 §0) | A2 §1; A3 §1+§7; A5 §5 | high | Source-type detection is the first parser pass |
| 2 | Tipping-off is binding regulatory constraint (A1 §1.1 #7, §3.4) | A2 §5 #12; A4 §3.3; A5 E2-3/5/6 + R3/R12 | high | Ship non-tipping vocab ref; auto-scan customer-facing copy ACs |
| 3 | Customer-facing simplicity vs back-office granularity conflict (A1 §0, §4.2) | A2 §3.2 #2; A3 §1.4; A5 E2-9 | high | Dual-state model becomes default story template |
| 4 | 7-year retention recurs across inputs (A1 §1.1 #11) | A2 §3.1 #1; A4 Table 1.1; A5 E1-3/6, E3-14 | high | Default-flag retention as P1 when unstated; require policy citation |
| 5 | "Legal absent but cited" (A1 §3.4, §6) | A2 §7 #8; A3 §8 #9; A4 §4; A5 R5 | high (4) | Hard-coded `legal_status` check; auto-P1 if mentioned-not-engaged |
| 6 | NRIC = direct PII / national ID (A1 §1.1 #13) | A2 §3.1 #2; A3 §6.1; A4 Priya rows; A5 E1-13 + I1-8 | high | Auto-tag NRIC/passport/biometric/financial-stmt into `pii_inventory` |
| 7 | Anonymous suggestion-as-default — N=3 (A1 §3.4, §4.4) | A2 §5; A3 §8 #11; A4 §3.6; A5 I1-11 | high | Detect anonymous authorship; refuse to treat as policy |
| 8 | Bracketed-owner action items `[Owner] task — due` (A1 §3.1) | A2 §1.3; A3 §1.8; A4 §1.3 | high | Meeting parser extracts `[Owner]` as authoritative |
| 9 | Mobile-vs-web parity deferral is systemic (A1 §4.1, §5.5) | A2 §3.1 #9 + §3.2 #3; A3 §2.2; A4 §8 | high | Auto-emit Parking Lot mobile entry; require deferral rationale |
| 10 | PM is reporter/sponsor, not compliance-decider (A1 §3.4) | A2 §3.1 #1; A4 §5.1, R2 | high | Distinguish Owner / Sponsor / Approver / SME in schema |
| 11 | Engineering owns scope reality-checks (A1 §3.4) | A2 §4.1; A3 §1.4; A4 §5.2 | high | Promote eng constraints to dependencies |
| 12 | Decisions made by 👍 reaction (A1 §3.4) | A2 §1.2; A3 §1.12; A4 §5.3 | high | Emoji = soft acceptance; auto-generate "confirm written sign-off" OQ |
| 13 | Informal sponsorship "Sarah can you sponsor?" → 👍 (A1 §3.4) | A2 §4.2; A3 §7.2; A4 §2.2 | high | Closed-Q + affirmative across two participants = sponsorship event |
| 14 | Source-of-funds is "most variable EDD step" (A1 §1.1 #14) | A2 §2.3; A3 §6.1; A5 E3-5 + I3-3 | high | Generate two flags: PII + SLA-variance |
| 15 | Threshold-before-calibration smell (A1 §4.1, §5.5) | A2 §3.2 #4; A3 §4.3; A4 §3.5; A5 I3-2 | high (4) | Split threshold proposals into AC + `data_maturity` dep + OQ |
| 16 | Vendor-rec vs security-review friction (A1 §4.2) — Acuant biometric | A2 §4.3; A3 §5.5; A4 R11; A5 E3-11 + R8 | high | Vendor + PII/biometric → mandatory security-review dep edge |
| 17 | ETA bucketing flattens multiple SLAs (A1 §4.1, §5.5) | A2 §3.2 #2; A3 §4.2; A5 I2-3 | high | Surface flattening as P2 open question |
| 18 | Audit trail "always asked, rarely scoped" (A1 §4.3) | A2 §4.1; A3 §6.2; A4 §3.3; A5 R7 | high | Auto-generate `event/actor/ts/before/after/reason/idem_key` per transition |

**Total: 18 triangulated findings.**

---

## 2. Contradicted Findings

**No hard contradictions** found. Two mild tensions, both A1-incomplete rather than A1-wrong:

1. **Tier of input 003** — A1 implicitly treats 003 as one initiative (§0, §1.1). A3 §3.3 and A5 §5 classify it as a **multi-epic program (5-6 epics)** and recommend T1 escalation. *Resolution*: A1's vocabulary work is sound; skill should add A3's `scope_kind` classifier. Gap, not contradiction.
2. **Compliance authority on thresholds** — A1 §3.4 states "Compliance holds veto over customer-facing language". A4 §3.5 refines: rule-mode (MUST NOT) binding; proposal-mode (the 0.75 threshold) negotiable — Jamie overrides Priya on calibration grounds. *Resolution*: A1 holds for customer-comms; adopt A4's `authority_mode` annotation.

**Why no hard contradictions**: A1's claims are quote-anchored and confidence-tagged, limiting the surface for direct contradiction. Where A1 risks overgeneralising, the other analyses extend rather than refute.

---

## 3. Gaps in A1 Noticed by Others

| # | What A1 missed | Caught by | Why it matters |
|---|---|---|---|
| G1 | **Forced-evaluation contract** (banking-grade rows fill-or-not-applicable; empty = schema fail) | A5 §6, R1 | Structural enforcement, not pattern matching |
| G2 | **Tier inference (T1/T2/T3)** with firing signals | A5 §5 | Mis-tiering = wrong temperature + governance |
| G3 | **Linguistic quality scorecard** (specificity / completeness / consistency / BA-readiness) | A2 §6 | Drives min clarifying-Q count; refuse handoff below 5.0 |
| G4 | **Scope-kind classifier (single-epic vs multi-epic)** | A3 §3+§8 #8 | 003 is actually 5-6 epics |
| G5 | **Authority mode per utterance** (rule/proposal/preference/estimate/pain) | A4 R2, §3 | Encodes binding-vs-negotiable |
| G6 | **Stakeholder gap heat-map** with per-scope severity | A4 §4 | A1 notes Legal only; A4 adds CS / Mobile / Data — ~70% of gap flags |
| G7 | **Idempotency + reversibility inferred from workflow shape, not text** | A3 §6.4; A5 R1 | Auto-generate on every mutation/notification |
| G8 | **Modal-verb closed-class detector** | A2 §7 #1 + §5 | Deterministic regex → P2 per occurrence |
| G9 | **Banking-grade signal counting as measurable artifact** | A5 §8 (125 total) | Signal-count is a tier-inference input |
| G10 | **Note-taker as meta-stakeholder w/ confidence penalty** | A4 §2.6, R9 | Mediated content = `attribution_confidence: paraphrase` |
| G11 | **Deference graph from @mentions + "X would know better"** | A4 R8 | Answer-owner recommender for OQs |
| G12 | **Tipping-off vocabulary file** as shipped asset | A5 R12 | A5 specifies the deliverable; A1 names the constraint only |
| G13 | **Hard dependencies that BLOCK TL handoff** (vs P2 OQs) | A5 R8 | Missing regulator citations, unattached policy docs, unnamed PII-vendors, open security spikes |
| G14 | **Hedge detector beyond modals** ("honestly i don't know", "to be safe") | A2 §7 #14 | Count-based completeness penalty (>5 hedges) |
| G15 | **State-machine → auto notification + audit + tipping-off AC per state** | A3 §8 #17 | Three ACs auto per state |

---

## 4. Quality Assessment of A1

### Comprehensiveness Score: **8.5 / 10**

A1 catalogues 32 quote-anchored terms, builds a concept-map, articulates three state machines, covers per-source-type conventions, catalogues four classes of "smells", and ends with five recommendations. Points lost for missing: input-quality scoring (A2), tier-inference (A5), operationalised stakeholder gaps (A4), forced-evaluation contract (A5).

### Accuracy

**Holds up strongly**: All 32 vocabulary entries are quote-grounded (cross-checked vs A5's signal table and A4's utterances). Three state machines match A3's structural read. "Legal absent" confirmed by A4 + A5; tipping-off confirmed by A2/A4/A5.

**Partial**: A1's "Compliance holds veto" lacks A4's rule-vs-proposal nuance; A1's implicit single-initiative framing of 003 understates the multi-epic shape A3+A5 identify.

**No over-claim**: A1 §7 appropriately downgrades inferred items (disbursement) and disclaims implementation-detail certainty, matching A5 R11.

### Top 3 Strongest Contributions

1. **Vocabulary catalogue (§1)** — 32 quote-anchored terms with PII/sensitivity/confidence tags; canonical glossary for every downstream sub-agent.
2. **State-machine articulations (§2.2)** — Re-upload, wire dual-path, EDD current-vs-target become A3's parsing backbone and A5's audit-per-transition rule.
3. **Cross-source convergence summary (§6)** — All-three-input patterns anchor the triangulation B1 itself performs.

### Top 3 Weakest Areas

1. **No forced-evaluation contract / no tier inference** — A5 supplies the structural forcing.
2. **Stakeholder gaps under-operationalised** — A4 quantifies Legal-absent at 100% plus 6+ other recurring gaps with per-scope severity.
3. **No input-quality scorecard / no minimum-clarification gate** — A2 ranks inputs and proposes a refuse-handoff threshold.

### Recommendation — A1 patterns to enshrine as defaults

Adopt A1 §5.1 default glossary; §5.2 citation-pattern regex; §5.3 PII auto-tagging from the term itself; §5.4 source-type-adaptive elicitation; §5.5 six-pattern conflict library → templated OQ generators.

**Add**: tier inference + forced-evaluation contract (A5); authority-mode tagging (A4); linguistic quality scorecard (A2); scope-kind classifier (A3); idempotency/reversibility from workflow shape (A3+A5).

---

## 5. High-Confidence Domain Patterns (triangulated 3+ ways)

These become **DEFAULT BEHAVIORS** in the skill:

| # | Pattern | Default behavior | Supporting |
|---|---|---|---|
| HCP-1 | **Legal absent in 100% of banking inputs** | Emit `legal_status` field; auto-P1 if absent on regulatory scope | A1 §3.4/§6, A2 §7 #8, A4 §4+R10, A5 R5 |
| HCP-2 | **Tipping-off prohibits direct customer disclosure** | Auto-AC: `When notifying, message does NOT contain {sanctions, AML, flagged, suspicious, regulated}` | A1 §1.1 #7, A2 §5 #12, A4 §3.3, A5 E2-3/5/6+R3/R12 |
| HCP-3 | **7-year retention is banking default** | Default 7y completed, 30d abandoned (Legal-confirm pending) | A1 §1.1 #11, A2 §3.1 #1, A4 §3.3, A5 E1-3/6+E3-14 |
| HCP-4 | **PII set: NRIC, passport, biometric, source-of-funds, bank stmt** | Auto-tag to `pii_inventory` w/ retention/residency/masking/audit | A1 §1.1 #13-15, A3 §6.1, A4 Priya rows, A5 E1-13+E3-3 |
| HCP-5 | **Compliance Officer = regulatory approver; Compliance ≠ Legal** | `rule mode` (MUST/can't) binding; `proposal mode` negotiable | A1 §3.4, A2 §3.1 #1, A4 §3.3+§3.5, A5 R5 |
| HCP-6 | **Dual-state model (customer vs back-office)** for compliance flows | Emit two parallel state diagrams + mapping function | A1 §2.2-B+§4.2, A3 §7.2, A5 E2-9+R7 |
| HCP-7 | **Mobile-vs-web deferral in every input** | Auto-Parking Lot mobile entry; require deferral rationale + owner | A1 §4.1, A2 §3.1 #9, A3 §2.2, A4 §8 |
| HCP-8 | **Anonymous / paraphrased content down-weighted** | Anonymous = low auth; mediated = `attribution_confidence: paraphrase` | A1 §3.4+§4.4, A2 §7 #5, A3 §8 #11, A4 R5+R9 |
| HCP-9 | **Action items use `[Owner] task — due` pattern** | Meeting parser extracts as authoritative; resolve relative dates vs metadata | A1 §3.1, A2 §1.3, A3 §1.8, A4 §1.3 |
| HCP-10 | **Audit trail on every state transition + doc replacement** | Emit `event/actor/ts/before/after/reason/idem_key` schema | A1 §1.1 #12, A2 §4.1, A3 §6.2, A4 §3.3, A5 R1+R7 |
| HCP-11 | **Threshold-before-calibration smell** | Split proposals into AC + `data_maturity` dep + OQ | A1 §4.1+§5.5, A2 §3.2 #4, A3 §4.3, A4 §3.5, A5 I3-2 |
| HCP-12 | **Vendor + PII → mandatory security-review dep** | Biometric / external PII flow → `security_review` edge; `$Xk` redaction → P2 | A1 §4.2/§4.3, A3 §5.5, A4 R11, A5 E3-11+R8 |
| HCP-13 | **Modal verbs in prescriptive sections are P2 flags** | Tokenize `may/might/could/should/probably/maybe/possibly/ideally` → P2 per occurrence | A1 §3.4, A2 §5 #25-30, A3 §8 #18 |
| HCP-14 | **PM-reporter / Compliance-gatekeeper / Eng-feasibility / Legal-absent quartet** is universal | Stakeholder schema defaults to four-role checklist; missing → gap flag | A1 §3.4+§6, A2 §1, A4 §6+§8, A5 §5 |
| HCP-15 | **One customer-facing ETA often hides multiple internal SLAs** | Surface flattening as P2 OQ when one ETA covers internal states w/ different SLAs | A1 §4.1+§5.5, A2 §3.2 #2, A5 I2-3 |

---

## 6. Bottom Line

A1 is a strong vocabulary-and-pattern foundation (8.5/10, high accuracy, well-anchored). Weaknesses are not errors but missing structural layers — tier inference, forced-evaluation contract, input-quality scorecard, authority-mode tagging, scope-kind classifier — which A2/A3/A4/A5 supply cleanly. No contradictions block composition; gaps are additive. Adopt A1 §5.1-§5.5 as defaults; stack the operational machinery from the other four on top.

---

*End of Phase B1.*
