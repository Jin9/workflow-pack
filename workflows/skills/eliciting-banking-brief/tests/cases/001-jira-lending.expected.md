# Expected Output Skeleton — Test 001 (Jira / Lending)

> **NOT** a literal expected output — a skeleton listing the KEY FIELDS the skill output must contain.
> Assertions verify specific cells; skeleton is the orientation.

## Frontmatter (must contain)

| Field | Expected value |
|-------|----------------|
| `id` | EPIC-{auto}|
| `workload_tier` | T2 |
| `source_type` | jira |
| `idempotency_key` | test-001-... |
| `ba_confidence` | high or medium (high if all stakeholders identifiable, medium otherwise) |
| `status` | `blocked_partial_brief` if Legal-absence treated as P1; `draft` if downgraded to P2 |
| `output_type` | `brief` or `blocked_partial_brief` |
| `processing_metadata.ground_truth_stripped` | true |
| `processing_metadata.tipping_off_scan_clean` | true |

## Epic

- **Title**: includes "Self-Service Document Re-Upload" or equivalent verb-noun phrase
- **Problem statement**: 142 cases/week of stuck applications + 4h avg resolution time
- **Why now**: Q3 marketing campaign launch (June)
- **Success criteria**: ≥1 measurable metric (support load reduction OR resolution time)

## Stakeholders (must include — `status` field per absence)

| Role | Name | Status | Authority |
|------|------|--------|-----------|
| Owner / Reporter | Sarah Lim | active | PM |
| SME — Compliance | Priya Naidoo | active | directive on retention + audit |
| SME — Support | Mike Chen | active | volume + workflow input |
| SME — Engineering | Raj Patel | active | feasibility |
| SME — Legal | (unnamed) | **absent** | engagement_required_for: retention regulatory grounding |
| SME — Security | (unnamed) | **absent** | engagement_required_for: PII handling for sensitive docs |
| Affected — Mobile team | (unnamed) | **mentioned_only** | mobile parity deferred |

## Stories (5-6 expected)

1. **Story-1**: Self-service re-upload (happy path) — Must
2. **Story-2**: Audit trail for document replacements — Must (Priya explicit)
3. **Story-3**: Archive policy for replaced sensitive docs — Must (retention 7y)
4. **Story-4**: Re-upload retry limit + escalation flow — Should
5. **Story-5**: Mobile app parity — Could (deferred)
6. **Story-6 (optional)**: Failed verification escalation workflow — Should

Each story must contain:
- Job Story or Classic User Story format
- ≥3 Gherkin scenarios (happy / error / banking-grade)
- Banking-grade 7-row table (force-filled)
- MoSCoW priority
- DoR checklist

## Governance Gaps (≥1 P1)

- `legal_absent_on_regulatory_content` — P1
  - Reason: Priya cites "data retention policy" + 7-year retention regulatory hook; Legal not engaged
  - Resolver: Loop in Legal before TL handoff

## Open Questions (5-8 P2)

- Version-vs-replace policy (Sarah's unanswered question)
- Mobile app scope (web first / mobile deferred — formally?)
- Re-upload limit N=3 (Anonymous comment → downgrade requires re-confirmation)
- Verification failure escalation path
- Abandoned application document state
- Bank statement "last 3 months" rule — hard or domain-dependent?

## Assumptions Made (4-6 P3)

- File size stays at 10MB
- N=3 attempts (from anonymous comment, treated as assumption)
- Retention 7 years (Priya confirmed)
- Compliance officer Priya is the approver
- Q3 deadline = hard
- PII fields: NRIC + bank statement classified as sensitive

## PII Inventory (must be present)

| Field | Treatment |
|-------|-----------|
| NRIC | mask + audit + retention 7y |
| Bank statement | encrypt-at-rest + audit + retention 7y |
| Customer name | standard PII handling |

## Assertions to Run

- `tests/assertions/invest-compliance.md`
- `tests/assertions/gherkin-quality.md`
- `tests/assertions/banking-grade-fields.md`
