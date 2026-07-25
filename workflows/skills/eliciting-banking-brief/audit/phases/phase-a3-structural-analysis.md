# Phase A3 — Structural Pattern Analysis

> **Purpose**: Identify HOW information is organized in raw BA inputs, and how those structural patterns should map to the epic + story output template. This analysis directly informs the parsing strategy of the `ba-elicit-from-raw` skill.
>
> **Inputs analyzed**:
> - `inputs/raw-request-001.md` — Jira ticket (Lending / LOAN-2847)
> - `inputs/raw-request-002.md` — Slack thread (`#ops-payments`)
> - `inputs/raw-request-003.md` — Meeting notes (Onboarding 2.0 / EDD)
> - `epic-and-stories.template.md` — output target shape (v2)
>
> **Note on quoting**: Quotes are cited as `{file-shorthand}:{line}` where shorthand = `r1` (raw-request-001), `r2` (002), `r3` (003), `tpl` (template).

---

## 1. Section Type Inventory

Across the three example inputs, the following section types appear. Each is a *signal carrier* — the parser should recognize and route them differently.

### 1.1 Header / Metadata Block
- **r1 lines 20-30**: Jira-style header — `Project`, `Type`, `Priority`, `Reporter`, `Assignee`, `Sprint`, `Labels`, `Created`, `Updated`. Highly structured key:value pairs.
- **r2 line 18**: One-line channel marker (`#ops-payments — Slack channel`). Minimal metadata; almost everything must be inferred.
- **r3 lines 17-32**: Meeting metadata block — `Meeting`, `Date`, `Time`, `Location`, `Note-taker`, full attendee list with roles, plus "Apologies" line for absentees.
- **Information**: source identifier, reporter/owner, dates, priority, tagging vocabulary, attendees with roles, absentees (which is metadata + a *stakeholder gap signal*).
- **Frequency**: present in r1 and r3 (rich); minimal in r2.

### 1.2 Description / Context Narrative
- **r1 lines 34-47**: A `## Description` block — prose problem statement plus a "why now" sentence (`Marketing wants this live before the Q3 campaign launch (end of June)`).
- **r3 lines 34-41**: A `## 1. Context (David, 5 min)` section — bullet-form problem statement, baseline metrics (`average 11 days (some up to 22)`), regulatory trigger.
- **r2 lines 21-25**: No explicit section. Context lives in the first message (`hey team, getting a LOT of escalations…`).
- **Information**: problem statement, baseline metrics, urgency drivers, regulatory triggers.
- **Frequency**: present in all three, but explicit only in r1 and r3.

### 1.3 Acceptance Criteria (Explicit)
- **r1 lines 51-56**: Explicitly labelled `## Acceptance Criteria (rough — from PM)` — bullet list, prose-form, not testable as-is.
- **r2**: None — there is no AC section at all. ACs must be *synthesized* from chat decisions.
- **r3**: None as an explicit section, but design decisions in section 3 (lines 64-99) read like proto-ACs.
- **Frequency**: explicit in 1 of 3 inputs only.

### 1.4 Comments / Conversation Thread (chronological)
- **r1 lines 60-108**: `## Comments` block, oldest-first, named commenter with timestamp. Each commenter brings a different concern (PM → support → compliance → engineering).
- **r2 lines 18-165**: The entire body is a conversation thread, oldest-first, name + relative timestamp (`Today HH:MM`).
- **r3**: Not chat-shaped but the body of section 2 (Pain points) and section 3 (Proposed re-design) functions as captured group conversation.
- **Information**: refinements, decisions-in-flight, dependency cues, stakeholder positions, regulatory caveats, implicit approvals (a thumbs-up emoji as decision evidence — r2:62, 63, 163).
- **Frequency**: present in all three but in different shapes.

