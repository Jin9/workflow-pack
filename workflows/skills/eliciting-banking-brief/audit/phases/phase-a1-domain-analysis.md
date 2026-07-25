# Phase A1 — Domain Anthropology: Vocabulary & Patterns

> **Role**: Domain Anthropologist for BA Skill Factory
> **Inputs analyzed**: 3 raw requests across Lending (001), Payments (002), KYC/Onboarding (003)
> **Mission**: Extract domain vocabulary, concept maps, conventions, smells, and skill design implications
> **Audience**: Downstream sub-agents designing the `ba-elicit-from-raw` atomic skill
> **Method**: Cross-source pattern recognition; quote-anchored evidence; explicit confidence tagging

---

## 0. Executive Orientation

Across three distinct source types — a Jira ticket (lending), a Slack thread (payments), and meeting notes (KYC/EDD) — a coherent **banking BA dialect** emerges. The dialect blends:

- **Regulator-anchored compliance terminology** (AML, sanctions, PEP, EDD, MAS, SAR, tipping-off, retention periods)
- **Operational ticket vocabulary** (priority, sprint, epic-vs-story, AC, sponsor, owner, blocker)
- **Product/UX language** (CSAT, NPS, status page, applicant experience, push notif)
- **Engineering shorthand** (rate-limit, P95 latency, schema change, idempotency, throughput, spike)
- **Vendor/integration jargon** (Acuant, biometric add-on, SLA 99.9%, data residency)

The three inputs co-instantiate a recurring **conflict pattern**: customer-facing simplicity vs back-office granularity vs regulator-mandated opacity. Each domain expresses it differently (loan re-upload audit, wire-hold messaging, EDD applicant status) but the structural tension is identical.

The skill must therefore treat banking vocabulary not just as keywords but as **multi-stakeholder semantic loadings** where the same word means different things to compliance, ops, eng, and customer.

---

## 1. Domain Vocabulary Catalog

Below: 32 terms harvested across the three inputs. Quotes use the pattern `NNN:Lxx` where `NNN` is the input file number and `Lxx` is the line number in the raw file.

### 1.1 Core Banking & Compliance Terms

