# Phase B5 — Cross-Validation of A5 Banking-Grade Signal Analysis

> **Role**: Cross-Validation Specialist (B5), BA Skill Factory
> **Primary subject**: `phase-a5-banking-grade-analysis.md`
> **Triangulation sources**: A1 (Domain), A2 (Linguistic), A3 (Structural), A4 (Stakeholder), raw inputs 001/002/003
> **Anchors**: `COGNITIVE_OS_PROJECT.md` §3, `DELIVERY_WORKFLOW_PLAN.md` (Tier system), `references/ba-best-practices.md`
> **Method**: Each A5 claim is checked against ≥2 other phases or the raw evidence. Output is the foundation for the skill's banking-grade field logic.

---

## 1. Triangulated Findings (cross-confirmed across ≥2 phases)

Each row was independently surfaced by A5 **and** at least one other phase **and** is anchored to raw evidence.

| # | Banking-grade signal | A5 ref | Other phases | Raw quote | Confirmed severity |
|---|---|---|---|---|---|
| T1 | Tipping-off prohibition is the highest-stakes regulatory pattern | E2-3/5/6, E3-9, R3, R12 | A1 §1.1 row 7; A2 §5 item 12; A3 §6.3; A4 §3.3 | 002:65-67 "we MUST NOT show anything that could be construed as tipping off" | **P1** |
| T2 | Audit trail mandatory for any state mutation or replace | E1-1, E1-2, E3-7, R7 | A1 §1.1 row 12; A3 §6.2; A4 §5.3 | 001:72 "We need an audit trail for any document replacement" | **P1** |
| T3 | NRIC + bank statement = high-grade PII | E1-4, I1-8, I1-9 | A1 §1.1 row 13; A2 §3; A3 §6.1 | 001:67-68 "NRIC, financial statement" | **P1** |
| T4 | 7-year retention default conflicts with abandoned-data lifecycle | E1-3, E1-6, E3-14, G1-13, G3-2 | A1 §3.3; A2 §3.2; A3 §1.5 | 001:74 "Retention: 7 years"; 003:115 "30 days for abandoned" | **P1** |
| T5 | Sanctions / AML / SAR vocabulary triggers T1-grade scrutiny | E2-1, E2-3, E2-8, E3-1, R4 | A1 §1.1 rows 3-8; A2 §7 item 11; A4 §5.3 | 002:24 "tightened sanctions screening"; 002:82 "suspicious activity report" | **P1** |
| T6 | Regulator named without citation = automatic P1 | E3-1, R4 | A1 §4.3; A2 §5 item 13; A3 §5.4 | 003:39 "MAS-AML-1A revision — Priya to forward exact citation" | **P1** |
| T7 | Legal absent on regulatory-touching scope = P1 governance gap | I1-7, I3-5, R5 | A2 §7 item 8; A3 §8 item 9; A4 §4.2 | 003:31 "Apologies: Legal — Sundar K." | **P1** |
| T8 | Dual/tiered approval = banking control requiring quorum audit | E3-7, E3-8, G3-1 | A1 §1.2 rows 26-27; A3 §6.2; A4 §2.7 | 003:89 "senior analyst + compliance officer dual approval" | **P1** |
| T9 | Customer-vs-internal dual-state model is forced by tipping-off | E2-2, I2-1, I2-4, R3 | A1 §0; A2 §3.3 conflict #3; A3 §2.2 | 002:99 "agent UI = same as back-office. customer UI = sanitized" | **P1** |
| T10 | Biometric integration requires security review before commit | E3-11, I3-13, G3-9 | A1 §1.1 row 15; A3 §5.5; A4 §4.2 | 003:105-106 "security review needed before integration" | **P1** |
| T11 | Data residency (SG region) is binding compliance constraint | E3-12 | A1 §1.1 row 10; A3 §6.3; A4 §3.7 | 003:108-109 "Acuant offers SG region — Priya confirmed acceptable" | **P1** |
| T12 | Idempotency on side-effect ops rarely stated, always required | E1-10, I2-2, I3-6, G1-2, G2-2, G3-10 | A3 §6.4; A2 §7 item 11 | 001:91 "Multiple re-uploads — limit how many times?" | **P1** for T1/T2 |
| T13 | Compliance Officer presence elevates input to ≥T2 minimum | E1-11, E3-16, §5 | A1 §3.4; A4 §3.3 | 001:72 Priya; 002:45 Mei; 003:25 Priya | **T2 floor** |
| T14 | Adverse media / PEP screening = T1 compliance | E3-3, E3-4, E3-6 | A1 §1.1 rows 5-6; A2 §3 | 003:57 "PEP screening"; 003:60-61 "Adverse media" | **P1** |
| T15 | Reversibility / compensating action required for funds movement | E2-7, I2-5 | A1 §1.2 row 18; A3 §6.4 | 002:74 "retrieved funds go back to originator bank" | **P1** for T1/T2 |
| T16 | State machine + per-transition audit = paired artifact | E2-10, I2-1, R7 | A1 §2.2 flow B; A3 §6.2; A4 §5.6 | 002:38 "compliance hold vs ops second-eye"; 002:87-89 | **P1** |
| T17 | Non-tipping safe phrasing requires Legal sign-off | E3-10, E2-11, R3, R12 | A2 §3.3 conflict #4; A3 §4.2; A4 §3.7 | 003:99 "generic 'in review' status"; 002:65 "need legal to bless" | **P1** |
| T18 | "Separate ticket / out of scope" hides live banking-grade obligation | R10, G1-13, G2-5, G3-6 | A2 §8; A3 §1.10; A4 §4.1 | 001:86 "Abandoned applications — separate ticket"; 003:154 parking lot | **P2** |

