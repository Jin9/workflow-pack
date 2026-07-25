# Phase B3 — Cross-Validation of A3 (Structural Pattern Detector)

> **Role**: Cross-Validation Specialist (B3)
> **Primary**: `audit/phases/phase-a3-structural-analysis.md`
> **Cross-refs**: A1 (Domain), A2 (Linguistic), A4 (Stakeholder), A5 (Banking-Grade)
> **Inputs**: `inputs/raw-request-001|002|003.md`; target shape: `epic-and-stories.template.md`
> **Quote convention**: `{file}:{line}` — `r1`, `r2`, `r3`, `a1..a5`, `tpl`.

---

## 1. Triangulated Findings

A3 claim is "triangulated" when at least one **other** phase confirms it independently.

| # | A3 Claim | Confirmed by | Evidence |
|---|---|---|---|
| 1 | Source types are deterministically distinguishable from header markers — Jira (key:value), Slack (channel + `Today HH:MM`), Meeting (banner + agenda) (A3 §1.1, §7) | A2 §1.1-1.3 | A2:13 "Jira (0.97)"; A2:27 "Slack (0.96)"; A2:39 "Meeting (0.98)"; A2:50 "detectable from first ~30 lines" |
| 2 | r3 `[Apologies: Legal — Sundar K.]` is a stakeholder-gap signal embedded in metadata (A3:22) | A4 §1.3; A5 §3c | A4:185 "Legal absent in 3/3"; A5:188 "G3-3 Legal absent — governance P1" |
| 3 | r1 `## Acceptance Criteria` is the weakest AC location — most ACs live in comments (A3 §1.3, §4.1) | A2 §2.1 | A2:75 "AC block is the shortest and weakest part … most content buried in comments" |
| 4 | r2 has **no** AC section; ACs must be synthesised from Tom's enumeration r2:84-92 (A3 §4.2) | A2 §2.2; A4 §1.2 | A2:90 "the ask … crystallises only in Tom's line 84-92 recap" |
| 5 | Emoji `👍` (r2:62, 63, 163) function as decision-acceptance speech acts (A3 §1.12, §7.2) | A2 §4.2; A4 §3.4 | A2:88 "👍 functioning as decision acceptance"; A4:245 "Decisions made by 👍 reaction" |
| 6 | r1 story boundaries align with named stakeholder concerns (Priya/Mike/Raj) (A3 §2.1) | A4 §1.1; A1 §2.3 | A4:18 "Priya … audit + retention"; A4:21 "Raj … feasibility / constraints" |
| 7 | Tom's enumeration `1…2…3…4…` is the spine of r2's story inventory (A3 §2.2) | A2 §2.2 | A2:84 "Tom's recap (4-point list) — HIGH" |
| 8 | r3 is multi-epic (5-6), not single-epic (A3 §3.3) | A2 §6.3; A5 §5 | A2:343 "multi-epic (5-6 epics)"; A5:246 "T1 by content (manual label T2)" |
| 9 | Dependency taxonomy needs `blocks`, `temporal_deadline`, `regulatory`, `vendor`, `cross_team`, `data_maturity` (A3 §5) | A1 §3.2; A5 §1c | A1:368 "MAS-AML-1A citation"; A5:67 "Vendor SLA … P95 <2s" |
| 10 | Compliance commenters = authoritative locus for PII/audit/regulatory ACs (A3 §6.1-6.3) | A4 §5.3; A5 §4 | A4:212 "Compliance (rule mode — MUST/can't) → binding"; A5:212 "Compliance Officer commenter → T2 minimum" |
| 11 | Idempotency + reversibility almost never stated; must be inferred (A3 §6.4, §8.5) | A5 §3 gaps | A5:152 "G1-2 Idempotency of re-upload undefined"; A5:171 "G2-2 Notification idempotency missing" |
| 12 | "Intentional Issues for R6 to Catch" block must be stripped (A3 §1.13, §8.2) | (Unique to A3; corroborated negatively — no other phase warns the parser.) | r1:137-181, r2:170-217, r3:167-221 are harness annotations |
| 13 | Hedged modals (`maybe`, `probably`, `(?)`) signal deferred decisions → Open Questions (A3 §8.18) | A2 §5 items 25-30 | A2:351 "Tokenize and flag modal verbs … `may, might, could, should, probably, maybe`" |
| 14 | Confidence weighting differs per source — meeting = paraphrase risk, Slack = pronoun ambiguity, Jira = cleanest (A3 §8.16) | A2 §6; A4 §5.7 | A2:329 "Slack (3.5) < Jira (4.8) < Meeting (5.5)"; A4:262 "treat statements as paraphrase" |
| 15 | r1 `Type: Story (but might need to be Epic — too big?)` is itself the strongest split signal (A3 §2.1) | A2 §3 item 8 | A2:280 "self-questioning declaration"; A1:269 "Product cleanliness vs ticket reality" |
| 16 | Anonymous attribution (r1:103-104) must be flagged (A3 §7.1, §8.11) | A2 §5 item 5; A4 §3.6 | A4:163 "weak weight"; A2:354 "flag if it touches a decision" |
| 17 | NFRs scatter across context/vendor/eng-voice; collect into one epic-level cluster (A3 §6.5, §8.13) | A1 §3.2; A5 §1c | A1:226 "p95 < 7d, P95 <2s, 99.9% uptime"; A5:64 "EDD cycle <7 days at p95" |
| 18 | Parking Lot (r3:151-157) is a future-epic seed for `tpl:67-73` Out-of-Scope Deferred (A3 §1.10, §8.15) | A2 §2.3 | A2:105 "Parking Lot … out of scope"; r3:151-157 future-epic seeds |

