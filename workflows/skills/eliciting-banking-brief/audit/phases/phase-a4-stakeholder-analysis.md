# Phase A4 — Stakeholder Topology Analysis

> **Purpose**: Map all stakeholders observed across the three pilot inputs (Jira/Lending, Slack/Payments, Meeting/KYC) to inform the stakeholder-extraction logic of the `ba-elicit-from-raw` skill.
> **Scope**: `raw-request-001.md`, `raw-request-002.md`, `raw-request-003.md`.

---

## 1. Stakeholder Inventory (per training example)

### 1.1 Input 001 — Jira Ticket / Lending (LOAN-2847)

| Name | Role / Function | Decision authority observed | Times appeared | Quotes / evidence (file:line) |
|------|-----------------|------------------------------|----------------|-------------------------------|
| Sarah Lim | Product Manager (Lending) — Reporter / Owner | High on priority and scope framing; **defers on technical specifics** (file-size to Raj) and **on compliance** (retention to Priya) | 5 (reporter + 4 comments) | 001:25 "Reporter: Sarah Lim (Product Manager)"; 001:80-82 "@Priya — can we delete after retention period or no?"; 001:97-101 "@Raj — mostly web for now…can you suggest?"; 001:106-108 "OK creating this ticket for handoff to BA team" |
| Mike Chen | Support Lead | SME on current pain — quantifies the problem; **no decision authority** on solution | 1 | 001:65-70 "+1 to this…Most common case: expired NRIC photos (about 40%)…agents have to verify the new upload manually too, which takes ~15 min each" |
| Priya Naidoo | Compliance Officer | **High authority on regulatory + audit + retention**; sets 7-year retention unilaterally | 2 | 001:72-78 "We need an audit trail…Retention: 7 years"; 001:84-86 "Delete after 7 years YES. Abandoned applications — separate ticket" |
| Raj Patel | Engineering Lead | **High authority on feasibility / constraints**; poses scoping questions | 1 (+1 anonymous) | 001:88-95 "What about file size limits?…Mobile app vs web portal — both or just web? @Sarah let me know." |
| "Anonymous (likely Raj)" | Unknown / probably Raj | **Low** — anonymous = weak authority signal even with attribution guess | 1 | 001:103-104 "Anonymous (likely Raj) — N could be 3" |
| Marketing team | Implicit — campaign owner | Deadline-setter, diffuse (no named individual) | 1 mention | 001:47 "Marketing wants this live before the Q3 campaign launch (end of June)" |
| BA team | Downstream consumer of the ticket | None — receives handoff | 1 | 001:108 "for handoff to BA team" |
| Loan applicants | Affected end-user — primary persona | None (no voice) — pain inferred from support data | Implicit, many | 001:36-41 "Customers…are getting stuck…last week we had 142 such cases" |
| Support agents | Affected internal user | None directly — voice mediated by Mike | Implicit | 001:38-40 "they have to call our support team" |
| Mobile app team | Adjacent team — deferred | None — explicitly out of this sprint | 1 mention | 001:98-99 "mobile app team is in separate sprint" |
| Legal | **ABSENT** (compliance ≠ legal) | N/A | 0 (gap flagged 001:162) | 001:162 "Compliance ≠ Legal — needed for retention policy compatibility" |
| Security team | **ABSENT** (PII review) | N/A | 0 (gap flagged 001:164) | 001:164 "Where is Security? PII in documents" |

### 1.2 Input 002 — Slack Thread / Payments (#ops-payments)