| # | Term | Inferred meaning in domain | Example occurrences | Confidence | PII / Sensitive? |
|---|---|---|---|---|---|
| 1 | **KYC** (Know Your Customer) | Regulatory process to verify customer identity at onboarding. Implicit baseline for EDD escalation. | 003: title, frontmatter "KYC / Customer Onboarding" (003:L4) | high | Yes (process touches PII) |
| 2 | **EDD** (Enhanced Due Diligence) | Stepped-up KYC for elevated-risk customers; triggered by flags. Cycle time 11d avg, target <7d p95 (003:L38-41). | "EDD Workflow Re-design" (003:L18), "EDD process: triggered manually by analyst when onboarding flag fires" (003:L36) | high | Yes |
| 3 | **AML** (Anti-Money Laundering) | Regulatory regime governing money laundering prevention. Drives sanctions screening, SAR filing. | "your wire is flagged for AML review" (002:L40) | high | Yes (in workflow context) |
| 4 | **Sanctions screening** | Automated check of parties against sanctions lists (OFAC, UN, MAS, etc.). Drives "hold" state on wires. | "we tightened sanctions screening last sprint" (002:L24-25), "sanctions hold" (002:L46), "rejected for sanctions reason" (002:L73) | high | Yes (results = regulated) |
| 5 | **PEP** (Politically Exposed Person) | Risk classification triggering enhanced scrutiny per FATF/local AML. | "PEP screening is run only at end" (003:L56), "PEP, sanctions, adverse media — all run automatically" (003:L77) | high | Yes |
| 6 | **Adverse media** | Negative news screening against an applicant; component of EDD. Currently manual google searches (003:L57). | "Adverse media screening — manual google searches" (003:L57), "adverse media vendor (?)" (003:L78) | high | Yes (results categorize person) |
| 7 | **Tipping-off** | Regulatory prohibition: must not tell customer they're under AML/sanctions review. Forces vague customer messaging. | "we MUST NOT show anything that could be construed as tipping off" (002:L66-67), "can't tip off if EDD escalates to SAR" (003:L96) | high | Yes (regulatory) |
| 8 | **SAR** (Suspicious Activity Report) | Confidential regulator filing when suspicious behavior detected. Cannot be disclosed to customer. | "we file the appropriate suspicious activity report" (002:L80-81), "EDD escalates to SAR" (003:L96) | high | Yes (regulatory) |
| 9 | **MAS** (Monetary Authority of Singapore) | Singapore's central bank & financial regulator. Source of the AML guidance referenced. | "MAS-AML-1A revision" (003:L39), "Share MAS regulator citation" (003:L134) | high | No (public regulator name) |
| 10 | **Data residency** | Rule about geographic location of data storage; SG residents → SG region. Vendor-feature negotiation point. | "Data residency: Acuant offers SG region — Priya confirmed acceptable" (003:L107-108) | high | Indirect (impacts PII storage) |
| 11 | **Retention (period)** | How long data is stored; 7-year baseline appears across inputs. Drives archive-vs-delete workflows. | "Retention: 7 years" (001:L74), "Delete after 7 years YES" (001:L85), "7 years for completed, 30 days for abandoned" (003:L114-115) | high | Indirect (governs PII lifecycle) |
| 12 | **Audit trail** | Immutable log of who-did-what-when; required for compliance scrutiny. | "We need an audit trail for any document replacement" (001:L72), "audit trail required" (003:L88), "audit trail for state transitions" (002:L204 hidden) | high | Sometimes (logs can contain PII) |
| 13 | **NRIC** | Singapore National Registration Identity Card number; explicit PII. | "expired NRIC photos (about 40%)" (001:L68), "NRIC, financial statement" (001:L77) | high | Yes (national ID) |
| 14 | **Source of funds** | KYC artifact proving legitimate origin of customer money; most variable EDD step. | "Source-of-funds verification — most variable step, ranges 1-9 days" (003:L58-59) | high | Yes (financial PII) |
| 15 | **Liveness check** | Biometric anti-spoofing on selfie / ID photo. Vendor-provided. | "Acuant API can do document type detection + liveness check + authenticity scoring" (003:L72-73) | high | Yes (biometric data) |
| 16 | **Authenticity scoring** | Vendor signal on whether an ID document is genuine. | Same line as above (003:L72-73) | high | Indirect |

### 1.2 Payments & Lending Operational Terms

| # | Term | Inferred meaning in domain | Example occurrences | Confidence | PII / Sensitive? |
|---|---|---|---|---|---|
| 17 | **Wire (transfer)** | High-value funds transfer through banking rails. Subject to sanctions screening. | "inbound wire desk" (002:L23), "their wires are stuck" (002:L23), "compliance ultimately rejects the wire" (002:L72) | high | Indirect (financial data) |
| 18 | **Originator bank** | Bank that initiated a wire transfer; receives returned funds on rejection. | "retrieved funds go back to originator bank" (002:L75) | high | No |
| 19 | **Hold / On hold** | Wire state suspending settlement pending review (sanctions or ops second-eye). | "wires are stuck 'on hold' for >24h" (002:L23-24), "sanctions hold" (002:L46), "compliance hold vs ops second-eye review" (002:L38) | high | No (state label) |
| 20 | **Second-level review / second-eye** | Ops verification by a second human; same-day SLA. Distinct from compliance hold. | "pending second-level review" (002:L29), "ops second-eye review" (002:L38), "for ops second-eye it's same day 95% of the time" (002:L55) | high | No |
| 21 | **Applicant / Applicant portal** | Loan or onboarding customer who has applied but not yet been approved. The end-user UI is the "application portal". | "applicants are getting stuck" (001:L36), "application portal" (001:L39), "Applicant can re-upload from the application portal" (001:L52) | high | Indirect (account holder) |
| 22 | **Loan origination** | End-to-end process from application to disbursement; the lending domain. | Frontmatter "Lending / Loan Origination" (001:L4) | high | No |
| 23 | **Document re-upload** | Self-service workflow allowing applicant to replace previously uploaded doc (the 001 ticket subject). | "Add document re-upload feature for loan applicants" (001:L20) | high | Indirect |
| 24 | **Onboarding** | New-customer creation flow including KYC. | "Onboarding 2.0 Working Session" (003:L17), "Head of Onboarding" (003:L25) | high | Indirect |
| 25 | **Risk decision engine / Risk engine** | Internal model that classifies applicant risk; consumes structured fields, outputs score. | "Risk decision engine input is partial" (003:L54), "engine pre-classifies" (003:L82), "score >= 0.75 from engine" (003:L89-90) | high | Yes (consumes PII) |
| 26 | **Tiered approval routing** | Routing of decisions by risk tier; low/medium/high with different approver requirements. | "Tiered approval routing" (003:L85), "Low-risk: analyst sole decider... High-risk: senior analyst + compliance officer dual approval" (003:L87-89) | high | No |
| 27 | **Dual approval** | Two-approver requirement for high-risk decisions. Banking control pattern. | "senior analyst + compliance officer dual approval" (003:L88) | high | No |
| 28 | **Disbursement** | Release of approved loan funds to applicant (implied lifecycle end-state). | Implied via "faster path to loan decision" (001:L129) and "loan origination" framing | medium | Indirect |