### 1.5 Attachments / References
- **r1 lines 113-115**: `## Attachments` — file names referenced, some not actually attached.
- **r3 line 65**: "David walked through slides — not attached here".
- **r2**: A single in-line linked-Jira `📎 Linked: PAY-1192 (closed)` at line 28.
- **Information**: external artifacts that may contain ground truth; flag for follow-up.
- **Frequency**: present in all three; **always partial** — none of the referenced docs are actually inline.

### 1.6 Linked Issues / Cross-references
- **r1 lines 119-123**: `## Linked Issues` block — explicit `Blocks:`, `Relates to:`, `Possibly relates to:` predicates.
- **r2 line 28**: One Jira link by ID, no relationship type.
- **r3**: No linked issues, but Q1 (line 111) hands off in-flight EDD to "separate workstream".
- **Information**: dependency graph edges.
- **Frequency**: explicit in r1, light in r2, absent in r3.

### 1.7 Business Value / Pitch
- **r1 lines 127-132**: `## Business Value (from Sarah's pitch)` — quantified savings, soft benefits.
- **r2 lines 124-128**: Inline question from Sarah Khoo (`what's the metric we'd track?`) followed by a partial answer — value definition is *negotiated mid-thread*.
- **r3 lines 124-128**: Q5 in Open Questions explicitly asks the success metric and partially answers (`p95 cycle time < 7 days`).
- **Information**: ROI claims, target metrics, baseline numbers.
- **Frequency**: present in all three, but only explicit + structured in r1.

### 1.8 Action Items
- **r3 lines 132-143**: `## 6. Action Items` — bulleted, `[Owner] task — due` format.
- **r3 lines 144-150**: `## 7. Next Steps` — narrative form, partial overlap with action items.
- **r1**: None as a distinct section; action items are buried in comments (e.g., `Sarah Lim` saying she will create the ticket — r1:106-108).
- **r2 lines 144-163**: Implicit — `Tom Becker` says "let me write this up as a ticket" (r2:144); Sarah Khoo says "yes go ahead" (r2:148). Action assignment via informal exchange.
- **Information**: owners, due dates, deliverables. Critical for "who does what next".
- **Frequency**: explicit only in r3; implicit in r1 and r2.

### 1.9 Open Questions / TBD
- **r3 lines 109-130**: `## 5. Open Questions Raised (not all resolved)` — numbered Q1..Q6 with partial answers or "Skipped" / "TBD".
- **r1**: Open questions are scattered inside comments (e.g., `What about file size limits?` — r1:90; `Multiple re-uploads of the same doc — limit how many times?` — r1:91).
- **r2**: Open questions interleaved (`is this for web banking only or also mobile?` — r2:101).
- **Information**: explicit ambiguity signals; high-value targets for AC clarification.
- **Frequency**: explicit only in r3; otherwise implicit.

### 1.10 Parking Lot / Out-of-Scope (Deferred)
- **r3 lines 151-157**: `## 8. Parking Lot` — explicit out-of-scope items with possible future epic candidates (`AI-assisted analyst tooling`, `Cross-product onboarding`).
- **r1**: No parking lot, but Priya defers a question (`Abandoned applications — separate ticket` — r1:84-86) and Sarah says split may be needed (r1:106-108).
- **r2 line 159**: Sarah Khoo prioritizes (`web customer-facing first, then agent UI, then mobile. legal in parallel.`) — effectively a phased-scope/parking signal.
- **Information**: future-epic seeds, deferral rationale.
- **Frequency**: explicit only in r3.

### 1.11 Vendor / Third-Party Section
- **r3 lines 100-108**: `## 4. Vendor Discussion (Hua, 15 min)` — vendor name (Acuant), SLA, residency, integration estimate, cost (TBD).
- **r1**: None.
- **r2**: None as a section; passing references to "originator bank".
- **Information**: external SLA commitments, security review triggers (`security review needed before integration` — r3:104), commercial dependencies.
- **Frequency**: 1 of 3 inputs, but when present it's a high-value cluster.