| Name | Role / Function | Decision authority observed | Times appeared | Quotes / evidence (file:line) |
|------|-----------------|------------------------------|----------------|-------------------------------|
| Jenny Wong | Ops Manager (Inbound Wire Desk) — **Originator** | High on operational pain framing; **defers on technical states and regulatory language** | 9 turns | 002:21-25 "getting a LOT of escalations…can we do something about visibility?"; 002:35-36 "i don't know…Mei would know better"; 002:127-128 "inbound calls primarily. CSAT secondary" |
| Tom Becker | Engineering (Payments) | **High on technical architecture**; drafts the formal ask list; **de-facto owner** | 10 turns | 002:29-30 "'on hold' = pending second-level review? or pending compliance? those are different states"; 002:85-92 "ok let me draft. so the asks are roughly: 1…am i missing anything?"; 002:144-146 "ok let me write this up as a ticket. Sarah can you sponsor?" |
| Mei Park | Compliance Officer (Payments) | **Highest authority on regulatory language**; directive ("MUST NOT") | 8 turns | 002:46-48 "we can't expose 'sanctions hold' to customer-facing ui. that's regulated comms"; 002:65-67 "need legal to bless the language. and we MUST NOT show anything that could be construed as tipping off"; 002:111-114 "the ETA range needs to be conservative" |
| Raj Sharma | Frontend Engineer | SME on cross-platform UI feasibility; scope-clarifying questions | 2 turns | 002:101-104 "question — is this for web banking only or also mobile? we're mid-redesign on mobile, doing it once across both would be easier" |
| Sarah Khoo | Product (Payments) — **Sponsor** | **Approver/sponsor**; sets priority ordering | 5 turns | 002:123-128 "catching up — quick q, what's the metric we'd track?"; 002:148-149 "yes go ahead. priority is high"; 002:158-160 "let's prioritize web customer-facing first, then agent UI, then mobile" |
| Customer wire senders | Affected end-user | None — measured via call volume | Implicit | 002:22-24 "customers calling because their wires are stuck"; 002:43 "agent capacity ↑40%" |
| Call-center agents | Affected internal user (dashboard consumers) | None — Jenny speaks for them | Implicit | 002:94-96 "agent dashboard should show real reason" |
| Originator banks | External actor | Procedural mention only | 1 | 002:73-74 "retrieved funds go back to originator bank" |
| Regulators (AML/sanctions regime) | External — sets the rules Mei enforces | Implicit binding authority | Implicit | 002:39-40 "your wire is flagged for AML review"; 002:81-82 "we file the appropriate suspicious activity report" |
| Legal | **ABSENT — mentioned 3x**, never engaged | N/A | 0 turns / 3 mentions | 002:65 "need legal to bless the language"; 002:120 "legal will probably push the same way"; 002:159 "legal in parallel" |
| Mobile PM | **ABSENT** — Raj asked, no lead surfaced | N/A | 0 (gap 002:195) | 002:195 "Raj asked but no PM/lead mentioned for mobile" |
| Customer Support (themselves) | **ABSENT** from agent-UI design | N/A | 0 (gap 002:194) | 002:194 "Customer support team (the agents themselves) — not consulted on agent UI design" |
| Data / Analytics | **ABSENT** — metric definition orphan | N/A | 0 (gap 002:196) | 002:196 "Data/Analytics — for tracking the metric" |
| Originator-bank ops | **ABSENT** — return-flow protocol owner | N/A | 0 | 002:197 "Originator bank operations…ops protocol not specified" |

### 1.3 Input 003 — Meeting Notes / KYC (Onboarding 2.0 EDD)