### 1.3 Process / Project Mechanics Vocabulary

| # | Term | Inferred meaning in domain | Example occurrences | Confidence | PII / Sensitive? |
|---|---|---|---|---|---|
| 29 | **Epic / Story** | Agile story-size hierarchy; epic = collection of stories. Repeatedly hits ambiguity. | "Type: Story (but might need to be Epic — too big?)" (001:L24), "let me write this up as a ticket" (002:L143) | high | No |
| 30 | **Acceptance Criteria (AC)** | Conditions a story must meet to be accepted by PO. Often missing or "rough". | "Acceptance Criteria (rough — from PM)" (001:L51) | high | No |
| 31 | **Sponsor / Owner** | Who funds (sponsor) vs who delivers (owner) the initiative. Often vague. | "Sarah can you sponsor?" (002:L143), Aisha as note-taker also assigned BA brief owner (003:L139-140) | high | No |
| 32 | **Spike** | Time-boxed exploration ticket; uncertainty-resolution effort. | "Karim — Spike on Acuant biometric API security review path" (003:L135) | high | No |

**Additional terms harvested but not tabulated (worth tracking)**: P95 latency, SLA, in-app, push notif, CSAT, NPS, throughput, idempotency (in hidden sections only — implied in main text via "shouldn't double-trigger"), wireframes, parking lot, action item, in-flight migration, schema change.

---

## 2. Domain Concept Map

### 2.1 Hierarchy (taxonomic relations)

```
Banking Operations
├── Customer Onboarding
│   ├── KYC (baseline)
│   │   └── EDD (enhanced tier)
│   │       ├── PEP screening
│   │       ├── Sanctions screening
│   │       ├── Adverse media screening
│   │       ├── Source-of-funds verification
│   │       └── Risk decision engine scoring
│   └── Document collection
│       ├── Identity docs (NRIC, passport)
│       ├── Liveness check
│       └── Authenticity scoring
├── Lending / Loan Origination
│   ├── Application intake
│   ├── Document upload / re-upload
│   ├── Underwriting decision
│   └── Disbursement
├── Payments / Wire transfers
│   ├── Customer-initiated transfer
│   ├── Compliance hold (AML/sanctions)
│   ├── Ops second-eye review
│   ├── Approval → Settlement
│   └── Rejection → Return to originator
└── Cross-cutting controls
    ├── Audit trail (universal)
    ├── Data retention (universal)
    ├── Tipping-off prohibition (compliance-driven)
    ├── PII handling
    └── Dual / Tiered approval
```

**Confidence**: high for the cross-cutting controls being shared across all three domains; medium for sub-tree completeness (real banking has many more leaves).

### 2.2 Process Flows (sequential states)

**A. Loan application re-upload (001)** — workable state machine:
```
applied → docs uploaded → docs verified
                       └→ verification failed → support flagged → 
                          [old: manual re-upload link by support agent]
                          [new: self-service re-upload] →
                          re-upload attempt (≤3?) → 
                                  ├→ verified → continue
                                  └→ failed again → escalate to support
```
Old doc lifecycle: `replaced → archive (7y) → delete`. Confidence: high (explicit at 001:L39-41, L74-85).