(18 rows; ≥15 required.)

---

## 2. Contradicted Findings

| # | A3 Position | Counter-evidence | Resolution |
|---|---|---|---|
| C1 | A3 §3.2: r2 = "1 epic, ~5-6 stories" | A5:248 puts r2 at "T2 borderline T1 — recommend escalate" (tipping-off + SAR + sanctions stack). At T1, scope splits into 2 epics (customer-comms vs back-office/agent). | Claim is too crisp — should be tier-conditional. Skill emits `epic_split_recommendation` when T1 escalation is plausible. |
| C2 | A3 §2.1: r1 = 5 story candidates + 2 deferred | A5 §3a adds 5 banking-grade-specific candidates (G1-2 idempotency, G1-3 authN, G1-4 authZ on archived-doc retrieval, G1-5 audit schema, G1-6 revert window) that A3 treats only as concerns *inside* stories. | A3 conflates banking-grade concerns with story bodies. In T1 these are independent stories; parser emits concerns as **embedded ACs** or **separate stories** based on tier. |
| C3 | A3 §8.7: stakeholder-as-boundary "in r1 gives the right answer" | A4 §1.1 also lists Marketing (r1:47), Mobile team (r1:98-99), BA team (r1:108) — stakeholders that are **not** stories. | Right but incomplete. Filter: stakeholder-as-boundary AND topic-introduces-≥1-AC. |
| C4 | A3 §3.3: r3 multi-epic (5-6) | A2 §6.3 warns "structure too clean masks unresolved gaps"; a meeting with a narrow agenda yields one focused epic. | Refine to "multi-epic only if ≥3 distinct workstreams *each* introduce ≥2 ACs". Avoids over-fragmentation. |
| C5 | A3 §1.13: never read intentional-issues annotations | A1/A2/A4/A5 do not warn the parser; they silently use the block as ground truth. | A3 correct and unique. Elevate §1.13 to a **hard preprocessing rule** — absence of this guard causes production failures. |
| C6 | A3 §4.1: r1 ACs "rewritten" into Gherkin in-place | A4 §5.1 — PMs are high on priority, low on feasibility. Sarah's AC bullets (r1:53-56) need *replacement* when Priya's compliance comment (r1:74-78) contradicts them. | When an AC and a compliance rule-mode comment conflict, **comment wins**. Original AC becomes "Assumption Overridden" with both `source_quote`s. |

---

## 3. Gaps in A3 Noticed by Other Phases

**3.1 Section types A3 missed but A2 caught**

- **Note-taker bracketed asides** (`[unconfirmed if EOW = …]` r3:43; `Aisha (me!) … Sigh.` r3:146-147). A3 §7.3 treats as noise; A2:48 classifies as "confidence-reducing signals … should be preserved".
- **Modal-density region** as an implicit section (A2 §5 catalogued 30 items; A2:315 "ambiguity load is the dominant linguistic feature").
- **Capitalised intensifier** as a deontic marker (`a LOT` r2:21; `MUST NOT` r2:65) — A2:300, A2:309.
- **Embedded mid-sentence speaker attribution** as a meeting-notes idiom (`Hua: Acuant API can do…` r3:73) — A2:46.

**3.2 Story boundaries A3 missed that A4 caught**

- **Vendor-liaison story** in r3 — Hua's section (r3:100-108) is treated by A3 §2.3 as cross-cutting only; A4 §1.3 supports promoting Acuant integration to its own story.
- **Risk/Data calibration story** in r3 — Jamie's pushback on Priya's 0.75 (r3:91-93) becomes an independent data-readiness story (A4:285).
- **Originator-bank-return** workflow as a story in r2 — A3 §1.10 puts it in parking-lot reasoning; A4:44 calls out the missing protocol owner.
- **Note-taker / BA-brief author** workflow (Aisha owns brief production) — A4:56.

**3.3 Banking-grade structural locations A3 missed that A5 caught**

- **Header `Labels: …urgent`** (r1:28) as a banking-grade feed — A2:269 "`urgent` … unbacked by SLA".
- **Implicit PII inventory** — A3 §6.1 lists surface terms (NRIC, passport); A5:152 forces full enumeration (name/address/photo/applicant-ID).
- **Dual-approval audit schema** as its own location — A5:188 "G3-1 … two events with quorum semantics" beyond A3 §6.2's single-event pattern.
- **State machine ↔ audit emission mapping** — A5:104 "State machine = audit surface (4 states, transitions need events)". A3 §1.4 catches the comment thread but not the per-transition emission contract.
- **Vendor DPA absence** when vendor processes PII — A5:191 "G3-5 … Acuant processes ID + biometric"; A3 §1.11 only logs the Vendor section.

