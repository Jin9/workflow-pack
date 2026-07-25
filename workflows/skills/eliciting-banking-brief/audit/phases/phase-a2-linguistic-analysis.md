# Phase A2 — Linguistic Forensics Analysis

**Auditor**: Linguistic Forensics Specialist, BA Skill Factory
**Inputs analyzed**: `raw-request-001.md` (Jira), `raw-request-002.md` (Slack), `raw-request-003.md` (Meeting notes)
**Purpose**: Surface the linguistic patterns, ambiguity sources, and density signals that the `ba-elicit-from-raw` skill must detect. Output feeds Phase B cross-validation and Phase C distillation.

---

## 1. Source Type Taxonomy

A correct classifier is the first gate of the skill — different source types carry different ambiguity profiles. Below is what each training example signals at the surface.

### 1.1 raw-request-001.md → **Jira ticket** (confidence: 0.97)

**Linguistic markers**:
- Bracketed ticket key in the title at line 20: `[LOAN-2847] Add document re-upload feature for loan applicants` — the `PROJECT-NNNN` pattern is a near-deterministic Jira fingerprint.
- Tabular metadata block lines 22-30: `Project:`, `Type:`, `Priority:`, `Reporter:`, `Assignee:`, `Sprint:`, `Labels:`, `Created:`, `Updated:`. This is Jira's standard issue-view layout.
- Field-style sections separated by ASCII rules (`────`) at lines 32, 49, 58, 110, 117, 125 — common Jira-export rendering.
- Comment threading with `**Name (Role) — YYYY-MM-DD HH:MM**` headers (lines 62, 65, 72, 80, 84, 88, 97, 103, 106).
- Explicit Jira concepts: `## Description`, `## Acceptance Criteria`, `## Linked Issues` ("Blocks", "Relates to"), `## Attachments`, sprint/labels vocabulary.
- Priority encoding `High (P1)` at line 25 — standard Jira priority taxonomy.

**Mild noise signals** the skill must tolerate:
- Inline narrator-style remarks inside metadata (`Type: Story (but might need to be Epic — too big?)` at line 23) — that parenthetical is human commentary, not a Jira field.
- "Anonymous (likely Raj)" comment at line 103 — semi-redacted speaker; the skill should treat it as low-confidence attribution.

### 1.2 raw-request-002.md → **Slack thread** (confidence: 0.96)

**Linguistic markers**:
- Channel header `#ops-payments — Slack channel` at line 18 — explicit platform tag.
- Speaker line pattern `Name (Role) — Today HH:MM` (lines 21, 29, 34, 45, 64, 71, 84, 101, 111, 123, 130, 137, 140, 144, 148, 151, 154, 158, 162). "Today" + minute-grain timestamps is a Slack tell.
- Lowercase prose, missing punctuation: `hey team, getting a LOT of escalations` (line 21), `honestly i don't know` (line 35), `right` (line 99) — chat register.
- Emoji as speech act: `👍` (lines 62, 64, 163), `😅` (line 41), `🙏` (line 165) — `👍` is functioning as an *agreement signal*, not decoration.
- Linked-attachment style: `📎 Linked: PAY-1192 (closed)` at line 27 — Slack attachment rendering.
- Reactions footer: `[Thread reactions: 12 🙏 from various ops folks]` at line 165 — Slack-specific affordance.
- Abbreviations: `fwiw` (line 30), `fyi` (line 111), `hm.` (line 134), `q` (line 123) — chat compression.
- Lack of structured headings; the "asks" appear as inline numbered list at lines 86-91 from one participant's summary, not as an AC section.

### 1.3 raw-request-003.md → **Meeting notes** (confidence: 0.98)

**Linguistic markers**:
- Document banner with `========` rules (lines 17, 32, 159, 162) — typical of plain-text meeting templates.
- Structured front matter: `Meeting:`, `Date:`, `Time:`, `Location:`, `Note-taker:`, `Attendees:`, `[Apologies: …]` (lines 18-31).
- Numbered agenda sections `## 1. Context`, `## 2. Current State Pain Points`, `## 3. Proposed Re-design`, `## 4. Vendor Discussion`, `## 5. Open Questions Raised`, `## 6. Action Items`, `## 7. Next Steps`, `## 8. Parking Lot` — classic minutes structure.
- Time-boxed agenda annotations like `(David, 5 min)` (line 34), `(group, 20 min)` (line 46), `(Hua, 15 min)` (line 100).
- Speaker attribution embedded in sentences, not on separate lines: `Hua: Acuant API can do…` (line 73), `Jamie: ok to batch if needed` (line 80), `Priya: careful with messaging` (line 96).
- Action-item block (`## 6. Action Items`) with bracketed owners `[David]`, `[Priya]`, `[Aisha]` (lines 134-142) — minutes idiom.
- Note-taker meta-commentary surfaces twice: `[unconfirmed if EOW = this or next week]` (line 43) and `Aisha (me!) … David wants it tomorrow latest. Sigh.` (lines 146-147). These are first-person clues that the writer is the junior PM, and they should be preserved as confidence-reducing signals.