**B. Wire transfer with compliance review (002)** — dual-state model:
```
[Customer-facing path]:
processing → additional review (ETA up to 5 business days) → 
    ├→ approved → settled (notify: email + in-app)
    └→ transfer could not be completed (notify: generic email)

[Internal/back-office path]:
submitted → 
    ├→ compliance hold (24-72h SLA)
    └→ ops second-eye (same-day 95%)
→ approved | rejected
```
Confidence: high. The split between customer-visible and internal states is the central artifact (002:L97-99).

**C. EDD workflow (003)** — current vs target:
```
[Current state]:
flag triggered manually → analyst opens case → docs collected piecemeal → 
analyst summarizes risk in prose → PEP screen (LATE) → adverse media manual → 
source-of-funds verified → approval (unclear routing) → decision
Cycle time: 11 days avg, up to 22

[Target state]:
flag fires → single intake portal → 
upfront screening (PEP + sanctions + adverse media, automated, <1h target) → 
risk engine consumes structured fields → 
tiered routing (low: analyst / med: peer / high: senior+compliance dual approval) → 
decision (audit-trailed) → applicant status updates
Cycle time target: <7 days p95
```
Confidence: high.

### 2.3 Entity Types

**Actors (people / roles)**:
- *Product Manager* — Sarah Lim (001), Sarah Khoo (002). Origin role for tickets; defines AC; sponsor candidate.
- *Compliance Officer* — Priya Naidoo (001, 003), Mei Park (002). Gatekeeper for retention, tipping-off, screening, language approval.
- *Engineering Lead / Manager / Eng* — Raj Patel (001), Tom Becker (002), Karim El-Sayed (003), Raj Sharma (002). Surfaces technical constraints (rate limits, schema changes, file sizes).
- *Support Lead / Ops Manager* — Mike Chen (001), Jenny Wong (002). Owns operational pain; provides volume metrics.
- *Risk Analytics* — Jamie Foster (003). Owns the risk engine model and calibration.
- *Vendor liaison* — Hua Liu (003 — Acuant). External-product interface.
- *CX Designer* — Ben Stewart (003). Owns wireframes / applicant experience.
- *Junior PM / Note-taker* — Aisha Rahman (003). Captures and converts notes.
- *Head of Department / Chair* — David Lim (003). Authoritative decision-maker.
- *Legal* — Sundar K. (003 — absent), Mei refers to legal in 002, Priya defers to Legal in 001. Conspicuously absent or referenced-without-engagement in all three.
- *Customer / Applicant* — End-user, never present in the conversation.

**Artifacts**:
- Documents: NRIC, bank statement, source-of-funds proof, ID photo, biometric capture
- Cases: loan application, wire transfer, EDD case
- States: hold, approved, rejected, additional review, in review, abandoned
- Records: audit trail entries, SAR filings, screening results
- UI surfaces: application portal, customer-facing status, agent dashboard, manager dashboard, status page, wireframes
- Logs: support call analysis xlsx (001:L114), retention policy PDF (001:L115)
- Tickets/Tracking: LOAN-2847, PAY-1192, LOAN-3001, LOAN-2401, SUPPORT-892

**Events / triggers**:
- Document re-upload requested
- Wire put on hold
- EDD flag fires
- Re-upload verification failure (escalation trigger)
- State transition (notification trigger)
- Sanctions match (SAR consideration)

**Rules / Policies**:
- 7-year retention for completed records (001, 003)
- 30-day retention for abandoned applications (003 — pending legal)
- Tipping-off prohibition (002, 003)
- Dual approval for high-risk (003)
- File size limit 10MB (001)
- Re-upload limit ≈ 3 attempts (001 — unconfirmed)
- ETA up to 5 business days for "additional review" (002 — conservative bucket)

Confidence: high across entity-type breakdown; specific rules tagged where uncertain (above).

---

## 3. Domain Conventions

### 3.1 Naming Conventions