---

## 4. Quality Assessment of A3

**Comprehensiveness**: High on section-type inventory (13 types), dependency taxonomy (7 subtypes), source-type parsing (§7.1-7.3). Medium on banking-grade locations (idempotency emission underspecified). Low on tier-conditioned epic-splitting (see C1).

**Accuracy vs ground truth**: r1 (1 epic + 5 stories + 2 deferred), r2 (1 epic + 6 stories + 2 OoS), r3 (multi-epic 5-6) — all match A3's calls. Banking-grade signal completeness moderate — A3 §6 covers ~40 of A5's 125 signals; expected since A3 is structural.

**Top 3 strongest**: (1) §1.13 + §8.2 — ground-truth annotation stripping rule (unique safety rule); (2) §7.1-7.3 — source-type parser dispatch (corroborated by A2 0.96-0.98 confidences); (3) §8.1 + §8.8 — single-vs-multi-epic scope detection with explicit signals.

**Top 3 weakest**: (1) §3.2 single-epic claim for r2 (C1); (2) §6.4 idempotency/reversibility underspecified — A5's forced-evaluation contract (A5:283-292) is missing; (3) §8.7 stakeholder-as-boundary needs the substantive-concern filter (C3).

**Recommendation**: Adopt A3 §7 as the **primary dispatcher**, augmented with: (1) hard pre-flight strip of `## Intentional Issues for R6 to Catch`; (2) tier-conditional epic splitting (emit `scope_kind` + `epic_split_recommendation` on plausible T1 escalation, A5:253-260); (3) **forced-evaluation banking-grade rows** per A5 §6 — A3 catches locations, A5 forces fill-or-explain on every story.

---

## 5. High-Confidence Parsing Patterns (Triangulated)

| Source type | Detection signals | Parser strategy | Story-boundary rule |
|---|---|---|---|
| `jira` | Bracketed key `[A-Z]+-\d+` in title; key:value header (`Project:`, `Type:`, `Priority:`, `Reporter:`, `Sprint:`, `Labels:`, `Created:`); ASCII rules `────`; sections `## Description / Acceptance Criteria / Comments / Linked Issues / Attachments`; comment headers `**Name (Role) — YYYY-MM-DD HH:MM**`. | Header → key:value map; `## Description` → problem + trigger; `## AC` → **draft** ACs (low testability); `## Comments` chronologically, tag by role (Compliance/Eng/PM/Support); `## Linked Issues` → typed dependency edges; strip everything after `## Intentional Issues for R6 to Catch`. | Each named-stakeholder concern that introduces ≥1 distinct AC = candidate story; self-questioning `Type:` field = epic-promotion signal; author handoff line ("may need to split") = explicit split confirmation. |
| `slack` | `#channel — Slack channel` banner; speaker `Name (Role) — Today HH:MM`; standalone emoji (`👍`, `😅`, `🙏`); `📎 Linked:` lines; `[Thread reactions: N 🙏 …]` footer; chat register (lowercase, `fwiw`, `fyi`). | First message = trigger; mid-thread enumeration (`ok let me draft. so the asks are roughly: 1…`) = story spine; final exchange ("let me write this up" / "yes go ahead") = ownership handoff; preserve emoji as decision-acceptance acts; resolve pronouns within ≤5-message window; flag every `👍` on a compliance topic as needing formal sign-off. | Each `1.` `2.` `3.` item in the spine = candidate; each late participant with a scope question = candidate; mobile-parity question + phased prioritisation answer = deferred story. |
| `meeting-notes` | `========` banner rules; metadata block (`Meeting:`, `Date:`, `Time:`, `Note-taker:`, `Attendees:`, `[Apologies: …]`); numbered agenda `## 1. … ## 8.`; time-boxed `(Speaker, N min)`; bracketed `[Owner] task — due`; note-taker meta-asides. | Parse attendees; auto-emit `[Apologies: Legal]` as **P1 stakeholder gap** when scope is regulatory; treat numbered agenda sections as candidate epics; each `### 3X.` sub-section = candidate story; `## Open Questions` → explicit P2/P3; `## Action Items` → deliverable + owner + normalised date; `## Parking Lot` → Out-of-Scope Deferred; mark all statements `attribution_confidence: paraphrase`. | Each `### 3X.` sub-section = at least one story; promote to epic when it adds vendor / migration / security spike; `## Vendor Discussion` is cross-cutting *and* a story candidate; `## Open Questions` items are NOT stories. |
| `doc` (fallback) | None of the above match. | Extract problem → constraints → decisions in order of appearance; emit `ba_confidence: low`; require human checkpoint before TL handoff (A2 §7 item 15). | Stakeholder-concern heuristic only; default to single-story; emit split recommendation if ≥4 distinct workstreams detected. |

---

*End of Phase B3 validation — feeds Phase B parser design and Phase C output mapping.*
