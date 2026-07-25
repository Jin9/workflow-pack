# Compliance Test Patterns

> Reference for `planning-banking-tests` v1.0.0. Loaded by **SKILL.md Step 7** on every run. Extensible per project.

## 1. Purpose

This document supplies per-regulator test templates that the skill emits into `compliance_tests[]` of the canonical `output.json`. The skill does not invent regulatory thresholds; it only renders test cases for regulator codes that the BA brief explicitly cites in `regulatory_dependencies[]`. Templates here are normative for the four Thai regulators present in the holdout brief (`PDPA-TH-2019`, `TRC-VAT-7PCT`, `CCA-TH-LOG-90D`, `CPA-TH-DISCLOSURE`) and indicative for any regulator added later.

The renderer guarantees Invariant 3 (regulator codes ↔ `compliance_tests`): every code in BA `regulatory_dependencies[].regulator.code` must produce at least one matching entry in `compliance_tests[].regulator_code`, or a documented suppression in `processing_metadata.facet_firing_log`.

## 2. How to use

For each `regulatory_dependencies[i]` in the BA brief:

1. Read `regulatory_dependencies[i].regulator.code` (e.g. `PDPA-TH-2019`).
2. Look up the matching template section below by exact code match.
3. Read `regulatory_dependencies[i].citation_status`:
   - `confirmed` — emit the full test set with concrete thresholds taken from the BA `citation` field.
   - `pending` — emit test cases with `compliance_scope_blocked: true` and populate `blocking_governance_gaps[]` with every governance-gap id that names this regulator (see §3).
4. Generate one `compliance_tests[]` entry per template row using the id pattern declared in that template.
5. Set `compliance_tests[].regulator_code` to the exact code from the BA brief (preserve casing).
6. Link `compliance_tests[].story_ids[]` to every story whose `acceptance_criteria` or `banking_grade_applies` row implicates the regulator's scope.
7. If the BA brief lists a regulator code that is **not** in §4 below, fall back to §5 "Extension pattern" and emit a `coverage_gap` of severity P1 with `gap_type: regulator_template_missing`.

## 3. `citation_status` handling

