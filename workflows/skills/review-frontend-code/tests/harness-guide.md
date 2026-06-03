# Test Harness — review-frontend-code

> **File-naming note.** This file was named `tests/README.md` in the project's
> default convention, but `scripts/quick_validate.py` (BANNED_DOCS) rejects
> any `README.md` inside a skill folder. Renamed to `harness-guide.md` —
> same trade-off as the other three skills.

## How the harness invokes the skill

The shared test harness (`COGNITIVE_OS.md` Section 9
`internal/test_harness/runner.go`) drives this skill the same way the
workflow engine will:

1. Load `SKILL.md` + every file in `references/` into LLM context.
2. Read `tests/cases/NNN-<name>.input.json`; validate against
   `schemas/input.json`. Case-level validation failure = harness bug,
   fix the case.
3. Send the input to the LLM as the stage payload; capture the raw response.
4. Parse the response as JSON; validate against `schemas/output.json`.
5. Compare against `tests/cases/NNN-<name>.expected.json` using the
   assertion set below.
6. Emit a per-case `TestResult` with per-assertion pass/fail.

Run the full suite:

```bash
go run ./cmd/harness -skill treasury/review-frontend-code -case-glob 'tests/cases/*.input.json'
```

## How assertions check schema validity

| Layer | Checks | On failure |
|-------|--------|-----------|
| `SchemaValidityAssertion` | Output JSON validates against `schemas/output.json` (including nested `a11y_verdict` and `security_verdict` required fields) | Fail case — schema break is always a blocker |
| Structural-diff against `expected.json` | `verdict`, `loop_back_target_stage`, finding *categories* + *severities* (not full evidence text), `claims_unverified` set, `a11y_verdict` enum values, `security_verdict` booleans | Fail with diff |
| `audit_metadata` envelope | Non-negative numerics, `rules_evaluated >= 26` | Fail with diff |

Evidence snippets and exact line numbers are NOT diffed verbatim — the LLM
may pick a different but equally valid citation. Harness checks shape of
verdict + findings; the human reviews exact wording.

## Banking-grade assertions (frontend-specific)

These run on every case in addition to schema validity.

| Assertion | What it verifies | Maps to |
|-----------|------------------|---------|
| `VerdictRoutingAssertion` | If `verdict == loop_back`, `loop_back_target_stage` non-null; otherwise null. | severity-guide.md verdict matrix |
| `P1RoutingAssertion` | Any `P1` finding → `verdict == human-queue`. No exceptions. | severity-guide.md P1 rule |
| `UnverifiedClaimsAssertion` | `claims_unverified` non-empty AND no `P1` → verdict `loop_back` to `implement`. | severity-guide.md claims rule |
| `DesignRoutingAssertion` | Any `uncertainty_flag.kind` in `{design_ambiguity, bundle_overrun, token_gap}` → verdict `loop_back`, target `design`. | severity-guide.md design override |
| `A11yBlockerAssertion` | `a11y_verdict.wcag_level_verified == below_AA` → at least one `P1 / a11y` finding present AND verdict `human-queue`. | F5 + severity-guide.md |
| `SecurityBlockerAssertion` | If any `security_verdict` boolean is `false`, corresponding `P1` finding present (xss / token_storage / pii_leak / csrf categories). | severity-guide.md P1 categories |
| `EvidenceCitationAssertion` | Every finding has either a file:line pair OR an explicit `[needs verification]` tag in `evidence`. | SKILL.md Anti-Patterns anti-fabrication rule |
| `NoCodeEmissionAssertion` | Output JSON contains no field delivering code (this skill is read-only). | SKILL.md Anti-Patterns "do not emit code" |
| `RulesEvaluatedFloorAssertion` | `audit_metadata.rules_evaluated >= 26` (12 F + 9 A + 5 C). Lower = reviewer skipped rules. | review-rubric.md scope |
| `ClaimsCheckedFloorAssertion` | `audit_metadata.claims_checked >= count(implement_stage_output claims fields)` (rough — for the 001 case, ≥ 11). | step 6 mandate |
| `PiiCoverageAssertion` | Every field in input's `implement_stage_output.security_review.pii_fields_handled[]` appears either in `claims_verified` OR `claims_unverified` — none dropped. | C4 + F9 |
| `AuditEventCoverageAssertion` | Every entry in `implement_stage_output.audit_events_emitted[]` appears in `claims_verified` OR `claims_unverified`. | C3 + F12 |

## Adding a new case

1. Pick the next prefix: `002-`, `003-`, …
2. Common cases worth adding:
   - `002-missing-a11y-claim.input.json` — Generate claims `keyboard_navigable: true` but code has `<div onClick>`. Expected: `human-queue`, P1 `a11y` + P1 `false_claim`.
   - `003-localstorage-token.input.json` — code has `localStorage.setItem('access_token', ...)` but Generate claims `token_storage_strategy: 'in-memory'`. Expected: `human-queue`, P1 `token_storage` + P1 `false_claim`.
   - `004-bundle-overrun.input.json` — input declares `bundle_budget_kb: 5`, Generate emits estimate 12. Expected: verdict `loop_back`, target `design`.
   - `005-design-ambiguity.input.json` — design says "TBD" on keyboard contract. Expected: `loop_back` to `design`, `design_ambiguity` flag.
   - `006-unverified-audit-event.input.json` — Generate claims event `loan.submitted` but code calls `track({event_type: 'loan.created', ...})`. Expected: `loop_back` to `implement`, `claims_unverified` non-empty.
3. Write `NNN-<name>.input.json` — must validate against `schemas/input.json`.
4. Write `NNN-<name>.expected.json` — must validate against `schemas/output.json`.
5. Re-run the suite.

## What a passing run looks like

```
ok   001-clean-display-component   schema=PASS verdict=approve routing=PASS a11y=PASS security=PASS evidence=PASS claims=PASS rules=26
```

`verdict=loop_back` and `verdict=human-queue` are also valid pass states
for cases written to exercise those routes — the harness checks shape, not
the verdict value.
