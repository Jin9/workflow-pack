# Phase B2 — Cross-Validation of A2 (Linguistic Forensics)

> **Validator**: B2 Cross-Validation Specialist
> **Under review**: `phase-a2-linguistic-analysis.md`
> **Cross-references**: A1 (Domain), A3 (Structural), A4 (Stakeholder), A5 (Banking-Grade)
> **Method**: Quote-anchored triangulation; quality scored; high-confidence patterns promoted to R6 defaults.

---

## 1. Triangulated Findings — A2 Confirmed by 1+ Others

| # | A2 claim | Corroborators | Strongest corroborating quote | Agree |
|---|---|---|---|---|
| 1 | Jira detectable from `[PROJECT-NNNN]` | A1, A3 | A1: "Ticket IDs: `PROJECT-NNNN`…`LOAN-2847`" | 3-way |
| 2 | Slack detectable from `Name (Role) — Today HH:MM` | A1, A3 | A3: "Relative timestamps ('Today HH:MM')" | 3-way |
| 3 | Meeting notes via `Attendees:` + `[Apologies:]` + numbered agenda | A1, A3 | A3: "Attendee block with explicit absences" | 3-way |
| 4 | Emoji is decision-bearing (`👍` = acceptance) | A1, A3, A4 | A4: "Decisions made by 👍 reaction" | 4-way |
| 5 | "Compliance is happy" (001:57) is non-testable | A1, A3 | A3: "`Compliance is happy`…is non-testable" | 3-way |
| 6 | "replaced (or maybe kept as version? unclear)" = self-contradicting AC | A1, A3, A5 | A1: "Versioning vs replacement…flagged unclear" | 4-way |
| 7 | "N could be 3" (anonymous) = low-confidence policy decision | A1, A4, A5 | A4: "flag for explicit attribution before treating as decision" | 4-way |
| 8 | Tipping-off / `MUST NOT` is binding regulatory rule | A1, A4, A5 | A4: "directive uppercase modals for binding rules" | 4-way |
| 9 | "EOW" is ambiguous; note-taker self-flags | A1, A3, A5 | A5: "EOW ambiguity = traceability risk" | 4-way |
| 10 | Modal hedges cluster as deferred-decision markers | A3, A4 | A3: "hedged language as deferred-decision marker" | 3-way |
| 11 | Placeholder tokens (`X req/min`, `$Xk`, `(?)`, `N`) are P2 default | A1, A3, A5 | A1: "Money placeholders ($Xk) as TBD" | 3-way |
| 12 | Pronoun ambiguity is the Slack failure mode | A1, A3 | A3: "Pronoun ambiguity…must resolve antecedents" | 3-way |
| 13 | "Need legal to bless the language" = Legal-engagement gap | A1, A4, A5 | A4: "Legal absent in 3/3 banking inputs" | 4-way |
| 14 | Mobile scope = canonical underspecified zone | A1, A3, A4, A5 | A1: "Always declared, rarely resolved" | 5-way |
| 15 | Retention duration is a recurring conflict | A1, A3, A5 | A1: "always cited but rarely tied to a written policy" | 4-way |
| 16 | "Story (but might need to be Epic — too big?)" = split signal | A1, A3 | A3: "this is itself the strongest split signal" | 3-way |
| 17 | Jira AC content lives in comments, not in AC block | A1, A3 | A3: "decisions emerge across multi-day comment exchanges" | 3-way |
| 18 | Meeting notes paraphrased — reduce confidence | A1, A3, A4 | A4: "treat statements as paraphrase unless explicitly quoted" | 4-way |

Eighteen rows triangulated; sixteen at 3-way+. A2's source-type classifier and its strongest ambiguity classes (modal, placeholder, anonymous attribution, pronoun, retention/mobile, paraphrase) are robustly corroborated.

---

## 2. Contradicted Findings — A2 vs A1/A3/A4/A5