When `citation_status == "pending"` (the holdout's state — all four regulators are `pending` per `06-regulatory-dependencies.md`):

- Every emitted test case carries `compliance_scope_blocked: true`.
- Every emitted test case populates `blocking_governance_gaps[]` with the ids of governance gaps that name the regulator. For the holdout, these are `legal_absent_on_regulatory`, `regulatory_citation_unresolved`, and (where retention is part of the test) `retention_policy_unstated`.
- The test's `expected_assertions[]` MUST NOT contain numeric thresholds invented by the skill. Targets that depend on the unresolved citation are rendered as `"TBD pending citation confirmation by {promisor} (due {due_date})"`, copied verbatim from the BA row.
- The test's `status` is `draft-blocked`, not `ready`.
- `qa_readiness_checklist[]` gains a P1 item: "Citation for {regulator_code} confirmed by {promisor} before {due_date}".

This mirrors AP-Q9 (no invented thresholds) and AP-Q11 (no tipping-off copy in compliance tests).

## 4. Per-regulator templates

### 4.1 PDPA-TH-2019 — Thai Personal Data Protection Act B.E. 2562 (2019)

**Regulator**: Personal Data Protection Committee (PDPC).
**Scope on holdout**: All ten PII fields in `05-pii-inventory.md` (direct: `email`, `password`, `phone`, `name`, `shipping_address`; indirect: `customer_id`, `order_number`, `tracking_number`, `review_text`; regulatory: `session_token`).
**ID pattern**: `COMP-PDPA-{seq:03d}` (e.g. `COMP-PDPA-001`).

| Template | Test type | Scope | Evidence required |
|---|---|---|---|
| DSAR-ACCESS | Data Subject Access Request — access | Verify customer can request and receive a copy of all PII held about them within the statutory response window (target: 30 calendar days; render as TBD if `citation_status == pending`). | Request submission audit-event; access-payload artifact; timing log. |
| DSAR-RECTIFY | DSAR — rectification | Verify customer-initiated correction of `name`, `phone`, `shipping_address` propagates to all downstream stores and snapshots (excluding immutable order snapshots). | Pre/post audit-event pair; downstream-store diff. |
| DSAR-DELETE | DSAR — deletion / erasure | Verify deletion request honored within window; verify retention-locked records (order snapshots under Thai Revenue Code) remain but customer-linkable PII is severed per lawful-basis precedence. | Deletion audit-event; tombstone record; severance proof. |
| RETENTION-AUTO | Retention-policy enforcement | Verify auto-delete or auto-anonymize fires at retention horizon for each `pii_inventory[].retention` value (TBD per field on holdout — see `retention_policy_unstated` gap). | Time-anchored fixture (T0, T+retention); deletion audit-event. |
| BREACH-72H | Breach-notification | Verify breach-detection alerting path reaches DPO within the window required to file a 72-hour PDPC notification. | Incident drill log; alerting trace; DPO acknowledgement record. |
| CONSENT-GRANULAR | Consent flow | Verify consent is captured per processing purpose (marketing, analytics, fulfilment) and not bundled; verify withdrawal stops the corresponding processing. | Consent ledger entry; withdrawal-to-processing-halt timing. |
| XBORDER-LAWFUL | Cross-border-transfer | Verify lawful basis is recorded for every cross-border data flow named in the BA (none enumerated on holdout; emit as `coverage_gap` if BA `processing_metadata.external_dependencies` shows non-TH residency). | Lawful-basis record per flow; transfer audit-event. |
| LAWFUL-BASIS-RECORD | Lawful-basis record per processing activity | Verify every processing activity in the BA has a recorded lawful basis (consent / contract / legitimate-interest / legal-obligation / vital-interest / public-task). | Record-of-Processing-Activities entry per activity. |

All eight templates emit `compliance_scope_blocked: true` on the holdout because PDPA citation is `pending`.

### 4.2 TRC-VAT-7PCT — Thai Revenue Code, VAT 7%

**Regulator**: Thai Revenue Department.
**Scope on holdout**: Order receipts, e-Tax invoice issuance, accounting retention on order snapshots (`shipping_address` 5-year retention per `05-pii-inventory.md`).
**ID pattern**: `COMP-TRC-{seq:03d}`.

| Template | Test type | Scope | Evidence required |
|---|---|---|---|
| ETAX-FORMAT | e-Tax invoice mandatory-field compliance | Verify generated e-Tax invoice contains every mandatory field per Notification of the Director-General of the Revenue Department No. 247 (seller TIN, buyer TIN where B2B, invoice number, date, item description, unit price, VAT amount, total). | Sample invoice artifact; field-by-field assertion. |
| ACCT-RETENTION-5Y | 5-year accounting record retention | Verify order/invoice records persist for the statutory accounting period and are not purged by other retention policies (PDPA deletion must respect this hold). | Time-anchored fixture (T+5y); record-still-readable proof. |
| VAT-LINE-DISPLAY | VAT line-item display | Verify receipt and order-confirmation surfaces show the VAT amount as a discrete line item, not embedded in the unit price. | UI snapshot or generated receipt payload. |
| B2B-TAXID | Customer tax-ID handling for B2B | Verify the order flow accepts a customer tax ID where B2B is in scope; verify it is rendered on the invoice; verify it is not exposed on B2C surfaces. | Conditional-render test per customer type. |

`citation_status: pending` on the holdout — all four emit `compliance_scope_blocked: true` and link `regulatory_citation_unresolved`.

### 4.3 CCA-TH-LOG-90D — Computer Crime Act, log retention 90 days

**Regulator**: Ministry of Digital Economy and Society (MDES).
**Scope on holdout**: Audit-log retention (BA section 5.9), access events on PII reads, lawful-access response procedure.
**ID pattern**: `COMP-CCA-{seq:03d}`.

| Template | Test type | Scope | Evidence required |
|---|---|---|---|
| LOG-RETAIN-90D | 90-day log retention | Verify access logs are retained for the statutory minimum (target: 90 days; render TBD if pending). | Time-anchored fixture (T0, T+90d); log-readable proof; deletion-not-before-horizon proof. |
| LOG-INTEGRITY | Log integrity — tamper-evident | Verify logs are protected by tamper-evident hashing (chained-hash or signed-batch) or written to WORM storage; verify alteration is detected. | Hash-chain verification artifact; tamper-detection drill output. |
| ACCESS-EVENT-LOG | Access-event logging | Verify every admin or system read of customer PII (per `05-pii-inventory.md` Access Audit column) emits an audit-log record with actor, target, timestamp, purpose. | Audit-log entry per simulated admin read. |
| LAWFUL-ACCESS | Lawful access procedure | Verify the documented procedure for responding to a lawful-access request (warrant, MDES order) produces a complete, signed log export within the documented SLA. | Procedure-execution drill; export artifact; signed manifest. |

`citation_status: pending` — all four emit `compliance_scope_blocked: true` and link `legal_absent_on_regulatory` plus `retention_policy_unstated`.

### 4.4 CPA-TH-DISCLOSURE — Consumer Protection Act

**Regulator**: Office of the Consumer Protection Board (OCPB).
**Scope on holdout**: Merchant identity disclosure, return policy visibility, price transparency, refund timeline (BA section 6.5 manual refund).
**ID pattern**: `COMP-CPA-{seq:03d}`.

| Template | Test type | Scope | Evidence required |
|---|---|---|---|
| MERCHANT-IDENTITY | Merchant identity disclosure | Verify merchant legal name, registered address, and contact channel are surfaced on every customer-facing transactional page (PDP, cart, checkout, receipt). | UI snapshot per surface. |
| RETURN-POLICY-VIS | Return policy visibility | Verify return / refund policy is reachable from PDP, cart, and the order-confirmation receipt; verify it is not buried behind login. | Crawl-and-locate test per surface. |
| PRICE-TRANSPARENCY | Price transparency — final price | Verify final price displayed before payment authorization equals item subtotal + VAT (7%) + shipping + any surcharge, with each component shown to the customer. | Cart-to-checkout delta assertion. |
| REFUND-TIMELINE | Refund timeline disclosure | Verify the refund SLA is disclosed at the point of cancellation/return and matches the named Finance owner's documented timeline (out-of-band manual refund per BA 6.5 — depends on `compensating_action_missing` P2 gap). | Disclosure copy snapshot; SLA-document cross-reference. |

`citation_status: pending` — all four emit `compliance_scope_blocked: true`.

## 5. Extension pattern

To add a new regulator (example placeholder for `GDPR-EU`):

1. Append a §4.N subsection with the same shape: regulator name, scope statement, ID pattern, template table.
2. The ID pattern MUST be unique across templates and MUST match the canonical regex `^COMP-[A-Z0-9]+-[0-9]{3}$`.
3. Each row must declare test type, scope, and evidence required.
4. The new template is automatically picked up by Step 7 of SKILL.md once the regulator code appears in a BA brief.

**Placeholder — GDPR-EU** (illustrative, not for use on the Thai holdout):

| Template | Test type | Scope | Evidence required |
|---|---|---|---|
| GDPR-DSAR-ACCESS | Article 15 right of access | Verify access response within 30 days. | Request log; export artifact. |
| GDPR-DSAR-ERASURE | Article 17 right to erasure | Verify deletion within 30 days, accounting for retention overrides. | Deletion audit; tombstone. |
| GDPR-PORTABILITY | Article 20 data portability | Verify machine-readable export. | Export artifact in structured format. |
| GDPR-DPO-72H | Article 33 breach notification (72 hours to supervisory authority) | Verify alerting path and notification artifact. | Incident drill; notification record. |

## 6. Anti-patterns

- **AP-Q11 — tipping-off in test plan copy.** Test plans MUST NOT contain copy that informs a customer their account is under AML, sanctions, or fraud review. Forbidden example: "Test that the customer is told their account is flagged for AML." This is a regulatory violation in itself. Permitted shape: "Test that the customer-facing response on a flagged account matches the documented neutral-rejection copy and that the flag, reviewer identity, and reason are written only to the internal audit trail."
- **AP-Q9 — invented thresholds.** Numeric thresholds (retention days, response windows, percentages) MUST come from the BA citation. When citation is `pending`, the threshold renders as `TBD pending citation` — never a guessed default.
- **AP-Q7 — real PII in compliance fixtures.** Compliance tests use only synthetic data per `test-data-design.md`.
- **AP-Q12 — silent regulator drop.** A regulator named in BA `regulatory_dependencies[]` MUST surface either as compliance tests or as a `coverage_gap`. Silent omission is forbidden.

## 7. References

- `tier-aware-test-policy.md` — depth of compliance coverage per tier.
- `test-data-design.md` — synthetic data rules for PII used in compliance tests.
- `anti-patterns.md` — full AP-Q1..AP-Q12 catalogue.
- Holdout source: `qa-holdout/e-commerce-v5/output-e5f8b9c2/06-regulatory-dependencies.md` and `05-pii-inventory.md`.
