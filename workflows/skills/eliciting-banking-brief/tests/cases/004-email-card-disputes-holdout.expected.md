# Expected Output Skeleton — Test 004 (Email / Card Disputes — HOLD-OUT)

> **Note**: The full actual skill output for this case is preserved at
> `../../audit/phases/phase-e2-test-output.md` (E2 self-test).
> E3 scored that output 44.5/50; E4 closed the gaps; F1 re-scored 50/50.

## Frontmatter

| Field | Expected value |
|-------|----------------|
| `workload_tier` | T2 |
| `source_type` | email |
| `status` | `blocked_partial_brief` |
| `output_type` | `blocked_partial_brief` |
| `processing_metadata.ground_truth_stripped` | true |
| `processing_metadata.stakeholder_availability[0].status` | handing_off |
| `processing_metadata.stakeholder_availability[0].return_date` | 2026-08-15 |

## Stakeholders

| Role | Name | Status |
|------|------|--------|
| Owner — Card Ops | Diana Costa | **handing_off** (parental leave 2026-06-01 to 2026-08-15) |
| Owner — Cover | Felix Tan | active (from 2026-06-01) |
| Sponsor (initial) | Marcus Vega | active |
| VP Product | Yvonne Brooks | active |
| Tech Lead | Tomas Werner | active |
| SME — Card Systems | Jamal (mentioned) | **mentioned_only** |
| SME — Legal | (unnamed) | **absent** | engagement_required_for: VCR ruleset + non-tipping for declined disputes |
| SME — DPO / Privacy | (unnamed) | **absent** | engagement_required_for: PII inventory for transaction history + statements |
| SME — Treasury | (unnamed) | **absent** | engagement_required_for: chargeback reversal accounting |
| SME — UX | (unnamed) | **absent** | engagement_required_for: Yvonne's required UX research sprint |
| SME — Card admin team | (unnamed) | **mentioned_only** | layering vs replace coordination |
| External — VISA rep | n/a | **absent** | systemic portal-timeout escalation channel |
| External — Mastercard rep | n/a | **absent** | session-keepalive long-term plan |

## Phase 1 Epic + 5 Stories

- Epic: Card Dispute Tooling — Phase 1 (VISA VCR alignment + analyst leverage)

### Phase 1 Stories (Must / Should mix)

1. **Map and ingest VISA VCR new reason codes** — Must (regulatory hard deadline 2026-07)
2. **Per-case SLA timer with countdown / breach** — Must
3. **Unified case view (layered)** — Should (UX-dependent)
4. **Mastercard portal session keepalive (interim)** — Should
5. **VISA network API integration expansion** — Must (where available)

### Phase 2 (out_deferred[])

- Customer communication templates
- Chargeback packet auto-assembly
- Win/loss analytics

## Governance Gaps (≥3 P1)

- `legal_absent_on_regulatory_content` — VISA VCR + card-fraud tipping-off — P1
- `regulator_citation_unresolved` — VCR mapping status per Felix — P1
- `pii_inventory_missing_dpo_review` — transaction history, statements — P1
- (E2 added) `retention_policy_unstated` — P1

## Open Questions (12 P2 per E2)

- SLA event field source (Tomas: needs data team)
- UX research sprint scope (Yvonne)
- Dollar estimate of un-submitted chargebacks ($X placeholder pending Felix)
- Diana → Felix handoff formalization
- "Half the time portal session times out" — quantifier vagueness
- Mastercard long-term plan (keepalive is "interim")
- VCR mapping status
- Cutover policy for in-flight cases
- MAS PSN-01 overlap?
- PDPA composition with VCR
- Mastercard rules separate from VISA
- VISA API-supported codes vs portal-only

## Assumptions (≥2 P3, ideally 6-8)

- Q3 2026 deadline driven by VISA VCR 2026-07
- Phase 1 owner = Felix post-Diana-leave
- Phase 2 deferred Q4 2026 / Q1 2027
- Layering (not replacing) card admin UI
- Email-only customer comms in Phase 1
- Win rate target = ≥ industry benchmark (71%)
- Attached deck content reflects email summary
- Analyst attrition is a real driver

## PII Inventory

| Field | Treatment |
|-------|-----------|
| Customer name | standard |
| Transaction history | encrypt-in-transit + audit + retention-aligned |
| Customer statements | encrypt-at-rest + DPO review |
| Card number (PAN) | tokenized — never in case body |
| Merchant info | standard |

## Critical Assertions

- 5 Phase 1 stories (matches ground truth)
- Story 5 (VISA API submission) has compensating-action: network arbitration
- Story 5 has idempotency-replay scenario on network submission
- All stories: 7-row banking-grade table force-filled
- Diana handoff metadata captured
- Ground-truth strip success (no R6 annotation echo)
- Tipping-off scan: Phase 1 = clean (internal only); Phase 2 customer comms flagged for Legal
