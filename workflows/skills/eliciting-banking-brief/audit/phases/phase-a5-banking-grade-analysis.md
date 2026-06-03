# Phase A5 — Banking-Grade Signal Analysis

> **Purpose**: Identify ALL banking-grade signals (explicit + implicit + gaps) in the 3 training examples so `ba-elicit-from-raw` can extract them deterministically.
> **Inputs**: `raw-request-001.md` (Jira, lending re-upload, T2), `raw-request-002.md` (Slack, payments status, T2), `raw-request-003.md` (Meeting, KYC EDD, T2-borderline-T1).
> **Anchored against**: `COGNITIVE_OS_PROJECT.md` §3, `DELIVERY_WORKFLOW_PLAN.md` Tier system + Pipeline Properties, `references/ba-best-practices.md` Banking-Grade BA Field Reference.

Banking-grade = the 5 non-negotiables (auditability, idempotency, determinism, graceful degradation, reversibility) PLUS banking-domain concerns (PII, compliance, authN/authZ, tipping-off, regulator references). The skill detects all of these as one unified signal set.

---

## 1. Explicit Banking-Grade Signals

Direct, quotable mentions invoking a banking-grade concept.

### 1a. Input 001 — Lending document re-upload

| # | Signal | Quote | File:Line | Category | Severity |
|---|---|---|---|---|---|
| E1-1 | Audit trail mandatory | "compliance team also asked us to track who replaced what document and when (probably for audit reasons — they didn't explain in detail)" | 001:43-45 | audit | P1 |
| E1-2 | Audit fields enumerated | "what got replaced, who replaced it, when, and any reason given" | 001:73-74 | audit | P1 |
| E1-3 | Retention period | "Retention: 7 years." | 001:74 | compliance | P1 |
| E1-4 | PII handling — sensitive doc class | "if the replaced document contains sensitive info (NRIC, financial statement), the old version should NOT just be deleted — needs to be archived per our data retention policy" | 001:76-78 | PII | P1 |
| E1-5 | Policy doc referenced (missing) | "I'll send the policy doc separately." | 001:78 | compliance | P2 |
| E1-6 | Lifecycle deletion rule | "Delete after 7 years YES." | 001:85 | compliance | P1 |
| E1-7 | Reversibility / abandonment | "if applicant abandons their application, what happens to the docs?" | 001:82-83 | reversibility | P2 |
| E1-8 | Graceful degradation | "What happens if the new upload also fails verification? Loop?" | 001:91 | graceful-degradation | P2 |
| E1-9 | AuthZ today's state | "they have to call our support team to delete the old upload and the support agent manually triggers a re-upload link" | 001:38-39 | authn/authz | P2 |
| E1-10 | Idempotency rate cap | "Multiple re-uploads of the same doc — limit how many times?" | 001:91 | idempotency | P2 |
| E1-11 | Compliance Officer authority | "Priya Naidoo (Compliance)" issuing binding policy statements | 001:72 | compliance | P2 |
| E1-12 | Audit readiness as value | "Compliance audit readiness (implicit)" | 001:132 | audit | P3 |
| E1-13 | Sensitive data class | "expired NRIC photos (about 40%)", "bank statements that don't show last 3 months (about 25%)" | 001:67-68 | PII | P2 |

### 1b. Input 002 — Payments wire transfer status