**Count**: **18 triangulated rows** (target ≥15). These define the **non-negotiable detection logic**.

---

## 2. Contradicted Findings

| # | Topic | A5 position | Contradicting phase | Resolution |
|---|---|---|---|---|
| C1 | Anonymous "N=3" comment severity | A5 I1-11 tags **P3** | A2 §3.1 #1 + §5 #23 treats as **P2**; A4 R5: "down-weight, flag for explicit attribution before treating as decision" | **Promote to P2**: anonymous + policy parameter = P2 automatic. |
| C2 | Tier 003 = "T1 by content" | A5 §5: escalate 003 to T1 | A4 supports T1; **A3 §3.3 frames 003 as multi-epic** — tier may be heterogeneous per epic | **Emit `inferred_tier` per epic, not per file**. Biometric + EDD-screening epics → T1; mobile follow-on → T2. |
| C3 | Audit fields for input 001 | A5 E1-2 lists fields as P1 audit | A2 §3.1 #3 calls "Compliance is happy" non-testable P2; A3 §4.1: r1 ACs need Gherkin conversion | **No real contradiction**: emit audit schema **AND** Gherkin scenario per transition. |
| C4 | PII inventory completeness in 001 | A5 G1-1 flags inventory P2 (incomplete) | A1 §1.1 row 13 + A3 §6.1: named PII is reliable | **Refine**: distinguish `pii_named` (high confidence) from `pii_inferred_missing` (require enumeration). G1-1 stays P2. |
| C5 | (Overlap) "regulated comms" — A2 P2 ambiguity vs A5 E2-4 P1 explicit | A5: P1 banking signal | A2 §5 #12: P2 pragmatic ambiguity | **Both fire**: one phrase can carry banking-grade + linguistic ambiguity flags. Don't deduplicate. |
| C6 | (Overlap) A5 I3-14 EOW = P2 audit risk vs A2 §5 #13 P3 | A5: P2 | A2: P3 generic; A3 §8 #14: emit open question | **Promote to P2** when relative-date is attached to a regulator-citation deliverable. Context lifts severity. |

**Net**: A5 is essentially aligned with the other phases — most "contradictions" are severity calibration, not direction-of-claim differences.

---

## 3. Gaps in A5 Noticed by Other Phases