**Cross-type recommendation**: All three formats are detectable from the first ~30 lines. The skill's source classifier should fire on metadata patterns first (Jira bracketed key, Slack `Today HH:MM`, meeting banner) and fall back to lexical markers (emoji, action-item brackets) only if structural markers are absent.

---

## 2. Information Density Map

A BA needs to ignore filler and focus on intent, constraints, dependencies, and decisions. Below is the signal-to-noise map per input.

### 2.1 raw-request-001.md (Jira)

| Section | Lines | Signal value | Notes |
|---|---|---|---|
| Metadata block | 22-30 | **HIGH** | Priority, reporter, labels, sprint state — all relevant. |
| Description | 36-47 | **HIGH** | Problem statement, volume (142 cases/wk), SLA (4h avg resolution), deadline (Q3). |
| Acceptance Criteria | 53-57 | **MEDIUM** | Bullets are vague ("Compliance is happy" is not testable). |
| Comments — Mike Chen | 65-70 | **HIGH** | Concrete percentages (40%, 25%) and process detail (15 min/agent). |
| Comments — Priya x2 | 72-78, 84-86 | **HIGH** | Compliance constraints (audit trail, 7yr retention, archive vs delete). |
| Comments — Sarah (questions) | 80-82 | **HIGH** | Surfaces unanswered scope question (abandoned applications). |
| Comments — Raj (technical Qs) | 88-95 | **HIGH** | Four constraint questions — most pivotal block in the ticket. |
| Comments — Anonymous | 103-104 | **LOW (toxic)** | "N could be 3" — looks like signal, but anonymity makes it unreliable. |
| Comments — Sarah handoff | 106-108 | **MEDIUM** | Signals epic-vs-story uncertainty. |
| Attachments | 113-116 | **LOW** | References, not content. |
| Linked Issues | 121-124 | **MEDIUM** | Reveals downstream blocker (Q3 campaign). |
| Business Value | 129-132 | **MEDIUM** | Rough ROI estimate; flagged as "rough". |

**Signal:noise ratio**: ~85:15. The "ask" (re-upload self-service) is stated explicitly at line 43, but the *full* ask (audit trail + archive + retry limit) is distributed across at least four comments. **The structure misleads**: the AC block (lines 53-57) is the shortest and weakest part of the ticket — most acceptance content is buried in comments.

### 2.2 raw-request-002.md (Slack)

| Section | Lines | Signal value | Notes |
|---|---|---|---|
| Opening problem statement (Jenny) | 21-25 | **HIGH** | Pain point, root cause hypothesis, magnitude ("LOT", "agent capacity ↑40%"). |
| Tom's state-machine clarification | 29-30, 37-41 | **HIGH** | Domain knowledge — two queues conflated. |
| Mei's compliance constraints | 45-47, 64-66, 71-82 | **HIGH** | Regulatory rules (tipping-off, retrieved funds language). |
| Tom's recap (the 4-point list) | 84-92 | **HIGH** | First explicit articulation of scope. |
| Raj's platform question | 101-103 | **HIGH** | Surfaces web-vs-mobile scope. |
| Mei's ETA conservatism | 111-122 | **HIGH** | Reveals SLA collapse decision (compliance vs ops merged). |
| Sarah Khoo's metric Qs | 123-126, 130-133, 137-138 | **HIGH** | Adds metrics + notification scope. |
| Emoji-only responses | 62, 64, 163 | **LOW (deceptive)** | `👍` looks like noise but is functioning as **decision acceptance** — skill must treat as commitment signal. |
| Reactions footer | 165 | **LOW** | Decorative. |

**Signal:noise ratio**: ~75:25. The "ask" is *never stated in one place* — it crystallises only in Tom's line 84-92 recap, and even that needs additions from Jenny (line 94), Sarah (lines 130, 137), and Mei (line 140). **Pragmatic decisions are encoded in 👍** — the skill must not strip emoji on preprocess.

### 2.3 raw-request-003.md (Meeting notes)

