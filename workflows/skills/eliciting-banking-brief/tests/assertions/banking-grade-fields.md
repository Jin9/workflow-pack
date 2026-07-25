# Banking-Grade Fields Assertions

> Per-rule checklist enforcing C18 force-fill contract: 7 banking-grade rows × non-null status × non-empty justification × cross-checks to governance_gaps and tier inference.

## Purpose

This file enforces the **forcing function** that is the skill's central architectural value (C18 + FM-11 + B5 §6). Schema rejects empty `status` or `justification < 10 chars`. This file's rules catch what schema cannot: applicable-without-treatment, tipping-off-without-AC, Legal-absent-without-gap, tier-escalation-not-flagged.

## Severity Semantics

- **must-pass** = test case fails on violation.
- **conditional must-pass** = predicate-gated; only triggers when condition holds.
- **must-pass state-change** = required only for state-change / notification stories.

## Rule Table

| # | Rule | Severity | Source |
|---|---|---|---|
| B-1 | **All 7 rows present**: `banking_grade_concerns` has exactly the keys `{pii_fields, audit_events, idempotency, reversibility, authn_authz, regulatory, tipping_off}`. | must-pass | C18; FM-11 |
| B-2 | **Status enum**: every row's `status ∈ {applies, not_applicable, unknown_p2}`. | must-pass | FM-11 |
| B-3 | **Justification ≥ 10 chars (AP-4.1)**: every row has `justification` length ≥ 10. `not_applicable` rows must cite workflow class reason. | must-pass | AP-4.1 |
| B-4 | **Applicable → treatment**: `status == "applies"` ⟹ at least one of `fields_or_events` (non-empty array) OR `treatment` (non-empty string). | must-pass | C18 |
| B-5 | **Tier inference**: `epic.inferred_tier ∈ {T1, T2, T3}` (or per-`epics[]` entry in multi-epic) AND `tier_signals[]` non-empty. | must-pass | C19 |
| B-6 | **Compensating action**: `reversibility.status == "applies"` AND `reversibility.treatment` contains substring `irreversible` ⟹ `reversibility.compensating_action` non-empty (length ≥ 10). | must-pass state-change | C21; AP-4.3 |
| B-7 | **Tipping-off cross-check**: any story with `banking_grade_concerns.tipping_off.status == "applies"` ⟹ (a) tipping-off AC present per `gherkin-quality.md` G-7 AND (b) `governance_gaps[]` contains `tipping_off_violation` OR `processing_metadata.tipping_off_scan_clean: true`. | must-pass | C20, FM-06 |
| B-8 | **Legal-absent + regulatory**: `epic.legal_status ≠ "present"` AND any story has `banking_grade_concerns.{regulatory \| tipping_off \| pii_fields}.status == "applies"` ⟹ `governance_gaps[]` contains entry `{type: "legal_absent_on_regulatory", blocks_tl_handoff: true}`. | must-pass | C14, FM-05, AP-5.1 |
| B-9 | **PII force-fill**: any story with `banking_grade_concerns.pii_fields.status == "applies"` ⟹ `fields_or_events` non-empty AND `treatment` non-empty AND `glossary[]` has ≥1 entry with `pii_sensitivity ∈ {direct, indirect, regulatory, financial}`. | must-pass | AP-4.1; C7 |
| B-10 | **Tier escalation (AP-1.3)**: `frontmatter.workload_tier` matches `tier_hint` from input AND `epic.inferred_tier` is rank-strictly higher than `frontmatter.workload_tier` ⟹ `processing_metadata.tier_decisions[]` contains entry with `inferred_higher_than_manual: true` AND `frontmatter.status ≠ "ready-for-tl"`. | must-pass | AP-1.3 |

## Per-Rule Pseudo-Check

### B-1 All 7 rows
For each `story.banking_grade_concerns`:
- Get `Set(keys)`.
- Assert equals `{pii_fields, audit_events, idempotency, reversibility, authn_authz, regulatory, tipping_off}`.
- Missing key → B-1 fails with `{story_id, missing_keys}`.

### B-2 Status enum
For each row in `banking_grade_concerns`:
- Assert `row.status ∈ {applies, not_applicable, unknown_p2}`.
- Otherwise → B-2 fails.

### B-3 Justification length
For each row:
- Assert `row.justification.length ≥ 10`.
- If `row.status === "not_applicable"`: assert `justification` contains workflow-class reason (regex: `pure[-_ ]?read|prototype|spike|stateless|no[-_ ]state[-_ ]change|n/a[-_ ]workflow[-_ ]class|investigation[-_ ]only`).
- Otherwise → B-3 fails.

### B-4 Applicable → treatment
For each row where `row.status === "applies"`:
- Assert `(row.fields_or_events?.length > 0) || (row.treatment?.length > 0)`.
- Otherwise → B-4 fails with `{story_id, row_key, evidence: "applies_without_treatment"}`.