- **Ticket IDs**: `PROJECT-NNNN` pattern. Observed: `LOAN-2847`, `LOAN-3001`, `LOAN-2401` (lending project), `PAY-1192` (payments), `SUPPORT-892` (support). Confidence: high. The skill must recognize this pattern as a citation reference.
- **Regulator citations**: `<Regulator>-<Topic>-<Code>` pattern. Observed: `MAS-AML-1A revision` (003:L39). Implied form: jurisdictional regulator code, area, version. Confidence: medium (one example, but format is widespread in banking).
- **Sprint references**: "this sprint", "next sprint", "next available". Loose, not numbered. Confidence: high.
- **Date references in tickets**: ISO-8601 with timezone — `2026-05-08 09:32 GMT+7` (001:L29). Strong convention in the formal Jira format; less consistent in Slack ("Today 09:14" — 002:L21) and meeting notes ("2026-05-07 (Thursday) Time: 14:00-15:30 GMT+7" — 003:L19).
- **Quarter labels**: `Q3 2026`, `Q3 campaign`, `Q4` (001:L47, 003:L121). Confidence: high.
- **People labels in Slack**: `Name (Role) — Today HH:MM` (002:L21). Roles always parenthetical at first mention.
- **Action items**: bracketed-owner pattern — `[David] Share MAS regulator citation — EOW` (003:L134). Confidence: high.

### 3.2 Date / Number Formats

- Dates: ISO-8601 (`YYYY-MM-DD`) in Jira and meeting notes; relative ("Today", "EOW", "by next session") in Slack and informal contexts. Mixing is common — the skill must normalize.
- Timezone: `GMT+7` explicit on Jira and meeting headers; absent in Slack chat. Singapore context confirmed by `MAS` and `SG region`. Confidence: high.
- Time targets: SLAs expressed as percentile (`p95 < 7 days`, `P95 latency <2s` — 003:L41, L105), uptime (`99.9% uptime` — 003:L105), or bucketed ("24-72h", "same day 95% of the time", "up to 5 business days" — 002:L55, L113).
- Counts: bare numerals with units ("142 such cases", "4 hours", "560 hours/week", "~140 cases/week"). Confidence: high.
- Cost: redacted as `~$Xk/year` (003:L104) when not yet disclosed — useful pattern to recognize as TBD.

### 3.3 Communication Style per Source Type