| # | Signal | Quote | File:Line | Category | Severity |
|---|---|---|---|---|---|
| E2-1 | Sanctions screening | "happening more since we tightened sanctions screening last sprint" | 002:23-25 | compliance | P1 |
| E2-2 | Customer-vs-internal state | "customers see 'processing' and we see in the back-office that the wire is sitting in a queue somewhere" | 002:35-36 | authn/authz | P2 |
| E2-3 | Tipping-off (explicit) | "we don't want to tell them 'your wire is flagged for AML review' 😅" | 002:39-40 | tipping-off | P1 |
| E2-4 | Regulated comms | "we can't expose 'sanctions hold' to customer-facing ui. that's regulated comms." | 002:46-47 | compliance | P1 |
| E2-5 | Anti-tipping-off rule | "we MUST NOT show anything that could be construed as tipping off (sanctions context)" | 002:65-66 | tipping-off | P1 |
| E2-6 | Non-tipping rejection language | "we cannot tell the customer 'rejected for sanctions reason'. it has to be a generic message." | 002:71-73 | tipping-off | P1 |
| E2-7 | Compensating action | "retrieved funds go back to originator bank" | 002:74 | reversibility | P2 |
| E2-8 | SAR filing | "we file the appropriate suspicious activity report on our end if applicable" | 002:82 | compliance | P1 |
| E2-9 | AuthZ split agent vs customer | "agent UI = same as back-office. customer UI = sanitized." | 002:99 | authn/authz | P2 |
| E2-10 | State machine (hold/review) | "compliance hold vs ops second-eye review" | 002:38 | audit (state) | P2 |
| E2-11 | Guarded rejection email | "careful with rejection emails — content has to be generic" | 002:140-142 | tipping-off | P1 |
| E2-12 | Legal review dependency | "need legal to bless the language" | 002:65 | compliance | P2 |
| E2-13 | Approved non-tipping phrase | "'the transfer could not be completed. please contact the sender.' that's the standard line." | 002:81 | tipping-off | P2 |

### 1c. Input 003 — KYC EDD workflow re-design

| # | Signal | Quote | File:Line | Category | Severity |
|---|---|---|---|---|---|
| E3-1 | Regulator citation | "New regulator guidance Q1 2026 (referenced 'MAS-AML-1A revision' — Priya to forward exact citation)" | 003:38-39 | compliance | P1 |
| E3-2 | Regulator-driven SLA | "Pressure to reduce EDD cycle to <7 days at p95" | 003:41 | determinism (SLA) | P2 |
| E3-3 | PEP screening | "PEP screening is run only at end — late discovery of high-risk profiles means rework" | 003:57-58 | compliance | P1 |
| E3-4 | Adverse media | "Adverse media screening — manual google searches by analyst (!!)" | 003:60-61 | compliance | P1 |
| E3-5 | Source-of-funds | "Source-of-funds verification — most variable step, ranges 1-9 days" | 003:62 | compliance | P1 |
| E3-6 | Upfront screening (sanctions + PEP + AM) | "PEP, sanctions, adverse media — all run automatically on submission" | 003:76-77 | compliance | P1 |
| E3-7 | Tiered audit | "Low-risk: analyst sole decider, audit trail required" | 003:87 | authn/authz + audit | P1 |
| E3-8 | Dual approval | "High-risk: senior analyst + compliance officer dual approval" | 003:89 | authn/authz | P1 |
| E3-9 | Tipping-off (SAR escalation) | "careful with messaging — can't tip off if EDD escalates to SAR" | 003:97 | tipping-off | P1 |
| E3-10 | Generic in-review status | "generic 'in review' status acceptable to compliance" | 003:99 | tipping-off | P2 |
| E3-11 | Biometric security review | "Acuant biometric add-on: NEW for us, security review needed before integration" | 003:105-106 | authn/authz | P1 |
| E3-12 | Data residency | "Data residency: Acuant offers SG region — Priya confirmed acceptable" | 003:109 | compliance | P1 |
| E3-13 | Vendor SLA | "SLA: 99.9% uptime committed, P95 latency <2s per call" | 003:108 | determinism | P2 |
| E3-14 | Partial PII retention | "7 years for completed, 30 days for abandoned — need to confirm with Legal" | 003:115-116 | compliance + PII | P1 |
| E3-15 | In-flight migration | "What happens to in-flight EDD cases when we cut over to new workflow?" | 003:112 | graceful-degradation | P2 |
| E3-16 | Compliance Officer attendee | "Priya Naidoo (Compliance Officer)" | 003:25 | compliance | P2 |
| E3-17 | Cycle-time variance | "Cycle time: average 11 days (some up to 22), variance is the issue" | 003:37 | determinism | P2 |

**Totals**: 13 + 13 + 17 = **43 explicit signals** (target 15+).