| Section | Lines | Signal value | Notes |
|---|---|---|---|
| Attendees + apologies | 23-31 | **HIGH** | Reveals **Legal absent** — a P1 gap. |
| Context (David) | 34-44 | **HIGH** | Cycle time numbers, regulator citation reference, target p95. |
| Pain points | 48-62 | **HIGH** | Seven concrete issues, each a candidate work item. |
| Proposed Re-design 3a-3e | 67-99 | **HIGH** | Solution shape across five workstreams. |
| Vendor Discussion | 102-108 | **MEDIUM** | Cost redacted ("$Xk/year"), SLA stated. |
| Open Questions Q1-Q6 | 111-130 | **HIGH** | Explicit unknowns — premium signal. |
| Action Items | 134-142 | **HIGH** | Owners + dates, but two say "EOW" (ambiguous). |
| Next Steps + note-taker aside | 146-149 | **MEDIUM** | The "Sigh" reveals time pressure on the BA brief. |
| Parking Lot | 153-157 | **LOW** | Explicitly out of scope. |

**Signal:noise ratio**: ~90:10. The "ask" (re-design EDD workflow with p95 < 7 days) is stated cleanly at line 41. **The danger here is the opposite of Slack**: the structure is *too clean*, which masks unresolved gaps (e.g., the threshold 0.75 hides un-calibrated engine).

---

## 3. Implicit Information Patterns

### 3.1 Assumed but not stated (5+ examples with quotes)

1. **Compliance officer Priya is the de facto approver for retention** — Sarah and Mike defer without confirmation she has authority. `raw-request-001.md:84` "Delete after 7 years YES." is treated as binding even though Priya is one voice.
2. **PII tagging applies** — `raw-request-001.md:74` mentions "NRIC, financial statement" but nowhere is "this is PII subject to data-protection workflow" stated.
3. **"Compliance is happy" is testable** — `raw-request-001.md:57` lists this as an AC, assuming someone knows what "happy" means.
4. **"Today" in Slack = a specific date** — `raw-request-002.md` uses `Today 09:14` etc. throughout; the actual calendar date is implicit. The skill must request or infer the date for any deadline math.
5. **"EOW" means end of this work week** — `raw-request-003.md:43` action item, the note-taker even flags `[unconfirmed if EOW = this or next week]` — so this is an *acknowledged* assumption gap.
6. **"3 weeks ideally" is calendar weeks from today** — `raw-request-002.md:152` "need this in 3 weeks ideally" — implicit anchor date.
7. **Acuant proposal pricing is acceptable in principle** — `raw-request-003.md:105` `Cost: ~$Xk/year` — the implicit assumption is that whatever the number turns out to be, it fits FY budget (`raw-request-003.md:75` says budget is allocated).
8. **The agent UI changes are part of the same epic** — `raw-request-002.md:155-156` Tom hedges "agent UI changes might slip a sprint" but never says "in scope vs out of scope".
9. **Mobile app team and Onboarding squad have separate sprints/timelines** — `raw-request-001.md:99` "mobile app team is in separate sprint" is mentioned offhand as if everyone knows.

### 3.2 Partially stated (need inference)

1. **Retry limit value** — `raw-request-001.md:101` "escalate to support after N attempts maybe" + `raw-request-001.md:104` "N could be 3" — proposed but never confirmed.
2. **ETA bucket policy** — `raw-request-002.md:53` "24-72h depending on workload" (compliance) vs "same day 95%" (ops) but `raw-request-002.md:114` collapses both to "up to 5 business days". The collapse is decided but the justification ("reputational risk on the long tail" at line 120) hand-waves the trade-off.
3. **Notification channel matrix** — `raw-request-002.md:135` "probably yes. email + in-app. push notif maybe optional" — channels for "approved" partially named, for "rejected" only email is implied.
4. **High-risk threshold 0.75** — `raw-request-003.md:91-93` Priya proposed 0.75 but Jamie cautions calibration takes 2 cycles. Threshold is *proposed*, not *agreed*.
5. **Senior approval definition** — `raw-request-003.md:59` "unclear when senior approval triggered vs analyst can decide" — pain point identified, future-state authority matrix only partly defined in 3d (lines 86-89).
6. **Adverse-media vendor identity** — `raw-request-003.md:78` "adverse media vendor (?) rate-limited" — vendor existence acknowledged, name not in record.
7. **Migration plan exists separately** — `raw-request-003.md:114-115` "defer to migration plan, separate workstream" — implies a workstream exists but no link, owner, or status.

### 3.3 Conflicting between commenters

