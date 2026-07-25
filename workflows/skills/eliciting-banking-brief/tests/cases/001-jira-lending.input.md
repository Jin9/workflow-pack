# Test Case 001 — Jira (Lending — Document Re-Upload)

> **Manifest**: Test fixture #001 for `ba-elicit-from-raw`
> **Source type**: jira
> **Domain**: lending / loan origination
> **Input file**: `../../../../inputs/raw-request-001.md`
> **Use in training**: YES (Phase A used this as training example #1)

## Synthesized Skill Input

```json
{
  "raw_content": "<full content of inputs/raw-request-001.md, ground-truth-stripped>",
  "source_type": "jira",
  "idempotency_key": "test-001-7a8b-c2d3-4e5f-6a7b8c9d0e1f",
  "tier_hint": null,
  "audit_mode": "enhanced",
  "ground_truth_strip_mode": "auto"
}
```

## Coverage Goals

- **Source-type detection**: jira (bracketed key `[LOAN-2847]`, Project/Type/Priority headers, ## Comments section)
- **Ground-truth strip**: detect + strip "## Intentional Issues for R6 to Catch" block
- **Multi-story split**: 5-6 stories within single epic (re-upload, audit, archive, retry-limit, mobile-deferred)
- **Stakeholder authority**: Sarah Lim (PM owner), Priya Naidoo (Compliance — directive language), Mike Chen (Support Lead), Raj Patel (Eng), Anonymous (likely Raj — DOWNGRADE)
- **Legal-absence detection**: Compliance is engaged (Priya); Legal is NOT — flag P1 governance gap
- **Banking-grade signals**: PII (NRIC, bank statement), audit trail (Priya explicit), data retention (7 years), idempotency (re-upload same doc), reversibility (revert to old doc?)
- **Ambiguity surfacing**: version-vs-replace (Sarah's question never answered), retry limit N=3 (anonymous), abandoned-application handling

## Expected Output Skeleton

See companion `001-jira-lending.expected.md`.

## Critical Assertions

- INVEST: all 5-6 stories pass (each may need split-required flag for "M" priority items)
- Gherkin: each story has ≥3 scenarios (happy, error, banking-grade idempotency-replay)
- Banking-grade: all 7 fields per story force-filled (35-42 rows total)
- Tipping-off: scan clean (no customer-facing-rejection language in scope — staff-facing internal flow)
- Output type: `brief` IF Legal-absent treated as P2; `blocked_partial_brief` IF treated as P1 (canonical behavior)
- Governance gaps: ≥ 1 (Legal absent on regulatory content — retention 7 years cites compliance, not Legal)
- Open questions: 5-8 P2 (version/replace, mobile scope, retry-limit, escalation path, abandoned-state)
- Tier: T2 (no sanctions / AML — internal applicant flow with PII)