---

## 2. Implicit Banking-Grade Signals

The text doesn't label these banking-grade but strongly implies them.

### 2a. Input 001 — implicit

| # | Implicit Signal | Cue | File:Line | Category | Severity |
|---|---|---|---|---|---|
| I1-1 | Idempotency: support-agent manual step replaced by automation → must not double-trigger | "support agent manually triggers a re-upload link" | 001:38-39 | idempotency | P2 |
| I1-2 | AuthN: applicant self-service is new authenticated capability | "self-service way for applicants to re-upload documents" | 001:42 | authn/authz | P2 |
| I1-3 | Determinism: 4h current SLA baseline | "average resolution time 4 hours" | 001:39-41 | determinism | P3 |
| I1-4 | Audit: version-vs-replace is an audit reconstruction decision | "Old document is replaced (or maybe kept as version? unclear)" | 001:54 | audit + reversibility | P2 |
| I1-5 | Reversibility: archive policy = recoverable doc | "needs to be archived per our data retention policy" | 001:77-78 | reversibility | P2 |
| I1-6 | Graceful degradation: escalation path | "Failed verification loop — escalate to support after N attempts maybe" | 001:99-101 | graceful-degradation | P2 |
| I1-7 | Governance: Compliance ≠ Legal, Legal absent | (no Legal anywhere; Priya is Compliance only) | 001:72 + absence | compliance | P2 |
| I1-8 | PII: NRIC is SG national ID = high sensitivity | "expired NRIC photos" | 001:67 | PII | P1 |
| I1-9 | PII: bank statement = financial-grade PII | "bank statements that don't show last 3 months" | 001:68 | PII | P1 |
| I1-10 | Determinism: 10MB file-size = bounded input contract | "What about file size limits? Currently 10MB per file." | 001:90 | determinism | P3 |
| I1-11 | AuthZ: "Anonymous (likely Raj)" set N=3 = missing identity binding on a policy decision | "Anonymous (likely Raj)" | 001:103-104 | authn/authz | P3 |
| I1-12 | Governance: marketing deadline vs compliance gating tension | "Marketing wants this live before the Q3 campaign launch" | 001:47 | compliance | P3 |
| I1-13 | Downstream compliance dependency | "Blocks: LOAN-3001 'Q3 marketing campaign go-live'" | 001:121 | compliance | P3 |

### 2b. Input 002 — implicit

| # | Implicit Signal | Cue | File:Line | Category | Severity |
|---|---|---|---|---|---|
| I2-1 | State machine = audit surface (4 states, transitions need events) | "compliance hold / ops review / approved / rejected" | 002:87-89 | audit | P1 |
| I2-2 | Idempotency on notifications | "when does the customer's status update if a wire goes from 'additional review' to 'approved'?" | 002:131-133 | idempotency | P2 |
| I2-3 | SLA: customer-facing "up to 5 business days" = commitment | "let's say 'up to 5 business days' to be safe" | 002:113-114 | determinism | P2 |
| I2-4 | AuthZ: customer UI must NOT reach back-office data | "agent UI = same as back-office. customer UI = sanitized" | 002:99 | authn/authz | P1 |
| I2-5 | Reversibility: rejected wire returns funds = compensating action on payment | "retrieved funds go back to originator bank" | 002:74 | reversibility | P1 |
| I2-6 | Compliance: AML inferred from hold-state vocabulary | "compliance hold vs ops second-eye review" | 002:38 | compliance | P1 |
| I2-7 | Audit: tipping-off violation = audit-class incident | "we cannot tell the customer 'rejected for sanctions reason'" | 002:71-73 | audit + tipping-off | P1 |
| I2-8 | PII: financial transaction data throughout | wire-transfer domain | 002:21+ | PII | P1 |
| I2-9 | SLA verbal not policy | "24-72h depending on workload. for ops second-eye it's same day 95% of the time" | 002:54-55 | determinism | P2 |
| I2-10 | Compliance: regulator defines customer messaging | "that's regulated comms" | 002:47 | compliance | P1 |
| I2-11 | AuthZ disclosure-control via agent script | "agent script: standard responses for the new status" | 002:91 | authn/authz | P2 |
| I2-12 | Tipping-off: only sanctions called out, PEP/AM/fraud silent | (gap) | 002 (gap) | tipping-off | P2 |
| I2-13 | Audit: ETA-bucket conservatism = audit-able policy | "reputational risk on the long tail" | 002:120 | audit | P3 |
| I2-14 | Compliance: legal review as gating dependency | "legal review timing is the wildcard" | 002:156 | compliance | P2 |

