# Test Harness — review-backend-code

> **File-naming note.** Originally `tests/README.md` per the project's
> standard naming, renamed to `harness-guide.md` because
> `scripts/quick_validate.py` (BANNED_DOCS) rejects any `README.md`
> inside a skill folder. Same content; the validator wins.

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

Run the full suite for this skill:

```bash
go run ./cmd/harness -skill treasury/review-backend-code -case-glob 'tests/cases/*.input.json'
```

## How assertions check schema validity

| Layer | Checks | On failure |
|-------|--------|-----------|
| `SchemaValidityAssertion` | Output JSON validates against `schemas/output.json` | Fail case — schema break is always a blocker |
| Structural-diff against `expected.json` | `verdict`, `loop_back_target_stage`, finding *categories* + *severities* (not full evidence text), `claim_checks` statuses (by `claim_ref`) | Fail with diff |
| `audit_metadata` envelope check | Numeric fields present and non-negative | Fail with diff |

Evidence snippets and exact line numbers are NOT diffed verbatim — the LLM
may pick a different but equally valid citation. The harness checks the
*shape* of the verdict and findings; the human reviews exact wording.

## Banking-grade assertions

These run on every case in addition to schema validity.

| Assertion | What it verifies | Maps to |
|-----------|------------------|---------|
| `VerdictRoutingAssertion` | If `verdict == "loop_back"`, `loop_back_target_stage` is non-null. If `verdict != "loop_back"`, it is null. | severity-guide.md verdict matrix |
| `P1RoutingAssertion` | Any `P1` finding produces `verdict == "human-queue"`. No exceptions. | severity-guide.md P1 rule |
| `UnverifiedClaimsAssertion` | If any claim check is `unverified` AND no `P1` is present, verdict is `loop_back` to `backend-implement` (each unverified check carries `finding_ref`). | severity-guide.md claims rule |
| `DesignAmbiguityRoutingAssertion` | If any `uncertainty_flag.kind == "design_ambiguity"`, verdict is `loop_back` and target is `design`. | severity-guide.md design override |
| `EvidenceCitationAssertion` | Every finding has either a file:line pair OR an explicit `[needs verification]` tag in `evidence`. | SKILL.md Anti-Patterns rule against fabrication |
| `NoCodeEmissionAssertion` | The output JSON contains no field that would deliver code (this skill is read-only). | SKILL.md Anti-Patterns DO NOT emit code |
| `RulesEvaluatedFloorAssertion` | `audit_metadata.rules_evaluated >= 22` (11 base + 7 augmentation + 4 contract). Lower means the reviewer skipped rules. | review-rubric.md scope |

## Adding a new case

1. Pick the next prefix: `002-`, `003-`, …
2. Common cases worth adding:
   - `002-missing-idempotency.input.json` — handler with side-effect but no key. Expected: `human-queue`, `P1`, category `idempotency`.
   - `003-design-ambiguity.input.json` — design says "TBD" on auth. Expected: `loop_back` to `design`.
   - `004-unverified-audit-claim.input.json` — Generate claims event_type X, code emits Y. Expected: `loop_back` to `backend-implement`, an `unverified` claim check with `finding_ref`.
3. Write `NNN-<name>.input.json` — must validate against `schemas/input.json`.
4. Write `NNN-<name>.expected.json` — must validate against `schemas/output.json`.
5. Re-run the suite.

## What a passing run looks like

```
ok   001-clean-handler   schema=PASS verdict=approve routing=PASS evidence=PASS claims=PASS rules=22
```

`verdict=loop_back` or `verdict=human-queue` are also valid pass states for
cases written to exercise those routes — the harness checks shape, not the
verdict value.
