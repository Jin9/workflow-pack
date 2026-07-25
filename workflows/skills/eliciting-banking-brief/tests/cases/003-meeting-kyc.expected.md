# Expected Output Skeleton — Test 003 (Meeting / KYC EDD)

## Frontmatter

| Field | Expected value |
|-------|----------------|
| `workload_tier` | T2 |
| `tier_signals.escalation_candidate` | T1 |
| `tier_signals.reason` | PEP + AML + MAS regulator + dual approval + adverse media |
| `source_type` | meeting-notes |
| `status` | `blocked_partial_brief` |
| `output_type` | `multi_epic_brief` OR `blocked_partial_brief` with multi-epic warning |
| `ba_confidence` | medium (note-taker mediation downgrade) |
| `processing_metadata.note_taker_paraphrase_detected` | true |

## Epics (5-6)

- Epic A: Single-intake document portal + Acuant integration
- Epic B: Upfront screening automation (PEP / sanctions / adverse media)
- Epic C: Risk engine schema upgrade + structured input
- Epic D: Tiered approval routing
- Epic E: Applicant status page + communications
- Epic F: Biometric verification add-on (gated by security review)
- (Separate workstream): Legacy data migration

If single-epic emitted, must flag `governance_gap: multi_epic_not_decomposed` P1.

## Stakeholders

| Role | Name | Status |
|------|------|--------|
| Chair | David Lim | active |
| Compliance | Priya Naidoo | active (directive on retention + tipping-off) |
| Risk Analytics | Jamie Foster | active |
| Engineering Manager | Karim El-Sayed | active |
| Vendor liaison | Hua Liu | active |
| CX Designer | Ben Stewart | active |
| Note-taker / PM | Aisha Rahman | active (mediator) |
| Legal — Sundar K. | **absent (apologies)** | engagement_required_for: regulator citation, tipping-off, retention |
| Customer Support | (unnamed) | **absent** | engagement_required_for: applicant communication |
| Migration owner | (unnamed) | **absent — TBD** | engagement_required_for: legacy data migration |
| Data team | (unnamed) | **absent** | engagement_required_for: confirm event field availability |
| DPO / Privacy | (unnamed) | **absent** | engagement_required_for: PII retention + cross-border |
| Senior Management Approval | (unnamed) | **absent** | engagement_required_for: high-risk dual approval |

## Governance Gaps (≥3 P1)

- `legal_absent_on_regulatory_content` — P1
- `regulator_citation_unresolved` — P1 (MAS-AML-1A revision)
- `pii_inventory_missing_dpo_review` — P1 (cross-border applicants + abandoned retention)
- If single-epic emitted: `multi_epic_not_decomposed` — P1

## Open Questions (P2 — 8-10)

- MAS-AML-1A revision citation pending (David action item, no date)
- Risk engine score threshold for "high-risk" — 0.75 proposed but engine not calibrated (2-cycle wait)
- Adverse media vendor name — Karim flagged "vendor (?)"
- Acuant biometric security review — spike timing
- Partial-PII retention for abandoned applications — 30 days proposed, needs Legal
- NPS target 6 from 3.8 — David said "secondary", didn't formally accept
- In-flight EDD migration ownership — separate workstream, no owner
- Mobile scope — Q4 deferred, no commitment
- Acuant pricing acceptability — proposal pending
- Cross-border applicants policy — skipped, out-of-scope for this phase

## Assumptions (P3 — 5-8)

- EOW = end of this week
- Acuant pricing acceptable
- SG data residency satisfies regulator
- Aisha is BA brief owner
- Tiered routing thresholds — "high" defined as 0.75, low/medium implicit
- "By next session" = 2026-05-14
- Note-taker paraphrase faithful (confidence downgrade)
- Sundar K. (Legal) will be engaged next session

## Critical Assertions

- Output emits ≥ 5 epics (or 1 epic with `multi_epic_not_decomposed` P1)
- Each epic has its own stories (≥3 each)
- Banking-grade 7-row table per story across all epics
- Tipping-off scan: tipping-off prohibition explicit (Priya) — applicant communication MUST use safe language
- Compensating actions: vendor SLA breach + Acuant data residency
- Tier escalation: T1 candidacy flagged with reason
