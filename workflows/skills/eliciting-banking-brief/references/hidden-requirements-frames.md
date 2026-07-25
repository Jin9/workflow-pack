# Hidden-Requirements Frames

Authoritative reference for Step 9.5 (hidden-requirements sweep) of `SKILL.md` v1.2.0. Loaded **after** Step 9 (ambiguity detection) and **before** Step 10 (Gherkin composition).

## Purpose

Step 9 catches what the **prose says ambiguously** (vague quantifiers, modal hedges, anonymous numeric defaults). This step catches what the **prose doesn't say at all** — questions the author never thought to ask. The two are categorically distinct:

| | Step 9 (ambiguity) | Step 9.5 (hidden-frame sweep) |
|---|---|---|
| Provenance | `prose_ambiguity` | `hidden_frame_sweep` |
| Trigger | A word/phrase in the input is fuzzy | The input is silent on a known-critical dimension |
| Severity baseline | Frame-agnostic; depends on the phrase | Frame-driven; baseline set per frame |
| Method | Lexical / syntactic / pragmatic detectors | Apply 10 fixed frames as a checklist |

Hidden-frame findings land in `open_questions[]` (tagged `provenance: hidden_frame_sweep, frame: N`) or `assumptions_made[]` (same tags, plus `default_revisit_trigger`). They do NOT live in a separate top-level array — downstream Stage 2 should see one unified list of "things to confirm".

## The 10 frames

Each frame has: (a) question pattern, (b) activation trigger, (c) default severity floor, (d) cap (max findings emitted per frame), (e) output pattern.

---

### Frame 1 — Scale & capacity

**Question pattern:** How many? How big? How fast? How much?

**Activation trigger:** **Always fires.** Every system has a scale dimension.

**Default severity floor:** **P1** for launch-blocking sizing; **P2** for growth-trajectory sizing.

**Cap:** 5 findings.

**Output pattern:** Mostly `open_questions[]`. Where the BA picks a defensible default (e.g., "assume 1k DAU at launch based on comparable-merchant benchmarks"), emit as `assumptions_made[]` with `default_revisit_trigger: "post-launch week-2 telemetry"`.

**Frame question library:**
- Expected registered user count (day 30 / day 90 / year 1)
- Daily active users; peak hour concurrent users
- Catalog/inventory size (orders of magnitude — 10²? 10⁴? 10⁶?)
- Average transaction value or unit-of-business size
- Transactions per day at launch / at 6 months / at peak
- Reservation / hold / lock TTL when concurrency invariants exist
- Read:write ratio (drives cache strategy)
- Concurrent admin/operator users
- Notification / message / event volume per day
- Data growth rate (rows/day, bytes/day) and storage budget
- Concurrent session count at peak
- Geographic distribution within the named market

**Anti-pattern to avoid:** Capacity numbers invented by the BA without source. If you assume, name the comparable benchmark or mark `unknown_p2`.

---

### Frame 2 — Time & timing

**Question pattern:** When peaks? When quiet? What rhythm? What schedule?

**Activation trigger:** **Always fires.** Every system has temporal dynamics.

**Default severity floor:** **P2** for peak-windows; **P1** for time-of-day SLA promises to customer.

**Cap:** 5 findings.