| Name | Role / Function | Decision authority observed | Times appeared | Quotes / evidence (file:line) |
|------|-----------------|------------------------------|----------------|-------------------------------|
| David Lim | Head of Onboarding — **Chair** | **Highest in-room authority** — scope cuts, accepts/rejects, assigns actions | ~9 | 003:25 "David Lim (Head of Onboarding) — Chair"; 003:117 "Skipped, out of scope for this phase per David"; 003:122-123 "David: web first, mobile follow-on in Q4"; 003:126 "David: NPS yes but secondary" |
| Priya Naidoo | Compliance Officer (cross-product) | **High on regulatory**; proposes 0.75 threshold; flags Legal dependency | ~6 | 003:91-92 "Priya suggested using score >= 0.75"; 003:96 "Priya: careful with messaging — can't tip off if EDD escalates to SAR"; 003:115 "align with existing retention policy (7 years for completed, 30 days for abandoned — need to confirm with Legal)" |
| Jamie Foster | Risk Analytics | **High on data/model feasibility**; pushes back on Priya's threshold | ~5 | 003:55-57 "model can't ingest it well (Jamie)"; 003:84-86 "we can add 4 new structured fields…can do in next sprint"; 003:92-93 "engine outputs not calibrated yet — Jamie says calibration takes 2 cycles" |
| Karim El-Sayed | Engineering Manager, Onboarding | **High on engineering feasibility, security flags, vendor estimates** | ~5 | 003:77-78 "throughput concern — adverse media vendor (?) rate-limited"; 003:102 "Acuant doc capture: integration estimate 2-3 weeks"; 003:104 "Acuant biometric add-on…security review needed — Karim flagged" |
| Hua Liu | Vendor liaison — Acuant | Vendor-facing SME; commits to proposal | ~3 | 003:29 "Hua Liu (Vendor liaison — Acuant)"; 003:71-72 "Acuant API can do document type detection + liveness check"; 003:139 "[Hua] Acuant proposal with pricing — EOW" |
| Ben Stewart | CX Designer | **High on UX**; introduces NPS data; owns wireframes | ~4 | 003:62 "Note from Ben: applicant experience scoring NPS 3.8 / 10"; 003:96-98 "Ben proposed status page like delivery tracking"; 003:125 "applicant NPS target >= 6 (from current 3.8)" |
| Aisha Rahman | Junior PM — note-taker / BA-brief author | **Low explicit authority**; **interpretive authority** as filter | ~3 + paraphrases everything | 003:24 "Note-taker: Aisha Rahman (Junior PM, Onboarding squad)"; 003:146-147 "Aisha (me!) — convert these notes…David wants it tomorrow latest. Sigh." |
| Sundar K. | Legal | **Should be highest on legal questions** but **physically absent** | 0 active, 3 mentions | 003:31 "[Apologies: Legal — Sundar K., conflict with board prep]"; 003:115 "need to confirm with Legal"; 003:148 "Loop legal in next time — Sundar's calendar already booked" |
| Onboarding applicants | Affected end-user — NPS 3.8 | None | Implicit | 003:62 "applicant experience scoring NPS 3.8 / 10" |
| EDD analyst | Affected internal user — primary operator | None — voice mediated | Implicit | 003:50-58 "analyst has to manually request…analyst summarizes risk in prose…manual google searches by analyst" |
| Senior analyst | Affected internal user — tier-2 approver in new model | None — role implied | Implicit | 003:89 "High-risk: senior analyst + compliance officer dual approval" |
| MAS (regulator) | External — drives the initiative | **Ultimate authority** | 1 explicit | 003:39-40 "New regulator guidance Q1 2026 (referenced 'MAS-AML-1A revision')" |
| Acuant (vendor entity) | External vendor | Sets SLA / pricing | 1 explicit | 003:106 "SLA: 99.9% uptime committed, P95 latency <2s" |
| Adverse-media vendor | External — **unnamed** | N/A | 1 | 003:77 "adverse media vendor (?) rate-limited" |
| Engineering leadership (above Karim) | Implicit — migration owner TBD | Delegated upward | 1 | 003:129-130 "TBD — David to clarify with engineering leadership" |
| Migration workstream owner | **ABSENT — not yet identified** | N/A | 0 (action item) | 003:142 "[David] Identify migration workstream owner" |
| Customer Support | **ABSENT** on applicant-comms | 0 | 0 | 003:196 "Customer Support — not consulted on applicant communication" |
| Marketing / acquisition | **ABSENT** — abandoned-flow analytics | 0 | 0 | 003:197 "abandoned-flow analytics not connected" |
| Senior management approver | **ABSENT** — high-risk dual approval has no named senior | 0 | 0 | 003:198 "Senior management approval owner — for high-risk dual approval" |

---

## 2. Stakeholder Type Taxonomy (cross-cutting)

### 2.1 Owner / Requester (triggers, frames problem)
| Example | Person | Signal |
|---|---|---|
| 001 | Sarah Lim (PM) | Jira "Reporter"; opens ticket |
| 002 | Jenny Wong (Ops Manager) | First message in thread |
| 003 | David Lim (Head of Onboarding) | Chairs; sets context |

### 2.2 Approver / Sponsor (signs off)
| Example | Person | Signal |
|---|---|---|
| 001 | Sarah Lim (owner+approver merged); Priya implicit on compliance | 001:159 "Compliance officer Priya is the approver (implicit)" |
| 002 | Sarah Khoo (Product) | Explicit: "Sarah can you sponsor? … yes go ahead" 002:144-149 |
| 003 | David Lim (chair-merged) | Accepts/rejects scope (Q3 cross-border out; NPS secondary) |

> **Pattern**: Owner/Approver can be the same (001), separate (002), or merged into a chair (003). The skill must distinguish all three.

### 2.3 Subject-Matter Experts (SMEs)
| Domain | References |
|---|---|
| Compliance / Regulatory | Priya Naidoo (001, 003); Mei Park (002) |
| Engineering feasibility | Raj Patel (001); Tom Becker (002); Karim El-Sayed (003) |
| Frontend / Cross-platform | Raj Sharma (002) |
| Risk / Data / Analytics | Jamie Foster (003) |
| Ops / Frontline | Mike Chen (001); Jenny Wong (002, doubles as owner) |
| UX / CX | Ben Stewart (003) |
| Vendor liaison | Hua Liu (003 — Acuant) |