| # | Gap | Surfaced by | Evidence | Recommended addition |
|---|---|---|---|---|
| G-A | Vendor `(?)` placeholder pattern as PII-processing risk | A1 §4.4; A2 §5 #10; A3 §5.5 | 003:78 "adverse media vendor (?)" | Detector: `vendor_unnamed → P1 if processes PII; P2 otherwise`. |
| G-B | "Anonymous (likely X)" attribution as policy-decision risk | A1 §4.4; A2 §7 #5; A4 R5 | 001:103 "Anonymous (likely Raj) — N could be 3" | Pattern: anonymous + policy-parameter = P2 (see C1). |
| G-C | Note-taker mediation as audit-confidence reducer | A3 §7.3; A4 R9 | 003:18 paraphrase admission | Mediated input → reduce confidence on quoted compliance statements; require verbatim verification for P1/P2. |
| G-D | Emoji-as-decision-signal on compliance topics | A2 §3; A3 §1.12; A4 §3.4 + R12 | 002:62/64 "👍" agreement on customer-facing language | 👍 from Compliance role on tipping-off/retention/customer-comms = soft endorsement, requires written sign-off (P2). |
| G-E | Anti-tipping-off vocabulary beyond sanctions | A1 §4.3; A2 §8 | A5 I2-12 mentions but doesn't promote | Treat *any* AML-related rejection (PEP, AM, fraud, SAR) as tipping-off-class. |
| G-F | Quantifier-without-quantity → audit-defensibility risk | A2 §5 #20-24 | 002:21 "a LOT"; 003:54 "most variable" | Unquantified banking-grade metric = P2 audit-defensibility gap. |
| G-G | Mobile parity = regulatory-parity gap | A1 §4.1; A3 §3.3; A4 §4.1 | 001:99, 002:107/161, 003:122 | A5 G1-11 marks P3. Promote: mobile deferral on regulated workflow = P2. |
| G-H | Compliance officer asserts policy without citation | A4 §3.3, §3.7 | 001:74 Priya "Retention: 7 years" (no citation); 003:115 "need to confirm with Legal" | Add symmetric pattern to "regulator named without citation" = P2 (binding without traceability). |
| G-I | State-machine ambiguity: same word, two meanings | A2 §5 #12; A3 §1.4; A4 §5.4 | 002:38 "compliance hold vs ops second-eye" — both called "on hold" | Elevate from §4 footnote to P2 audit-class signal (state machine without disambiguation = audit replay failure). |
| G-J | Affected-user voicelessness as banking-grade gap | A4 §4 voicelessness; A1 §0; A2 §3.3 | All 3 inputs: applicant/customer never speaks | No proxy → fairness/explainability gap, especially risk-engine routing (003). P2 minimum. |
| G-K | Calibration debt = audit + determinism dual issue | A1 §4.1; A2 §3.3 #5; A4 §3.5 | 003:91-93 "engine outputs not calibrated yet" | A5 I3-2 captures determinism; missing audit aspect (audit log must capture engine_version + calibration_date). |
| G-L | Tier-inference per epic vs per file | A3 §3.3; per C2 | 003 multi-epic | Emit tier per epic; extend R2. |

**Count**: 12 gaps, none catastrophic. Severity calibration and detector specificity, not foundational signal gaps.

---

## 4. Quality Assessment of A5

### 4.1 Strengths
- **Volume**: 43 explicit + 42 implicit + 40 gap = 125 signals (over-delivers).
- **Quote-anchored evidence throughout**: every row carries `file:line` + verbatim quote.
- **Severity calibration consistent** with A2's P1/P2/P3 taxonomy and A4's authority-mode framework.
- **§4 detection patterns are operational** (regex + structural + false-positive guards) — directly implementable.
- **Tier inference rule (§5) is compact and decidable** — maps cleanly to skill logic.
- **§6 default-vs-override contract is the strongest contribution**: "forced-evaluation output contract" YAML makes banking-grade detection a **forcing function** rather than a pattern matcher.
- **R1-R12 are concrete and testable** — each maps to a downstream artifact.

