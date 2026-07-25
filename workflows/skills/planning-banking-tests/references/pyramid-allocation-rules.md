# Pyramid Allocation Rules (v1.0)

## Purpose

This reference provides the deterministic rules for assigning each test
case in the QA plan to a pyramid level (`unit`, `integration`, `e2e`)
or to the orthogonal `contract` lane. It is loaded at SKILL.md Step 5
on every run, after the scenario-type mapping has produced the initial
roster. The allocation rules are applied in the order defined below;
the first rule that matches a test case wins, and the chosen level is
recorded with a reason code on the test case for audit. This document
is paired with `scenario-type-mapping.md`, which produces the default
level; this document defines the overrides and the per-tier mix
ratios.

## Pyramid ratios per tier

The ratios below are the **starting allocation targets** consumed by
SKILL.md Step 5. They are not hard quotas: the actual emitted plan
may deviate from these ratios when the decision rules in the next
section force a different level. The SKILL.md tests assert the final
mix is within ±10 percentage points of the target per category, and
the run records the realized mix in `coverage_matrix.pyramid_mix`.

| tier | unit_pct | integration_pct | e2e_pct | contract_pct |
|------|----------|-----------------|---------|---------------|
| T1   | 40       | 40              | 5       | 15            |
| T2   | 50       | 30              | 5       | 15            |
| T3   | 60       | 30              | 5       | 5             |

These are illustrative starting ratios. They are revised by the
SKILL.md test suite at calibration time and may be re-tuned per
brief; the revised values are pinned per run in
`processing_metadata.pyramid_ratio_targets`. Contract tests are
counted separately and do not consume the unit/integration/e2e
budget, because they verify cross-service shape rather than internal
behavior.

The ratios reflect the banking-grade preference for verifiable
behavior at the deepest practical level: T1 weights integration
higher than T2 or T3 because banking-grade scenarios
(audit, idempotency, authz, reversibility) almost always default to
integration, and T1 emits all of them; T3 weights unit highest
because banking-grade concerns rarely fire on T3 workloads.

## Decision rules

The rules are applied per test case in the listed order. The first
match assigns the level, and the matching rule's identifier is
recorded in `test_cases[].pyramid_level_reason`.

1. **R1 — Banking-grade default**. Any test case whose source
   scenario_type starts with `banking_grade_` defaults to
   `integration` regardless of the per-tier ratio target. Demotion
   to unit requires an explicit `pyramid_demotion_reason` and a
   reviewer approval reference recorded on the test case. Promotion
   to e2e requires that the banking-grade behavior is only
   observable through a customer-facing surface (rare).
2. **R2 — Happy + error duplication**. When a scenario is mapped to
   both a unit and an integration test by the scenario-type table
   (`happy` and `error` rows), both cases are emitted. The unit
   case asserts pure logic with all collaborators stubbed; the
   integration case asserts the same outcome with realistic
   adapters. The two cases share `scenario_ref` and differ only in
   `pyramid_level` and `expected_assertions[]`.
3. **R3 — Concurrency, race, ordering**. Any scenario whose
   description or `tags[]` mentions concurrency, race condition,
   ordering, replay, or out-of-order delivery is allocated to
   `integration` with deterministic primitives (controlled clock,
   in-memory queue, single-threaded executor). E2E-level
   concurrency tests are forbidden under R3 because they are not
   reproducible at the determinism contract the kit requires.
4. **R4 — E2E reservation**. The `e2e` level is reserved for two
   categories of test case, and no others: (a) customer-facing
   Must-priority happy paths whose value proposition is visible
   only end-to-end (checkout completion, onboarding success,
   regulated disclosure rendering); (b) acceptance-demo flows
   explicitly named in the brief's `signoff_criteria.demo_flows[]`.
   All other tests live at unit or integration level.
5. **R5 — Edge-case storage dependence**. Edge cases that depend
   on storage or wire semantics (decimal precision, JSON null vs
   absent, charset collation, timezone arithmetic at DST
   boundaries) are promoted from `unit` to `integration` with
   reason `R5_storage_dependent_edge`.