### 2.4 Affected Users (usually voiceless)
- External: Loan applicants (001); wire customers (002); onboarding applicants (003)
- Internal: Support agents (001, 002); EDD analysts (003); senior analysts (003)

### 2.5 External Actors
- Regulators: MAS (003); AML/sanctions regime (002)
- Vendors: Acuant (003); adverse-media vendor unnamed (003)
- Correspondent banks: Originator bank (002)
- Marketing campaigns: Q3 launch (001) — partly external timing pressure

### 2.6 Meta-Stakeholders (workflow-internal)
- Note-taker / paraphraser: Aisha Rahman (003)
- Downstream BA / TL consumer (001:108, 003:141)

### 2.7 Often-Missing Stakeholder Types
| Type | Missing in | Severity heuristic |
|---|---|---|
| **Legal** | 001, 002, 003 | **P1 — missing in 100% of examples** |
| Security team | 001 (PII), 003 (biometric partial) | P2 if PII / biometric |
| Customer Support as co-designer | 002 (agent UI), 003 (applicant comms) | P2 if internal tooling or customer comms |
| Mobile PM / lead | 001, 002, 003 | P2 |
| Data / Analytics owner | 002 (metric), 003 (NPS) | P2 if declared metric |
| Migration workstream owner | 003 | P2 if cutover required |
| Senior management approver | 003 | P2 if tiered approval |
| Marketing / acquisition | 003 | P3 |

---

## 3. Implicit Authority Patterns

How authority is signaled even without an org chart. Six recurring signals:

### 3.1 Title / parenthetical role
Direct, greppable. `(Product Manager)` 001:25, `(Compliance)` 001:72 / 002:45, `(Engineering Lead)` 001:88, `(Ops Manager)` 002:21, `(Head of Onboarding) — Chair` 003:25, `(Engineering Manager, Onboarding)` 003:28. Verbs **Head of**, **Chair**, **Manager**, **Lead**, **Officer** signal escalating authority.

### 3.2 Deference patterns
Person X publicly defers to Y → Y holds authority on that topic.
- 001:80 Sarah → Priya on retention ("@Priya — can we delete after retention period")
- 001:95 Raj → Sarah on scope ("@Sarah let me know")
- 002:35-36 Jenny → Mei on compliance states ("Mei would know better")
- 003:91-93 Priya proposes 0.75 → Jamie pushes back → **data-feasibility overrides compliance proposal**

### 3.3 Directive / modal language
Compliance uses uppercase modals when speaking in **rule mode**:
- 002:65 Mei: "we **MUST NOT** show anything that could be construed as tipping off"
- 002:46-47 Mei: "we **can't** expose 'sanctions hold'…that's regulated comms"
- 003:96 Priya: "can't tip off if EDD escalates to SAR"
- 001:74 Priya: "Retention: 7 years" (pronouncement, no hedge)

### 3.4 Approval / acceptance speech acts
- 002:148-149 Sarah Khoo: "yes go ahead. priority is high" — explicit go-ahead
- 003:124-126 David: "NPS yes but secondary" — accept-with-amendment
- 003:117 "Skipped, out of scope for this phase per David" — chair-level scope cut

### 3.5 Override / push-back patterns
- 003:91-93 Jamie overrides Priya's threshold proposal on **data-readiness grounds** — engineering/data can override compliance *proposals* (not compliance *rules*).
- 002:111-117 Mei pushes "up to 5 business days" against Tom's "5 days feels long" → Tom yields ("fine") — compliance overrides engineering preference on customer comms.