### 1.12 Reactions / Implicit Approvals
- **r2 lines 62-63 ("👍"), line 163 ("👍"), line 165 ("[Thread reactions: 12 🙏 from various ops folks]")**: Emoji-as-vote.
- **r1**: None at this level (no upvote mechanic surfaced).
- **r3**: None — group consensus captured in prose paraphrase.
- **Information**: implicit decision capture; a 👍 from compliance carries different weight than 👍 from a frontend dev. Must be tracked but **never treated as formal sign-off**.
- **Frequency**: only in r2.

### 1.13 Ground Truth / Audit Annotations (skill-internal)
- **r1 lines 137-181, r2 lines 170-217, r3 lines 167-221**: "Intentional Issues for R6 to Catch (Hidden from BA Workflow)".
- **Information**: training-set ground truth. **The skill must never read these in production** — they are after-the-fact audit annotations.
- **Frequency**: all three; this is the *evaluation harness*, not user input. The skill should detect this exact heading and strip it.

---

## 2. Implicit Story Boundaries (per training example)

### 2.1 r1 — Jira (Lending)
- Stories are **not** explicitly enumerated in the body. The author hints at split-need: the Type field literally says `Story (but might need to be Epic — too big?)` (r1:22) — this is itself the strongest split signal.
- Sarah's final comment "we may need to split into multiple stories. Let's discuss in sprint planning." (r1:106-108) confirms implicit-multi-story shape.
- **Story-boundary signals inside the prose**:
  - "Applicant can re-upload from the application portal" (r1:53) → happy-path re-upload story.
  - "Compliance team also asked us to track who replaced what document and when (probably for audit reasons)" (r1:43-44) → audit-trail story.
  - "if the replaced document contains sensitive info … the old version should NOT just be deleted — needs to be archived" (r1:76-79) → archive-policy story.
  - "escalate to support after N attempts maybe" (r1:99-101) → retry-limit + escalation story.
  - "mostly web for now (mobile app team is in separate sprint)" (r1:98-99) → mobile parity story (deferred candidate).
- Hidden ground truth (r1:173-180) confirms **5 story candidates + 2 deferrals** — matches author-derived signals.
- **Boundary marker**: each named *stakeholder concern* (Priya/Mike/Raj) maps to a story candidate. Stakeholder-as-boundary is a robust heuristic for Jira tickets.

### 2.2 r2 — Slack (Payments)
- Stories are completely implicit. Tom's enumeration at lines 84-92 is the closest thing to an inventory of stories:
  > "1. customer-facing status: add 'additional review' state with ETA bucket / 2. customer-facing on rejection: generic non-tipping language / 3. internal back-office: keep granular state … / 4. agent script: standard responses for the new status"
  This list is the spine of the epic's stories.
- Sarah Khoo's questions add two more candidate stories: customer notification on state change (r2:130-142) and email-only rejection messaging.
- Raj Sharma's question (r2:101-103) opens a mobile-parity story (later deferred per r2:158-160).
- **Boundary markers**: each `1.` `2.` `3.` `4.` in Tom's draft, plus each new participant joining and asking a scope question.
- Hidden truth (r2:209-217) lists 6 stories + 2 explicitly out-of-scope — matches Tom's draft + Sarah's questions + Raj's question.

### 2.3 r3 — Meeting Notes (KYC / EDD)
- Stories are **partially** explicit via the section-numbered re-design subsections (3a..3e). Each `### 3a..3e` is a story-or-epic-sized chunk.
- The Vendor Discussion section (r3:100-108) is *not* a user story — it's a cross-cutting concern (Acuant integration) that touches multiple stories (3a doc capture, 3f biometric).
- The Parking Lot (r3:151-157) explicitly marks future-epic candidates.
- Hidden ground truth (r3:212-221) calls out **6 epics** here, not stories — confirming r3 is multi-epic scoped.
- **Boundary marker**: each `### 3X.` is at least one story; some are full epics (e.g., 3a = doc portal + Acuant = an epic on its own).

---

## 3. Implicit Epic Scope (per training example)

