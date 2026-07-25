# Assertion — Tier Respect

## Scope

Test cases 001 (multi-epic T2) and 002 (single-epic T1). Verifies AP-Q3 (no single-tier collapse on heterogeneous briefs).

## What's tested

When a BA brief carries heterogeneous tiers across epics, the test plan respects per-epic tier — pyramid allocation, mandatory test types, sign-off thresholds — and never collapses to one tier across the whole plan.

## Per-case assertions

1. **Per-epic test tier matches BA.**
   ```
   jq '.epics[] | {epic_id, test_tier}' output.json > planned_tiers.json
   jq '.initiative.per_epic_tier[] | {epic_id, tier}' brief/output.json > brief_tiers.json
   # planned_tiers[i].test_tier == brief_tiers[i].tier
   ```

2. **Pyramid allocation reflects per-epic tier.** For each epic, derive the expected pyramid ratios from `references/pyramid-allocation-rules.md` per its `test_tier`. If multi-epic brief has both T1 + T2 + T3 epics, the global `strategy.test_pyramid_allocation` should be a weighted average (or per-epic strategy doc, depending on plan version). Either way: not all 16 stories' tests should fall into one pyramid level.

3. **Sign-off criteria are tier-specific.** `signoff_criteria.tier` matches the highest tier present in `epics[].test_tier`. If the brief is multi-tier, signoff is at the strictest tier (T1 > T2 > T3 strictness order).

4. **Mandatory test types per tier present.** For each T1 epic: expect all banking_grade_* + compliance + perf + accessibility tests present. For each T2 epic: expect banking_grade_* + compliance + authz + perf p95 tests. For each T3 epic: expect smoke + critical-path E2E.

5. **No "test_tier mismatch" warning silently dropped.** If `tier_hint` is supplied and is looser than BA-inferred, expect `failure_state.failure_code == "tier_downgrade_warning"` (TM-11), NOT silent acceptance.

## Pass criterion

All 5 assertions pass. (5) is a hard gate; (1)–(4) are hard for T1, soft (warning) for T3.

## What failure means

- Per-epic tier mismatch → SKILL.md Step 3 broke; `processing_metadata.tier_decisions[]` should record the override decision per epic. AP-Q3 violation.
- Pyramid collapsed to one ratio across heterogeneous tiers → strategy doc isn't per-tier-aware. Re-read `references/pyramid-allocation-rules.md` and `references/tier-aware-test-policy.md`.
- Silent tier downgrade → TM-11 mis-implemented. Hard refuse.
