# Test Harness — implement-frontend-feature

> **File-naming note.** This file was named `tests/README.md` in the original
> brief, but `scripts/quick_validate.py` (BANNED_DOCS) rejects any
> `README.md` inside a skill folder. Renamed to `harness-guide.md` to satisfy
> the validator. See `RATIONALE.md` for the decision trail. Same trade-off
> applied in `implement-backend-feature` and `review-backend-code`.

## How the harness invokes the skill

A shared cross-skill test harness (a design intent from the pre-consolidation pack; no such harness ships in this workspace)
(`internal/test_harness/runner.go`) drives this skill exactly as the
workflow engine will:

1. Load `SKILL.md` + every file in `references/` into LLM context.
2. Read `tests/cases/NNN-<name>.input.json`; validate against
   `schemas/input.json`. Case-level validation failure = harness bug,
   fix the case.
3. Send the input to the LLM as the stage payload. Capture the raw response.
4. Parse the response as JSON. Validate against `schemas/output.json`.
5. Compare against `tests/cases/NNN-<name>.expected.json` using the
   assertion set below.
6. Emit a per-case `TestResult` with per-assertion pass/fail.

Run the full suite for this skill with:

```bash
go run ./cmd/harness -skill treasury/implement-frontend-feature -case-glob 'tests/cases/*.input.json'
```

## How assertions check schema validity

| Layer | Checks | On failure |
|-------|--------|-----------|
| `SchemaValidityAssertion` | Output JSON validates against `schemas/output.json` (including nested `a11y_compliance` and `security_review` required fields) | Fail immediately — schema break is a blocker |
| Structural-diff against `expected.json` | File paths, component pillars, test types, a11y boolean fields, security strategy enums, state ownership map keys, audit event types, uncertainty flag kinds | Fail with diff |
| `bundle_impact_estimate_kb` envelope | Numeric, non-negative | Fail with diff |

`content_hash` placeholders (`sha256:0...`) and `coverage_pct` exact values
are NOT diffed verbatim — formatting differences in the regenerated code
should not register as regressions. The harness checks shape and presence.

## Banking-grade assertions (frontend-specific)

These run on every case in addition to schema validity.

| Assertion | What it verifies | Maps to |
|-----------|------------------|---------|
| `A11yCompletenessAssertion` | All 6 fields of `a11y_compliance` are present AND `wcag_level >= AA` AND no boolean is `false` for an a11y-claimed component. | implementation-rules.md F5; a11y-checklist.md routing |
| `SecurityReviewCompletenessAssertion` | All 5 fields of `security_review` are present. `xss_surfaces` non-empty entries each have a mitigation. `token_storage_strategy` is one of `httpOnly-cookie | in-memory | n/a`. | security-checklist.md routing |
| `PiiCoverageAssertion` | Every entry in input's `pii_field_classification` appears in `security_review.pii_fields_handled` with the same treatment. | security-checklist.md G; implementation-rules.md F9 |
| `PillarConsistencyAssertion` | Every file in `files_generated` declares one valid pillar. Files of pillar `Primitive` never appear alongside fetching imports (cross-check requires reading file contents in a richer harness — flagged as a manual review item in v1). | react-typescript-conventions.md pillars |
| `StateOwnershipCompletenessAssertion` | Every state piece named in the design (parsed heuristically — look for `**State ownership**:` or `state_ownership` markers) appears in `state_ownership` output. | state-management-rules.md decision tree |
| `BundleBudgetAssertion` | If `bundle_budget_kb` is in input AND `bundle_impact_estimate_kb` exceeds it, an `uncertainty_flag` of kind `bundle_overrun` MUST be present. | implementation-rules.md A8 |
| `AnalyticsAuditAssertion` | If any file's pillar is `Feature` or `Page` AND the design declares a mutation / submit / navigation, `audit_events_emitted` MUST be non-empty. Display-only Primitives may have empty array. | implementation-rules.md F12 |
| `MutationCompensationAssertion` | If the feature includes any mutation path, `compensating_actions` MUST be non-empty. | implementation-rules.md A3 |
| `NoSecretsAssertion` | Regex scan over emitted file contents (fetched separately) for `password`, `token`, `secret`, `private_key`, AWS-style access key patterns. | security-checklist.md F |
| `UncertaintyHonestyAssertion` | If `uncertainty_flags` is non-empty, harness records the case as `LOOP_BACK` not `PASS`. Correct behavior, not a failure. | Procedure step 1 |

## Adding a new case

1. Pick the next numeric prefix: `002-`, `003-`, …
2. Suggested next cases:
   - `002-form-with-mutation.input.json` — RHF + Zod form with optimistic update.
     Expected: `compensating_actions` non-empty, `audit_events_emitted` includes submit event, `Idempotency-Key` strategy in `decision_metadata`.
   - `003-page-with-tanstack-query.input.json` — Next.js page that fetches a paginated list.
     Expected: `Page` pillar file, `state_ownership` includes `pagination: URL`.
   - `004-design-with-a11y-tbd.input.json` — design has `TBD` on keyboard contract.
     Expected: `uncertainty_flag` of kind `design_ambiguity`, verdict ultimately `loop_back` to design at the Review stage.
3. Write `NNN-<name>.input.json` — must validate against `schemas/input.json`.
4. Write `NNN-<name>.expected.json` — must validate against `schemas/output.json`.
5. Re-run the suite.

## What a passing run looks like

```
ok   001-simple-display-component   schema=PASS a11y=PASS security=PASS pii=PASS pillars=PASS state=PASS bundle=PASS analytics=N/A mutation=N/A secrets=PASS uncertainty=PASS
```

`mutation=N/A` and `analytics=N/A` are valid for display-only components.
`LOOP_BACK` and `HUMAN_QUEUE` are valid pass states for cases written to
exercise those routes.