6. **R6 — Contract-test routing**. Scenarios that cross a service
   boundary owned by a different team or vendor (payment provider,
   identity provider, regulator submission endpoint) emit an
   additional contract test in the `contract` lane. The contract
   test asserts request and response shape against the recorded
   provider contract; it does not assert business outcomes.

When no rule above matches, the test case keeps the
`default_pyramid_level` from the scenario-type mapping table, and
`pyramid_level_reason` is set to `default_from_mapping`.

## Smoke subset definition

The smoke subset is a deterministic minimal-roster slice of the full
plan, surfaced at the top level of `output.json` as `smoke_subset[]`.
Its purpose is to give CI a single roster that can be run on every
PR without consuming a full test budget. The definition is:

1. **One test case per Must-priority story**. The brief's
   `stories[].priority` field is the authority. For every story
   whose priority is `Must`, the smoke subset includes exactly one
   test case from that story.
2. **Selection rule**. Prefer the highest-coverage happy-path
   integration test for the story. If no integration happy test
   exists, fall back to the highest-coverage unit happy test. If no
   happy test exists at all (rare), select the
   `banking_grade_audit` test as a last resort.
3. **Wall-clock budget**. Each smoke test must complete in under
   30 seconds wall-clock against the per-PR ephemeral environment.
   The sum across all smoke tests must complete in under 5 minutes.
   Tests that cannot meet the per-test budget are excluded from
   the smoke subset, even if they would otherwise be selected by
   rule 2; in that case the story records a
   `smoke_subset_gap` in `coverage_gaps[]`.
4. **Stability**. The same brief, run twice with the same
   `idempotency_key`, must produce the same smoke subset. Smoke
   subset membership is recorded on the test case as
   `smoke_subset_member: true`.

The smoke subset is not a coverage target. It is a fast-feedback
slice, and missing coverage outside the smoke subset is the
responsibility of the broader plan, not of the smoke runner.

## Contract test scope

Contract tests are emitted under any of the following triggers:

1. The brief lists an external dependency in
   `processing_metadata.external_dependencies[]` with `kind` of
   `payment_provider`, `identity_provider`, `regulator_endpoint`,
   `kyc_provider`, or `notification_provider`.
2. A story's acceptance criteria reference a cross-service flow,
   identified by the brief's
   `stories[].technical_notes.crosses_service_boundary == true`.
3. A banking-grade scenario whose audit or compensation action
   crosses a service boundary owned by a different team.

Contract tests live in their own pyramid lane and consume the
`contract_pct` budget defined per tier above. They do not displace
unit, integration, or e2e tests for the same scenario; they are
additive. The contract test asserts shape, status codes, and
required headers; it explicitly does not assert business outcomes,
which are the job of the integration or e2e test pointing at the
same boundary.

## Allocation versioning

Every test case emitted by this skill carries, inside its parent
`processing_metadata` block, the field
`pyramid_allocation_rules_version: "1.0"`. The versioning discipline
matches the scenario-type mapping table:

1. Adding a new rule (e.g., R7) without altering the existing rules'
   precedence is a minor bump.
2. Changing the order of rule application, or altering the per-tier
   ratio targets, is a major bump because both materially change
   the historical interpretation of a prior plan.
3. The renderer asserts that the version string emitted in
   `processing_metadata` matches the version recorded at the top
   of this file; a mismatch fails the run.

## Anti-patterns

See `anti-patterns.md` for the full list. The following applies
directly to allocation:

- **AP-Q5** — Coverage-target obsession. Forcing additional unit
  tests onto a story purely to meet the per-tier unit_pct target
  is rejected. The ratios are starting allocations, not quotas, and
  the SKILL.md tests assert the ratio with a tolerance band
  precisely to prevent this anti-pattern. When the realized mix
  falls outside the tolerance band, the cause is recorded as a
  coverage gap, not papered over by manufacturing tests.
