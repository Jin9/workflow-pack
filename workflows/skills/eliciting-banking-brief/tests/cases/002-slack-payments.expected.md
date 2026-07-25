# Expected Output Skeleton — Test 002 (Slack / Payments)

## Frontmatter (must contain)

| Field | Expected value |
|-------|----------------|
| `workload_tier` | T2 (with tier_signals indicating T1-escalation-candidacy) |
| `source_type` | slack |
| `status` | `blocked_partial_brief` |
| `output_type` | `blocked_partial_brief` |
| `processing_metadata.tipping_off_scan_clean` | **false** |

## Stakeholders (`status` field)

| Role | Name | Status |
|------|------|--------|
| Owner / Ops Manager | Jenny Wong | active |
| SME — Compliance | Mei Park | active (directive on tipping-off) |
| SME — Engineering | Tom Becker | active |
| SME — Frontend | Raj Sharma | active |
| Sponsor — Product | Sarah Khoo | active |
| SME — Legal | (unnamed) | **absent** | engagement_required_for: customer-facing language tipping-off review |
| SME — Customer Support | (unnamed) | **mentioned_only** (agent script discussed, no rep) |
| SME — Mobile PM | (unnamed) | **mentioned_only** (mobile deferred but no formal scope) |
| SME — Data / Analytics | (unnamed) | **absent** | engagement_required_for: inbound-call-volume metric tracking |

## Stories (5-6)

1. Customer-facing "additional review" status with ETA bucket (web) — Must
2. Internal back-office granular state model (compliance-hold / ops-review / approved / rejected) — Must
3. Agent UI showing real reason (auth/authz separated) — Must
4. Customer state-change notification (email primary, in-app secondary, push optional) — Should
5. Rejection messaging (non-tipping, Legal-reviewed) — Must
6. Mobile parity — Could (deferred Q4)

## Governance Gaps (≥2 P1)

- `legal_absent_on_regulatory_content` — P1
- `tipping_off_risk` — P1 (customer-facing language touches sanctions context per Mei)

## Open Questions (P2 — 6-8)

- ETA bucket conflation: compliance-hold 24-72h + ops-review same-day — same "up to 5 business days" — acceptable?
- Notification policy on rejection (email only? in-app?)
- Legal review timeline (wildcard mentioned, no date)
- Agent UI in 3-week scope or slipping a sprint?
- Tipping-off generic language: applies to sanctions only or also PEP / adverse media?
- Mobile scope: deferred or in-epic?

## Assumptions (P3 — 4-6)

- "Additional review" is the customer-facing label (👍 emoji accepted)
- 24-72h compliance / same-day ops SLAs (verbal numbers)
- Inbound call volume is the primary metric
- Sponsor = Sarah Khoo
- Customer state-change notification policy = approved (email + in-app), rejected (email-only generic)

## PII Inventory

| Field | Treatment |
|-------|-----------|
| Customer name | standard |
| Transaction details (originator bank, amount) | encrypt-in-transit + audit |
| Account identifiers | mask in customer-facing UI |

## Critical Assertions

- All stories pass `invest-compliance.md`
- Story 5 (Rejection messaging) has tipping-off-safe Gherkin scenario per `gherkin-templates.md` §6.3 (`non-tipping-vocabulary.md` substitutions applied)
- Idempotency-replay scenarios on Story 1 (state-change notification) and Story 4 (notification dispatch)
- Banking-grade 7-row table per story (force-fill)