1. **Document version-vs-replace policy** — `raw-request-001.md:55` AC says "Old document is replaced (or maybe kept as version? unclear)" — single bullet contains its own contradiction; Priya later (line 76-78) effectively requires *archive not delete* for sensitive docs, which leans toward versioning, but never reconciled with Sarah's AC. Ground truth flags this as P2 #1.
2. **Retention duration** — Sarah asks at `raw-request-001.md:80` whether deletion *after* 7 years is permitted; Priya confirms at line 86 ("Delete after 7 years YES"). Initial Priya post at line 74 implies indefinite archive ("needs to be archived per our data retention policy"). Resolution is in favor of 7-year limit, but earlier wording is in tension.
3. **Mobile scope** — `raw-request-002.md:107` Jenny "both ideally but web first if we have to pick" vs `raw-request-002.md:161` Sarah Khoo "web customer-facing first, then agent UI, then mobile". One says "both, web first"; the other says "web, then agent, then mobile" — implies mobile is *in* the plan vs queued separately.
4. **ETA timing** — `raw-request-002.md:117` Tom: "5 days feels long for the 95% case" vs `raw-request-002.md:120` Mei: "agreed but reputational risk on the long tail". Mild disagreement resolved via deference to compliance, but the underlying SLA tension is unresolved.
5. **NPS as success metric** — `raw-request-003.md:126-128` Ben proposes "applicant NPS target >= 6" → David: "NPS yes but secondary". Partial agreement; "secondary" leaves it ambiguous whether it's tracked or not.
6. **Note-taker's assignment** — `raw-request-003.md:140-141` action item assigned to Aisha vs `raw-request-003.md:146-147` Aisha's aside "this got assigned to me at the end" + "Sigh" — agreement is grudging; no formal handoff documented.

---

## 4. Speech Acts Inventory

For each input, at least 5 instances per speech-act category, with quotes (line refs).

### 4.1 raw-request-001.md (Jira)

**Requests**:
- `:43` "We need a self-service way for applicants to re-upload documents." (Sarah, the headline request)
- `:54` "Applicant can re-upload from the application portal" (AC bullet — request as outcome)
- `:74` "We need an audit trail for any document replacement." (Priya, compliance requirement)
- `:77-78` "the old version should NOT just be deleted — needs to be archived" (Priya, prohibition + alternative)
- `:88-95` Raj's four bullet questions, each implicitly requesting a decision: "What about file size limits?", "limit how many times?", "Loop?", "both or just web?"

**Assertions** (claims of fact):
- `:40-41` "last week we had 142 such cases, average resolution time 4 hours" (Sarah, quantitative)
- `:67-70` Mike's percentages: 40% expired NRIC, 25% bank statements, agent time ~15 min
- `:74` "Retention: 7 years." (Priya, regulatory fact)
- `:99` "mobile app team is in separate sprint" (Sarah, org fact)
- `:129` "Reduce support load by ~140 cases/week × 4 hours = 560 hours/week" (Sarah, derived assertion — hedged "rough estimate")

**Promises / commitments**:
- `:78` "I'll send the policy doc separately." (Priya, deliverable)
- `:101` "escalate to support after N attempts maybe" (Sarah, weak commitment — modal "maybe")
- `:108` "creating this ticket for handoff to BA team" (Sarah, completed commitment)
- `:104` "N could be 3." (Anonymous, low-conviction suggestion masquerading as commitment)
- AC bullet `:56` "Support agents no longer need to handle this" (implicit commitment to outcome)

**Questions** (open/closed):
- Closed: `:80-82` "can we delete after retention period or no?"
- Open: `:82` "if applicant abandons their application, what happens to the docs?"
- Closed: `:90` "Keep same?" (file size limits)
- Open: `:91` "Multiple re-uploads of the same doc — limit how many times?"
- Open: `:92` "What happens if the new upload also fails verification? Loop?"