### 3.1 r1
- **Judgment**: **1 epic, ~5 stories + 1 deferred mobile + 1 out-of-scope abandoned-app workflow**.
- Signals: Type field flagged as ambiguous ("Story (but might need to be Epic — too big?)" — r1:22); multiple distinct workflows (re-upload, audit, archive, retry/escalation); cross-functional stakeholders (PM + Support + Compliance + Eng).
- Ground truth (r1:174-180) says: "This is likely **Epic-sized**, not single story". Matches.

### 3.2 r2
- **Judgment**: **1 epic, ~5-6 stories**, with mobile as a deferred candidate.
- Signals: multiple UI surfaces (customer web, customer mobile, agent UI, back-office); multiple state classes (review, approved, rejected); cross-domain regulation (sanctions, tipping-off, AML, SAR). Tom's enumeration (r2:84-92) is single-epic-shaped.
- Ground truth (r2:208-216) says: "Epic-sized — split candidates: 6 stories". Matches.

### 3.3 r3
- **Judgment**: **Multi-epic initiative (5-6 epics)**. This is fundamentally different from r1/r2.
- Signals: each `### 3X.` section is itself epic-sized; vendor integration is a separate workstream; biometrics gated by security review (different cadence); legacy data migration is "separate workstream" (r3:111-113, 141). Phase markers ("web first, mobile follow-on in Q4" — r3:122).
- Ground truth (r3:212-220) confirms 6 epics + 1 separate migration workstream. Matches.

**Implication for the skill**: scope detection must distinguish "1 epic, N stories" (r1, r2) from "multi-epic program" (r3). The author should always state explicitly whether the output is one epic-and-stories file or multiple.

---

## 4. Acceptance Criteria Patterns

### 4.1 r1
- **Explicitness**: explicit but informal — author labels it `Acceptance Criteria (rough — from PM)` (r1:51).
- **Format**: bullet prose. Not Gherkin.
- **Testability**: low. Example: `Compliance is happy` (r1:56) is non-testable. `Old document is replaced (or maybe kept as version? unclear)` (r1:54) contains an embedded ambiguity.
- **Implication**: the skill must rewrite each ACs into Gherkin and surface the embedded uncertainty as an *Open Question*.

### 4.2 r2
- **Explicitness**: implied; no AC section.
- **Format**: distilled from Tom's enumeration (r2:84-92) and inline decisions.
- **Testability**: nil as-stated. Decisions like "let's say 'up to 5 business days'" (r2:113-114) need to be rewritten as Gherkin: *Given a wire in additional review, When 5 business days elapse, Then ETA expiry behavior is X*.
- **Implication**: from Slack the skill must *synthesize* ACs from the longest decision chain, not extract them. It must also bucket decisions by who agreed and whether legal/compliance has *blessed* the language ("need legal to bless the language" — r2:64).

### 4.3 r3
- **Explicitness**: implicit. Section 3a-3e contains design decisions that read like proto-ACs.
- **Format**: bullet prose with parenthetical caveats. Example: `"High-risk" definition — Priya suggested using score >= 0.75 from engine, but engine outputs not calibrated yet — Jamie says calibration takes 2 cycles of real data` (r3:90-92) — combines *threshold* + *dependency* + *timeline blocker*.
- **Testability**: requires unpacking. The 0.75 threshold is testable only after calibration — so the AC must be *conditional* and flagged as a dependency.
- **Implication**: meeting-note ACs frequently contain compound clauses (decision + dependency + caveat). The skill needs to split each compound clause into separate fields: an AC, an open question, and a dependency edge.

---

## 5. Dependency Signals

Catalog of every dependency cue observed across the three inputs.

### 5.1 Explicit "Blocks" / "Blocked by"
- r1:121 — `Blocks: LOAN-3001 "Q3 marketing campaign go-live"` — outbound dependency.
- r1:122 — `Relates to: LOAN-2401 "Improve application portal UX" (closed)` — historical/contextual.
- r1:123 — `Possibly relates to: SUPPORT-892 "Reduce manual support load"` — soft dependency, low confidence.