| # | A2 position | Conflict | Resolution |
|---|---|---|---|
| C1 | §5 #1 calls Jira label `urgent` (001:28) **Lexical P3** | A1 §1.1 / A3 §7.1: established Jira label vocab in metadata block | Demote to metadata-assumption ("no SLA tied to label `urgent`"), not lexical ambiguity |
| C2 | §5 #3/#15 treat "additional review" / "rare deep-dive" as lexical/pragmatic ambiguity | A1 §1.2 + A5 E2-4/E2-13: deliberate tipping-off-compliant compressions, regulator-mandated vagueness | New tipping-off-language class: R6 does not disambiguate; require Legal sign-off on exact string |
| C3 | §6.3 scores meeting notes **5.5 (highest)** for BA-readiness | A3 §3.3 + A5 §5: r3 is multi-epic (5-6 epics), T1 by content (46 signals vs 39/40) | Apply scope+tier penalty: high readability ≠ BA-readiness for multi-epic T1 brief with Legal absent |
| C4 | §5 #29 calls Priya's "should NOT just be deleted" a modal ambiguity (should where must is required) | A4 §3.3 + A5 E1-4: compliance directives are rule-mode (binding); P1 PII rule | Authority-mode override: compliance-officer "should" in regulatory context = rule-grade |
| C5 | §4.3 lists Aisha's "Sigh" as **disagreement / pushback** | A4 §5.7: note-taker editorial aside = meta-stakeholder confidence-reducing signal | Add speech-act class `meta-aside` / `note-taker editorial`, distinct from disagreement |

Contradictions are about lens / weight / category, not fact. No A2 claim is factually overturned.

---

## 3. Gaps in A2 Noticed by Others

**3.1 Structural ambiguities A3 caught**: (a) attachments referenced-not-attached — A3 §1.5 + A5 G1-8 flag `support-call-analysis…xlsx`, `compliance-data-retention-policy-v3.2.pdf`, David's slides; A2 §2.1 scored attachments "LOW" without flagging the unresolved-reference class. (b) State-transition obligations — A3 §6.4 + §8 #17 treat each state (review/approved/rejected/hold) as implying a notification AC, audit emission, and tipping-off check; A2 stays at lexical/modal level. (c) Compound-clause meeting-note ACs — A3 §4.3 calls out that "0.75 threshold, but engine not calibrated…2 cycles" packs decision + dependency + caveat; A2 catches the uncertainty (§3.2 #4) but not the compound-clause shape. (d) Closed vs active "Relates to" links — A3 §7.1 separates LOAN-2401 (closed, context) from active dependency; A2 flat-scores the block "MEDIUM".

**3.2 Speech-act patterns A4 caught**: (a) authority mode per utterance (A4 §3.3 / §6) — rule mode (compliance MUST NOT, binding) vs proposal mode (compliance suggests threshold, negotiable); A2's flat categories drive C4. (b) Deference as authority signal (A4 §3.2) — `@Priya — can we delete…`, "Mei would know better" (002:35) assign authority to addressee; A2 keeps surface text only. (c) Sponsor-grade approval (A4 §3.4) — "yes go ahead. priority is high" (002:148) is explicit go-ahead, not a peer commitment; A2 lumps under Promises. (d) Cross-role override (A4 §3.5) — Jamie's calibration push-back overrides compliance proposal on data-feasibility; A2 §4.3 sees only disagreement. (e) Diffuse/unnamed speakers (A4 §6) — Marketing (001:47), adverse-media vendor `(?)` (003:77); A2 has no class for institutional/unnamed speakers.