**Disagreements / pushback**:
- Mild: `:23` "Type: Story (but might need to be Epic — too big?)" (Sarah pushing back on her own classification)
- Implicit: Priya's `:74` "needs to be archived" directly counters AC `:54` "Old document is replaced"
- Hedged: `:99-101` Sarah's reply to Raj uses "mostly", "probably", "maybe" — pushback as uncertainty rather than refusal
- `:86` "Abandoned applications — separate ticket, that's a different concern." (Priya scopes out Sarah's question — soft pushback on scope)
- `:108` "Note: we may need to split into multiple stories." (Sarah pushing back on the ticket's own structure)

### 4.2 raw-request-002.md (Slack)

**Requests**:
- `:24-25` "can we do something about visibility?" (Jenny)
- `:47` "we can give them an ETA range maybe?" (Mei, proposal-as-request)
- `:51` "ETA would be huge" (Jenny, request-as-emphasis)
- `:145-146` "let me write this up as a ticket. Sarah can you sponsor?" (Tom — two requests, one for sponsorship)
- `:158-160` "let's prioritize web customer-facing first, then agent UI, then mobile" (Sarah Khoo, prioritisation request/decree)

**Assertions**:
- `:30` "those are different states fwiw" (Tom, domain fact)
- `:43` "agent capacity ↑40% on wire status questions" (Jenny, metric)
- `:54-55` "we typically resolve in 24-72h depending on workload. for ops second-eye it's same day 95% of the time" (Mei, operational facts)
- `:74-75` "if compliance ultimately rejects the wire, we cannot tell the customer 'rejected for sanctions reason'" (Mei, regulatory fact)
- `:120` "reputational risk on the long tail. legal will probably push the same way" (Mei, predictive claim)

**Promises / commitments**:
- `:85` "ok let me draft" (Tom)
- `:144-146` "let me write this up as a ticket" (Tom)
- `:149` "yes go ahead" (Sarah Khoo, sponsorship granted)
- `:152` "need this in 3 weeks ideally" (Jenny, demand-as-commitment-request)
- `:155-156` "3 weeks for the customer-facing piece probably doable" (Tom, hedged commitment with modal "probably")

**Questions**:
- Closed: `:29` "'on hold' = pending second-level review? or pending compliance?" (Tom)
- Open: `:75` "how do we tell the customer the wire didn't come through then" (Jenny)
- Closed: `:101-103` "is this for web banking only or also mobile?" (Raj)
- Open: `:123-125` "what's the metric we'd track? reduction in inbound calls? customer satisfaction score? both?" (Sarah Khoo)
- Open: `:130-132` "when does the customer's status update if a wire goes from 'additional review' to 'approved'? do we email them? push notif?"

**Disagreements / pushback**:
- `:30` Tom corrects Jenny's frame: "those are different states fwiw" (gentle)
- `:38-41` Tom defends the current opacity as "by design"
- `:65` Mei's `:64` "👍 with caveats" — agreement with conditions
- `:117` Tom: "fine. though 5 days feels long for the 95% case…" (concession + protest)
- `:140` Mei tempers Sarah Khoo's notification plan: "careful with rejection emails — content has to be generic" (constraint pushback)

### 4.3 raw-request-003.md (Meeting notes)

**Requests**:
- `:41` "Pressure to reduce EDD cycle to <7 days at p95" (David, performance target)
- `:97` "generic 'in review' status acceptable to compliance" (group, accepted request)
- `:99` "Ben to draft 3 wireframes for review" (request → action)
- `:115` Q2 "If applicant abandons mid-flow, retention of partial PII?" (open question = elicitation request)
- `:127` Q5 "What's the success metric specifically?" (request for definition)

**Assertions**:
- `:37` "Cycle time: average 11 days (some up to 22), variance is the issue"
- `:62` "applicant experience scoring NPS 3.8 / 10 in current process" (Ben)
- `:74` "Acuant API can do document type detection + liveness check + authenticity scoring in one call" (Hua)
- `:107` "SLA: 99.9% uptime committed, P95 latency <2s per call"
- `:108` "Data residency: Acuant offers SG region — Priya confirmed acceptable"

**Promises / commitments**:
- `:43` "David — share regulator citation by EOW"
- `:135` "[Priya] Confirm partial-PII retention rule with Legal — by next session"
- `:136` "[Karim] Spike on Acuant biometric API security review path — 1 week"
- `:138` "[Ben] 3 wireframes for applicant status page — by 2026-05-14"
- `:140-141` "[Aisha] Convert these notes into a structured BA brief for handoff — by 2026-05-12"

**Questions**:
- Open: `:111` Q1 "What happens to in-flight EDD cases when we cut over to new workflow?"
- Closed: `:121` Q4 "Mobile app vs web parity?"
- Open: `:129` Q6 "Who owns the migration of legacy data structures?"
- Closed (implied): `:79-80` "throughput concern — adverse media vendor (?) rate-limited at X requests/min, need check" (Karim — asking if rate limit is binding)
- Closed: `:91` "'High-risk' definition — Priya suggested using score >= 0.75 from engine"

**Disagreements / pushback**:
- `:81-82` Jamie counters Karim's throughput worry: "ok to batch if needed, results within 1h is target"
- `:91-93` Jamie pushes back on Priya's 0.75: "engine outputs not calibrated yet … calibration takes 2 cycles of real data"
- `:128` David tempers Ben's NPS proposal: "NPS yes but secondary"
- `:119` "Q3. Cross-border applicants … Skipped, out of scope for this phase per David" (David scoping out a question)
- `:147` Aisha's "Sigh." (silent pushback at being assigned the writeup)

---

## 5. Ambiguity Sources Catalog (target 15+)

Each ambiguity is tagged by type and a severity hint aligned with the ground-truth taxonomy (P1 blocker, P2 must-address, P3 assumption-to-document).

### Lexical ambiguity (vague words)

1. **"urgent"** — `raw-request-001.md:28` label `urgent` is unbacked by SLA. Severity **P3** (assumption).
2. **"Compliance is happy"** — `raw-request-001.md:57` AC bullet. "Happy" is not a testable predicate. Severity **P2**.
3. **"additional review"** — `raw-request-002.md:59` "bucket the hold reasons into a generic 'additional review' status". Deliberately vague; needs canonical phrasing + legal sign-off. Severity **P2**.
4. **"vague-but-helpful"** — `raw-request-002.md:69` "the language has to be vague-but-helpful". Self-referential vagueness; cannot be specified without legal copy. Severity **P2**.
5. **"reasonable"** — `raw-request-001.md:101` "probably need limit but not sure what's reasonable". Severity **P3**.
6. **"appropriate suspicious activity report"** — `raw-request-002.md:81-82` "we file the appropriate … if applicable". Two vague modifiers in one clause. Severity **P3**.
7. **"piecemeal"** — `raw-request-003.md:49` "applicant emails docs piecemeal over days" — qualitative descriptor of cadence; no measurable threshold. Severity **P3**.

### Syntactic / structural ambiguity

8. **"Type: Story (but might need to be Epic — too big?)"** — `raw-request-001.md:23` self-questioning declaration; not a parseable Jira value. Severity **P2** (work-item shape).
9. **"Old document is replaced (or maybe kept as version? unclear)"** — `raw-request-001.md:55` — parenthetical *negates* the main clause. Severity **P2** (ground-truth P2 #1).
10. **"adverse media vendor (?) rate-limited at X requests/min"** — `raw-request-003.md:78` — `(?)` and `X` are placeholder tokens, not values. Severity **P2**.

### Pragmatic ambiguity (context-dependent)

11. **"this is bottlenecking our application throughput"** — `raw-request-001.md:39-40` — "this" refers to manual support handling, but skill must infer. Severity **P3**.
12. **"that's regulated comms"** — `raw-request-002.md:46` Mei — "that's" refers to exposing sanctions hold; only a domain expert resolves it. Severity **P2** (banking-grade signal).
13. **"by next session"** — `raw-request-003.md:135` — meaning depends on whether next session 2026-05-14 is confirmed. Severity **P3** (ground-truth P3 #6).
14. **"Compliance audit readiness (implicit)"** — `raw-request-001.md:132` — "(implicit)" is the author's own pragmatic flag. Severity **P3**.
15. **"covers the rare deep-dive cases"** — `raw-request-002.md:114` — "rare deep-dive" undefined; pragmatic shorthand for an internal escalation type. Severity **P3**.

### Pronominal ambiguity

16. **"showing same thing to the customer is sort of by design"** — `raw-request-002.md:38` — "same thing" antecedent is "on hold"; tolerable in chat, hostile to specification. Severity **P3**.
17. **"agree?"** — `raw-request-002.md:60` — "agree" with which bullet of the four? Resolved by Jenny's 👍 but unattached to a specific clause. Severity **P3**.
18. **"yes"** — `raw-request-002.md:135` Jenny's response to two questions in one breath ("do we email them? push notif?") — single "hm. probably yes" cannot bind to both. Severity **P2** (notification matrix gap, ground-truth P2 #2).
19. **"that's a different concern"** — `raw-request-001.md:86` — "that's" = abandoned applications. Clear in context but skill should normalize. Severity **P3**.

### Quantifier ambiguity

20. **"a LOT of escalations"** — `raw-request-002.md:21` — capitalised intensifier with no number. Severity **P3**.
21. **"some up to 22"** — `raw-request-003.md:37` — "some" is uncounted. Severity **P3**.
22. **"most variable step"** — `raw-request-003.md:54` — superlative without comparator data. Severity **P3**.
23. **"a few attempts" / "after N attempts"** — `raw-request-001.md:101` — variable N never bound to a value. Severity **P2** (ground-truth P2 #3).
24. **"Multiple side topics"** — implicit across `raw-request-002.md`; quantifier "multiple" suppresses count.

### Modal ambiguity

25. **"may need to split"** — `raw-request-001.md:108` — modal "may" softens commitment; ambiguous between possibility and intention. Severity **P2**.
26. **"probably yes. email + in-app. push notif maybe optional"** — `raw-request-002.md:135` — three modals (`probably`, `maybe`, `optional`) in two sentences. Severity **P2**.
27. **"might slip a sprint"** — `raw-request-002.md:155-156` — "might" + indefinite article. Severity **P2** (ground-truth P2 #4 — agent UI scope).
28. **"could be future"** — `raw-request-003.md:154` — parking-lot modal. Severity **P3** (explicitly deferred).
29. **"should NOT just be deleted"** — `raw-request-001.md:77` — deontic "should" used where regulatory force suggests "must". Severity **P2** (banking-grade modal escalation).
30. **"need to confirm with Legal"** — `raw-request-003.md:117` — "need" is high-modal force, but no owner or date attached. Severity **P2** (ground-truth P2 #5).

(30 catalogued, far exceeding the 15-target — the volume confirms ambiguity load is the dominant linguistic feature across all three inputs.)

---

## 6. Linguistic Quality Scores

Scoring rubric: 0 = absent / hostile; 5 = present but weak; 10 = production-grade. Composite is mean of the four sub-scores, rounded to one decimal.

### 6.1 raw-request-001.md (Jira) — overall **4.8 / 10**

- **Specificity: 5/10** — Has concrete numbers in the description (142 cases/week, 4h, 10MB, 40%/25%) but ACs are vague ("Compliance is happy") and key parameters are placeholders ("N attempts", versioning policy).
- **Completeness: 4/10** — Multiple unanswered questions remain (abandoned applications, mobile scope, retry limit, archive vs delete policy). Half the AC content lives in comments, not in the AC block.
- **Consistency: 5/10** — Conflicts between AC ("replaced") and Priya's archive requirement; modal hedges throughout. Sarah herself questions the ticket type.
- **BA-readiness: 5/10** — Workable but **must not** go to TL without ambiguity pass. Matches ground truth ("workable, just messy").

### 6.2 raw-request-002.md (Slack) — overall **3.5 / 10**

- **Specificity: 3/10** — Operational SLAs are stated (24-72h, same-day 95%) but customer-facing copy is described as "vague-but-helpful". Numbers are anecdotal ("↑40%", "LOT").
- **Completeness: 3/10** — No AC, no clear authoritative scope statement. Tom's recap at lines 84-92 is the only structured artifact and explicitly says "am i missing anything?".
- **Consistency: 4/10** — Mobile scope contradicted (lines 107 vs 161). ETA bucket merging unresolved trade-off.
- **BA-readiness: 4/10** — Lower than Jira because format provides no anchors. Banking-grade signals (tipping-off, retrieved funds) raise the floor, but require translation to spec language.

### 6.3 raw-request-003.md (Meeting notes) — overall **5.5 / 10**

- **Specificity: 6/10** — Strong numbers (11-day cycle, p95 < 7 days, 0.75 threshold, NPS 3.8, $Xk redacted, 99.9% / 2s SLA). But several placeholders (`$Xk`, `(?)`, "EOW").
- **Completeness: 5/10** — Six open questions explicitly logged (Q1-Q6) — *good*. But Legal absent (P1 blocker), and tiered routing only defines "high" of three tiers.
- **Consistency: 6/10** — Cleanest of the three; the note-taker imposes structure. Contradictions exist (NPS as primary vs secondary, Aisha's grudging ownership).
- **BA-readiness: 5/10** — Format helps, but **scale is the killer** — ground truth notes this is multi-epic (5-6 epics) being treated as one initiative.

**Ranking** (lowest BA-readiness first, i.e. worst case for the skill): Slack (3.5) < Jira (4.8) < Meeting notes (5.5). The skill must perform worst-case on Slack-like inputs.

---

## 7. Implications for Skill Design

Concrete recommendations for the `ba-elicit-from-raw` ambiguity-detection logic, in order of priority.

1. **Tokenize and flag modal verbs in any prescriptive section**. Build a closed-class list — `may, might, could, should, would, probably, maybe, possibly, perhaps, ideally, tentatively, hopefully` — and emit a P2 flag for each occurrence in Description / AC / Decisions. The catalog above (items 25-30) shows modals are the highest-volume P2 source.
2. **Normalize time expressions before downstream phases**. Replace `EOW`, `today`, `tomorrow`, `next sprint`, `next session`, `Q3`, `Q4`, `by next week`, `in 3 weeks ideally`, `next available` with absolute dates and flag any that cannot be normalised (e.g., `EOW` when current date is mid-week is ambiguous between this Friday and next). Anchor everything to the conversation date when present.
3. **Detect placeholder tokens and treat as P2 by default**. Patterns: `X requests/min`, `$Xk/year`, `(?)`, `N attempts`, `TBD`, `???`, `(figure TBD)`, single capital letters in numeric position. Each is a P2 unless the surrounding context explicitly binds it.
4. **Quantifier-without-quantity detector**. Maintain a list — `some, several, a few, many, most, lots of, a LOT, multiple, often, sometimes, frequently, rare, typically` — and emit an `assumption-to-document` for each unbound occurrence. Pair with adjacent numerics when present (e.g., "some up to 22" → flag "some" but capture "22").
5. **Anonymous or low-attribution speaker handling**. If a comment is anonymous (`raw-request-001.md:103`) or attribution-collapsed ("group, 20 min" at `raw-request-003.md:46`), reduce confidence of any commitments or numeric facts in that span, and flag if it touches a decision (the `N = 3` case is canonical).
6. **Emoji-as-decision recognition**. `👍`, `👎`, `✅`, `❌`, `+1`, `-1`, `🙏` in chat sources should be recognised as **acceptance / rejection** speech acts, not stripped. Treat as low-conviction acceptance unless paired with a text affirmation (`raw-request-002.md:62, 64, 163` are decision points).
7. **AC-content extraction must include comment threads**. The Jira example proves the AC block is *not* where AC content lives; the skill should aggregate constraints from all comment timestamps and reconcile against the declared AC bullets, flagging mismatches (e.g., `replaced` in AC vs `archived` in Priya's comment).
8. **Stakeholder-completeness pass**. Build a domain-aware required-stakeholder map (for banking: Legal, Compliance, Security, Privacy/PII, Data, Ops, Engineering Lead, PM, CX). If any required stakeholder is *referenced* in the body but *not present* in attendees / commenters, emit a P1 (e.g., `raw-request-003.md` mentions Legal three times but `[Apologies: Legal — Sundar K.]`). This matches ground-truth P1 in raw-request-003.
9. **Conflict detection across speakers**. Maintain a per-entity decision ledger; if two speakers make incompatible claims on the same field (mobile scope, retention duration, replace-vs-archive), surface a P2. The skill should accept the *latest* claim as the working answer but log the conflict.
10. **Pronoun resolution with low confidence by default**. `this, it, they, that, those` referring across more than one sentence boundary should be tagged. If resolution requires speaker domain knowledge ("that's regulated comms"), emit assumption-to-document; for in-sentence references, resolve silently.
11. **Banking-grade signal extractor**. Keyword-driven (regex + domain dictionary): `audit trail, retention, NRIC/SSN/passport/PII, sanctions, tipping-off/tipping off, AML, KYC, PEP, adverse media, suspicious activity report, SAR, idempotency, data residency, encryption at rest, segregation of duties`. Each match should escalate the input to require Banking-Grade non-functional ACs (audit, idempotency, reversibility, retention, access control, privacy).
12. **Epic-shape detector**. Score input size by (a) number of distinct workstreams mentioned, (b) cross-team dependencies (Mobile, Legal, Vendor), (c) number of P2 open questions. Above thresholds (e.g., ≥4 workstreams or ≥6 P2 items), emit a "likely epic — propose split" recommendation matching the ground truth story-splitting hints in all three inputs.
13. **Source-type-aware noise filter**. For Slack, preserve emoji + recognise reaction-as-commitment; for Jira, parse the metadata block as structured fields; for meeting notes, preserve note-taker meta-commentary in square brackets as confidence signals (e.g., `[unconfirmed if EOW = this or next week]` at `raw-request-003.md:43`).
14. **Hedge-language detector beyond modals**. Catch *hedged commitments* like "honestly i don't know", "let me know", "probably doable", "feels long", "let's not spam", "to be safe", "if applicable", "depending on workload". These rarely rise to P1 individually but cluster as completeness signals; surface a count-based completeness penalty if more than ~5 occur in a single input.
15. **Output the linguistic-quality scorecard at intake**. The skill should emit the four sub-scores (specificity / completeness / consistency / BA-readiness) for every raw input, with the lowest sub-score driving the *minimum* number of clarifying questions to ask back. Below a composite 5.0, the skill should refuse silent handoff and require a human checkpoint.

---

## 8. Cross-Cutting Observations (handover to Phase B)

- **Recurring ambiguity hotspots** across all three inputs: *mobile scope*, *retention duration*, *retry/escalation thresholds*, *notification channels*, *who owns approval*. These are not coincidences — they are the genres' canonical underspecified zones, and Phase C distillation should hard-code probes for each.
- **The Slack input is the worst case** and should be the skill's stress test. If the skill handles Slack adequately, Jira and meeting notes are easier.
- **Banking-grade signals appear in all three** (PII in Jira, tipping-off in Slack, MAS/data-residency in Meeting). The skill must always run the banking-grade pass for T1/T2 inputs regardless of source type.
- **Ground-truth taxonomy P1/P2/P3 maps cleanly** onto the modal / quantifier / placeholder / stakeholder-gap detectors recommended above; the skill should keep that three-tier severity output for downstream R6 consumption.

— End of Phase A2 Linguistic Forensics Analysis —