### 5.2 Temporal Hints ("after X" / "before Y" / "by date")
- r1:47 — `Marketing wants this live before the Q3 campaign launch (end of June)` — hard date with downstream consumer.
- r2:152 — `need this in 3 weeks ideally — ops team is bleeding capacity` — soft deadline with business-pain justification.
- r3:42 — `Pressure to reduce EDD cycle to <7 days at p95` — performance target as effective deadline.
- r3:39-40 — `New regulator guidance Q1 2026 ("MAS-AML-1A revision") tightens timeline expectations` — regulatory cadence.
- r3 action items (r3:134-143) — `EOW`, `next sprint`, `by 2026-05-14`, `by next session` — multi-relative due dates, some ambiguous ("EOW = this or next week?" — r1 cross-ref to r3:189).

### 5.3 Cross-references to Other Tickets / Projects
- r1:121-123 — LOAN-3001, LOAN-2401, SUPPORT-892.
- r2:28 — PAY-1192 (closed) — linked Jira inline.

### 5.4 Regulatory Hard Deadlines
- r3:39 — `MAS-AML-1A revision` (Q1 2026) — *citation pending*, treat as a hard dependency until validated.
- r1:44 — `compliance team also asked us to track who replaced what document and when` — soft regulatory pressure, no citation.
- r2:46-47 — `regulated comms`, "we MUST NOT show anything that could be construed as tipping off" — regulatory constraint, not a deadline but a hard scope wall.

### 5.5 External Vendor Dependencies
- r3:71-76 — Acuant API integration (doc detection, liveness, authenticity).
- r3:101-108 — Acuant SLA / pricing / SG residency. **Vendor proposal not yet seen** (r3:104).
- r3:77-79 — Adverse-media vendor — "vendor (?)" — unnamed, **a P2 open question**.
- r2:78-79 — "retrieved funds go back to originator bank" — external bank dependency.

### 5.6 Cross-team / Cross-workstream
- r1:98-99 — "mobile app team is in separate sprint" — cross-team scheduling.
- r2:158-160 — phased prioritization across web → agent UI → mobile.
- r3:111-113 — "migration plan, separate workstream" — separate program.

### 5.7 Calibration / Maturity Dependencies
- r3:90-92 — risk engine score threshold gated by *2 cycles of real-data calibration*. This is a dependency on a data-maturity state, not a date.

**Implication**: the skill must extract these into a dedicated `dependencies` collection per story (and per epic) with at least these subtypes: `blocks`, `blocked_by`, `temporal_deadline`, `regulatory`, `vendor`, `cross_team`, `data_maturity`.

---

## 6. Banking-Grade Field Inference (Where in Structure)

### 6.1 PII Signals
- **Reliable location**: in compliance-named commenters' notes.
  - r1:72-79 — Priya (Compliance) names NRIC + bank statement as sensitive.
  - r2:45-47 — Mei (Compliance) names sanctions context.
  - r3:114-117 — Priya (Compliance) on partial-PII retention.
- **Less reliable**: in PM descriptions where PII is *implicit* (e.g., r1:36-38 mentions "ID, bank statement" without tagging them sensitive — the skill must lift them out).
- **Heuristic**: search for terms `NRIC | passport | ID | bank statement | source of funds | DOB | account | identity document | biometric`.

### 6.2 Audit Requirements
- **Reliable location**: compliance commenter blocks.
  - r1:72-79 — "audit trail for any document replacement. Show me what got replaced, who replaced it, when, and any reason given."
  - r3:84-86 — "Low-risk: analyst sole decider, audit trail required".
  - r2:204 (in ground truth) — "Audit trail for state transitions (regulatory — must be logged)" — i.e., the ground truth expects audit emission for r2 even though it isn't stated explicitly in the chat body.
- **Heuristic**: any "who/what/when/why" tuple from a compliance party = audit requirement. Also: every state transition in a workflow ≈ audit-emission candidate.