> **Distillation**: When compliance speaks in **regulatory/rule mode** (MUST NOT, can't, regulated), the constraint is binding. When in **proposal mode** (suggesting thresholds), it is negotiable.

### 3.6 Anonymous / weak attribution
- 001:103 "Anonymous (likely Raj)" — even with attribution guess, weak weight. Down-weight anonymous contributions.

### 3.7 Who answers regulatory/compliance/legal definitively?
| Topic | Authority observed |
|---|---|
| Retention period | Priya (001:74, 001:84-86) |
| Tipping-off language | Mei (002:46-67), Priya (003:96) |
| Regulator citation | David promises; defers to Priya (003:39-40) |
| Data residency | Priya (003:108) |
| **Final legal sign-off on customer-facing language** | **Nobody present in any of 3 inputs → Legal gap** |

Most important pattern: **compliance officers describe the regulation, but only Legal can bless customer-facing legal language.** Compliance presence ≠ Legal sign-off.

---

## 4. Stakeholder Gap Patterns (recurring across examples)

### 4.1 Per-input gaps
| Input | Missing stakeholders |
|---|---|
| **001** | Legal (compliance ≠ Legal); Security (PII); Mobile team (deferred without confirmation) |
| **002** | Legal (3x mentioned, never engaged); Customer Support agents (agent UI); Mobile PM; Data/Analytics; Originator bank ops |
| **003** | **Legal (Sundar absent — P1)**; Customer Support; Marketing channel; Senior management approver; Migration workstream owner |

### 4.2 Cross-example gap patterns

| Gap pattern | Present in | Severity |
|---|---|---|
| **Legal absent on regulatory-touching scope** | 001, 002, 003 | **P1** if scope touches customer-facing legal language, retention, regulator citation |
| Customer Support / agents not consulted on tooling they'll use | 001, 002, 003 | P2 |
| Mobile / cross-platform owner not engaged | 001, 002, 003 | P2 |
| Data / analytics owner missing for declared metrics | 002, 003 | P2 |
| Security team missing when PII or biometric involved | 001, 003 | P2 |
| Named senior approver missing in escalation flows | 001, 003 | P2 |
| External vendor unnamed | 003 | P3 |
| Anonymous contributor | 001 | P3 |

> **Conclusion**: **Legal is absent in 3/3 banking inputs** — most reliably missing role. Followed by Customer Support as co-designer, Mobile owner, and Data/Analytics. These four account for ~70% of gap flags. The skill should treat them as **default-check stakeholders** for any banking input.

---

## 5. Communication Style per Stakeholder Role

Fingerprints for **role inference from writing style**, not just stated title.

### 5.1 Product Managers — Sarah Lim (001), Sarah Khoo (002)
| Trait | Evidence |
|---|---|
| Vague on edge cases, optimistic on timeline | 001:55 "Old document is replaced (or maybe kept as version? unclear)" |
| Defer technical questions back to engineering | 001:97-101 "@Raj — mostly web for now…probably need limit but not sure what's reasonable, can you suggest?" |
| Ask about metrics late | 002:123-124 "catching up — quick q, what's the metric we'd track?" |
| Hedging ("probably", "maybe", "let's") | 002:130-135 "probably yes…push notif maybe optional. let's not spam." |
| Prioritization by ordering | 002:159 "let's prioritize web customer-facing first, then agent UI, then mobile" |

### 5.2 Engineering Leads / Engineers — Raj Patel (001), Tom Becker (002), Karim (003), Raj Sharma (002)
| Trait | Evidence |
|---|---|
| Pose constraints as questions | 001:88-94 "What about file size limits?…Mobile app vs web portal — both or just web?" |
| Disambiguate states explicitly | 002:29-30 "'on hold' = pending second-level review? or pending compliance? those are different states" |
| Surface integration / scope-overlap concerns | 002:103-104 "we're mid-redesign on mobile, doing it once across both would be easier than retrofitting later" |
| Quantitative estimates with caveats | 003:102 "Acuant doc capture: integration estimate 2-3 weeks" |
| Flag security/spike needs | 003:104 "Acuant biometric add-on: NEW for us, security review needed — Karim flagged" |
| Drafting / summarizing | 002:85-92 "ok let me draft. so the asks are roughly: 1…am i missing anything?" |

### 5.3 Compliance Officers — Priya (001, 003), Mei (002)
| Trait | Evidence |
|---|---|
| Directive uppercase modals for binding rules | 002:65 "we **MUST NOT** show anything that could be construed as tipping off" |
| Declarative regulatory statements (no hedge) | 002:46-47 "we can't expose 'sanctions hold'…that's regulated comms" |
| Reference regulations by name | 003:39-40 "New regulator guidance Q1 2026 (referenced 'MAS-AML-1A revision')"; 001:77-78 "needs to be archived per our data retention policy" |
| Specific retention numbers | 001:74 "Retention: 7 years"; 003:115 "7 years for completed, 30 days for abandoned" |
| Flag Legal as next-step authority | 003:115 "need to confirm with Legal"; 002:65 "need legal to bless the language" |
| Conservative defaults on customer comms | 002:111-114 "the ETA range needs to be conservative…'up to 5 business days' to be safe" |
| Caveats / red-team thinking | 002:64 "👍 with caveats —" |

### 5.4 Operations Managers — Jenny (002), Mike (001 — Support Lead)
| Trait | Evidence |
|---|---|
| Lead with customer pain + metrics | 002:21-25 "getting a LOT of escalations…agent capacity ↑40%" |
| Quantify (cases/week, hours, %) | 001:40-41 "142 such cases, average resolution time 4 hours"; 001:67-70 "expired NRIC photos (about 40%)" |
| Pragmatic about partial wins | 002:51-52 "ETA would be huge. even 'expected resolution within 3 business days' beats silence" |
| Time-pressure framing | 002:151 "need this in 3 weeks ideally — ops team is bleeding capacity" |
| Acknowledge limits of own knowledge | 002:35-36 "honestly i don't know…Mei would know better" |

### 5.5 Designers / UX — Ben Stewart (003)
| Trait | Evidence |
|---|---|
| User-centric framing | 003:62 "applicant experience scoring NPS 3.8 / 10…That's not in our analyst tooling — that's the applicant's perception" |
| Familiar mental-model analogies | 003:96-97 "Ben proposed status page like delivery tracking" |
| NPS / satisfaction-target oriented | 003:125 "applicant NPS target >= 6 (from current 3.8)" |
| Concrete deliverables (wireframes) | 003:138 "[Ben] 3 wireframes…by 2026-05-14" |

### 5.6 Risk / Data Analysts — Jamie Foster (003)
| Trait | Evidence |
|---|---|
| Talk about model inputs / structured fields | 003:55-57 "Risk decision engine input is partial — analyst summarizes risk in prose, model can't ingest it well" |
| Commit to schema-level deliverables | 003:84-86 "we can add 4 new structured fields…can do in next sprint" |
| Push back on calibration / data-readiness | 003:92-93 "engine outputs not calibrated yet…calibration takes 2 cycles of real data" |

### 5.7 Note-takers / Junior PMs — Aisha (003)
| Trait | Evidence |
|---|---|
| Paraphrases not verbatim | 003:18 "Note-taker filtered some content (paraphrase, not verbatim)" |
| Flag own assumptions in brackets | 003:43 "[unconfirmed if EOW = this or next week]" |
| Self-references / emotional asides | 003:147 "Aisha (me!)…David wants it tomorrow latest. Sigh." |

> **Skill implication**: When input is mediated by a junior PM / note-taker, treat statements as **paraphrase** unless explicitly quoted.

---

## 6. Stakeholder Weight Heuristics for the Skill

| Speaker role | High authority on… | Lower authority on… | Heuristic |
|---|---|---|---|
| Compliance officer (**rule mode** — MUST/can't/regulated) | Regulatory rules, retention, tipping-off, customer-comms constraints | Engineering feasibility, prioritization | **High authority, low negotiability** — record as constraint. Evidence: 002:65, 003:115 |
| Compliance officer (**proposal mode** — "I suggest") | Thresholds, suggested wording | Same but **may be negotiated by data/eng** | Medium — record as proposed, validate with affected SME. Evidence: 003:91-93 |
| Product Manager | Priority, scope ordering, business value | Timeline feasibility (often optimistic), edge cases, technical feasibility | **High on priority, low on feasibility** — flag PM timelines for eng validation. Evidence: 001:97-101, 002:123-128 |
| Sponsor / Approver | Go/no-go, prioritization across competing scope, budget | Detailed technical or compliance | High on prioritization. Evidence: 002:148-149 Sarah Khoo "yes go ahead. priority is high" |
| Engineering Lead / Manager | Feasibility, sizing, integration risk, security flags | Prioritization, business value | **High on feasibility, low on prioritization.** Evidence: 001:88-94, 003:104 |
| Frontend / Cross-platform Eng | Cross-platform parity feasibility, UI scope | Backend, compliance | Medium — useful on scope-spanning questions. Evidence: 002:101-104 |
| Ops Manager / Support Lead | Operational pain quantification, customer-impact, frontline workflow | Solution design, technical implementation | **High on problem framing, medium on solution shape.** Evidence: 001:65-70, 002:21-25 |
| CX / UX Designer | User-experience direction, satisfaction targets, copy | Engineering & compliance | High on user-facing decisions. Evidence: 003:96-98 |
| Risk / Data Analyst | Model inputs, calibration readiness, schema | Customer comms, ops | **High on data feasibility — can override compliance proposals on calibration grounds.** Evidence: 003:92-93 |
| Vendor liaison | Vendor capabilities & limits | In-house policy | Medium — feasibility signal, **not a buy-decision authority**. Evidence: 003:71-72 |
| Note-taker / Junior PM (paraphrase) | Capture of others' decisions | Original assertion | **Low direct; treat statements as paraphrase**. Evidence: 003:17-18, 003:43 |
| Anonymous contributor | None | All | **Low — flag for explicit attribution before treating as decision**. Evidence: 001:103-104 |
| Affected user (no voice) | None | All | Voice constructed by ops/support/UX — flag if no proxy speaks for them |
| External regulator / vendor (cited) | Sets binding rule (regulator) or pricing/SLA (vendor) | N/A | **Cite-only — verify citation**. Evidence: 003:39-40 (MAS-AML-1A) |

---

## 7. Implications for Skill Design

Concrete recommendations for the stakeholder-extraction logic of `ba-elicit-from-raw`.

### R1 — Distinguish Owner / Sponsor / Approver / SME / Affected explicitly
The skill must not collapse these into one "stakeholders" list. 001 merges Owner+Approver (Sarah Lim); 002 separates Owner (Tom drafts) from Sponsor (Sarah Khoo); 003 has chair-style merged Owner+Approver (David). **Output schema**: each stakeholder gets `{name, role_title, function, type ∈ {owner, sponsor, approver, sme, affected, external, meta}, evidence}`.

### R2 — Capture authority level / mode per utterance
A bare name list loses binding-vs-preference. Annotate each utterance with **authority mode**:
- `rule` (compliance MUST NOT) → binding constraint
- `proposal` (compliance suggests threshold) → negotiable
- `preference` (PM "probably yes") → soft assumption
- `estimate` (eng 2-3 weeks) → range to validate
- `pain` (ops 142 cases) → problem-framing evidence

### R3 — Flag scope-implied missing stakeholders
Define a scope-to-stakeholder map:

| Scope touches… | Required stakeholders (else gap flag) |
|---|---|
| Customer-facing legal language, retention | **Legal — P1 if absent** |
| PII, biometrics, sensitive docs | **Security — P2 if absent** |
| Internal tooling redesign | **Customer Support — P2 if absent** |
| Cross-platform UI | **Mobile owner — P2 if absent** |
| Declared metrics (CSAT, NPS, call volume) | **Data/Analytics — P2 if absent** |
| Tiered escalation / approval | **Named senior approver — P2 if absent** |
| Vendor integration with PII flow | **Security + Legal — P1 if both absent** |
| Regulator-driven initiative | **Compliance present AND Legal scheduled — P1 if Legal not scheduled** |

### R4 — Detect "mentioned but not engaged" stakeholders
Different from "absent": named (Legal, Sundar, Acuant) with **0 utterances**. Examples: 002:65/120/159 — Legal 3x, never speaks; 003:31/115/148 — Sundar apologies. Heuristic: `count_mentions(person) ≥ 2 AND count_utterances(person) == 0` → engagement gap flag.

### R5 — Down-weight anonymous / paraphrased / mediated content
- 001:103 "Anonymous (likely Raj)" → mark `attribution: anonymous, guessed: Raj` and down-weight.
- 003 entirely paraphrased by Aisha → mark all attributions `mediated_via: Aisha (note-taker)`; recommend verbatim verification before treating any statement as a quote.

### R6 — Surface diffuse / unnamed stakeholders
Unnamed pressure sources are common: 001:47 "Marketing wants this live before Q3"; 003:77 "adverse media vendor (?)"; 001:38 "the compliance team also asked us". Flag unnamed stakeholders as P2/P3 gaps requiring a named individual before TL handoff.

### R7 — Use communication-style fingerprints as a role classifier
Apply Section 5 fingerprints to detect role mismatch or off-role operation:
- MUST / can't / regulated → compliance signature
- probably / maybe / let's → PM signature
- "N could be" / file-size questions → engineering signature
- "142 cases / 4 hours / ↑40%" → ops signature
- "NPS 3.8 / status page like delivery tracking" → UX signature

### R8 — Build a deference graph from @mentions and "X would know better"
Examples: 001:80 Sarah → Priya (compliance); 001:95 Raj → Sarah (scope); 002:35-36 Jenny → Mei (compliance states). The graph encodes who-answers-what and helps the skill recommend whom to consult on each open question.

### R9 — Treat note-taker / mediator as a meta-stakeholder
003 has Aisha deciding what was captured. Record the note-taker explicitly; mark all statements `attribution_confidence: paraphrase`; recommend verbatim follow-up for any P1/P2 item.

### R10 — Hard-code a Legal-engagement check for banking/regulatory inputs
Legal is missing in 3/3 examples. The skill should always emit `legal_status ∈ {present, scheduled, mentioned_only, absent}` with severity for any input flagged banking, regulatory, or customer-facing-comms.

### R11 — Distinguish vendor SME from vendor entity
Hua Liu (003) is a **vendor liaison in the meeting**; Acuant is the **vendor entity** owning the SLA. Record both — liaison gives feasibility input, but the contract owner is the entity. Matters for SLA tracking and dependency listing.

### R12 — Flag affected-user voicelessness
End-users have zero voice in 3/3 examples. Record affected users explicitly even with no direct quote; flag if no proxy (ops/UX/support) has spoken for them; recommend citing research artifacts (NPS, CSAT, call analysis).

---

## 8. Quick Reference — Cross-Example Stakeholder Heat Map

| Stakeholder Type | 001 (Lending) | 002 (Payments) | 003 (KYC) | Skill default |
|---|---|---|---|---|
| Owner / Requester | Sarah Lim (PM) | Jenny Wong (Ops) | David Lim (Head) | **Required** |
| Sponsor / Approver | Sarah Lim (implicit) | Sarah Khoo (Product) | David Lim (Chair) | **Required — distinguish from owner** |
| Compliance SME | Priya Naidoo | Mei Park | Priya Naidoo | **Required if regulatory** |
| Engineering SME | Raj Patel | Tom Becker | Karim El-Sayed | **Required for feasibility** |
| Ops / Frontline | Mike Chen | Jenny Wong (doubles) | (voiceless analyst) | Recommend |
| UX / Designer | — | — | Ben Stewart | Recommend if customer-facing |
| Risk / Data | — | — | Jamie Foster | Required if model/metric driven |
| Vendor liaison | — | — | Hua Liu (Acuant) | Required if vendor integration |
| **Legal** | **MISSING** | **MISSING** (3x mentioned) | **MISSING** (Sundar absent) | **P1 if regulatory + absent** |
| Security | MISSING (PII) | (implicit access-control gap) | partly via Karim | P2 if PII / biometric |
| Customer Support (co-design) | mediated only | MISSING (agent UI) | MISSING (applicant comms) | P2 if internal tool / customer comms |
| Mobile owner | deferred | Raj asked, no answer | Q4 deferred | P2 — confirm deferral |
| Data / Analytics | — | MISSING (CSAT) | implicit via Jamie | P2 if metric declared |
| Senior management approver | escalation TBD | — | MISSING (high-risk dual) | P2 if tiered approval |
| Affected end-user (voiceless) | applicants | wire senders | applicants | Always note + cite research |
| External regulator | implicit | implicit (AML/sanctions) | MAS explicit | Cite if mentioned, verify citation |

---

## 9. Summary

Across the three banking-domain inputs, **30+ named or implicit stakeholders** appear in seven distinct types: Owner/Requester, Sponsor/Approver, SME (compliance, engineering, risk/data, UX, ops, vendor), Affected User, External Actor, Meta-stakeholder (note-taker), and an **Always-Missing tier** (Legal, Security, CS-as-designer, Mobile owner, Data/Analytics owner). The single strongest recurring signal: **Legal is absent in 100% of inputs** despite all three touching regulated customer-facing language or retention — this must be a hard-coded check. Authority is signaled through titles, deference patterns (`@X what do you think?`, "Y would know better"), directive modal language ("MUST NOT", "can't", "regulated"), and explicit approval acts ("yes go ahead"); the skill must capture both the speaker's name **and** their authority mode on each utterance. Communication-style fingerprints (compliance directive uppercase, PM hedging, engineering quantitative-with-caveats, ops metric-led, UX user-centric, data-analyst calibration-aware) allow role inference even when titles are missing. The twelve design implications (R1-R12) operationalize these findings into concrete extraction logic: distinguish Owner / Sponsor / Approver, attach authority levels per utterance, flag scope-implied missing roles, detect mentioned-but-not-engaged stakeholders, down-weight anonymous and paraphrased content, build a deference graph, and always emit a Legal-engagement check for banking inputs.
