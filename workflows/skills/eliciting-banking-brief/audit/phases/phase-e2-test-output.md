---
id: EPIC-CARD-DISPUTES-001
workload_tier: T2
created_at: 2026-05-12T10:00:00Z
created_by: ba-elicit-from-raw-v1.0.0
source_ref: inputs/raw-request-holdout.md
source_type: email
idempotency_key: e2-holdout-test-2026-05-12-uuidv4-placeholder
ba_confidence: medium
status: blocked
output_type: blocked_partial_brief
blocks_tl_handoff: true
scope_kind: single-epic
upstream_refs:
  source_artifacts:
    - inputs/raw-request-holdout.md
downstream_will_be_consumed_by:
  stage: 2-tl-design
  role: tl-squad

# Processing metadata (per skill spec — Step 12)
processing_metadata:
  parsing_mode: structured
  parsing_inversion_applied: true
  quoted_replies_deduplicated: 2
  ground_truth_stripped:
    found: true
    byte_range: [7423, 14215]
    strip_method: heading_regex_##_intentional_issues_to_eof
  chunking: null
  tipping_off_scan_clean: true
  external_dependencies:
    - dispute-ops-q1-2026-review-v2.pptx
    - VISA VCR rule mapping (Felix's team WIP)
    - Data team event-field confirmation (Jamal)
  stakeholder_availability:
    - name: Diana Costa
      role: Senior Manager, Card Operations (Initial Owner)
      status: handing_off
      cover: Felix Tan
      return_date: 2026-08-15
  inbound_handoff_metadata:
    from_name: Diana Costa
    from_role: Senior Manager, Card Operations
    context: Thread escalated by Diana over 2 quarters; reply chain shows Marcus reframing into 2-phase scope; Diana confirms Felix as Phase 1 owner post-leave.
  tier_decisions:
    - epic_id: EPIC-CARD-DISPUTES-001
      inferred_tier: T2
      manual_tier: T2
      inferred_higher_than_manual: false
      signals:
        - "Regulator named (VISA VCR 2026-07) but not a sovereign regulator — card-network rule"
        - "Customer-impacting (chargeback outcome affects customer funds) but Phase 1 is internal staff tooling"
        - "PII handling required (transaction history, customer statements) — indirect category"
        - "No sanctions / SAR / EDD scope explicit"
        - "Compliance officer not engaged in thread — Compliance dimension of VCR not yet addressed"
        - "No dual approval explicit; high-value cases not scoped"
  language_inventory:
    - script: Latin-en
      sample: "primary thread content"
      frequency: 100%
---

# Epic: Card Dispute Analyst Tooling — Phase 1 (VISA VCR Compliance + SLA Visibility + Unified Case View)

## Business Context

### Problem Statement

Card dispute analysts currently work across four disconnected systems (card admin, transaction history, customer comms, network portal) to process chargeback cases. Per Diana Costa (Senior Manager, Card Operations, message 2026-05-05 11:08): Q1 2026 case volume was 4,200/month (up 18% YoY) with average handling time of 47 minutes against a <30 minute target; 6.2% of cases (~260/month) breach the 45-day network SLA. Chargeback win rate sits at 64% versus the industry benchmark of 71%, and analyst attrition reached 22% in 12 months with exit interviews citing tooling as the #1 driver. The dollar value of lost chargebacks is described as "material" but is unquantified pending Felix Tan's confirmation. Compounding the operational pain, the VISA VCR (Visa Claims Resolution) ruleset revision effective 2026-07 changes dispute categories and reason codes — making tooling updates a hard external deadline rather than a discretionary roadmap item.

### Why Now (Trigger)

VISA VCR ruleset effective 2026-07 is a non-negotiable external deadline. Diana describes this as a "hard regulatory deadline" and Yvonne Brooks (VP Product) confirms "the VISA VCR is a hard external deadline so we don't have a choice on the rule mapping piece." Coupled with two quarters of operational complaints and a 22% analyst attrition rate, the trigger is the convergence of compliance-must-do (VCR) with quantified ops pain (47 min handling time, 6.2% SLA breach, 64% win rate).

### Hypothesis

We believe that consolidating the analyst workflow (Phase 1: VCR rule mapping + SLA timer + unified case view layer + network portal session keepalive) before the 2026-07 VCR effective date will (a) achieve VCR compliance on day-1, (b) reduce SLA breach rate from 6.2% toward <2%, and (c) recover chargeback win rate toward the 71% industry benchmark. We will validate by measuring SLA breach, average handling time, and win rate across the first 90 days post-Phase-1 release.

---

## Success Criteria (Measurable)

| # | Metric | Baseline | Target | Measurement Method |
|---|--------|----------|--------|---------------------|
| 1 | VCR rule mapping coverage | 0% of new reason codes supported | 100% of new VCR reason codes available in tooling by 2026-07-01 | VCR reason-code parity audit run pre-go-live; gap report = zero |
| 2 | SLA breach rate (cases sitting beyond 45-day network limit) | 6.2% (~260/month) | <2% within 90 days post-launch | Monthly ops dashboard query: count(cases where age_in_days > 45 AND state != "submitted_to_network") / total_cases |
| 3 | Average case handling time | 47 min | <30 min within 180 days post-launch | Case audit-log: median(time_between case_opened and case_submitted_to_network) over rolling 30 days |
| 4 | Chargeback win rate | 64% | Toward 71% industry benchmark (interim target ≥68% within 180 days) | Win-rate report from network responses; numerator/denominator definition TBD with Felix |
| 5 | Network portal session timeout incidents | "Half the time" sessions timeout (Diana, qualitative) | <1 timeout-related re-login per analyst per shift | Front-end telemetry on re-authentication events to network portals |
| 6 | Analyst attrition citing tooling as primary cause | 22% / 12 mo with tooling cited #1 in exit interviews | Tooling drops out of top-3 cited reasons within 12 months | Exit-interview thematic coding by HR; report quarterly |

**Note**: Criterion #5 currently uses a qualitative baseline ("half the time") — OQ-08 requests quantification before locking the metric.

---

## Scope

### In Scope (Phase 1, Q3 2026)

- VISA VCR new reason-code mapping in case-creation workflow
- SLA timer per case, visible to analyst, with countdown and breach-warning state
- Unified case view layered on top of existing card admin UI (NOT a replacement)
- Network portal session keepalive — VISA via API where available; MC via session-keepalive interim
- Audit-event emission for all case state transitions (Phase 1 banking-grade requirement)

### Out of Scope (Explicit)

- Replacement of the existing card admin UI (Tomas: "no chance Q3, 6-9mo project minimum")
- Network rep relationship for systemic portal-timeout resolution (no contact established; out of BA scope)
- In-app customer comms (Diana: "in-app would be Phase 2")
- New templating service with variables/conditionals (Tomas: Phase 2 territory)
- Treasury / accounting reconciliation of chargeback reversal events (Marcus mentioned but no scope committed)

### Out of Scope (Deferred — Phase 2, Q4 2026 / Q1 2027)

- Customer communication email templates (6-7 standard situations)
- Chargeback packet auto-assembly (currently 18-25 min/case manual collation)
- Win/loss analytics dashboard
- Mastercard network API integration (post-session-keepalive interim)
- Card admin UI replacement (long-term, separate initiative)

---

## Stakeholders

| Role | Name | Type | Decision Authority | Affected? | Authority Mode | Attribution |
|------|------|------|---------------------|-----------|----------------|-------------|
| Initial Owner (handing off) | Diana Costa | owner | Ops scope + acceptance of analyst tooling | Yes | pain + proposal | high |
| Phase 1 Owner (post-2026-06-01) | Felix Tan | owner | Phase 1 detail scoping + post-Diana acceptance | Yes (handoff) | proposal | mentioned (no direct utterance in thread beyond Cc) |
| Sponsor | Marcus Vega | sponsor | Prioritization + cross-team loop-in | Yes | proposal | high |
| Product Owner | Yvonne Brooks (VP Product, Card Services) | approver | Q3 roadmap commitment + scope discipline | Yes | proposal + preference | high |
| Tech Lead | Tomas Werner | sme | Engineering feasibility + delivery commitment | Yes | estimate + proposal | high |
| Ops users (consumers) | Ops-Cards-Lead distribution list | affected | None (use the tool) | Yes | n/a | group |
| SME (data field) | Jamal (card-systems team) | sme | SLA timer event-field source confirmation | No (advisor) | rule (when confirmed) | mentioned_only |
| **Legal / Regulatory Counsel** | **NOT NAMED** | **absent** | **VCR interpretation, customer-comm wording (Phase 2), tipping-off review for fraud cases** | **N/A** | **absent** | **absent** |
| **Compliance** | **NOT NAMED** | **absent** | **VCR ruleset compliance review, audit-trail sufficiency** | **N/A** | **absent** | **absent** |
| **UX / Design** | **NOT NAMED** | **absent** | **Unified case view UX research sprint (Yvonne explicitly called for this)** | **N/A** | **absent** | **absent** |
| **Treasury** | **NOT NAMED** | **absent** | **Chargeback-reversal accounting (Marcus flagged)** | **N/A** | **absent** | **absent** |
| **Card admin team owner (legacy system)** | **NOT NAMED** | **absent** | **Coordination on layering vs replace** | **N/A** | **absent** | **absent** |
| **Customer Support** | **NOT NAMED** | **absent** | **Differentiate analyst comms vs CS comms** | **N/A** | **absent** | **absent** |
| **Data team owner (confirmation pending)** | **NOT NAMED** (Jamal referenced only) | **mentioned_only** | **Event-field source for SLA timer** | **N/A** | **absent** | **mentioned** |

**legal_status: absent** — see governance gap GG-1 below.

---

## Governance Gaps (P1 — Halt-Worthy)

> Per SKILL.md Step 6 + Step 12 + AP-5.1, AP-3.2, AP-4.4. Any P1 sets `blocks_tl_handoff: true`.

| # | Type | Severity | Evidence | Required Action | Blocks TL handoff? |
|---|------|----------|----------|-----------------|---------------------|
| GG-1 | legal_absent_on_regulatory | **P1** | Thread CC list across 5 emails (Marcus, Diana, Felix, Yvonne, Tomas, Ops-Cards-Lead) does not include Legal or Compliance. Scope includes (a) VISA VCR 2026-07 regulatory deadline; (b) future customer-facing comms templates (Phase 2) with potential tipping-off exposure for fraud-related disputes; (c) audit-trail requirements for network arbitration. AP-5.1 fires; AP-3.2 fires (no Compliance present and Compliance ≠ Legal). | Loop in Legal and Compliance before TL handoff. Legal must confirm: (i) VCR rule mapping does not require external counsel review of customer-facing reason-code language; (ii) Phase 2 customer-comms template scope must include Legal sign-off gate; (iii) tipping-off vocabulary applies to declined-dispute notifications for confirmed-fraud cases. Sponsor (Marcus) to record risk acceptance in writing if any item is deferred. | **true** |
| GG-2 | regulatory_citation_unresolved | **P1** | "VISA VCR" named with effective date 2026-07 but no citation_id, document attachment, or revision number. Felix's team is "mapping" — status unknown. The attached `dispute-ops-q1-2026-review-v2.pptx` is referenced but not analyzed. | Felix to attach (a) current VCR ruleset document or VISA-published changelog; (b) mapping status; (c) regulator-of-record clarification (VISA = card network rule, not sovereign regulator — confirm whether MAS PSN-01 also applies to payment-dispute timing). | **true** |
| GG-3 | pii_inventory_missing | **P2** (lifted to P1 in absence of Privacy/DPO) | Phase 1 stories will surface transaction history, customer statements, customer-comm previews, and dispute reason codes — all PII or PII-adjacent. No DPO / Privacy stakeholder named. AP-4.1 disable-path requires explicit `not_applicable + justification` — instead we have absent owner. | Engage DPO / Privacy to (a) ratify the PII inventory table emitted below; (b) confirm retention, residency, masking, and access-audit rules per field; (c) confirm whether unified case view layer introduces any new PII surface relative to existing card admin UI. | **true** |
| GG-4 | retention_policy_unstated | **P2** | Dispute case lifecycle records (audit events, customer statements attached, chargeback packets) carry retention obligations under network arbitration windows + bank record-keeping policy. No retention rule cited in thread. | Compliance + Legal to confirm retention duration for (a) dispute case object; (b) attached customer statements; (c) audit-event log. AP-1.1 forbids skill-inferred retention. | **true** |

> **Because GG-1 through GG-4 are all `blocks_tl_handoff: true`**, this brief is emitted as `output_type: blocked_partial_brief` with `frontmatter.status: blocked`. The stories below are draft-quality; do NOT route to TL for design until governance gaps are resolved or Sponsor records explicit risk acceptance in writing.

---

## User Stories

> Phase 1 carries 5 stories driven by the VISA VCR 2026-07 deadline. Phase 2 stories are catalogued in `Out of Scope (Deferred)` and are NOT in this brief's `stories[]`.

---

### Story EPIC-CARD-DISPUTES-001-1: Map and ingest VISA VCR new reason codes into case-creation flow

**Format**: Job Story (regulatory trigger over single role)

**When** a new card dispute case is opened on or after 2026-07-01,
**I want to** select a reason code from the VISA VCR 2026 revision ruleset (not the legacy code list),
**So I can** submit a network-compliant chargeback packet that satisfies VISA's new dispute-category rules.

#### Context

The VISA VCR ruleset revision effective 2026-07 changes dispute categories and reason codes. This is a hard external deadline. Felix's team is currently mapping the legacy-to-new reason-code crosswalk; the mapping outcome and revision document are external dependencies. This story is the regulatory must-do for Phase 1.

#### Acceptance Criteria (Gherkin)

```gherkin
Scenario: Happy path — analyst selects new VCR reason code on case open
  Given an analyst is authenticated with role "card_dispute_analyst"
  And the current date is on or after 2026-07-01
  And the VCR 2026 ruleset is loaded in the reason-code registry
  When the analyst opens a new dispute case and selects a reason code
  Then the reason-code picker displays only VCR 2026 codes (no legacy codes)
  And the selected code is recorded on the case with code_version = "VCR_2026"
  And the case is eligible to submit to VISA network

Scenario: Error — legacy reason code rejected post-cutover
  Given an analyst is authenticated as "card_dispute_analyst"
  And the current date is 2026-07-15
  When the analyst attempts to set reason_code = "legacy_R10" on a new case
  Then the case is rejected with error "REASON_CODE_RETIRED"
  And no case is persisted
  And the analyst is shown the VCR 2026 mapping link

Scenario: Banking-grade audit — code change emits audit event
  Given an open case in state "draft" with reason_code = "VCR_13_1"
  And the analyst is authenticated as "card_dispute_analyst"
  When the analyst changes the reason code to "VCR_13_2"
  Then the case reason_code is updated to "VCR_13_2"
  And an audit event is emitted with payload:
    | field      | value                              |
    | event      | case.reason_code_changed           |
    | actor      | <analyst_id>                       |
    | ts         | <ISO-8601 timestamp>               |
    | before     | VCR_13_1                           |
    | after      | VCR_13_2                           |
    | reason     | <analyst-entered reason>           |
    | idem_key   | <client-generated idempotency_key> |

Scenario: Banking-grade idempotency — duplicate code-set call no-ops
  Given a case with reason_code = "VCR_13_1" set via idempotency_key = "ik-rc-001"
  When the same set-reason-code request with idempotency_key = "ik-rc-001" is replayed
  Then no duplicate side effect occurs
  And no duplicate audit event is emitted
  And the response returns the original result

Scenario: Edge case — cutover window straddling
  Given a case opened on 2026-06-30 with legacy reason_code = "R10"
  When the analyst submits the case on 2026-07-02
  Then the system applies the cutover rule (TBD per OQ-11: do we re-map legacy cases or grandfather?)
  And the analyst is shown the cutover policy in-line
```

#### Banking-Grade Concerns

| Concern | Status | Justification | Fields/Events | Treatment | Compensating Action |
|---------|--------|---------------|---------------|-----------|---------------------|
| pii_fields | applies | Case object references customer card identity and transaction history per dispute | card_number_masked, customer_id, transaction_id | Mask card_number to last-4 in UI; audit access to full PAN | n/a |
| audit_events | applies | Reason code change is a material network-impacting state change requiring auditable trail | case.reason_code_changed, case.opened, case.submitted_to_network | Standard audit-event schema per template §6.2 | n/a |
| idempotency | applies | Reason-code set/change is a state-change op; replay must be safe | set_reason_code, submit_to_network | client-generated idempotency_key on every state-change call | n/a |
| reversibility | applies | Reason code is reversible pre-submission; irreversible post-network-submission | case.reason_code | Pre-submission: free edit; post-submission: network arbitration only | Network arbitration (slow, expensive — flag for TL design) |
| authn_authz | applies | Only card_dispute_analyst role may set reason codes; senior approver may override post-submission | role check on case mutations | RBAC at API gateway + UI hiding | n/a |
| regulatory | applies | VISA VCR 2026 ruleset is the regulatory authority for this AC | VCR-2026 (citation_status: pending per GG-2) | Bind to VCR document version on load; reject if version stale | n/a |
| tipping_off | not_applicable | Reason code is internal-facing; not exposed verbatim to customer in Phase 1 (Phase 2 templates will require re-evaluation) | n/a | n/a | n/a |

#### Priority (MoSCoW)
**Must** (regulatory hard deadline 2026-07)

#### Story Sizing
**Estimated story points**: TBD_by_TL (`split_required: true` if mapping list exceeds 30 new codes; otherwise 8)
**Estimated complexity**: high (regulatory + cutover semantics + unknown mapping scope)

#### Dependencies
- **Depends on**: EXTERNAL — Felix's VCR mapping completion; VCR document attachment (GG-2)
- **Blocks**: EPIC-CARD-DISPUTES-001-5 (VISA API expansion submits using these reason codes)

#### Definition of Ready Checklist
- [x] User story format is clear (Job Story, situation-bound)
- [x] At least 1 happy path Gherkin scenario
- [x] At least 1 error/edge case Gherkin scenario (legacy code rejected; cutover window)
- [x] Banking-grade concerns evaluated (7/7 force-filled)
- [x] Priority set (Must — regulatory)
- [x] Dependencies identified (external dep on VCR doc + mapping)
- [ ] Sizing done (TBD_by_TL pending mapping list size)
- [ ] **No blocking ambiguities** — FAIL: GG-1, GG-2 unresolved; OQ-11 cutover policy

---

### Story EPIC-CARD-DISPUTES-001-2: Per-case SLA timer with countdown and breach-warning visibility

**Format**: Job Story (trigger = case lifecycle state)

**When** a dispute case is opened in our system,
**I want to** see a visible countdown timer per case showing days remaining against the 45-day VISA network SLA,
**So I can** prioritize cases approaching the breach threshold and stop losing chargebacks to expired windows.

#### Context

Currently 6.2% of cases (~260/month) breach the 45-day SLA, losing chargebacks Diana describes as "real money lost". The control point is "dispute opened in our system" (Diana, message 2026-05-07 13:22) — but the exact event field is pending Jamal in card-systems (Tomas, message 2026-05-07 08:51). Timer must be deterministic and audit-defensible because SLA breach disputes against the network may rely on it.

#### Acceptance Criteria (Gherkin)

```gherkin
Scenario: Happy path — timer displays for open case
  Given an analyst is authenticated as "card_dispute_analyst"
  And a case was opened 5 days ago at 2026-07-10T09:00:00Z
  When the analyst views the case
  Then the SLA timer displays "40 days remaining"
  And the timer color is "green" (>= 14 days remaining)

Scenario: Warning state — case approaching breach
  Given a case opened 35 days ago
  When the analyst views the case
  Then the SLA timer displays "10 days remaining"
  And the timer color is "amber" (4 to 13 days remaining)
  And the case appears in the "SLA at risk" filter

Scenario: Breach state — case past 45 days
  Given a case opened 46 days ago
  When the analyst views the case
  Then the SLA timer displays "BREACHED — 1 day over"
  And the timer color is "red"
  And an audit event "case.sla_breached" was emitted at the 45-day boundary

Scenario: Banking-grade audit — breach emission
  Given a case at age 44 days, 23 hours, 59 minutes
  When the timer reaches 45 days
  Then an audit event is emitted with payload:
    | field      | value                            |
    | event      | case.sla_breached                |
    | actor      | system                           |
    | ts         | <ISO-8601 of breach moment>      |
    | before     | "within_sla"                     |
    | after      | "sla_breached"                   |
    | reason     | "45-day VISA network limit exceeded" |
    | idem_key   | "sla-breach-<case_id>"           |
  And no duplicate breach event is emitted on subsequent reads

Scenario: Determinism — timer uses authoritative event field
  Given a case with event field "dispute_opened_at" = 2026-07-10T09:00:00.000Z
  And the system clock is in UTC
  When the timer computes remaining days
  Then the calculation uses (dispute_opened_at + 45 days) - now()
  And no client-side clock is used
  And the displayed value is the same regardless of analyst timezone

Scenario: Edge case — event field not yet confirmed (OQ-04)
  Given OQ-04 is unresolved (Jamal has not confirmed the source field)
  When this story is implemented without source-field confirmation
  Then the story is held at "blocked" status with OQ-04 referenced
```

#### Banking-Grade Concerns

| Concern | Status | Justification | Fields/Events | Treatment | Compensating Action |
|---------|--------|---------------|---------------|-----------|---------------------|
| pii_fields | applies | Case object accessed; PII via case association even though the timer field itself is non-PII | case_id (joins to PII), customer_id (indirect) | Access controlled per RBAC; no PII in timer payload itself | n/a |
| audit_events | applies | SLA breach is auditable for both regulator and network arbitration | case.sla_breached, case.opened, case.viewed | Standard audit schema; breach event idempotent by case_id | n/a |
| idempotency | applies | Breach detection must fire exactly once per case; replay safety required | sla_breach_evaluator (scheduled job) | idempotency_key = "sla-breach-<case_id>"; one event per case | n/a |
| reversibility | not_applicable | Timer is read-only display + event emission; no state change to dispute itself | n/a — read path | n/a | n/a |
| authn_authz | applies | Visible to card_dispute_analyst and senior approver; not customer-facing | role check on view | RBAC + UI scoping | n/a |
| regulatory | applies | 45-day window is VISA network rule; potentially MAS PSN-01 also applies (unconfirmed — see OQ-12) | VISA-network-SLA-45d; MAS-PSN-01? (citation_status: pending) | Bind 45-day constant to a config sourced from VCR doc | n/a |
| tipping_off | not_applicable | Timer is internal analyst tooling, not customer-facing | n/a | n/a | n/a |

#### Priority (MoSCoW)
**Must** (Marcus: "SLA timer + unified case view are the two highest-leverage items")

#### Story Sizing
**Estimated story points**: 5 (assuming event field is single + known)
**Estimated complexity**: medium

#### Dependencies
- **Depends on**: OQ-04 (Jamal confirms event-field source); EXTERNAL data team
- **Blocks**: none

#### Definition of Ready Checklist
- [x] User story format is clear
- [x] At least 1 happy path Gherkin scenario
- [x] At least 1 error/edge case Gherkin scenario
- [x] Banking-grade concerns evaluated (7/7 force-filled)
- [x] Priority set (Must)
- [x] Dependencies identified (data team)
- [x] Sizing done (subject to event-field confirmation)
- [ ] **No blocking ambiguities** — FAIL: OQ-04 (event field), OQ-12 (MAS-PSN-01?)

---

### Story EPIC-CARD-DISPUTES-001-3: Unified case view layered atop existing card admin

**Format**: Job Story (situation = analyst working a case)

**When** I am working on a dispute case,
**I want to** see card-admin data, transaction history, customer comms summary, and network-portal case state in a single layered view,
**So I can** stop flipping between 4 separate systems and resolve cases faster.

#### Context

Yvonne flagged this as a "fuzzy ask" requiring a UX research sprint to nail down what the analyst actually needs front-and-centre (message 2026-05-06 16:33). Diana confirmed "layer, not replace" (2026-05-07 13:22). Tomas confirmed engineering can deliver layered ("UI shell + composed data views from existing services") but not a full replace in Q3. Scope risk is high. **No UX designer is in the thread** — this is a stakeholder absence (see governance gap context, also OQ-05).

#### Acceptance Criteria (Gherkin)

```gherkin
Scenario: Happy path — analyst opens a case and sees all four panels
  Given an analyst is authenticated as "card_dispute_analyst"
  And a case exists with id = "CASE-12345"
  When the analyst opens case CASE-12345 in the unified view
  Then the view displays four panels: card_admin_summary, transaction_history, customer_comms_summary, network_portal_status
  And each panel loads within 3 seconds (95th percentile)
  And the case_id is visible at the top of the view

Scenario: Error — one upstream service unavailable
  Given the customer_comms service is returning 5xx errors
  When the analyst opens case CASE-12345 in the unified view
  Then three panels render normally
  And the customer_comms panel shows a degraded-state message "Comms summary temporarily unavailable — open in source system"
  And a link is provided to the source system
  And no fatal error blocks the view

Scenario: Banking-grade audit — case-view access is logged
  Given an analyst is authenticated as "card_dispute_analyst"
  When the analyst opens case CASE-12345 in the unified view
  Then an audit event is emitted with payload:
    | field      | value                          |
    | event      | case.viewed                    |
    | actor      | <analyst_id>                   |
    | ts         | <ISO-8601 timestamp>           |
    | before     | n/a                            |
    | after      | n/a                            |
    | reason     | "analyst opened unified view"  |
    | idem_key   | "view-<case_id>-<actor>-<minute_bucket>" |
  And the event includes which panels rendered successfully

Scenario: Authorization boundary — non-analyst denied
  Given a user is authenticated with role "marketing"
  When the user attempts to GET /cases/CASE-12345/unified-view
  Then the request is rejected with HTTP 403
  And no panel data is returned
  And an authz_denied audit event is emitted

Scenario: Edge case — UX research outcome may alter layout (OQ-05)
  Given OQ-05 (UX research sprint) is not yet complete
  When this story enters implementation
  Then the implementation is gated on UX-confirmed wireframes
  And no premature panel layout is locked
```

#### Banking-Grade Concerns

| Concern | Status | Justification | Fields/Events | Treatment | Compensating Action |
|---------|--------|---------------|---------------|-----------|---------------------|
| pii_fields | applies | Composes transaction history, customer comms summary, card-admin data — all PII surfaces | card_number_last4, customer_name, transaction_amounts, customer_messages | Inherit treatment of each source system; no new persistence; redact in logs | n/a |
| audit_events | applies | Read-access to composed PII view must be audit-trail-able for regulator and DPO | case.viewed, panel.render_failed | Standard audit schema; per-view event | n/a |
| idempotency | not_applicable | Pure read composition; no state change. Audit emission deduped via minute_bucket key. | n/a — read path | n/a | n/a |
| reversibility | not_applicable | Read-only composition layer; no mutations | n/a — read path | n/a | n/a |
| authn_authz | applies | Composed PII view requires elevated read access — analyst role only | RBAC enforcement at API + UI | role-check on every panel load | n/a |
| regulatory | unknown_p2 | VCR does not directly govern this; PDPA / bank record-keeping may apply to composed PII access logs (unconfirmed) | (citation_status: pending — OQ-13) | Bind to outcome of GG-3 (DPO engagement) | n/a |
| tipping_off | not_applicable | Internal analyst view; customer_comms panel shows past comms in summary form, not new outbound copy | n/a | n/a | n/a |

#### Priority (MoSCoW)
**Should** (Marcus: high-leverage, but Yvonne flagged scope risk; OK to descope if UX sprint reveals 2x scope)

#### Story Sizing
**Estimated story points**: TBD_by_TL (`split_required: true` likely after UX sprint)
**Estimated complexity**: high (composition + UX-dependent)

#### Dependencies
- **Depends on**: OQ-05 (UX research sprint outcome); upstream service availability for 4 panels
- **Blocks**: none (other Phase 1 stories deliver independent value)

#### Definition of Ready Checklist
- [x] User story format is clear
- [x] At least 1 happy path Gherkin scenario
- [x] At least 1 error/edge case Gherkin scenario
- [x] Banking-grade concerns evaluated (7/7 force-filled)
- [x] Priority set (Should)
- [x] Dependencies identified (UX sprint + 4 upstream services)
- [ ] Sizing done — pending UX outcome
- [ ] **No blocking ambiguities** — FAIL: OQ-05, OQ-13

---

### Story EPIC-CARD-DISPUTES-001-4: Mastercard network portal session keepalive (interim)

**Format**: Job Story (situation = analyst working in MC portal)

**When** I am working a Mastercard chargeback case in the MC network portal,
**I want to** stay logged in for the duration of my active session without forced re-authentication,
**So I can** complete case work without losing context to session timeouts (currently "half the time").

#### Context

VISA has API access already used for case management (Tomas, 2026-05-07 08:51). MC has less API access. Diana confirms "session-keepalive interim" for MC (2026-05-07 13:22). The word "interim" is doing important work — there is no committed long-term plan (see OQ-09). Implementation likely involves a browser-extension or proxy-layer keepalive — TL design decision.

#### Acceptance Criteria (Gherkin)

```gherkin
Scenario: Happy path — session stays alive during active work
  Given an analyst is authenticated to the MC network portal
  And the analyst has the unified case view open with an MC case
  When 30 minutes pass with no portal interaction
  Then the MC portal session is still authenticated (no forced re-login)
  And the keepalive mechanism has fired at least once during the window
  And the analyst can continue work without re-authenticating

Scenario: Error — keepalive mechanism fails
  Given an analyst is authenticated to the MC network portal
  And the keepalive mechanism throws an exception
  When the keepalive heartbeat is due
  Then the analyst sees a banner "Session may expire — click to refresh"
  And the session is NOT silently dropped without warning
  And the failure is logged with severity = "warn"

Scenario: Banking-grade audit — keepalive activity is logged
  Given an analyst with an active MC portal session
  When the keepalive mechanism fires a heartbeat at 2026-07-15T10:30:00Z
  Then an audit event is emitted with payload:
    | field      | value                              |
    | event      | mc_portal.keepalive_heartbeat      |
    | actor      | <analyst_id>                       |
    | ts         | 2026-07-15T10:30:00Z               |
    | before     | session_active                     |
    | after      | session_active                     |
    | reason     | "scheduled keepalive"              |
    | idem_key   | "keepalive-<session_id>-<minute_bucket>" |
  And the keepalive does not constitute analyst activity for audit purposes (machine-attributed)

Scenario: Edge case — analyst logs out explicitly
  Given an analyst with an active MC portal session
  When the analyst clicks "Log out"
  Then the keepalive stops immediately
  And the session is terminated
  And the audit log shows analyst-initiated logout, not keepalive

Scenario: Interim-scope acknowledgement (OQ-09)
  Given this story is implemented as the "interim" approach
  When the story is delivered
  Then the long-term plan (MC API integration when available) is documented as Phase-2-or-beyond
  And the keepalive code is tagged "interim — replace when MC API ships"
```

#### Banking-Grade Concerns

| Concern | Status | Justification | Fields/Events | Treatment | Compensating Action |
|---------|--------|---------------|---------------|-----------|---------------------|
| pii_fields | not_applicable | Keepalive is a session-level mechanism; no customer PII is read or written by the keepalive itself (PII visible inside the portal is portal's own concern) | n/a — session mechanism only | n/a | n/a |
| audit_events | applies | Keepalive activity must be auditable to distinguish machine activity from human activity (important for analyst-attribution claims) | mc_portal.keepalive_heartbeat, mc_portal.keepalive_failed | Tag actor as "system_on_behalf_of=<analyst_id>" | n/a |
| idempotency | applies | Heartbeats are scheduled and must not double-fire if scheduler retries | heartbeat fire | minute-bucketed idempotency_key | n/a |
| reversibility | applies | Keepalive is reversible — analyst can log out explicitly; system can disable keepalive | session lifecycle | Explicit logout terminates keepalive cleanly | n/a |
| authn_authz | applies | Keepalive must only fire while analyst session is valid; must not extend stolen-session lifetime indefinitely | session_token validity | Session-token expiry still respected; keepalive extends within token validity, not beyond | n/a |
| regulatory | unknown_p2 | MC network rules on automated session extension (unknown — see OQ-14) | (citation_status: pending) | Bind to outcome of OQ-14 | n/a |
| tipping_off | not_applicable | Session mechanism; not customer-facing | n/a | n/a | n/a |

#### Priority (MoSCoW)
**Should** (Marcus listed it in Phase 1; tactical fix not regulatory)

#### Story Sizing
**Estimated story points**: 5
**Estimated complexity**: medium (depends on portal authentication mechanism — TL spike likely)

#### Dependencies
- **Depends on**: TL spike on MC portal auth mechanism; OQ-09 long-term plan
- **Blocks**: none

#### Definition of Ready Checklist
- [x] User story format is clear
- [x] At least 1 happy path Gherkin scenario
- [x] At least 1 error/edge case Gherkin scenario
- [x] Banking-grade concerns evaluated (7/7 force-filled)
- [x] Priority set (Should)
- [x] Dependencies identified (TL spike + OQ-09)
- [x] Sizing done
- [ ] **No blocking ambiguities** — FAIL: OQ-09, OQ-14

---

### Story EPIC-CARD-DISPUTES-001-5: VISA network API integration expansion for case management

**Format**: Job Story (situation = submitting / updating chargeback to VISA)

**When** an analyst submits or updates a dispute case to the VISA network,
**I want to** push case data via VISA API (instead of the portal UI) where the API supports the action,
**So I can** reduce manual portal time and avoid portal-timeout-related lost submissions.

#### Context

Tomas confirmed VISA API access is already in use for case management (2026-05-07 08:51), implying expansion (not greenfield). Felix and Tomas to confirm exact API surface and which VCR 2026 reason codes are API-supported on day 1.

#### Acceptance Criteria (Gherkin)

```gherkin
Scenario: Happy path — API submission for supported reason code
  Given an analyst is authenticated as "card_dispute_analyst"
  And a case has reason_code = "VCR_13_1" (API-supported)
  And the case has all required fields populated
  When the analyst clicks "Submit to VISA"
  Then the case is submitted via the VISA API
  And the response status is recorded on the case
  And the case transitions to state "submitted_to_network"
  And an audit event "case.submitted_to_network" is emitted

Scenario: Error — VISA API returns rejection
  Given an analyst submits a case to VISA via API
  And VISA returns HTTP 400 with error code "INVALID_PACKET"
  When the response is received
  Then the case state remains "ready_to_submit" (no false-positive transition)
  And the analyst is shown the VISA error code and message
  And the failure is logged with case_id and visa_error_code

Scenario: Banking-grade idempotency — replay safety
  Given a case was submitted with idempotency_key = "ik-sub-001" and VISA accepted it
  When the same submission with idempotency_key = "ik-sub-001" is replayed (e.g., analyst double-click)
  Then no duplicate submission is sent to VISA
  And no duplicate state transition occurs
  And no duplicate audit event is emitted
  And the response returns the original VISA-accepted result

Scenario: Banking-grade audit — submission emission
  Given a case is being submitted to VISA via API
  When the API call succeeds
  Then an audit event is emitted with payload:
    | field      | value                              |
    | event      | case.submitted_to_network          |
    | actor      | <analyst_id>                       |
    | ts         | <ISO-8601 timestamp>               |
    | before     | "ready_to_submit"                  |
    | after      | "submitted_to_network"             |
    | reason     | "analyst-initiated submission"     |
    | idem_key   | <idempotency_key>                  |
  And the audit event includes visa_response_id

Scenario: Banking-grade reversibility — post-submission edits go through arbitration
  Given a case has been submitted to VISA (state = "submitted_to_network")
  When the analyst attempts to edit the reason code
  Then the edit is rejected with error "POST_SUBMISSION_LOCKED"
  And the analyst is shown the network-arbitration path as the compensating action
  And no edit is persisted

Scenario: Edge case — reason code not API-supported, fall back to portal
  Given a case has reason_code = "VCR_44_X" (NOT API-supported, portal-only)
  When the analyst clicks "Submit to VISA"
  Then the system shows "This reason code requires portal submission — opening MC/VISA portal..."
  And no API call is attempted
  And the analyst proceeds via portal
```

#### Banking-Grade Concerns

| Concern | Status | Justification | Fields/Events | Treatment | Compensating Action |
|---------|--------|---------------|---------------|-----------|---------------------|
| pii_fields | applies | Submission payload includes customer transaction details, card number, customer statement | card_number, transaction_id, transaction_amount, customer_statement_excerpt | Submit over TLS to VISA; minimize payload to required fields; do not log full PAN | n/a |
| audit_events | applies | Network submission is the critical irreversible event of the entire epic — full audit required | case.submitted_to_network, visa_api.call_made, visa_api.response_received | Standard audit schema + payload schema with visa_response_id | n/a |
| idempotency | applies | Submission to external network is the highest-stakes idempotency surface — double-submission would create duplicate chargebacks | submit_to_visa | client-generated idempotency_key required on every submission call; VISA's own idempotency-id used for downstream replay safety | n/a |
| reversibility | applies | Post-submission edits to network are NOT reversible without arbitration (Diana / VCR rules). Compensating action is the arbitration path itself | case.reason_code post-submission | Post-submission state lock; arbitration is the only path | **Network arbitration** (slow + expensive — TL must design the analyst workflow for arbitration initiation) |
| authn_authz | applies | Only card_dispute_analyst (and senior approver for overrides) may submit | role check on POST /cases/<id>/submit | RBAC at API gateway | n/a |
| regulatory | applies | VCR 2026 rules govern what is API-supported vs portal-only; VISA network operating regulations bind the submission semantics | VCR-2026 (citation_status: pending) | Bind reason-code-to-channel mapping to VCR doc | n/a |
| tipping_off | not_applicable | Submission to network is internal-to-bank-to-network; no customer-facing copy is produced by this story | n/a | n/a | n/a |

#### Priority (MoSCoW)
**Must** (paired with Story 1 — without API submission, the new VCR reason codes have nowhere to go for API-supported codes)

#### Story Sizing
**Estimated story points**: TBD_by_TL (`split_required: true` likely — split by which API methods are in scope)
**Estimated complexity**: high (external integration + idempotency + reversibility + regulatory)

#### Dependencies
- **Depends on**: EPIC-CARD-DISPUTES-001-1 (reason codes must exist before submission); VCR doc (GG-2); Felix's API-support mapping
- **Blocks**: none (Story 2 SLA timer is independent of API integration)

#### Definition of Ready Checklist
- [x] User story format is clear
- [x] At least 1 happy path Gherkin scenario
- [x] At least 1 error/edge case Gherkin scenario
- [x] Banking-grade concerns evaluated (7/7 force-filled)
- [x] Priority set (Must)
- [x] Dependencies identified
- [ ] Sizing done — TBD pending API-support scope
- [ ] **No blocking ambiguities** — FAIL: GG-2, OQ-15 (API-support mapping)

---

## Open Questions (for TL — Stage 2)

> 15 open questions. Severities per `references/ambiguity-patterns.md`. P1 OQs match governance gaps above (one row per concern, cross-referenced).

| # | ID | Severity | Question | Why it matters | Suggested resolver | Conflict evidence |
|---|----|----------|----------|----------------|---------------------|-------------------|
| 1 | OQ-01 | **P1** | Will Legal be engaged for VCR 2026 customer-facing reason-code language interpretation and tipping-off scan on Phase 2 customer-comms templates? | AP-5.1 / FM-05 — regulatory scope without Legal-engaged is the highest-leverage governance defect; FM-06 risk for Phase 2 deferred items now hard-deferred but not exempt | Marcus (Sponsor) → Legal | Email thread CC list contains no Legal participant across 5 emails 2026-05-05 to 2026-05-07 |
| 2 | OQ-02 | **P1** | Who is the Compliance officer of record for VCR 2026 ruleset adherence, and have they ratified Felix's mapping? | AP-3.2 — Compliance ≠ Legal but BOTH are absent; VCR is regulatory and Compliance dimension is not addressed | Marcus → Compliance | "Felix's team has been mapping" (Diana, 2026-05-05 17:42) with no Compliance attestation |
| 3 | OQ-03 | **P1** | Will DPO / Privacy ratify the PII inventory below and confirm retention / residency / masking / access-audit rules for dispute case objects? | AP-4.1 — PII surface (transaction history, customer statements, customer-comms summary) without DPO sign-off is a handoff block | Marcus → DPO | "the dispute analyst team is drowning… 4,200 cases/month" (Diana, 2026-05-05 11:08) implies high-volume PII access |
| 4 | OQ-04 | **P2** | What is the exact event field that anchors the SLA timer (Diana: "dispute opened in our system"; Tomas: "need data team to confirm we capture all required event types")? | SLA timer determinism + audit defensibility against network arbitration depends on a single authoritative source-of-truth event | Felix → Jamal (card-systems team) → Data team | Diana 2026-05-07 13:22: "from dispute opened in our system… talk to Jamal in card-systems for the exact event field." Tomas 2026-05-07 08:51: "straightforward IF we have authoritative event-time fields." Conflict mode: estimate-vs-rule |
| 5 | OQ-05 | **P2** | What is the scope and timeline of the UX research sprint Yvonne requested for the unified case view? | "Unified case view" is a fuzzy ask per Yvonne; scoping the layer without UX risk-of-rework is high; no UX designer in thread | Yvonne → UX team lead (not named) | Yvonne 2026-05-06 16:33: "'unified case view' is a fuzzy ask. We'd need a UX research sprint first to nail down what the analyst actually needs front and centre." |
| 6 | OQ-06 | **P2** | What is the dollar value of chargebacks currently lost due to SLA breach and packet quality? | Diana's "$X million/year" placeholder is unbound; success-criteria #4 needs a baseline. AP-2.3 placeholder token requires named-owner | Felix Tan (Diana deferred: "Felix can get you the dollar figure") | Diana 2026-05-05 11:08: "$X million/year (please don't quote me on this until Felix confirms)" — placeholder token attached to material financial impact |
| 7 | OQ-07 | **P2** | Is Phase 1 owner handoff from Diana to Felix formalized in writing (RACI / DACI / project-charter equivalent), and what is the SLA on Felix's availability during Diana's leave window 2026-06-01 to 2026-08-15? | Continuity gap during leave; Felix has not directly authored anything in this thread (only Cc) | Marcus + Diana before 2026-06-01 | Diana 2026-05-05 17:42: "I'm going on parental leave 2026-06-01 to 2026-08-15 so any decisions made after that, Felix is the point of contact." 2026-05-07 13:22: "Felix will pick up after my leave starts." Verbal — not formalized |
| 8 | OQ-08 | **P2** | What is the quantified baseline for network portal session timeouts (currently "half the time" — qualitative)? | Quantifier ambiguity per AP-6.3; success-criteria #5 needs measurable baseline | Felix + Tomas (instrument portal telemetry) | Diana 2026-05-05 17:42: "Half the time the network portal session times out and they have to log in again." Quantifier word: "Half the time" |
| 9 | OQ-09 | **P2** | What is the long-term plan for Mastercard network integration after the "interim" session-keepalive ships? | "Interim" implies temporary but no committed roadmap exists; technical debt risk if interim becomes permanent | Tomas + Yvonne (post-Phase-1) | Diana 2026-05-07 13:22: "Network portal: API where available (VISA), session-keepalive interim for MC." Tomas 2026-05-07 08:51: "MC less so. May need session-keepalive interim for MC." Modal "may" |
| 10 | OQ-10 | **P2** | What is the current status of Felix's VCR 2026 rule mapping (% complete, blockers, expected completion date)? | Story EPIC-CARD-DISPUTES-001-1 is gated on this mapping; Q3 2026 timeline depends on mapping availability for engineering | Felix Tan | Diana 2026-05-05 17:42: "Felix's team has been mapping" — status unstated |
| 11 | OQ-11 | **P2** | What is the cutover policy for cases opened pre-2026-07-01 with legacy reason codes? (Re-map to VCR 2026 codes, grandfather under legacy until close, or other?) | Story 1 edge case; affects user experience and audit reconciliation across the cutover window | Felix + Compliance | No source quote — derived from VCR cutover semantics; not addressed in thread |
| 12 | OQ-12 | **P2** | Does MAS PSN-01 (or other sovereign regulator) apply to payment-dispute timing in addition to the VISA network 45-day SLA? | Tier inference signal — if MAS regulator binds the SLA window, tier may lift to T1 per AP-1.3 | Compliance | No source quote — derived from regulatory-completeness check |
| 13 | OQ-13 | **P2** | Does composing PII fields from multiple systems into a unified read view create new PDPA / regulatory access-log obligations relative to existing card admin UI? | DPO ratification dependency; affects audit-event schema for Story 3 | DPO + Compliance | No source quote — derived from PII composition concern |
| 14 | OQ-14 | **P2** | Are there Mastercard network rules governing automated session keepalive that constrain implementation? | Story 4 regulatory row marked unknown_p2 — needs MC network-rules review | Compliance + Tomas | No source quote — derived from MC network rules check |
| 15 | OQ-15 | **P2** | Which VCR 2026 reason codes are API-supported by VISA at 2026-07-01 vs portal-only? | Story 5 scope; reason-code-to-channel mapping needed for analyst UX | Felix + VISA technical-account contact | Tomas 2026-05-07 08:51: "VISA has API access we already use for case management" — but coverage map not stated |
| 16 | OQ-16 | **P3** | What is the in-band telemetry for measuring analyst handling time (47 min baseline) — is it case-system audit log or external time-tracking? | Success-criteria #3 measurement method needs anchored data source | Felix + data team | Diana 2026-05-05 11:08: "Average case handling time: 47 min (target <30)" — measurement source unstated |
| 17 | OQ-17 | **P3** | Should dual approval be required for high-value chargeback submissions (e.g., > $10K), and what is the threshold? | Banking-grade authz hardening; not in scope per any source quote but typical T2-card-ops control | Felix + Compliance | No source quote — derived from banking-grade authz check |

---

## Assumptions Made (Explicit)

> Assumptions BA had to make to write this brief. TL may challenge.

- **A1** — Q3 2026 implementation timeline is driven by VISA VCR 2026-07 effective date (regulatory hard). *Why*: Diana and Yvonne both treat VCR as non-negotiable; Marcus's Phase 1/Phase 2 split aligns scope to that deadline.
- **A2** — Phase 1 owner from 2026-06-01 onward is Felix Tan. *Why*: Diana explicitly named Felix in 2026-05-05 17:42 and reconfirmed 2026-05-07 13:22. Formalization pending — see OQ-07.
- **A3** — Phase 2 stories (customer comms templates, packet auto-assembly, win/loss analytics) are deferred to Q4 2026 / Q1 2027. *Why*: Marcus explicitly framed them as Phase 2; Yvonne agreed "would prefer to defer until Phase 1 lands."
- **A4** — Unified case view is a layer atop existing card admin UI, NOT a replacement. *Why*: Diana explicit 2026-05-07 13:22; Tomas confirmed replace is 6-9mo and out of Q3 scope.
- **A5** — Phase 1 customer comms = email only; in-app is Phase 2. *Why*: Diana explicit 2026-05-07 13:22.
- **A6** — Industry win-rate benchmark 71% is the long-term target (interim target ≥68% within 180 days). *Why*: Diana cited the benchmark; explicit target commitment not stated — flagged as derived target.
- **A7** — VISA VCR is treated as a **card-network rule with regulatory weight** (T2-shadow). Treated as if MAS PSN-01 may also apply pending OQ-12. *Why*: VISA = card-network operating regulator; sovereign overlap unclear in thread.
- **A8** — Analyst attrition is treated as a real driver of business value but not a hard target for Phase 1 stories (no story commits to attrition reduction). *Why*: Diana cited 22% / 12mo but no commitment to a fix-attrition target in thread.
- **A9** — The attached `dispute-ops-q1-2026-review-v2.pptx` is treated as supporting evidence but its content is NOT incorporated into this brief (cannot analyze attachments). *Why*: Attachment referenced but not analyzable in this elicitation pass — see GG-2 / OQ-10.

---

## Glossary (Domain Terms)

| Term | Canonical Form | Surface Forms | Definition | Source | PII Sensitivity | Regulatory Tie |
|------|----------------|---------------|------------|--------|------------------|----------------|
| VISA VCR | VISA_VCR_2026 | "VISA VCR", "VCR", "VCR ruleset", "VISA Claims Resolution" | VISA Claims Resolution ruleset revision effective 2026-07; changes dispute categories and reason codes | Thread (Diana, Marcus, Yvonne) | none | regulator: VISA Network; code: VCR-2026; status: **unresolved** (no document attached) |
| Chargeback | chargeback | "chargeback", "dispute" | A formal dispute initiated by a cardholder challenging a transaction; processed via card-network rules | Domain knowledge | indirect (PII via case association) | regulator: VISA / MC Network; status: resolved (industry standard) |
| Reason code | dispute_reason_code | "reason code", "VCR reason code", "legacy code" | Categorical code identifying the basis for a dispute (e.g., fraud, non-receipt, duplicate); changes under VCR 2026 | Thread + VCR domain | none | regulator: VISA; status: pending |
| Network portal | network_portal | "network portal", "VISA portal", "MC portal" | The vendor-provided UI for submitting and managing chargebacks to the card network | Thread (Diana, Tomas) | none | none |
| SLA (45-day) | network_sla_45d | "SLA", "45 days", "network SLA" | The 45-day window in which a bank must submit a chargeback to the card network or forfeit the dispute | Thread (Diana) | none | regulator: VISA Network; code: 45d-rule; status: pending (cite needed) |
| Chargeback packet | chargeback_packet | "packet", "chargeback packet" | The bundle submitted to the network: reason code + transaction details + customer statement + supporting docs | Thread (Diana) | indirect (contains customer PII) | none |
| Card admin (UI) | card_admin_ui | "card admin", "card admin UI" | The existing internal system for managing card accounts; case-mgmt today flips between this and 3 other screens | Thread (Diana, Tomas) | indirect | none |
| Analyst | card_dispute_analyst | "analyst", "dispute analyst", "analyst team" | The Ops role processing dispute cases; current attrition cite 22% / 12mo | Thread (Diana) | none | none |
| Senior approver | senior_approver | "senior approver" | Hypothetical role for dual-control on high-value cases; not explicitly named in thread but typical T2 banking control | Derived | none | none |
| Network arbitration | network_arbitration | "arbitration" | The slow + expensive process to contest a network rule outcome post-submission; serves as compensating action for irreversibility | Domain knowledge | none | regulator: VISA / MC; status: pending |
| Tipping-off | tipping_off | (not in thread) | Forbidden disclosure that an AML / fraud investigation is underway; applies to customer comms language for confirmed-fraud disputes | Domain knowledge | regulatory | regulator: MAS / FATF; status: pending |

---

## PII Inventory

| Field | Category | Treatment | Retention Rule | Residency Rule | Masking Rule | Access Audit |
|-------|----------|-----------|----------------|----------------|--------------|--------------|
| card_number (PAN) | direct | Never display full PAN in unified case view; always last-4 only; full PAN accessible only via explicit override with audit | TBD (GG-4 / OQ-03) | TBD (GG-3) | mask to last-4 in UI and logs | log access to full PAN per case_id + actor_id |
| customer_id | indirect | Display in case header; not exposed in customer-facing copy | TBD (GG-4) | TBD (GG-3) | display in clear to analyst | log access per case_id |
| transaction_id | indirect | Display in case header and transaction history panel | TBD (GG-4) | TBD (GG-3) | none required | implicit via case access log |
| transaction_amount | indirect | Display in unified view; pass through to VISA submission payload | TBD (GG-4) | TBD (GG-3) | none required | implicit via case access log |
| customer_name | direct | Display in case header; not exposed in any customer-facing Phase 1 copy | TBD (GG-4) | TBD (GG-3) | display in clear to analyst | log access per case_id |
| customer_statement (text) | indirect (free-text PII possible) | Display in customer comms panel; submit to VISA in chargeback packet | TBD (GG-4) | TBD (GG-3) | scan for inadvertent NRIC / SSN in free text before submission | log access per case_id |
| customer_email | direct | Out of Phase 1 scope (no email composition); display only | TBD (GG-4) | TBD (GG-3) | mask domain in low-priv views | log access per case_id |
| dispute_reason_code | none | Internal code; not customer-facing | n/a | n/a | n/a | implicit via case access log |
| sla_timer_value | none | Computed value; not PII per se but PII-adjacent via case_id | n/a | n/a | n/a | implicit via case access log |

> **All retention / residency / masking rules above are marked TBD pending DPO engagement (GG-3, GG-4, OQ-03). This table is a draft; DPO ratification is required before TL handoff.**

---

## Regulatory Dependencies

| Regulator | Code | Revision | Citation Status | Promisor | Due Date |
|-----------|------|----------|-----------------|----------|----------|
| VISA Network | VCR-2026 | 2026 revision | pending | Felix Tan | 2026-07-01 (effective) |
| VISA Network | network_sla_45d | n/a | pending | Felix Tan | n/a (ongoing) |
| MAS (?) | PSN-01 | n/a | pending | Compliance (OQ-12) | TBD |
| Mastercard Network | mc_session_rules | n/a | pending | Tomas + Compliance (OQ-14) | TBD |
| Local Privacy (PDPA?) | n/a | n/a | pending | DPO (OQ-13) | TBD |

---

## BA-Level Compliance Checklist

- [x] **All PII fields identified** — see PII Inventory above (treatments marked TBD pending DPO — see GG-3)
- [x] **Audit trail requirements** stated per story (all 5 stories carry audit_events row = applies with payload schema)
- [x] **Regulatory references** included — VCR-2026 cited; citation_status = pending (GG-2)
- [x] **No assumption of irreversible action** without explicit compensation requirement — Story 5 (submission to network) declares compensating_action = network arbitration; flagged for TL design
- [x] **All stories pass INVEST** (with split_required: true noted where applicable) — Stories 1, 3, 5 carry split_required pending external dependencies
- [x] **All ACs in Gherkin format** (testable) — 5 stories × ≥4 scenarios each, all Gherkin
- [ ] **Definition of Ready met** for each story — FAIL: all 5 stories carry "no_blocking_ambiguities = false" because of unresolved OQs and governance gaps
- [x] **MoSCoW prioritization** complete — Stories 1, 2, 5 = Must (regulatory + high-leverage); Stories 3, 4 = Should
- [x] **Open questions** explicit (not buried as assumptions) — 17 OQs surfaced; 3 marked P1 mirroring governance gaps
- [x] **Dependencies** mapped between stories — Story 1 blocks Story 5; Story 2 independent; Story 3 independent; Story 4 independent

---

## Definition of Done (Epic Closure)

When this epic is considered "delivered":

- [ ] All Must stories (1, 2, 5) implemented and passing tests pre-2026-07-01
- [ ] All Should stories (3, 4) implemented OR explicitly deferred with written sponsor sign-off
- [ ] Success criteria metrics #1 (VCR coverage = 100%) and #2 (SLA breach < 2%) measured and meet targets within 90 days post-launch
- [ ] Documentation updated (analyst runbook + VCR mapping reference)
- [ ] Audit logging in production for case.opened, case.reason_code_changed, case.submitted_to_network, case.sla_breached, case.viewed
- [ ] Compensating action (network arbitration workflow) documented for Story 5 reversibility row
- [ ] No P0/P1 bugs from QA outstanding
- [ ] Stakeholder sign-off obtained (incl. Legal, Compliance, DPO — currently absent; see GG-1 / GG-2 / GG-3)
- [ ] Production validation complete

---

## BA Reasoning Trace (Audit)

### Why this epic boundary?

The thread describes a single coherent ops problem (card dispute workflow under VCR 2026 regulatory pressure) with Marcus's reply explicitly framing it as **Phase 1 + Phase 2** in one initiative. Per AP-3.3 (multi-epic squashing), I evaluated whether Phase 1's 5 workstreams (VCR mapping, SLA timer, unified view, MC keepalive, VISA API expansion) constitute distinct epics. Verdict: **single epic** because (a) all 5 stories serve a single user (card dispute analyst), (b) all 5 are bounded by the same regulatory deadline (VCR 2026-07), (c) the workstreams compose into a single dispute-case object lifecycle (no separate user value tracks). Phase 2 items are catalogued in `out_of_scope_deferred` rather than emitted as a second epic — Phase 2 has not been committed to by Yvonne ("would prefer to defer") and committing them prematurely would inflate scope.

### Why this story decomposition?

I split Phase 1 along **workflow steps + regulatory-driven feature axes** per `references/invest-checklist.md` split-patterns table:

- Story 1 (VCR reason-code mapping) — **workflow step** axis (case-creation pre-submission); regulatory must-do
- Story 2 (SLA timer) — **data-variation** axis (timer is a derived field added to existing case object); high-leverage standalone
- Story 3 (unified case view layer) — **role-boundary** axis (single user, but UX composes across systems); UX-dependent
- Story 4 (MC session keepalive) — **workflow step + vendor variation** axis (network-specific behavior); tactical
- Story 5 (VISA API integration expansion) — **workflow step** axis (case-submission); blocks completion of Story 1's value

I avoided **tech-layer splits** per AP-7.1 (no "Re-upload UI" / "Re-upload API" pattern). I considered splitting Story 1 into "reason-code registry" + "reason-code picker UI" but rejected it (tech-layer). I considered merging Stories 1 + 5 (both VCR-driven) but kept them separate because Story 5 also enables existing-VCR codes and has independent VISA-API scope; merging would inflate to >7 ACs (AP-7.3). Story 3 may itself split after the UX sprint (OQ-05) — flagged `split_required: true`.

### Best practices applied

- **INVEST** applied per story (per `references/invest-checklist.md`); 3/5 stories carry `split_required: true` where external dependency or sizing is unbounded
- **Gherkin** applied to every AC (per `references/gherkin-templates.md`); all 5 stories carry happy + error + banking-grade scenarios as minimum
- **Job Story format** used as default per `references/job-story-decision-tree.md` because trigger (case state / regulatory cutover / portal session) drives behavior more than role; analyst role is consistent across all 5 stories
- **MoSCoW** prioritized per regulatory bind: VCR-mandated and high-leverage = Must (Stories 1, 2, 5); tactical / scope-risk = Should (Stories 3, 4); deferred = Won't-for-Phase-1 (Phase 2 items in `out_of_scope_deferred`)
- **Banking-grade force-fill** per `SKILL.md` Step 8 + AP-4.1 + AP-4.3 + AP-4.4: all 35 banking-grade rows (5 stories × 7 fields) carry non-null status + justification ≥10 chars
- **Surface-don't-repair** per AP-2.1: 15 OQs surfaced; 3 lifted to P1 to mirror governance gaps; placeholder tokens ("$X million") preserved verbatim with named owner action (OQ-06)
- **Legal-absence detection** per AP-5.1: GG-1 fires; status = blocked

### Best practices intentionally deviated

- **None.** This brief surfaces all detected gaps rather than repairing them. The `output_type: blocked_partial_brief` is the correct shape given FM-05 (Legal absent on regulatory).

---

## BA Reasoning Trace — Skill Procedure Self-Check

(Per `SKILL.md` Step 12 final-gates evaluation.)

| Gate | Result | Notes |
|------|--------|-------|
| FM-01 (quality < 5.0) | PASS | Linguistic composite ≈ 7.2 (structured email thread, good attribution, quantified metrics on most key facts) |
| FM-02 (any unresolved P1) | **FAIL** | 3 P1 OQs (OQ-01, OQ-02, OQ-03) — blocked_partial_brief is correct shape |
| FM-05 (Legal absent + regulatory) | **FAIL** | GG-1 fires; legal_status = absent; scope = VCR regulatory + future customer-comms |
| FM-06 (tipping-off violation) | PASS (Phase 1 internal-only; Phase 2 deferred — flag carried to Phase 2 OQ-01) |
| FM-11 (schema validation) | PASS | All 35 banking-grade rows non-null + justification ≥10 chars; story IDs match pattern; all required frontmatter present |
| FM-12 (ground-truth strip) | PASS | Strip detected at line 237 "## Intentional Issues for R6 to Catch (Hidden from BA Workflow)"; stripped to EOF; byte range emitted; no substring survival in output |
| FM-13 (post-generation PII echo) | PASS | No NRIC / account number / credit card / passport patterns in output (placeholders only; no actual PII in source) |

**Final disposition**: `output_type: blocked_partial_brief`, `blocks_tl_handoff: true`, `frontmatter.status: blocked`. Resolve GG-1 through GG-4 (or record Sponsor risk acceptance) before TL handoff for design.