### 2c. Input 003 — implicit

| # | Implicit Signal | Cue | File:Line | Category | Severity |
|---|---|---|---|---|---|
| I3-1 | Audit: tiered routing → traceable (who, score, calibration version) | "Low-risk: ... audit trail required" + ">=0.75" | 003:87-92 | audit | P1 |
| I3-2 | Determinism: uncalibrated engine = non-deterministic routing | "engine outputs not calibrated yet" | 003:91-92 | determinism | P1 |
| I3-3 | PII: source-of-funds doc = highly sensitive | "Source-of-funds verification" | 003:62 | PII | P1 |
| I3-4 | AuthZ: vendor data-sharing boundary | "Acuant API can do document type detection + liveness check + authenticity scoring" | 003:69-71 | authn/authz | P1 |
| I3-5 | Governance: Legal absent in regulatory-touching meeting | "Apologies: Legal — Sundar K." | 003:30 | compliance | P1 |
| I3-6 | Idempotency: single-session intake → session-scoped key | "Applicant uploads everything in 1 session" | 003:67 | idempotency | P2 |
| I3-7 | Reversibility: in-flight cases need migration path | "What happens to in-flight EDD cases when we cut over" | 003:112 | reversibility | P2 |
| I3-8 | PII data-minimization for abandoned cases | "30 days for abandoned" | 003:115-116 | PII + compliance | P1 |
| I3-9 | AuthZ: role-based risk-decision authority | "Approval routing — unclear when senior approval triggered vs analyst can decide" | 003:63-64 | authn/authz | P1 |
| I3-10 | Determinism: vendor P95 propagates to workflow SLA | "P95 latency <2s per call" | 003:108 | determinism | P2 |
| I3-11 | Graceful degradation: vendor rate limit | "adverse media vendor (?) rate-limited at X requests/min" | 003:78-79 | graceful-degradation | P2 |
| I3-12 | Governance: NPS could mask compliance trade-offs | "applicant experience scoring NPS 3.8 / 10" | 003:63 | audit | P3 |
| I3-13 | AuthN: new biometric attack surface | "security review needed before integration" | 003:105-106 | authn/authz | P1 |
| I3-14 | Audit: EOW ambiguity = traceability risk on the regulator citation | "[unconfirmed if EOW = this or next week]" | 003:44 | audit + compliance | P2 |
| I3-15 | AuthZ: quorum-like approval | "senior analyst + compliance officer dual approval" | 003:89 | authn/authz | P1 |

**Totals**: 13 + 14 + 15 = **42 implicit signals** (target 15+).

---

## 3. Missed Signals — Gaps

Banking-grade concerns NOT called out in raw input but that the skill should flag.

### 3a. Input 001 — gaps