### 6.3 Compliance References
- **Reliable location**: regulatory citations and named compliance officers.
  - r3:39 — "MAS-AML-1A revision".
  - r2:46-47 — "regulated comms", "tipping off".
  - r1:75-78 — "data retention policy" by name (v3.2 PDF referenced).
- **Heuristic**: parser should scan for `MAS | OJK | FATF | AML | KYC | EDD | CDD | PEP | sanctions | tipping off | SAR | suspicious activity | adverse media | data retention | residency | tipping-off`.

### 6.4 Idempotency / Reversibility Hints
- **r1:170-172** (ground truth) — "Idempotency — re-upload same file shouldn't double-trigger anything" and "Reversibility — can applicant revert to old document?". *Body never says this explicitly* — the skill must infer it from the workflow shape (any replace operation invites these questions).
- **r2:204** (ground truth) — "Idempotency on customer notifications (don't email twice on same state change)". Same pattern: inferred, not stated.
- **r3:205** (ground truth) — "Idempotency: re-submission of same docs shouldn't create duplicate cases". Inferred.
- **Implication**: idempotency + reversibility are **rarely stated in raw input**. The skill must *always* generate these as questions/concerns for any mutation, state transition, or notification operation.

### 6.5 Non-functional Requirements (SLAs, Performance, Volume)
- **r3:106-107** — "SLA: 99.9% uptime committed, P95 latency <2s per call" — vendor SLA in Vendor Discussion section.
- **r3:42** — "Pressure to reduce EDD cycle to <7 days at p95" — domain SLA in Context section.
- **r2:43** — "agent capacity ↑40% on wire status questions" — volume signal (not exactly SLA, but capacity).
- **r1:39-41** — "last week we had 142 such cases, average resolution time 4 hours" — current-state volume baseline.
- **r3:74-75** — "throughput concern — adverse media vendor (?) rate-limited at X requests/min" — performance constraint with unknown value.
- **Heuristic**: NFRs scatter across context, vendor, and engineering-voice comments. The skill should collect them into a single NFR cluster on the epic.

---

## 7. Source-Type-Specific Parsing Patterns

### 7.1 Jira (r1)
- **Reliable signal locations**:
  - Header block (lines 20-30) → metadata, priority, labels.
  - `## Description` → problem statement + business trigger.
  - `## Linked Issues` → dependency edges (typed: blocks/relates).
  - `## Comments` (chronological, named) → refinement, decisions, open questions, stakeholder positions.
- **Common noise**:
  - The "Anonymous (likely Raj)" comment (r1:103-104) — author attribution is fuzzy; do not lose the signal but flag the uncertainty.
  - Closed/historical relates-to links (LOAN-2401 closed) — useful context, not active dependency.
- **Special syntax**:
  - `@mentions` (e.g., `@Sarah`, `@Priya`, `@Raj` — r1:81, 95, 98) — directed asks; the addressee is the implicit answer-owner.
  - Ticket IDs `LOAN-XXXX`, `SUPPORT-XXXX` — anchor for dependency resolution.
  - Author labels include role (`Mike Chen (Support Lead)`, `Priya Naidoo (Compliance)`) — robust role inference.
- **Inversion patterns**: Jira comments are chronological top-down — **opposite** of email threads.

### 7.2 Slack (r2)
- **Reliable signal locations**:
  - First message of the thread = the trigger ("getting a LOT of escalations" — r2:21-25).
  - Mid-thread summary message ("ok let me draft. so the asks are roughly: 1… 2… 3… 4…" — r2:84-92) is a high-density story-inventory anchor.
  - Final messages ("ok let me write this up as a ticket" — r2:144; "yes go ahead" — r2:148) = ownership handoff.
- **Common noise**:
  - Emoji-only messages ("👍" — r2:62, 63, 163).
  - Off-topic side branches (none egregious in r2 but flagged as a likely shape).
  - Pronoun ambiguity ("it", "this", "they") — explicitly called out in r2:8-12 metadata. The skill must resolve antecedents.