### B-5 Tier inference
For single-epic output:
- Assert `epic.inferred_tier ∈ {T1, T2, T3}` AND `epic.tier_signals.length ≥ 1`.

For multi-epic output:
- For each `epics[i]`: same assertion.

### B-6 Compensating action (state-change)
For each story where `banking_grade_concerns.reversibility.status === "applies"`:
- Get `treatment = banking_grade_concerns.reversibility.treatment ?? ""`.
- If `treatment.toLowerCase().includes("irreversible")` OR `treatment.toLowerCase().includes("non-reversible")`:
  - Assert `banking_grade_concerns.reversibility.compensating_action?.length ≥ 10`.
- Otherwise → B-6 fails.

### B-7 Tipping-off cross-check
For each story where `banking_grade_concerns.tipping_off.status === "applies"`:
- (a) Assert ≥1 AC with `scenario_type === "banking_grade_tipping_off"` (see `gherkin-quality.md` G-7).
- (b) Assert either: `governance_gaps[].some(g => g.type === "tipping_off_violation")` OR `processing_metadata.tipping_off_scan_clean === true`.
- Otherwise → B-7 fails. **Highest-leverage cross-check.**

### B-8 Legal-absent + regulatory
For each epic (single or multi):
- If `epic.legal_status !== "present"`:
  - Get stories belonging to this epic.
  - For each, get `banking_grade_concerns.regulatory.status`, `tipping_off.status`, `pii_fields.status`.
  - If any equals `"applies"`:
    - Assert `governance_gaps[].some(g => g.type === "legal_absent_on_regulatory" && g.blocks_tl_handoff === true)`.
    - Otherwise → B-8 fails. **Canonical always-fires detector.**

### B-9 PII force-fill
For each story where `banking_grade_concerns.pii_fields.status === "applies"`:
- Assert `banking_grade_concerns.pii_fields.fields_or_events.length > 0`.
- Assert `banking_grade_concerns.pii_fields.treatment.length ≥ 10`.
- Assert `glossary[].some(g => g.pii_sensitivity ∈ {direct, indirect, regulatory, financial})`.
- Otherwise → B-9 fails.

### B-10 Tier escalation
- Get `manual = frontmatter.workload_tier`.
- For each epic, get `inferred = epic.inferred_tier`.
- Tier rank: T1 > T2 > T3.
- If `rank(inferred) > rank(manual)`:
  - Assert `processing_metadata.tier_decisions[].some(d => d.inferred_higher_than_manual === true && d.epic_id === epic.id)`.
  - Assert `frontmatter.status !== "ready-for-tl"`.
  - Otherwise → B-10 fails.

## Cross-Check Summary

| Rule | Cross-checks against | Purpose |
|---|---|---|
| B-7 | `gherkin-quality.md` G-7 | Tipping-off applies ⇒ AC present AND governance recorded |
| B-8 | `epic.legal_status`, `governance_gaps[]` | Legal-absent ⇒ gap emitted (highest-leverage rule) |
| B-10 | `frontmatter.workload_tier` vs `epic.inferred_tier` | Tier escalation flagged in processing_metadata |

## Pass/Fail Interpretation

- **B-1, B-2, B-3 are absolute structural** — any failure fails the case.
- **B-4 .. B-10 are condition-based** — only fire when predicate holds.
- **B-7 and B-8 are highest-leverage** — failures expose silent governance defects. Treat any failure as case-fail (no should-pass downgrade).

## Per-Story Report Format

```json
{
  "assertion_file": "banking-grade-fields.md",
  "story_id": "EPIC-LOAN-2847-1",
  "rule_results": [
    { "rule_id": "B-1", "status": "pass" },
    { "rule_id": "B-2", "status": "pass" },
    { "rule_id": "B-3", "status": "pass" },
    { "rule_id": "B-4", "status": "pass" },
    { "rule_id": "B-5", "status": "pass" },
    { "rule_id": "B-6", "status": "n/a", "reason": "reversibility.status: not_applicable" },
    { "rule_id": "B-7", "status": "n/a", "reason": "tipping_off.status: not_applicable" },
    { "rule_id": "B-8", "status": "pass", "evidence": "legal_absent_on_regulatory governance_gap present" },
    { "rule_id": "B-9", "status": "pass" },
    { "rule_id": "B-10", "status": "n/a", "reason": "no tier escalation" }
  ]
}
```

## Cross-References

- `references/anti-patterns.md` §4 (AP-4.1, AP-4.3, AP-4.4) + §5 (AP-5.1)
- `references/edge-case-catalog.md` (FM-05, FM-06, FM-11)
- `gherkin-quality.md` G-7, G-8 (Gherkin-side cross-checks)
- `invest-compliance.md` (separate concern — INVEST not banking-grade)