### 4.2 Weaknesses
- **Tier inference runs once per file** — for multi-epic 003 should be per epic.
- **§4 "false-positive guard" column is sparse**. Each non-negotiable should have ≥1 negative example.
- **Note-taker mediation not addressed** (G-C). Critical for 003.
- **Emoji-as-decision-evidence not handled** (G-D). Slack banking-grade decisions live in 👍.
- **No explicit T1-promotion threshold**. Recommend: ≥3 T1 indicators OR (regulator-cited + compliance-officer-directive) = T1.
- **No cross-reference to `epic-and-stories.template.md`** — the §6 YAML should map field-by-field.

### 4.3 Tier-escalation supportability

**002 → T1**: **Supported**. A1 (sanctions vocab), A2 (tipping-off modals), A3 (regulated comms), A4 (Mei rule-mode) all surface T1-grade content despite Slack format. Recommendation: escalate with R6 review note.

**003 → T1**: **Supported but conditional**. A4 confirms (regulator + dual approval + Compliance + Legal-absent P1). **A3 introduces multi-epic wrinkle**: T1 applies per epic — EDD-redesign + biometric → T1; mobile follow-on → T2.

**001 stays T2 with T1-shadow on retention+PII**: **Supported** — no regulator cited; PII + retention + Legal-absence warrant T2 floor.

### 4.4 R1-R12 consistency

All 12 A5 recommendations are **consistent** with A1-A4. No phase argues against any. **R5 (Legal/Security absence = P1) is the strongest convergence** — independently surfaced by A1, A2, A3, A4. Approved with C1-C6 reconciliations + G-A through G-L additions.

---

## 5. High-Confidence Banking-Grade Patterns (triangulated ≥3 ways)

CORE banking-grade detection logic. Each pattern is corroborated by **A5 + ≥2 other phases**, anchored to raw quotes, with deterministic skill behavior.

| # | Pattern | Detection (linguistic + structural) | Severity | Skill behavior |
|---|---|---|---|---|
| **P-01** | Tipping-off vocabulary lockdown | `tipping off`, `regulated comms`, `MUST NOT`, `can't tell the customer`, `generic message` + customer-facing comm change + Compliance speaker | **P1** | Emit `tipping_off_scan` + risk level; force non-tipping safe phrasing AC; block TL handoff until Legal sign-off captured. |
| **P-02** | Regulator named without citation | `[A-Z]+-[A-Z]+-[A-Z0-9-]+` AND no attached document AND no URL | **P1** | Open question with `dependency: regulatory_citation`; block TL handoff. |
| **P-03** | Compliance officer + AML/sanctions/EDD/SAR/PEP vocabulary | Speaker role = Compliance; content includes any AML/sanctions/EDD/SAR/PEP/adverse-media term | **T1 trigger** | Auto-escalate tier to T1; run all T1 mandatory rows. |
| **P-04** | PII direct identifier mentioned | `NRIC`, `passport`, `national ID`, `biometric`, `bank statement`, `source of funds`, `DOB`, `account number` | **P1** | Emit `pii_inventory` row with retention/residency/masking/access-audit; T1 refuses without enumeration. |
| **P-05** | Audit-trail directive from compliance | Speaker = Compliance + `audit trail`, `track who/when/what`, `for audit reasons`, `retention X years` | **P1** | Emit per-transition audit-event schema (event, actor, ts, before, after, reason, idem_key) + Gherkin replay scenario. |
| **P-06** | Dual / tiered approval | `dual approval`, `senior + compliance`, tiered routing (`low/med/high`) | **P1** | Emit quorum audit schema (two linked audit events); identify named senior approver; flag P2 if unnamed. |
| **P-07** | State machine without disambiguation | Same lexical term used for ≥2 distinct states by ≥2 speakers | **P1** | Emit state-machine artifact; force per-state name disambiguation + per-transition audit. |
| **P-08** | Customer-vs-internal dual UI surface | `customer UI`, `agent UI`, `back-office`, `sanitized` + tipping-off context | **P1** | Force AuthZ role matrix; audit privileged view access; AC: customer surface contains no regulated terminology. |
| **P-09** | Reversibility for funds/data mutation | Replace / archive / delete / return-funds operation | **P1** | Force `compensating_action`; if irreversible, emit `human_queue` policy AC + escalation owner. |
| **P-10** | Idempotency on side-effect | Any state-change notification, replace op, screening re-run, vendor call | **P1** for T1/T2 | Force `idempotency_key` strategy + Gherkin replay test. |
| **P-11** | Data residency hard rule | `SG region`, `data residency`, `EU region`, `local storage` adjacent to Compliance utterance | **P1** | Force `residency` field on PII inventory; block vendor selection without residency match. |
| **P-12** | Vendor processing PII without name / DPA | Vendor processes PII/biometric; vendor unnamed (`(?)`) or DPA not referenced | **P1** | Block vendor integration AC; emit P1 open question with `dependency: vendor_dpa` + `dependency: vendor_name`. |
| **P-13** | Biometric / new sensitive surface | `biometric`, `liveness check`, `face match`, `fingerprint` | **P1** | Force `security_review_status` field; block integration AC until spike closed. |
| **P-14** | Legal absent on regulatory-touching content | Legal not in attendees AND (tipping-off | retention | sanctions | customer-comms-language | biometric | regulator-cited) | **P1** | Emit governance gap; block formal sign-off; recommend Legal scheduling before TL handoff. |
| **P-15** | Compliance asserts policy without citation | Speaker = Compliance; declarative; no policy doc URL/attachment | **P2** | Emit `dependency: policy_doc_attachment`; conditional acceptance pending citation. |
| **P-16** | Anonymous comment on policy parameter | Speaker = Anonymous; content sets numeric policy threshold (N, retention days, score) | **P2** | Down-weight; require named owner before treating as decision. |
| **P-17** | "Separate ticket / out of scope" with live obligation | Deferral language + abandoned-data / partial PII / SAR workflow / migration / cross-border topic | **P2** | Emit `deferred_compliance_risk` flag; require explicit risk-acceptance owner. |
| **P-18** | Regulatory-parity gap (mobile deferred) | Mobile deferred on workflow touching PII/tipping-off/sanctions | **P2** | Emit regulatory-parity question; force acceptance that regulated obligations apply on both surfaces or document exemption. |
| **P-19** | Calibration debt on risk routing | Threshold (`>=0.75`) + qualifier ("not calibrated yet") | **P1** determinism + audit | Audit schema must capture `engine_version` + `calibration_date`; block hard threshold acceptance pending evidence. |
| **P-20** | Emoji-only decision on compliance topic | 👍/✅/+1 as sole agreement on tipping-off/retention/customer-comms decision | **P2** | Emit `formal_signoff_pending`; convert to open question. |