- **Special syntax**:
  - Names with role parens (`Jenny Wong (Ops Manager)`, `Mei Park (Compliance)`).
  - Relative timestamps ("Today HH:MM").
  - In-line Jira link with `📎 Linked: PAY-1192`.
  - Emoji reactions and aggregate reactions ("[Thread reactions: 12 🙏 from various ops folks]" — r2:165) — *implicit endorsement*, not formal sign-off.
- **Inversion patterns**: Slack threads are oldest-first; replies within a sub-thread can be out-of-order vs main channel. In r2 the body is a single linear thread; the skill should not assume that's always the case.

### 7.3 Meeting Notes (r3)
- **Reliable signal locations**:
  - Attendee block (r3:24-31) with explicit absences ("Apologies: Legal — Sundar K." — r3:31) → stakeholder gap detection.
  - Numbered agenda sections (`## 1. Context`, `## 2. Current State Pain Points`, …) → canonical structure.
  - `## 6. Action Items` (r3:132-143) → bracketed owner + deliverable + due date.
  - `## 8. Parking Lot` → out-of-scope / future-epic seeds.
- **Common noise**:
  - Note-taker editorial asides ("(this got assigned to me at the end — see 'next steps')" — r3:140-141; "David wants it tomorrow latest. Sigh." — r3:147). Drop or preserve verbatim but never treat as decisions.
  - Paraphrased speaker attribution — note-taker's filter (r3:11) means quotes are *not* verbatim. Confidence on quoted decisions drops.
- **Special syntax**:
  - `[Apologies: …]` for absentees.
  - Bracketed action-item owners: `[David]`, `[Priya]`, etc.
  - `(Hua, 15 min)` — section time-boxing reveals speaker for that section.
  - `→` for nested resolution notes after a numbered question.
  - TBD / unconfirmed markers — explicit, surface as open questions.
- **Inversion patterns**: meeting notes follow agenda order, *not* importance order. Story-relevance scoring requires re-ranking sections.

---

## 8. Implications for Skill Design

Concrete recommendations for the `ba-elicit-from-raw` skill:

1. **Detect source type first, then dispatch to a source-specific parser.** Use these tells:
   - Jira → key:value header (`Project:`, `Reporter:`, `Priority:`), `## Description`/`## Acceptance Criteria` headings, `## Linked Issues`.
   - Slack → channel banner (`#channel`), `Name (Role) — Today HH:MM` pattern, emoji reactions, `📎 Linked:` lines.
   - Meeting notes → date+time header, `Attendees:` list with apologies, numbered agenda, `[Owner] task` action-item brackets.
   - Default fallback: prose-document parser (lowest confidence).

2. **Strip the "Intentional Issues for R6 to Catch" annotation block** before any parsing. It begins with the literal header `## Intentional Issues for R6 to Catch` and is training-set ground truth, not user input. Production inputs will not contain it; if it does appear, the skill must refuse to consume it (and could optionally use it for self-evaluation in `audit/` mode only).

3. **Always extract dependency signals into a dedicated field** with subtypes: `blocks`, `blocked_by`, `temporal_deadline`, `regulatory_deadline`, `vendor`, `cross_team`, `data_maturity`. Never inline a dependency into a story description without also surfacing it in the dependency list.

4. **Treat compliance-named commenters as authoritative for PII / audit / regulatory fields.** Match the speaker against a small known-role lexicon (`Compliance | Legal | Risk | Security`). Their utterances should be promoted to AC-grade requirements, even if delivered conversationally.

5. **Generate idempotency and reversibility concerns from workflow shape, not text.** For every mutation, state transition, replace operation, or outbound notification, the skill must emit at least one "Banking-Grade Concerns" entry asking whether the operation is idempotent / reversible / requires a compensating action. These are *almost never* stated in raw input.