| # | Gap | Why it should be flagged | Severity |
|---|---|---|---|
| G1-1 | PII inventory incomplete | NRIC + financial statement named, but not name/address/photo/applicant-ID | P2 |
| G1-2 | Idempotency of re-upload undefined | Double-click → 2 audit events? No key strategy | P1 |
| G1-3 | AuthN context for self-service unstated | Session? magic-link? unspecified | P1 |
| G1-4 | AuthZ on archived-doc retrieval undefined | Who can read 7-year archive? No role matrix | P1 |
| G1-5 | Audit event schema not enumerated | "who/what/when/reason" only; missing hash, IP, attempt count, idempotency key | P2 |
| G1-6 | Revert window for accidental replace undefined | Version-vs-replace ambiguity is unresolved | P2 |
| G1-7 | Tipping-off not considered | Lending can trigger AML; what if re-upload reveals a hit? | P2 |
| G1-8 | Retention policy doc not attached | Cannot proceed without it (T1) / dependency (T2) | P1 |
| G1-9 | Legal absent — PDPA compatibility risk | 7-yr retention may conflict with privacy law | P1 |
| G1-10 | Security team absent — upload attack surface | File type / size / malware not reviewed | P1 |
| G1-11 | Mobile not formally classified W (Won't Have) | Could create regulatory parity gap | P3 |
| G1-12 | N=3 limit anonymous and unbound | No policy basis, no audit on lockout | P2 |
| G1-13 | Abandoned-application docs deferred but live obligation | Retention rule applies today | P2 |

### 3b. Input 002 — gaps

| # | Gap | Why it should be flagged | Severity |
|---|---|---|---|
| G2-1 | Tipping-off mentioned, not formalized | No AC, no detection, no incident class | P1 |
| G2-2 | Notification idempotency missing | Re-flag → 3 emails? | P1 |
| G2-3 | Audit trail on state transitions absent | State machine implied, no event schema | P1 |
| G2-4 | AuthZ between agent UI and customer UI is policy, not enforcement | Same system role-gated or two systems? | P1 |
| G2-5 | SAR workflow scoped out, integration undefined | Rejection triggers SAR; boundary unclear | P1 |
| G2-6 | Originator-bank return undefined | Format, timing, audit on irreversible action missing | P1 |
| G2-7 | Legal language not drafted | Workflow blocked on actual strings | P2 |
| G2-8 | PEP / adverse media tipping-off silence | Only sanctions called out | P2 |
| G2-9 | Agent access logging on "real reason" view | Privileged data view must audit | P1 |
| G2-10 | Notification reversibility | Mis-fired email retraction undefined | P2 |
| G2-11 | Cross-border wire jurisdiction | OFAC/UN list variance ignored | P2 |
| G2-12 | ETA-bucket determinism | Static or computed? Audit-able? | P2 |
| G2-13 | Re-submission pattern flag | Re-attempt = fraud/AML signal, no handling | P2 |

### 3c. Input 003 — gaps

| # | Gap | Why it should be flagged | Severity |
|---|---|---|---|
| G3-1 | Dual-approval audit schema undefined | High-risk = two audit events with quorum semantics | P1 |
| G3-2 | Abandoned-data lifecycle vague | What fields? Delete vs anonymize? | P1 |
| G3-3 | Legal absent — governance P1 | Decisions taken anyway | P1 |
| G3-4 | Regulator citation pending | "MAS-AML-1A" name without citation | P1 |
| G3-5 | Vendor DPA / data-processing-agreement absent | Acuant processes ID + biometric | P1 |
| G3-6 | Cross-border out of scope but PII risk | Foreign disclosure risk parked | P2 |
| G3-7 | Risk-engine calibration debt → unreliable routing | Audit must capture engine version | P1 |
| G3-8 | Adverse-media vendor unnamed | No DPA, no risk assessment | P1 |
| G3-9 | Biometric security spike = open dependency | Can't commit until done | P1 |
| G3-10 | Screening idempotency / list-version pinning undefined | Lists change daily, re-runs non-deterministic | P1 |
| G3-11 | "Generic in review" exact wording not produced | Legal sign-off required | P1 |
| G3-12 | Migration owner unidentified | PII migration ownerless | P1 |
| G3-13 | NPS-secondary could conflict with compliance | Trade-off rule needed | P2 |
| G3-14 | Manager dashboards parking-lot: access control undefined | Case-level data exposure | P3 |

**Total gaps**: 13 + 13 + 14 = **40** (target 10+).

---

## 4. Banking-Grade Field Mapping (linguistic patterns the skill detects)

| Non-negotiable | Patterns to detect | Example matches (file:line) | False-positive guard |
|---|---|---|---|
| **Auditability** | "track who/when/what", "for audit", "log", "audit trail", "retention X years", "record", "trace" | 001:43; 003:87; 001:74 | Debug-log ≠ audit emission |
| **Idempotency** | "duplicate", "retry", "re-submission", "same request", "twice", "multiple", "limit how many times", state-change notification | 001:91; 002:131-133 | UI duplicate element ≠ idempotency |
| **Determinism** | SLA / p95 / latency / cycle-time / "consistent" / "calibrated" / variance / temperature | 003:41; 003:108; 003:91; 003:37 | "Fast" w/o numbers = quantifier ambiguity |
| **Graceful degradation** | "if X fails", "loop", "escalate", "fallback", "rate-limited", "stuck", "timeout" | 001:91; 003:78; 002:23 | UI error copy ≠ degradation policy |
| **Reversibility** | "undo", "revert", "abandon", "rollback", "delete", "archive", "return funds", "in-flight when we cut over" | 001:82; 002:74; 003:112 | UI Ctrl-Z ≠ compensating action |
| **PII** | "ID", "NRIC", "passport", "statement", "biometric", "source of funds", KYC docs, retention | 001:67; 001:76; 003:62; 003:105 | "Personal preferences" ≠ PII |
| **AuthN / AuthZ** | "support agent", "admin", "role", "permission", "who can", "agent UI vs customer UI", "dual approval", "senior approval", "self-service" | 001:38; 003:89; 002:99 | "User role in survey" ≠ authZ |
| **Compliance** | Regulator names (MAS, OFAC, FinCEN, FATF, PDPA, GDPR, PCI), "AML", "KYC", "EDD", "SAR", "sanctions", "PEP", "adverse media", "tipping off", "regulated comms", "data residency", retention | 003:38; 002:23; 003:57; 002:82; 003:108 | "Marketing compliance" w/o regulator = soft |
| **Tipping-off** | "don't tell customer", "generic message", "non-tipping", "regulated comms", "vague but helpful", "standard line", "in review" as opaque status | 002:39; 002:65; 003:99; 002:81 | UX surprise ≠ tipping-off |

### Structural patterns beyond keywords

- Compliance Officer as commenter/attendee → escalate to T2 minimum.
- Regulator name without citation → automatic P1.
- Legal absent on regulatory-touching content → P1 (T1/T2) governance gap.
- Hard business deadline overriding compliance → P2 conflict.
- "Vendor (?)" unnamed third party processing PII → P1.
- Same word with multiple meanings ("on hold" = compliance vs ops) → P2 state-machine ambiguity.
- "Separate ticket" / "out of scope" for retention/abandonment → P2 deferred-compliance-risk.
- Verbal SLA without policy doc → P2 SLA-formalization-needed.

---

## 5. Tier Inference Heuristics

### T1 strong indicators
Regulator cited + citation; Compliance Officer as decision-maker; sanctions/AML/EDD/PEP/SAR/adverse-media language unprompted; dual or quorum approval; real customer money at risk; tipping-off invoked; regulator-defined SLA; data-residency hard rule; "regulated comms" language.

### T2 indicators
Customer-facing impact without regulator name; internal SLAs; KYC docs without compliance citation; ops metrics drive priority; compliance team as advisor not gatekeeper; business-driven deadline.

### T3 indicators
"Prototype", "spike", "POC"; no customer impact; no regulator, no compliance officer; internal tooling; cost-first language.

### Per-input tier assignment

| Input | Tier | Driving signals | Justification |
|---|---|---|---|
| **001 Lending** | **T2 (T1-shadow on retention+PII)** | E1-3, E1-4, E1-11, I1-12, G1-9 | Customer-facing + real PII at scale + binding compliance statements, no regulator cited. Borderline T1 on retention + PII; manual T2 label agreed. |
| **002 Payments** | **T2 borderline T1 (recommend escalate)** | E2-1, E2-3/5/6, E2-4, E2-8, G2-1 | Sanctions + SAR + tipping-off + regulated comms = T1 by content. Raw is informal (Slack), no policy citation. Tipping-off penalty exposure is regulatory. R6 should flag the discrepancy. |
| **003 KYC EDD** | **T1 by content (manual label T2)** | E3-1, E3-3/4/6, E3-7/8, E3-9, E3-11, E3-12, I3-5 | Full T1 stack. Manual T2 reflects "working session" status. Recommend T1 once Legal joins. Legal absence = P1 blocker. |

### Skill tier-inference rule (compact)

```
IF (regulator_named AND citation_provided) → T1
ELIF (compliance_officer_present AND (sanctions|aml|kyc|edd|sar|pep|tipping_off)) → T1 candidate, confirm
ELIF (compliance_officer_present AND PII_high_grade) → T2 with T1-shadow on retention + PII
ELIF (customer_facing AND PII_any) → T2
ELIF (no_regulator AND no_compliance_officer AND prototype_language) → T3
ELSE → T2 default + P2 "tier ambiguous"
```

---

## 6. Default vs Override Behavior

When raw input is silent the skill **must not** silently skip — every banking-grade row is force-filled with `applies` / `not_applicable + reason` / `unknown_P2_open_question`.

| Field | Default if silent (T2 baseline) | Override | Risk if skipped |
|---|---|---|---|
| **PII fields** | Enumerate fields or 'none with reason'. T1 refuse to proceed. T3 allow "prototype, no real data". | Explicit no-PII justification | Audit failure when prod data lands |
| **Audit emission** | Standard emission on state change. Schema = (event, actor, ts, before, after, reason, idem_key). Empty only if pure-read + T3. | List exempt stages w/ justification | Workflow non-compliant |
| **Idempotency** | Evaluate by side-effect presence. Any external side effect → key required. T1: replay test mandatory. | Pure-function stages may declare n/a | Double-charge / double-notify |
| **Reversibility** | Any external write → compensating action or "irreversible — human queue". | Soft-reversible allowed for analyze/design/generate | Rollback impossible |
| **AuthN** | Customer-touching = authenticated session. Internal = service account w/ role. | "Anonymous OK" only in public flows | Privilege escalation |
| **AuthZ** | Specify allowed roles — least privilege. | "Any authenticated user" w/ data-class justification | Unauthorized access |
| **Regulatory** | List applicable regs or 'none — non-regulated'. T1 refuse w/o citation. T2 at minimum domain regulator. T3 skip w/ note. | "No specific reg" | Workflow runs blind to legal exposure |
| **Tipping-off** | Customer-facing comm change? If yes, non-tipping safe phrasing required. | "Internal-only stage" | Regulatory penalty |
| **Determinism (LLM temp)** | T1=0.1, T2=0.3, T3=0.5 per Pipeline Properties table. | Stage-specific override w/ note | Audit replay fails |
| **Graceful degradation** | Specify failure policy. Default = retry 3x → human-queue (analyze); human-queue (commit/notify). | Per-stage `failure_policy` in workflow YAML | No escape valve |

### Forced-evaluation output contract

```yaml
banking_grade_concerns:
  pii_fields:        { status: applies|not_applicable|unknown_p2, fields: [...], justification: ... }
  audit:             { status: standard|enhanced|none_pure_read, events: [...] }
  idempotency:       { status: required|not_applicable_pure_function, key_strategy: ... }
  reversibility:     { status: reversible|soft_reversible|irreversible_human_queue, compensating_action: ... }
  authn_authz:       { actors: [...], role_matrix: ... }
  regulatory:        { citations: [...] }   # at least one for T1
  tipping_off:       { risk_level: none|low|medium|high, mitigation: ... }
```

Empty rows = schema-validation failure. This is the forcing function.

---

## 7. Implications for Skill Design

**R1. Emit `banking_grade_concerns` table for every story, always.** Force-filled (no nulls). Empty rows fail schema validation. Gaps in inputs 001-003 show humans drop these evaluations when not structurally enforced.

**R2. Tier inference runs BEFORE story extraction.** Output an explicit `inferred_tier` with the firing signals (audit traceability of the tier decision itself). Tier drives mandatory rows, LLM temperature, and Legal/Security-absence severity. Input 003 is mis-labeled T2; mis-tiering = silent compliance risk.

**R3. Tipping-off scan on any customer-facing communication change.** If ACs touch email/push/SMS/status/error message/agent script/rejection text → run `tipping_off_scan` → output risk level + mitigation. Convert "legal needs to bless the language" wishes into testable ACs: *"Given a wire is rejected for sanctions reason, When the customer is notified, Then the message uses the standard non-tipping phrase and does NOT contain 'sanctions', 'AML', 'flagged', or specific compliance terminology."*

**R4. Escalate to P1 when regulator is named without citation.** Input 003 says "MAS-AML-1A revision" — that's a name, not a citation. Skill emits automatic P1 open question.

**R5. Detect Legal/Security absence as P1 (T1/T2) governance gap.** Scan for Legal and Security participation in inputs touching retention, PII, biometric, tipping-off, sanctions, customer-facing language, dual approval. Compliance ≠ Legal; Security ≠ either. Input 003 explicitly lists "Apologies: Legal" with decisions made anyway.

**R6. PII inventory mode — full enumeration.** For any input mentioning PII, produce a `pii_inventory`: every field by category (identity, financial, biometric, contact, government-ID); each row carries retention rule, residency rule, masking rule, access-audit requirement. Inputs name NRIC + bank statement + biometric but never enumerate name/address/photo/applicant-ID.

**R7. State-machine + audit emission extracted together.** For any state/status transitions (input 002 has 4 states), produce: state-machine artifact, per-transition audit-event schema, Gherkin idempotency-replay scenario, flag missing transitions.

**R8. Identify hard dependencies that block TL handoff.** Distinct from P2 open questions — these BLOCK: missing regulator citations, unattached policy docs, unnamed vendors processing PII, Legal/Security sign-off pending (T1/T2), calibration debt on risk engines used for routing, open security spikes (biometric).

**R9. Split candidates aligned to banking-grade concern boundaries.** When input bundles different concern profiles, propose splits where audit/PII/idempotency/reversibility shift — not by tech layer. Inputs 001 and 003 illustrate this.

**R10. "Deferred to separate ticket" gets a compliance-risk tag if obligation is live today.** "Separate ticket", "out of scope", "different concern", "Q4 follow-on" → check live banking-grade obligation. Inputs 001 (abandoned apps), 002 (SAR workflow, originator-bank return), 003 (legacy migration, cross-border, mobile Q4) all defer items with active obligations.

**R11. Weight corroborated signals over single-keyword matches.** One mention of "compliance" alone < (Compliance Officer attendee + retention policy + sensitive doc class). Reduces false-positive tier escalation while preserving sensitivity.

**R12. Ship a non-tipping-language reference** (`references/non-tipping-vocabulary.md`): approved phrases ("the transfer could not be completed. please contact the sender."), forbidden terms ("sanctions hold", "AML review", "flagged"), detection patterns. Apply to any customer-facing AC text.

---

## 8. Signal Counts (Cross-Reference)

| Class | Input 001 | Input 002 | Input 003 | Total |
|---|---|---|---|---|
| Explicit | 13 | 13 | 17 | **43** |
| Implicit | 13 | 14 | 15 | **42** |
| Gaps | 13 | 13 | 14 | **40** |
| **Per-input total** | **39** | **40** | **46** | **125** |

Input 003 carries the heaviest load — confirms the recommendation to escalate it to T1.

---

## 9. Concluding Notes

Dominant patterns across all 3 inputs: (1) banking-grade concerns appear everywhere but mostly informally (Slack, meeting notes, ticket bodies); (2) gaps are predictable — PII enumeration, audit schema, idempotency replay, formal tipping-off tests, Legal/Security stakeholders, regulator citations are *always* missing in some form; (3) the skill's main value is the **forcing function** — structurally requiring fill-or-explicit-not-applicable, not pattern matching alone; (4) tier inference precedes everything (wrong tier = wrong strictness = wrong governance); (5) tipping-off is highest-stakes (regulatory penalty, not business) AND easiest to miss because it's about *not* outputting something. These are the architectural pillars for `ba-elicit-from-raw`.