**Output pattern:** Mix of OQs and assumptions. Time-zone defaults are usually assumable (use input's named market or system metadata); peak windows usually need PM input.

**Frame question library:**
- Peak season(s) — annual events, paydays, regional festivals, mega-sale dates (11.11, Black Friday, Songkran, Lunar New Year)
- Peak hour daily (e-commerce typically evenings; B2B mid-day)
- Pay-cycle spikes (monthly, weekly)
- Order/transaction cutoff time for same-period processing promise
- TTL / expiry durations (reservation, session, password reset, coupon, draft)
- Grace windows (cancel-before-X, return-within-Y)
- Working hours / business hours boundary
- Public-holiday handling (does the SLA pause?)
- Time-zone convention (especially when input is silent and serves a specific market)
- Daylight-saving-time impact (none for Thailand; relevant elsewhere)
- Audit / accounting retention period — must align with jurisdictional law
- Backup/archive cadence

**Anti-pattern to avoid:** Treating "soon" / "fast" / "quick" as already-detected by Step 9 — those are prose ambiguities. The hidden-frame finding is the **absence** of a number where one is required.

---

### Frame 3 — Money & economics

**Question pattern:** Who pays? Who owes? Who collects? How is it counted? How is it reconciled?

**Activation trigger:** **Fires when input mentions:** money, price, fee, charge, subscription, payment, refund, settlement, payout, billing, invoice, tax. Skip for pure-content / pure-internal-tooling systems.

**Default severity floor:** **P1** for tax/regulatory; **P2** for margin/pricing strategy.

**Cap:** 5 findings.

**Output pattern:** Tax obligations are usually OQs (must consult Finance + jurisdiction). Pricing strategy can be assumed with `default_revisit_trigger: "before public launch"`.

**Frame question library:**
- VAT / GST / sales-tax applicability and rate; tax-invoice format mandated by local tax authority
- Currency precision / rounding policy (e.g., bankers' rounding for fractional units)
- Payment-processing fees (chargeback economics, refund fees, settlement timing)
- Margin policy / pricing strategy (compare-at price abuse exposure)
- Settlement period from PSP (T+1? T+3? Weekly?)
- Refund accounting workflow (who debits which account)
- Chargeback workflow (dispute deadline, evidence package)
- Failed-payment cost recovery (opportunity cost of reserved-but-unpaid stock)
- Promotional spend budget cap
- Cost per acquisition (CAC) budget / target
- FX handling if multi-currency (locked-in rate vs market rate at settlement)
- Bad-debt provisioning

**Anti-pattern to avoid:** Assuming the merchant is VAT-registered without confirming. VAT triggers tax-invoice format obligations that the system architecture must support.

---

### Frame 4 — Regulatory & legal

**Question pattern:** Which laws apply in this jurisdiction to this customer type for this data type?

**Activation trigger:** **Fires when input mentions any of:** personal data, contact info, payment, financial transaction, health, biometric, age-restricted product, alcohol, tobacco, gambling, lending, advice, content with user-generated component. **Also fires when input names a specific country/market.** Skip only for true zero-PII zero-regulated-activity systems.

**Default severity floor:** **P1** by default. P2 only if PM explicitly acknowledges and accepts the regulatory deferral.

**Cap:** **10 findings** (higher cap because this frame is fail-closed by default). Soft cap; mandatory FM-17 sub-topic coverage takes precedence. When `findings_per_frame[4] > 10`, declare the overshoot in `processing_metadata.hidden_requirements_sweep.cap_exceptions["4"]` with `{cap, observed_count, reason (>=8 chars)}` per the **v1.3.1+ protocol** (assertion F-8 in `tests/assertions/frame-coverage-completeness.md`).

**Output pattern:** Almost always OQs that escalate to `governance_gaps[]`. Assumed defaults are rare and only with PM sign-off (`default_revisit_trigger: "Legal review milestone — confirmed date"`).

**Frame question library (general, then jurisdiction-specific):**

*General:*
- Privacy law applicability (GDPR / CCPA / PIPEDA / PDPA / LGPD / equivalent local act)
- Consent capture UX (granular? bundled? opt-in vs opt-out)
- Lawful basis for each data category processed
- Retention schedule per data class
- Data Subject Access Request (DSAR) workflow
- Right to erasure workflow + scope
- Right to portability
- Breach notification process + statutory deadline
- Cross-border data transfer mechanism (adequacy, SCC, BCR, consent)
- Sub-processor / vendor due-diligence and DPA
- Consumer protection law: mandatory disclosures, return policy, cooling-off period
- Tax law: registration thresholds, invoice format, retention, e-filing
- Accounting law: record retention, auditor access, immutability of journals
- Cybersecurity law: incident reporting, log retention, identity verification
- Industry-specific: PCI DSS (payments), HIPAA (health), KYC/AML (financial), CIPA (children's online)
- Trade competition law: deceptive pricing, anti-competitive bundling
- Telecom/marketing law: SMS opt-in, email CAN-SPAM compliance

*Thai-specific examples (when market is Thailand):*
- PDPA (B.E. 2562 / 2019)
- Consumer Protection Act (B.E. 2522)
- Direct Sales and Direct Marketing Act
- Thai Revenue Code (VAT, accounting record retention)
- e-Tax invoice (Revenue Department)
- Computer Crime Act (log retention, content liability)
- Trade Competition Act
- NBTC SMS regulations

**Anti-pattern to avoid:** Citing a regulator the input doesn't name AND inventing the regulation's specifics. Cite the regulator name; mark the citation as `pending`; require Legal sign-off; never invent statute text.

#### Required sub-topics when activated (v1.2.2+)

This sub-section is the **FM-17 enforcement basis**: every required sub-topic listed under an active trigger MUST receive at least one OQ or assumption in the brief. Coverage is checked at emission time (FM-17) by keyword matching against OQ `question + why_matters` and assumption `assumption + why_made`. If a required sub-topic has no covering finding, the brief renders with a hard error (renderer's `validate_frame4_subtopics()`); the BA must either add a covering OQ/assumption OR explicitly skip with reason in `processing_metadata.hidden_requirements_sweep.frames_skipped_reasons` under key `4:<sub_topic_id>` (value ≥8 chars).

**Why this exists.** In v1.2.1 holdout runs, Frame 4 dropped from 10 findings to 6 between two independent runs on the same input. The dropped sub-topics — cross-border PDPA transfer, right-to-erasure-vs-retention reconciliation, PCI-DSS scope, cookie consent, merchant disclosure — are now mechanically required when their activation triggers fire.

##### Activation triggers (v1.2.2 — five enforced)

The renderer's `_detect_frame4_triggers()` detects five triggers from the brief JSON (not from input prose — the BA's encoded judgment in the brief is what we check):

| Trigger | Detection signal in the brief |
|---|---|
| `pii_collection` | `pii_inventory[]` has ≥1 entry with `category ∈ {direct, regulatory}` |
| `jurisdiction_thailand` | `processing_metadata.language_inventory` mentions Thai OR `regulatory_dependencies[]` cites PDPA |
| `payment_processing` | epic title / problem_statement OR story title / context mentions payment / checkout / PSP / mock provider / card / wallet |
| `audit_logging` | any story has `banking_grade_concerns.audit_events.status == "applies"` |
| `consumer_facing` | any epic stakeholder has role mentioning customer / end user / shopper / buyer / consumer |

Each trigger fires independently; multiple usually fire (on the ShopPilot input all 5 fire). Triggers `children`, `health/medical`, `financial/lending`, `telecom/SMS-marketing` are catalogued below as **v1.3-pending** — the keyword library exists but the renderer's trigger-detection logic does not yet recognize them. v1.3 candidate.

##### Required sub-topic detection table (v1.2.2 enforced)

The renderer's `FRAME4_SUBTOPIC_RULES` constant maps trigger → list of `(sub_topic_id, coverage_keywords[])`. Coverage requires at least one keyword (case-insensitive substring) in any frame-tagged OQ or assumption text. As of **v1.3.0**, this table is the human-readable mirror of `references/frame-rule-data.json` (the runtime source-of-truth that the renderer loads at import time); drift is caught by `scripts/check_frame_rule_data_drift.py` (assertion F-7).

| Trigger | sub_topic_id | Coverage keywords (any one matches) | Jurisdiction-specific note |
|---|---|---|---|
| `pii_collection` | `dsar_workflow` | dsar; data subject access; subject access request; right of access | PDPA s.30; GDPR art.15; CCPA right-to-know |
| `pii_collection` | `right_to_erasure` | right to erasure; right-to-erasure; right to be forgotten; erasure workflow; deletion request | PDPA s.33; GDPR art.17; CCPA right-to-delete |
| `pii_collection` | `retention_schedule` | retention schedule; retention period; retention policy; data retention | Thai tax: 5y; PDPA: purpose-bound; GDPR: storage limitation |
| `pii_collection` | `breach_notification` | breach notification; breach notice; 72h; 72 hour; incident notification | PDPA s.37 (72h); GDPR art.33-34 (72h) |
| `pii_collection` | `lawful_basis` | lawful basis; consent ux; consent capture; legal basis; consent flow | PDPA s.19; GDPR art.6 / art.7 |
| `pii_collection` | `cross_border_transfer` | cross-border; cross border; data transfer; SCC; adequacy; data residency | PDPA Chapter 5; GDPR art.44-50 |
| `jurisdiction_thailand` | `pdpa_applicability` | pdpa | PDPA B.E. 2562 / 2019 |
| `jurisdiction_thailand` | `consumer_protection_act` | consumer protection act; cpa; cooling-off; direct sales | CPA B.E. 2522 + DSDMA |
| `jurisdiction_thailand` | `computer_crime_act` | computer crime act; cca; log retention | CCA B.E. 2550 (90d log retention) |
| `jurisdiction_thailand` | `revenue_code_vat` | revenue code; vat; e-tax; tax invoice | Thai Revenue Code (VAT 7% + e-Tax invoice broker) |
| `payment_processing` | `psp_vendor_decision` | psp; payment provider; payment service provider; real payment | Omise / 2C2P / GBPrimePay / Stripe TH |
| `payment_processing` | `pci_dss_scope` | pci-dss; pci dss; pci scope; saq | SAQ A vs A-EP vs D |
| `payment_processing` | `settlement_fees` | settlement; merchant fee; transaction fee; processing fee | T+1 to T+7 typical TH |
| `payment_processing` | `webhook_signature` | webhook signature; webhook verification; callback signature | HMAC + idempotency-key |
| `payment_processing` | `chargeback_workflow` | chargeback; dispute | Visa/MC 120-day window typical |
| `audit_logging` | `log_retention_period` | log retention; audit retention; log preservation | CCA 90d [TH]; SOX 7y [US]; PCI 1y |
| `audit_logging` | `log_immutability` | tamper-evident; tamper evident; append-only; immutable log; log immutability | PCI-DSS req. 10.5 |
| `audit_logging` | `log_pii_redaction` | pii redaction; log redaction; sensitive field exclusion | PDPA / GDPR: logs are personal data when linked |
| `consumer_facing` | `privacy_policy_authoring` | privacy policy; privacy notice; privacy statement | PDPA s.23; GDPR art.13; CCPA notice-at-collection |
| `consumer_facing` | `terms_of_service` | terms of service; t&c; terms and conditions | Contract formation per local CPA |
| `consumer_facing` | `cookie_consent` | cookie consent; cookie banner; cookie notice | ePrivacy [EU]; PDPA s.19 if cookies link to identifiable user |
| `consumer_facing` | `merchant_identity_disclosure` | merchant identity; merchant disclosure; seller identification; business identification | Thai CPA + DSDMA |

##### Skip-justification protocol

When a required sub-topic is genuinely inapplicable, the BA marks it skipped:

```json
"processing_metadata": {
  "hidden_requirements_sweep": {
    "frames_skipped_reasons": {
      "4:pci_dss_scope": "Payment method is COD-only per epic scope; no card-data path. PCI-DSS not in scope for v1 launch.",
      "4:cookie_consent": "Initial release is native-mobile-only; no web cookies. Web surface phase 2."
    }
  }
}
```

Skip reasons must be ≥8 characters. The renderer accepts the skip and does not fire FM-17 for that sub-topic.

##### v1.3-pending triggers (catalogued but not yet enforced)

The following triggers and sub-topics are defined here for forward planning but the renderer's `_detect_frame4_triggers()` does NOT yet detect them. v1.3 candidate work:

- **`children`** — age-gate UX, parental consent flow, COPPA / Children's Code applicability. Activation: input mentions children / family / kids / school / age-restricted minors.
- **`health_medical`** — HIPAA scope, medical-data-broker registration, special-category-data lawful basis. Activation: input mentions health / medical / prescription / fitness / mental wellness / dietary tracking / vital signs.
- **`financial_lending`** — KYC obligations, AML scope, lender / payment-services licensing, credit-reporting disclosures. Activation: input mentions credit / loan / lending / deposit / BNPL / financing.
- **`telecom_sms_marketing`** — opt-in capture, opt-out mechanism, local marketing-consent statute (TCPA / GDPR-marketing / CASL / DSDMA). Activation: input mentions SMS / marketing campaign / push notification (marketing) / automated outreach.

These triggers' detection logic + sub-topic rules will land in a future v1.3.x cycle. The data-file lift itself shipped in **v1.3.0** (`references/frame-rule-data.json`); v1.3-pending triggers must be added there as new top-level `triggers` keys *and* simultaneously to `_detect_frame4_triggers()` plus this table.

---

### Frame 5 — Operational & organizational

**Question pattern:** Who runs it? Who answers? Who decides? Who reconciles? Who is on-call?

**Activation trigger:** **Always fires.** Every shipped system needs operators.

**Default severity floor:** **P2.** Promote to P1 only when input is silent on an operationally-critical role (e.g., the doc describes manual-refund but names no refund-approver).

**Cap:** 5 findings.

**Output pattern:** Most findings become absent-but-implied stakeholder rows (Step 5 enumeration duty). The frame ensures Step 5's enumeration is exhaustive across operational roles, not just compliance roles.

**Frame question library:**
- Customer-support channel (phone / email / chat / in-app)
- Customer-support hours + first-response/resolution SLA
- Escalation path (T1 → T2 → expert) with owners
- On-call rotation for production
- Incident-response runbook ownership
- Disaster recovery RPO / RTO numbers
- Inventory/data reconciliation cadence + owner
- Fulfillment/operations capacity per shift
- Account suspension / abuse handling policy + owner
- Coupon / promo fraud detection + owner
- Review/UGC moderation queue + SLA + owner
- Refund-approval workflow owner (if manual)
- Returns processing owner
- Reporting cadence + recipient (daily KPI, weekly business review)
- Merchant legal-entity identity (sole prop / corp / partnership — affects liability)

**Anti-pattern to avoid:** Naming a role abstractly ("the merchant team") when a specific named function is needed (e.g., "Customer Support Lead" or "Finance Reconciliation Owner").

---

### Frame 6 — Failure & edge cases

**Question pattern:** What if X breaks? What if X and Y fight? What if X is malicious?

**Activation trigger:** **Always fires.** Every system has failure modes.

**Default severity floor:** **P2** for normal failure; **P1** for failure with audit/compliance/financial consequences.

**Cap:** 7 findings (higher because failure modes typically interact and cover concurrent scenarios). Soft cap; the same v1.3.1+ `cap_exceptions` protocol applies when a future Frame-6 mandatory-coverage rule (backlog #4 — Frame 6 sub-topic library) drives findings past 7.

**Output pattern:** Mostly OQs; some assumed defaults where the input + industry norm provide one (e.g., "assume 409 CONFLICT on duplicate primary-key insert").

**Frame question library:**
- Race conditions on contested resources (last unit, last coupon redemption, last seat)
- Partial-success scenarios (some items in stock, some not; some recipients reached, some not)
- External-service downtime (payment provider, shipping API, email)
- Webhook delivery failure / duplication / out-of-order
- Customer-side cancellation/edit AFTER commit but BEFORE downstream effect
- Admin-side delete with active in-flight dependencies
- Adversarial use: bot/scraping, credential stuffing, account takeover
- Promotional abuse: multi-account redemption, guest-checkout coupon stack
- Customer dispute / "I never received it" workflows
- Damaged/wrong/late delivery workflows
- Cross-customer-data leakage scenarios (IDOR, query injection, log access)
- Audit-log compromise / admin-acting-as-customer detection
- Concurrent admin edits to same resource (optimistic locking policy)
- Time-of-check vs time-of-use windows (price-changed-between-cart-and-pay)
- Recovery from inconsistent state (payment authorized but downstream commit failed)
- Replay attacks; idempotency-key reuse with different payload

**Anti-pattern to avoid:** Listing failures that the existing AC scenarios already cover. The frame sweep is for failures NOT in the ACs.

---

### Frame 7 — Integration & dependencies

**Question pattern:** What external system makes this work? What contracts? What SLAs from vendors? Who owns the integration boundary?

**Activation trigger:** **Fires when input mentions:** any external party, vendor, third-party service, mock-to-real swap, "we'll integrate", "later", "phase 2". Skip for fully-internal closed-system tooling.

**Default severity floor:** **P2** for known-pending integrations; **P1** for required-for-launch integrations with no named vendor.

**Cap:** 5 findings.

**Output pattern:** OQs for each undetermined vendor; assumptions for industry-default integration shapes.

**Frame question library:**
- Real payment provider (vendor, contract status, fees, settlement, refund API, webhook signature)
- Real shipping/logistics provider (pickup, labels, tracking, COD support, lost-package process)
- Email delivery (deliverability, language template support, bounce handling, domain reputation)
- SMS gateway (regulatory opt-in, character-segment cost, regional aggregator)
- Tax-invoice integration (jurisdiction-mandated e-invoice broker)
- Accounting / ERP / inventory sync
- CRM / customer-data platform
- Analytics (and privacy implications of cross-border transfer)
- Search service (when DB filtering stops scaling)
- Image CDN
- DNS / domain ownership
- Application monitoring / observability stack
- Database backup destination + retention
- SSL/TLS certificate management
- Identity provider (SSO, social login) — if implied
- Push notification service
- Cloud region selection (and PDPA/GDPR cross-border implications)
- Reverse-proxy / WAF / DDoS protection layer

**Anti-pattern to avoid:** Treating "mock provider" as terminal. The mock-to-real swap is itself a hidden requirement — when, by whom, against which vendor.

---

### Frame 8 — Localization & culture

**Question pattern:** What does THIS specific market do differently from generic-Western-defaults?

**Activation trigger:** **Fires when input names a specific country, region, language, or currency.** Skip for generic / multi-market / not-yet-localized scope.

**Default severity floor:** **P2.** Promote to P1 when localization affects regulatory compliance (e.g., tax-invoice format).

**Cap:** 5 findings.

**Output pattern:** OQs for cultural-product-taxonomy and major holiday handling; assumptions for technical localization (time-zone, number format) with `default_revisit_trigger: "before customer-facing release"`.

**Frame question library:**
- Calendar system (Gregorian, Buddhist, Islamic, Hebrew, Hindu) — for receipts, invoices, expiry display
- Address format (region-specific structure: subdistrict/district/province/postal; ZIP+4; postcode-with-letter)
- Address-registry validation (canonical address list per jurisdiction)
- Phone number format and validation
- Name structure (given-then-family vs family-then-given; honorifics; multi-part family names)
- Number/currency formatting convention (digit grouping, decimal mark)
- Time-zone convention (named market's default)
- Daylight-saving-time applicability
- National-holiday calendar (affects fulfillment SLA promises)
- Cultural product taxonomy (Thai categories differ from US: "Mom & Baby" as single; alcohol restrictions)
- Religious / cultural restrictions on advertising or product mix
- Local payment methods (PromptPay, Pix, WeChat Pay, iDEAL, UPI)
- Local shipping conventions (COD prevalence varies; e.g., 30–40% of Thai e-commerce)
- Local content/review style (emoji-heavy, vernacular mixed-language, address-as-greeting)
- Mandatory disclosures (merchant identity per local consumer-protection law)
- Right-to-left language support if applicable

**Anti-pattern to avoid:** Assuming the named market is monolithic. A Thai-market system serving Bangkok + provinces may need different fulfillment SLAs by zone.

---

### Frame 9 — Lifecycle

**Question pattern:** What happens BEFORE this entity exists? What happens AFTER it ends? What state transitions are NOT in the obvious lifecycle?

**Activation trigger:** **Always fires.** Every domain entity has a lifecycle.

**Default severity floor:** **P2** for post-lifecycle handling; **P3** for pre-lifecycle (marketing/sourcing usually upstream of MVP).

**Cap:** 5 findings.

**Output pattern:** Mix of OQs (where input is genuinely silent) and assumptions (where industry default applies and PM acceptance is implied).

**Frame question library:**

For each major domain entity, ask:
- **Pre-creation:** How does the entity arrive? What upstream process? What identity/identifier convention?
- **Post-termination:** What survives? What's archived? What's deleted? Right-to-erasure interaction?
- **Suspended / dormant:** What state(s) exist between active and terminated? What can users do in dormant state?
- **Resurrection:** Can a terminated entity come back? Under what rules?
- **Audit immutability:** What about this lifecycle is regulator-required to be tamper-evident?
- **Compensating actions:** When the lifecycle goes wrong (refund after delivered, un-cancel a cancelled order), what's the compensation path?

Apply this to: customer account, product, order, transaction, coupon, review, address, session, subscription, refund, dispute, audit-log entry.

**Anti-pattern to avoid:** Mistaking "the input named 3 states" for a complete lifecycle. Post-terminal states (deleted-but-recoverable, hard-deleted, suspended-pending-review) are usually unstated.

---

### Frame 10 — Customer experience

**Question pattern:** What does the user FEEL? What is the user's emotional state at each moment? What word, what tone, what reassurance does the system provide?

**Activation trigger:** **Fires when system has any human-facing surface.** Skip for B2B-only / pure-API systems.

**Default severity floor:** **P2** for trust-bearing moments (payment, account creation, dispute); **P3** for routine UX.

**Cap:** 5 findings.

**Output pattern:** Mostly OQs to be answered by PM + Designer. Assumptions only when industry pattern is unambiguous.

**Frame question library:**
- First-visit trust signal (reviews on PDP, security badge, return policy visible)
- Account-creation reassurance (welcome message, verification UX)
- Empty states (cart, search results, order history, review list)
- Loading states (skeleton vs spinner vs progress)
- Error message tone (empathic vs terse; provides retry path)
- Confirmation reassurance ("thank you", expected next steps, expected timeline)
- Wait-state communication ("we're packing your order")
- Tracking handoff UX (embedded vs carrier-site redirect)
- Negative-event communication (out-of-stock, payment-failure, delivery-delay)
- Account-deletion confirmation gravity
- Mid-session language/currency switch
- Mobile-vs-desktop UX divergence
- Accessibility standard target (WCAG level)
- Browser/device support matrix
- Customer-facing copy voice & tone document (does one exist?)

**Anti-pattern to avoid:** Specifying UI implementation in a CX finding. The frame surfaces "the customer should feel reassured after payment"; the actual UI design happens in Stage 2.

---

## Anti-explosion guard

Without limits, this sweep produces 80–150 findings on a typical 700-line input — the PM rejects the brief as unworkable. Three guards:

1. **Per-frame cap.** Each frame emits at most its cap (5–10). The BA ranks findings by blast radius (launch-blocker > growth-trajectory > optimization). Excess findings go into `processing_metadata.hidden_requirements_sweep.deferred_findings_count` as a count only, not a list.

2. **Conditional activation.** Frames 3, 4, 7, 8, 10 fire conditionally per their activation triggers. A Thai e-commerce brief fires all 10. A pure internal admin tool fires Frames 1, 2, 5, 6, 9 only.

3. **Severity floors are floors, not ceilings.** A finding that's worse than the floor (e.g., a P1 finding within Frame 5 where the floor is P2) MUST be emitted at its true severity. A finding less severe than the floor is suppressed.

## Output shape (what lands in the JSON)

### In `open_questions[]`:

```json
{
  "id": "OQ-21",
  "severity": "P1",
  "question": "What's the expected order volume per day at launch? At 6 months? At peak season?",
  "why_matters": "Sizes order DB, web tier, fulfillment team. Hidden-frame Frame 1.",
  "suggested_resolver": "PM + Operations Lead",
  "related_story_ids": [],
  "provenance": "hidden_frame_sweep",
  "frame": 1
}
```

### In `assumptions_made[]`:

```json
{
  "assumption": "Default reservation TTL set to 5 minutes pending PM confirmation.",
  "why_made": "Industry standard for non-flash-sale e-commerce; aligns with checkout-form-fill duration. Frame 2 default + revisit pattern.",
  "related_story_ids": ["EPIC-INVENTORY-1", "EPIC-CHECKOUT-1"],
  "provenance": "hidden_frame_sweep",
  "frame": 2,
  "default_revisit_trigger": "post-launch week-2 telemetry on abandoned-checkout duration"
}
```

### In `processing_metadata.hidden_requirements_sweep`:

```json
{
  "frames_applied": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  "frames_skipped": [],
  "frames_skipped_reasons": {},
  "findings_per_frame": {
    "1": 4, "2": 5, "3": 3, "4": 6, "5": 4,
    "6": 5, "7": 4, "8": 3, "9": 3, "10": 3
  },
  "deferred_findings_count": 12,
  "total_findings": 40,
  "coverage_score": "complete"
}
```

`coverage_score` ∈ `{complete, partial, skipped}` reports whether all activated frames produced at least one finding. `partial` means at least one activated frame produced zero findings (worth flagging — either the input is unusually complete for that frame, or the sweep missed something).

## Cross-references

- `SKILL.md` Step 9.5 — invokes this reference.
- `SKILL.md` Step 5 — stakeholder enumeration duty; Frame 5 findings feed back here as absent-but-implied rows.
- `SKILL.md` FM-15 — sweep-coverage gate (defines `complete` / `partial` / `skipped` grading and the `frames_applied ∪ frames_skipped == {1..10}` invariant).
- `references/ambiguity-patterns.md` — Step 9, the prose-ambiguity sibling.
- `references/anti-patterns.md` — AP-1.3 (tier inference from content), AP-5.1 (Legal absence), AP-4.1 (PII force-fill) are independently active; frame sweep does not duplicate.
- `references/markdown-rendering-spec.md` §3.5 (cross-cutting files table) — emission of `09-hidden-requirements.md`.
- `schemas/output.json` — `OpenQuestion` and `Assumption` carry optional `provenance` and `frame`; `processing_metadata.hidden_requirements_sweep` is optional.

## Provenance enum reference (intentional asymmetry)

The schema uses two different enum values for non-sweep provenance:

| Collection | Non-sweep enum | Sweep enum | Why |
|---|---|---|---|
| `OpenQuestion` | `prose_ambiguity` | `hidden_frame_sweep` | A question that arose because the prose said something *fuzzy*. |
| `Assumption` | `prose_inference` | `hidden_frame_sweep` | A default that the BA *inferred* because the prose was silent on the value. |

This asymmetry is intentional: the BA's act of "noticing an ambiguity" (which produces an OQ) and "filling a silence with a reasonable default" (which produces an assumption) come from different operations on the prose. The sweep enum is shared because the same Step 9.5 produces both OQs and assumptions, just routed differently based on whether a defensible default exists.

---

## Worked example — ShopPilot MVP (the v3 naked input)

This appendix shows what Frames 1, 4, and 7 produce when applied to `ecommerce_mvp_business_only.v3.md` — a 730-line Thai-market e-commerce business-only spec. Not the full sweep — just three frames as a concrete reference for how findings get phrased and how `default_revisit_trigger` is named.

### Frame 1 — Scale & capacity (always-fires)

The input states the merchant is single-shop, the market is Thai, currency is THB, and the shipping-fee cutoff is 1,500 THB. It does NOT state how many customers, orders, or products.

**Findings emitted (3 of cap=5):**

- **OQ-101** [P1, frame 1] — "Expected order volume at launch (day 30 / day 90 / day 365) and at peak season (year-end mega-sale, Songkran, paydays)?"
  - Why matters: sizes order DB, web tier, fulfillment shift capacity. Free-shipping threshold of 1,500 THB is set without AOV reference, so 'free shipping' may be either rare or default depending on AOV.
  - Suggested resolver: PM + Operations Lead
  - Stories affected: every EPIC-CHECKOUT and EPIC-FULFILL story
- **OQ-102** [P1, frame 1] — "Expected catalog size at launch (number of SKUs)?"
  - Why matters: DB-LIKE search vs ElasticSearch decision pivots on order-of-magnitude. Seed data shows ~20 products, but the system must scale to merchant's full catalog.
  - Suggested resolver: PM + merchant onboarding
- **Assumption A-23** [frame 1] — "Default reservation TTL: 10 minutes pending PM confirmation."
  - Why: industry standard for non-flash-sale e-commerce; aligns with the average Thai-customer checkout-form-fill duration (~7–9 min including address entry).
  - `default_revisit_trigger`: "post-launch week-2 telemetry on abandoned-checkout duration distribution (p50, p95)"
  - Stories: EPIC-INVENTORY-1, EPIC-CHECKOUT-2

**Per-frame cap status:** 3 of 5 emitted; 2 deferred (peak concurrent users, notification volume) — counted in `deferred_findings_count`.

### Frame 4 — Regulatory & legal (fires: PII collected, Thai market named)

The input lists PII (email, name, phone, address) and mentions the Thai market. Names no regulator. Has no privacy policy, no T&C, no retention policy.

**Findings emitted (4 of cap=10):**

- **OQ-103** [P1, frame 4] — "PDPA (Thai Personal Data Protection Act 2019) applicability: confirm controller identity, lawful basis, retention schedule, DSAR workflow, breach-notification process (72h)."
  - Why matters: every collected PII field (email, phone, name, address) requires PDPA-compliant treatment. The brief currently cannot ship to production without Legal sign-off.
  - Escalates to `governance_gaps[]` as `legal_absent_on_regulatory_content` (P1, blocks TL handoff)
- **OQ-104** [P1, frame 4] — "Thai Revenue Code: VAT (7%) treatment + e-Tax invoice integration. Will the merchant be VAT-registered? If yes, e-Tax invoice broker integration required."
  - Why matters: pricing display, invoice format, accounting retention (5 years). Architecturally affects the order-line schema (tax line) and the accounting integration boundary.
  - Suggested resolver: Finance + Legal
- **OQ-105** [P1, frame 4] — "Consumer Protection Act + Direct Sales and Direct Marketing Act: mandatory disclosures — merchant identity, complaint channel, return/refund policy. Refund process is 'manual' but the policy text must be public."
  - Why matters: missing required disclosures expose the merchant to consumer-protection claims.
- **OQ-106** [P2, frame 4] — "Computer Crime Act: log retention (90-day minimum) and breach-reporting workflow. Audit log requirement in §5.9 satisfies the spirit but not the explicit retention duration."
  - Why matters: log retention period is unspecified; default to 90 days minimum but Legal should confirm.

**Per-frame cap status:** 4 of 10 emitted; 0 deferred. Coverage of Frame 4 is the dominant source of P1 OQs in this brief.

### Frame 7 — Integration & dependencies (fires: input mentions vendor swap)

The input says "mock payment provider — design for swap to real PSP later" and "mock shipping provider". Names no vendor for either.

**Findings emitted (3 of cap=5):**

- **OQ-107** [P1, frame 7] — "Real payment provider — which vendor? Thai market candidates: Omise, 2C2P, GBPrimePay, Stripe Thailand. Vendor choice drives fee structure (2-3%), webhook signature, settlement period (T+1 to T+7), refund API contract, and PCI scope."
  - Why matters: the Idempotency-Key contract in the mock implementation MUST match the real vendor's contract. Mock-vs-real divergence is a launch blocker.
  - `default_revisit_trigger`: "before MVP-to-production handoff; first real-PSP integration sprint"
- **OQ-108** [P2, frame 7] — "Real shipping/logistics provider — Thailand Post, Kerry Express, Flash, J&T, Ninjavan, Lalamove? Affects label format, pickup workflow, tracking webhook, COD support."
  - Why matters: shipping integration is deferred but the order schema must accommodate the chosen carrier's tracking-number format.
- **Assumption A-24** [frame 7] — "Default email delivery provider: AWS SES Singapore region (or SendGrid SG)."
  - Why: Singapore region keeps PII data within the same APAC zone (PDPA-friendly cross-border posture).
  - `default_revisit_trigger`: "Privacy/DPO review before customer-facing emails go live"
  - Stories: EPIC-OBSERVE-2 (notification)

**Per-frame cap status:** 3 of 5 emitted; 2 deferred (CDN choice, monitoring stack).

### Aggregate `hidden_requirements_sweep` for this input

```json
{
  "frames_applied": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  "frames_skipped": [],
  "frames_skipped_reasons": {},
  "findings_per_frame": {
    "1": 3, "2": 4, "3": 3, "4": 4, "5": 5,
    "6": 6, "7": 3, "8": 3, "9": 2, "10": 4
  },
  "deferred_findings_count": 9,
  "total_findings": 37,
  "coverage_score": "complete"
}
```

Notice: all 10 frames are applied (Thai market + PII + monetary + human-facing surface + external-vendor language all activate the conditional frames). `coverage_score: complete` because no frame produced zero findings and `frames_applied ∪ frames_skipped == {1..10}`. `deferred_findings_count` of 9 reflects the BA respecting the per-frame caps and counting the remainder.