6. **Convert every existing AC line into Gherkin and flag embedded ambiguities.** When source ACs contain words like "maybe", "unclear", "probably", "or version?" (r1:54), split into: a Gherkin scenario *and* an Open Question. Never silently drop the ambiguity.

7. **Detect story boundaries by stakeholder concern, not by section heading alone.** Each named compliance/risk/security/UX participant typically introduces at least one story. In r1 this gives the right answer (5 stories); in r2 a draft-enumeration message is the spine; in r3 it's the numbered re-design subsections.

8. **Distinguish "single epic" vs "multi-epic program" up front.** Use these signals:
   - Number of distinct workflows touched (>3 → suspect multi-epic).
   - Presence of "phase 1 / phase 2" or "Q3 / Q4" language.
   - Vendor-integration cluster as a self-contained block (it's usually its own epic).
   - Migration / legacy-data references = separate workstream (separate epic).
   Produce a top-level `scope_kind: single-epic | multi-epic` value and adjust output accordingly. r3 must emit ~5-6 epic files; r1/r2 emit one each.

9. **Capture stakeholder gaps explicitly.** Maintain a known role checklist (`Legal | Compliance | Security | Risk | Mobile | Data/Analytics | Customer Support`) and emit an open question for every role mentioned-but-not-engaged or absent-but-decision-relevant (e.g., the `[Apologies: Legal — Sundar K.]` marker in r3 should auto-generate a P1 gap entry).

10. **Preserve quote provenance.** Every story / AC / dependency drawn from raw text should carry a `source_quote` and `source_line_ref` so TL review can trace anything back. The template's frontmatter already supports `source_ref`; extend per-story too.

11. **Handle author-attribution uncertainty.** When a comment is anonymous-but-likely-X (r1:103 — "Anonymous (likely Raj)"), record both the attributed author and a confidence flag. Do not collapse to one.

12. **Treat emoji and informal endorsements as soft evidence only.** A 👍 from compliance ≠ a formal sign-off. Generate a follow-up open question ("Confirm written approval from {role} for {decision}") whenever an emoji is the only evidence of agreement on a compliance-touching item.

13. **Pull NFRs into a single cluster.** SLAs (r3:106-107), throughput (r3:74-75), volume baselines (r1:39-41), p95 targets (r3:42) — they scatter. Collect them into a single epic-level "Non-Functional Requirements" block to surface to the TL.

14. **Resolve relative dates against the input's metadata date.** "EOW" (r3:134), "next session" (r3:135), "3 weeks" (r2:152), "Today" (r2 timestamps) are all relative. The skill must compute absolute ISO-8601 dates using the input's Created/Date metadata; where the source is ambiguous (EOW = this/next week), emit an open question rather than guessing.

15. **Always emit a Parking Lot / Out-of-Scope section in the output.** Both explicit (r3:151-157) and implicit (r1 "abandoned applications — separate ticket" — r1:84-86; r2 mobile parity — r2:158-160). The output template (`tpl:67-73`) already has Out-of-Scope Deferred; populate it consistently.

16. **Apply different confidence weighting per source type.** Meeting notes carry note-taker paraphrasing risk (r3:11 explicitly admits this); slack carries pronoun ambiguity; Jira carries the cleanest signal but oldest comments may be stale. Confidence should be encoded in `ba_confidence: high | medium | low` per the template (tpl:18) — meeting-notes-only input rarely earns "high".

17. **For every state in a state machine, emit at least one notification + audit question.** r2 surfaces this gap (notification policy for each transition asked late, answered partially). The skill should pre-empt the gap: for every state introduced (review, approved, rejected, on-hold, escalated), generate (a) a notification AC, (b) an audit-emission AC, (c) a tipping-off check if regulatory context applies.

18. **Recognize hedged language as a deferred-decision marker.** Phrases like "maybe", "ideally", "we may need to", "probably", "TBD", "(?)" should be detected and each occurrence escalated to an Open Question in the output rather than silently captured as fact.

---

*End of Phase A3 analysis — informs Phase B parser design and Phase C output mapping.*