**Count**: **20 high-confidence patterns**, each triangulated. These are the **foundational detection logic** for the skill's banking-grade field — implementable as regex + speaker-role + structural-location rules with deterministic behaviors.

---

## 6. Concluding Notes — Foundation for Skill Banking-Grade Logic

A5 is **substantially correct and operationally usable** as the foundation for the banking-grade field. The 18 triangulated findings, 6 contradictions, 12 gaps, and 20 high-confidence patterns are the actionable cross-validation residue.

**Three structural decisions emerge from triangulation that A5 alone did not explicitly state**:

1. **Tier inference runs per emitted epic, not per raw file** (forced by A3's multi-epic framing of 003). A5's tier rule remains correct; the loop boundary changes.
2. **A single phrase can carry multiple flag types** (banking-grade + linguistic ambiguity + stakeholder-mode). The skill must not deduplicate across detectors — each phase contributes a different facet (A5: regulatory force; A2: linguistic shape; A4: speaker authority mode).
3. **Banking-grade detection is half pattern-matching, half forcing function**. A5 §6 captures this; reinforced by A3 §6.4 (idempotency/reversibility "rarely stated, always required") and A4 R3 (scope-to-stakeholder gap detection). The skill's value is mostly in **forcing fields to be filled or explicitly declared n/a**, not in keyword matching alone.

The **single highest-leverage rule** across the entire analysis: **`Legal absent + regulatory content = P1 governance gap`** — triangulated by A1, A2, A3, A4, and A5 independently, with raw evidence in all three inputs. This is the canonical "always-fires" detector.

---

*End of Phase B5 Cross-Validation. Output feeds Phase C distillation and skill banking-grade field design.*