- **Jira ticket (001)**: Hybrid — structured headers ("Description", "Acceptance Criteria", "Comments", "Attachments", "Linked Issues") with conversational comment threads embedded. Decisions emerge across multi-day comment exchanges. Tone: professional but candid (Sarah's "OK creating this ticket for handoff" at 001:L106-108 reveals organic process).
- **Slack thread (002)**: Conversational, lowercase, emoji-laden ("👍", "😅"), pronoun-heavy ("it", "this"), decisions encoded as `👍` reactions (002:L62, L64). Side topics interleaved (Raj's mobile question at 002:L101). No headings. The "ok let me draft. so the asks are roughly:" turn (002:L84-92) is the closest thing to a structured summary, but it's an informal draft.
- **Meeting notes (003)**: Semi-structured outline with numbered sections (Context, Pain Points, Proposed Re-design, Vendor Discussion, Open Questions, Action Items, Next Steps, Parking Lot). Mix of paraphrase and direct quotes. Note-taker bias visible ("Sigh." at 003:L143). Confidence: high.

The skill must **adapt elicitation strategy by source-type** — Slack requires pronoun resolution; meeting notes require owner-disambiguation on action items; Jira requires reconciling stated AC with comment-thread amendments.

### 3.4 Decision-Making Patterns

- **PM is reporter / sponsor, not decider on compliance topics**. Sarah Lim defers retention to Priya (001:L80). Sarah Khoo confirms priority but defers compliance language to Mei (002:L143-148).
- **Compliance holds veto over customer-facing language** (002, 003). Tipping-off rules trump UX preferences. Confidence: high.
- **Eng owns scope reality-checks**. Tom Becker drafts the synthesized asks (002:L84-92). Raj Patel surfaces technical questions about limits (001:L88-94). Karim flags security-review path for biometric (003:L101-103).
- **Legal is absent but cited**. All three inputs reference legal as a future blocker without engaging legal directly. Confidence: high. This is itself a domain pattern.
- **Decisions made by 👍 reaction or "ok let's do that"** (002 — "ok so customer-facing: bucket the hold reasons into a generic 'additional review' status with an ETA range. backend keeps the real reason. agree?" → 👍, 002:L57-62). Risky from a BA perspective: no formal sign-off paper trail.
- **Anonymous suggestions accepted as defaults**. "N could be 3" (001:L103) — anonymous comment becomes the working assumption.

---

## 4. Domain "Smells" (recurring complexity patterns)

### 4.1 Areas Where Requirements Get Vague

- **Versioning vs replacement of documents** (001:L54). "Old document is replaced (or maybe kept as version? unclear)" — directly flagged unclear. Recurring banking question: immutable archive vs mutable version chain.
- **Abandoned / partial states**. Mentioned in all three: "if applicant abandons their application, what happens to the docs?" (001:L82-83), "30 days for abandoned — need to confirm with Legal" (003:L115). Skill should expect this gap.
- **Retry limits with vague "N"**. "Multiple re-uploads — probably need limit but not sure what's reasonable" (001:L98-99) followed by "N could be 3" (001:L103). The "after N attempts" placeholder pattern recurs.
- **ETA bucketing**. Mei's "up to 5 business days" (002:L113) is conservative but masks two underlying SLAs (24-72h vs same-day). Skill must surface when a single bucket flattens multiple realities.
- **Threshold definitions without calibration**. "score >= 0.75 from engine, but engine outputs not calibrated yet" (003:L89-91). Risk-tier thresholds frequently appear before the underlying signal is stable.
- **Mobile-vs-web parity**. All three inputs mention mobile as deferred ("mobile app team is in separate sprint" 001:L98, "web first" 002:L107, "mobile follow-on in Q4" 003:L121). Always declared, rarely resolved.

### 4.2 Areas Where Stakeholder Conflict Surfaces

- **Compliance vs UX**: "5 days feels long for the 95% case…" (Tom, 002:L116) vs "reputational risk on the long tail. legal will probably push the same way" (Mei, 002:L118). Productivity-comfort vs blast-radius-aversion.
- **Engineering capacity vs deadline pressure**: "3 weeks for the customer-facing piece probably doable. agent UI changes might slip a sprint" (Tom, 002:L154-156) vs "need this in 3 weeks ideally — ops team is bleeding capacity" (Jenny, 002:L152).
- **Product cleanliness vs ticket reality**: "Type: Story (but might need to be Epic — too big?)" (001:L24). PMs often default to "Story" then discover Epic-scale work.
- **Vendor recommendation vs in-house preference**: Karim flags Acuant biometric needs security review (003:L102-103), introducing friction into Hua's clean integration story.
- **Compliance vs Legal**: Priya defers to Legal multiple times (001:L80, 003:L115), but Legal is unavailable. Compliance has authority over policy but Legal has authority over its interpretation.

### 4.3 Areas Where Regulatory / Compliance Hints Appear

- **Tipping-off language constraints** (002:L66-67, 002:L80, 003:L96). Customer-facing copy must be approved.
- **Retention periods** (001:L74, 001:L85, 003:L114-115). Always cited but rarely tied to a written policy on-screen — Priya says "I'll send the policy doc separately" (001:L77-78).
- **Audit trail requirements** (001:L72, 003:L88). Always asked for, rarely scoped.
- **Data residency** (003:L107). Country-specific storage requirement.
- **Dual approval requirements** (003:L88). Required for high-risk; control-pattern smell.
- **SAR workflows** (002:L80-81, 003:L96). Mentioned in passing — must be respected but never scoped.
- **Sanctions screening** (002:L24-25, 003:L77). Treated as commodity, but parameter changes ("we tightened…") have downstream cascading effects.
- **Regulator citations** (003:L39). Cited by reference, often without the actual document attached.

### 4.4 Areas Where Information is Lost

- **Pronoun ambiguity**: 002 is dense with "it", "this", "they" referring back to entities mentioned 5-10 lines earlier (e.g., "showing same thing to the customer is sort of by design" 002:L37-38 — "thing" = the queue/state).
- **Attachments not attached**: "support-call-analysis-week-2026-w18.xlsx (not analyzed in detail here)" (001:L114), "compliance-data-retention-policy-v3.2.pdf (referenced by Priya, not attached)" (001:L115), David's slides "not attached here" (003:L65).
- **Action items without dates**: "Loop legal in next time" (003:L142), "Identify migration workstream owner — by next session" (003:L141) — relative deadlines that depend on inferred dates.
- **Roles inferred from context, not stated**: "Anonymous (likely Raj)" (001:L103). Skill must surface attribution gaps.

---

## 5. Implications for Skill Design

This section translates anthropological findings into concrete recommendations for the downstream `ba-elicit-from-raw` skill designers. Five recommendations:

### 5.1 Maintain a Structured "Domain Glossary" Field in Output

The skill should emit a **glossary object** alongside its primary brief, listing every domain term encountered with:
- canonical form (`enhanced_due_diligence`)
- surface form as quoted (`EDD`, `Enhanced Due Diligence`)
- inferred definition with confidence
- PII / sensitivity flag
- regulatory tie (if any)

Rationale: Three different sources used **the same regulatory vocabulary** (tipping-off, SAR, sanctions, retention) in three different framings. Downstream consumers (TL, risk reviewer, R6 ambiguity reviewer) need a single resolved vocabulary table to disambiguate. Without it, every reviewer re-parses the same dialect from scratch.

### 5.2 Recognize a Fixed Set of Banking-Grade Citation Patterns

The skill must regex-detect and surface as first-class artifacts:
- Ticket IDs: `[A-Z]+-\d+` (e.g., `LOAN-2847`, `PAY-1192`)
- Regulator citations: `[A-Z]+-[A-Z]+-[A-Z0-9-]+` (e.g., `MAS-AML-1A`)
- Document references with attachments not attached (`*.pdf`, `*.xlsx` mentioned but not opened)
- Date deadlines including relative forms (`EOW`, `by next session`, `Q3`, `end of June`)
- Percentile SLAs (`p95 < 7 days`, `P95 latency <2s`, `99.9% uptime`)
- Money placeholders (`~$Xk`, `TBD pricing`)

Each surfaced reference should be flagged as **resolved** (citation provided, file linked) or **unresolved** (cited but missing). Unresolved references should populate an "open dependencies" list because R6 will need them.

### 5.3 Tag PII and Regulatory-Sensitive Terms Aggressively

The skill should treat the following term-classes as automatic **sensitivity flags**:
- Direct identifiers: NRIC, passport number, biometric data, financial statements
- Indirect identifiers in workflow context: source-of-funds, PEP classification, adverse media results, sanctions match
- Regulatory-confidential events: SAR filings, sanctions holds, tipping-off-prohibited communications

Each tagged term should drive a downstream **handling requirements section**: retention policy, access control, redaction in logs, who-can-see-what. The 001 and 002 inputs both surfaced this need ("NRIC, financial statement = clearly sensitive" 001:L159 hidden; "PII in agent dashboard" 002:L205 hidden). The skill should generate the same surface output **without** having access to the hidden ground-truth notes — meaning it must infer sensitivity from the term itself, not from explicit "PII" labels.

### 5.4 Apply Source-Type Adaptive Elicitation

The skill should detect the source type of each input and adjust its elicitation passes accordingly:
- **Jira-like (structured + comments)**: reconcile stated AC against comment thread amendments. Treat the final comment as authoritative; surface contradictions between AC and comments.
- **Slack-like (conversational + reactions)**: resolve pronouns; treat 👍 / "ok" as soft decisions and flag them as needing formal sign-off; surface side-topics interleaved in the thread.
- **Meeting-notes-like (outlined + paraphrased)**: scan Action Items for ambiguous owners and unresolved deadlines; treat absent stakeholders as P1 risks for compliance-touching topics; promote Parking Lot items into a separate "deferred" list.

Without source-type adaptation, the skill will systematically miss the most error-prone artifacts of each format.

### 5.5 Detect Domain-Specific Conflict Patterns and Surface Them as Open Questions

The skill should ship with a library of known banking-BA conflict shapes and pattern-match against them:
- **Customer-facing vs internal state separation** (002 archetype) — whenever customer messaging is constrained by compliance (tipping-off), generate explicit dual-state model requirements.
- **Archive vs delete on replacement** (001 archetype) — whenever a document is "replaced", ask if old version is archived, versioned, or deleted, and tie to retention period.
- **Threshold-before-calibration** (003 archetype) — whenever a score threshold is proposed without calibration history, surface as a hard dependency.
- **Mobile-vs-web parity deferral** — whenever mobile is mentioned as "follow-on" or "Q4" or "separate sprint", explicitly mark as deferred-vs-out-of-scope and require resolution.
- **Anonymous / unattributed assumptions** — whenever a numerical limit appears without owner (e.g., "N could be 3"), tag as needing formal owner.
- **Legal absent on compliance-touching decisions** — flag as P1 stakeholder gap for any topic involving retention, customer messaging, tipping-off, or screening parameters.
- **ETA bucketing that flattens multiple SLAs** — whenever one customer-facing ETA covers internal states with different SLAs, surface the flattening as an open question.

Each conflict pattern should produce a templated "Open Question" entry with suggested resolution path — making the skill not just a parser but a **risk-pattern detector**.

---

## 6. Cross-Source Convergence Summary

To anchor the downstream skill designers in what's truly universal:

**Terms present in all three inputs**: retention, audit trail, compliance, PII (implicit), tipping-off (002 + 003 explicit, 001 implicit via "sensitive info"), mobile-vs-web deferral, applicant/customer, approval routing, deadlines tied to quarters or "EOW", missing-Legal, vague-N-limit pattern.

**Conflict pattern present in all three**: customer-facing simplicity vs internal granularity (re-upload status visibility in 001, wire status messaging in 002, EDD applicant status page in 003).

**Stakeholder pattern present in all three**: PM as reporter, Compliance as gatekeeper, Engineering as scope-reality-checker, Legal as absent-but-cited, Customer as unseen.

**Process pattern present in all three**: a state machine with at least one "in review / hold / pending" interior state that triggers compliance constraints on external messaging.

The skill should treat these convergences as **default expectations** when parsing any banking-domain raw request — and surface any input *missing* a convergence (e.g., no compliance officer named) as a potential gap.

---

## 7. Confidence Audit (transparency on this analysis)

- **High confidence**: All terms in §1.1 and §1.2; the dual-state pattern in 002; the cycle-time pain in 003; the retention-7y rule; the tipping-off prohibition; the mobile-deferral pattern; the absent-Legal pattern.
- **Medium confidence**: Disbursement as terminal state in lending (inferred, not directly stated); MAS-AML-1A regulator citation format generalizability (one observed example); the exact taxonomy of `Banking Operations` in §2.1 (could be re-cut).
- **Low confidence**: Anything inferred about systems not directly mentioned (e.g., the actual technical implementation of audit trails, the back-office wire-queue architecture). The skill should not over-claim about implementation details from these requests.

---

## 8. Appendix: Quick-Reference Glossary Table (alphabetical)

| Term | Domain Cluster | Sensitivity |
|---|---|---|
| Acuant | Vendor (KYC) | No |
| Adverse media | Compliance / KYC | Yes (results) |
| AML | Regulatory | Yes (in context) |
| Applicant | Lending / Onboarding | Indirect |
| Audit trail | Cross-cutting control | Sometimes |
| Authenticity scoring | Vendor / KYC | Indirect |
| Compliance hold | Payments | No (state) |
| Data residency | Cross-cutting / Regulatory | Indirect |
| Disbursement | Lending | Indirect |
| Dual approval | Cross-cutting control | No |
| EDD | KYC / Onboarding | Yes |
| Epic / Story | Process | No |
| Hold | Payments | No (state) |
| KYC | Onboarding | Yes |
| Liveness check | KYC / Vendor | Yes |
| Loan origination | Lending | No |
| MAS | Regulator | No |
| NRIC | PII | Yes (direct ID) |
| Onboarding | KYC | Indirect |
| Originator bank | Payments | No |
| PEP | Compliance | Yes (classification) |
| Retention | Cross-cutting control | Indirect |
| Re-upload | Lending | Indirect |
| Risk decision engine | Cross-cutting | Yes (consumes PII) |
| SAR | Regulatory | Yes |
| Sanctions screening | Compliance | Yes (results) |
| Second-eye / Second-level review | Payments | No |
| Source of funds | KYC | Yes |
| Spike | Process | No |
| Tiered approval routing | Cross-cutting | No |
| Tipping-off | Regulatory | Yes |
| Wire (transfer) | Payments | Indirect |

---

**End of Phase A1 Domain Analysis.** Downstream sub-agents may consume this as their canonical vocabulary and pattern catalog when designing the `ba-elicit-from-raw` skill.