**3.3 Implicit banking signals A5 caught that A2 did not class as ambiguity**: idempotency / reversibility almost-never-stated (A5 I1-1, I2-2, I3-6) — A2 catches re-upload-limit symptom, not idempotency as a class; AuthN/AuthZ implicit role-matrix gaps (A5 G1-3, G1-4, G2-9) — no A2 entries; calibration debt as determinism class (A5 I3-2) — A2 surfaces the threshold, misses the routing-determinism risk; regulator named without citation = P1 (A5 R4 + E3-1) — A2 marks `MAS-AML-1A` P2 placeholder, A5 escalates on regulatory consequence; tipping-off scope completeness (A5 G2-8) — A2 lists tipping-off occurrences, misses the absence of PEP/adverse-media coverage in 002; notification matrix per transition (A5 I2-2) — A2 catches "yes" binding two questions (§5 #18) but not the broader matrix obligation.

---

## 4. Quality Assessment of A2

**Comprehensiveness: 8.5 / 10.** A2 exceeded the 15-item ambiguity target (30 delivered), shipped speech-act inventories with 5+ examples per category per source, and produced 15 skill-design implications. Points deducted for the banking-grade-as-ambiguity blind spot and the missing authority-mode dimension.

**Accuracy of A2's quality scores**:

| Input | A2 composite | Validator view | Holds? |
|---|---|---|---|
| r1 Jira | 4.8 | A1+A3+A5 consistent; ground truth matches | Yes |
| r2 Slack | 3.5 (worst) | A1: "👍 risky from BA perspective"; A3/A5 confirm AC-synthesis burden | Yes |
| r3 Meeting | 5.5 (best) | A3+A5: scope=multi-epic, tier=T1, Legal absent P1 — rank correct, absolute too high | Partial — needs scope/tier weighting |

Specificity and Consistency are well-grounded. Completeness under-weights structural completeness (Q1-Q6 are partial answers). BA-readiness does not factor scope/tier — the C3 contradiction.

**Strongest contributions**: (1) source-type fingerprinting (§1) — 3-way confirmed, directly seeds the dispatcher; (2) §5 ambiguity catalog — 30 P1/P2/P3-tagged quoted entries, R6-ready; (3) §7 #1-15 — concrete tokenizers, source-aware filtering, scorecard contract.

**Weakest areas**: (1) no authority-mode tagging on speech acts (drives C4); (2) banking-grade-as-ambiguity blind spot — A5 lists 42 implicit + 40 gap signals A2 did not classify; (3) BA-readiness without scope/tier penalty (the r3 = 5.5 score is misleading once you know it is 5-6 epics + T1 + Legal absent).

### 4.5 Recommendation — patterns to enshrine in R6

Twelve triangulated patterns mapped to the P1/P2/P3 ladder: modal-verb scanner (P2; compliance-speaker override → P1); placeholder-token detector (P2; P1 if attached to a regulator name); quantifier-without-quantity (P3; cluster > 5 → completeness penalty); anonymous/weak-attribution detector (P2 on decision); emoji-as-speech-act recognizer (auto-emit "Confirm written sign-off from {role}"); pronoun scanner across sentence boundaries; relative-time normalizer (`EOW, today, in 3 weeks`); compliance-rule-mode detector (override soft textual modals); self-contradicting AC detector (P2); compound-clause splitter for meeting-note ACs; attachment-not-attached detector (P2; P1 if regulatory/PII policy); stakeholder-gap auto-emitter for Legal/Security/CS/Mobile/Data per A4 §4.2.

---

## 5. High-Confidence Ambiguity Patterns (Triangulated 3+ Ways)

DEFAULT detection patterns. "Phases" column lists corroborators (3-way+ minimum).

| # | Pattern | Detection signal | Sev. | Example | Phases |
|---|---|---|---|---|---|
| HC1 | Self-contradicting AC | Parenthetical aside negates main clause (`or maybe…?`, `(unclear)`) | P2 | "replaced (or maybe kept as version? unclear)" (001:55) | A2/A1/A3/A5 |
| HC2 | Anonymous policy decision | Author "Anonymous"/"likely X" + numeric or policy default | P2 | "Anonymous (likely Raj) — N could be 3" (001:103) | A2/A1/A4/A5 |
| HC3 | Compliance directive, rule mode | Compliance-role speaker + uppercase modal (`MUST NOT`/`CAN'T`) or `regulated`/`tipping-off` | P1 AC-grade | "we MUST NOT show anything…tipping off" (002:65) | A2/A1/A4/A5 |
| HC4 | Regulator named without citation | `MAS-XXX`, `OFAC-XXX` appears with no document attached | P1 | "MAS-AML-1A revision — Priya to forward exact citation" (003:38) | A2(P2)→A5 P1, A1, A3 |
| HC5 | Modal-hedged commitment | PM/Eng + cluster `probably/maybe/might/ideally` in commitment utterance | P2 | "agent UI changes might slip a sprint" (002:155) | A2/A1/A3/A4 |
| HC6 | Quantifier-without-quantity | `a LOT, some, most, multiple, rare` without adjacent numeric | P3 (cluster→penalty) | "getting a LOT of escalations" (002:21) | A2/A1/A3 |
| HC7 | Placeholder token | `(?), X req/min, $Xk, N attempts, TBD, ???`, single-cap in numeric slot | P2 (P1 if regulator/PII vendor) | "adverse media vendor (?) rate-limited at X requests/min" (003:78) | A2/A1/A3/A5 |
| HC8 | Mobile-vs-web deferral | "mobile" + `separate sprint / web first / Q4 follow-on` without Won't-Have | P2 | "web first, mobile follow-on in Q4" (003:122) | A2/A1/A3/A4/A5 |
| HC9 | Relative-date opacity | `EOW, by next session, in 3 weeks, Today` not resolvable against metadata date | P2 action-item / P3 else | "[unconfirmed if EOW = this or next week]" (003:43) | A2/A1/A3/A5 |
| HC10 | Emoji-only decision | `👍 / ✅ / 🙏` as sole affirmation on compliance-touching decision | P2 (force written-sign-off Q) | "👍 with caveats — need legal to bless the language" (002:64) | A2/A1/A3/A4 |
| HC11 | Pronoun with domain antecedent | `this, it, they, that, same thing` requiring domain knowledge | P3 (P2 if in AC) | "that's regulated comms" (002:46) | A2/A1/A3 |
| HC12 | Compliance ≠ Legal gap | Compliance present, Legal absent, scope touches retention/PII/customer-comms | P1 | "[Apologies: Legal — Sundar K.]" (003:31) | A2/A1/A4/A5 |
| HC13 | AC vs comment-thread conflict | Jira AC says X; later compliance/eng comment says Y; never reconciled | P2 | AC :54 "replaced" vs Priya :77 "archived" | A2/A1/A3/A5 |
| HC14 | Notification matrix gap | State machine introduced; notification policy partial across transitions | P2 | "do we email them? push notif?" → "hm. probably yes" (002:130) | A2/A3/A5 |
| HC15 | Attachment referenced not attached | Filename in text with no active link | P2 (P1 if regulatory/policy doc) | "compliance-data-retention-policy-v3.2.pdf (referenced…not attached)" (001:115) | A1/A3/A5 (A2 gap) |
| HC16 | Calibration-debt threshold | Numeric threshold against uncalibrated model; multi-cycle calibration cited | P1 determinism | "score >= 0.75…engine outputs not calibrated…2 cycles" (003:90) | A2/A1/A3/A5 |

Sixteen patterns triangulated 3+ ways, each quote-anchored and severity-tagged — R6's default rule set.

---

## 6. Closing Note for Phase C

A2 is a strong artifact — comprehensive on surface forms and excellent on source-type fingerprinting. Its weaknesses are downstream: under-weighted authority mode (A4 fills), banking-grade obligations unclassed as ambiguities (A5 fills), structural gaps like attachments-not-attached and notification matrices (A3 fills). The sixteen §5 patterns are safe to enshrine; the five C-row contradictions imply small rubric adjustments (authority-mode override, regulated-vagueness class, scope/tier penalty, meta-aside speech-act). Phase C should adopt A2's catalog as the spine, layer A4 authority-mode and A5 banking-grade-as-ambiguity on top, and add A3 structural-gap detectors as horizontal passes.

— End of Phase B2 Cross-Validation of A2 —
