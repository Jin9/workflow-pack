# Test Harness — implement-backend-feature

> **File-naming note.** This file was named `tests/README.md` in the original
> prompt, but `scripts/quick_validate.py` (BANNED_DOCS) rejects any
> `README.md` inside a skill folder. Renamed to `harness-guide.md` to satisfy
> the validator. See `RATIONALE.md` for the full decision trail.

## How the harness invokes the skill

The shared test harness from `COGNITIVE_OS.md` Section 9
(`internal/test_harness/runner.go`) drives this skill the same way the
workflow engine will in production:

1. Load `SKILL.md` and its referenced files into LLM context.
2. Read `tests/cases/NNN-<name>.input.json` and validate it against
   `schemas/input.json`. A case whose input fails validation is a harness
   bug, not a skill failure — fix the case.
3. Send the input to the LLM as the stage payload. Capture the raw response.
4. Parse the response as JSON. Validate against `schemas/output.json`.
5. Compare against `tests/cases/NNN-<name>.expected.json` using the assertion
   set below.
6. Emit a per-case `TestResult` with per-assertion pass/fail.

Run the full suite for this skill with:

```bash
go run ./cmd/harness -skill treasury/implement-backend-feature -case-glob 'tests/cases/*.input.json'
```

## How assertions check schema validity

Two layers run on every case:

| Layer | What it checks | On failure |
|-------|----------------|-----------|
| `SchemaValidityAssertion` | Output JSON validates against `schemas/output.json` | Fail case immediately — schema break is a blocker |
| Structural-diff against `expected.json` | File paths, idempotency strategy, compensation set, audit event types, uncertainty flag kinds | Fail with diff (content hashes are not compared — see below) |

Content hashes in `expected.json` are placeholders (`sha256:0...`). The
harness ignores hash mismatches and instead diffs the *fields that must be
stable* across runs: file paths, idempotency strategy class, decision
choices, and uncertainty flag kinds. Hashes will differ when the LLM
re-generates the same file with different formatting; that is not a regression.

## Banking-grade assertions

These run on top of schema validity and are non-skippable.

| Assertion | What it verifies | Maps to |
|-----------|------------------|---------|
| `AuditCompletenessAssertion` | If `files_generated` includes a write-shaped file, `audit_events_emitted` is non-empty. Read-only features may have empty audit. | Implementation Rule A1 |
| `IdempotencyClaimAssertion` | If any file is a write-shaped handler / consumer / producer, `idempotency_strategy` mentions a key, a store, and a replay behavior — OR explicitly states "naturally idempotent" with a reason. | Base Rule "Idempotency is required for retries"; Augmentation A2 |
| `CompensationAssertion` | If any code path publishes events / calls partner APIs / sends notifications, `compensating_actions` is non-empty. | Augmentation A3 |
| `TestCoveragePerFileAssertion` | Every entry in `tests_generated` has `coverage_pct >= test_coverage_target` (from the input case, default 0.80). | Procedure step 5 |
| `NoSecretsAssertion` | None of the assertions reveal a `password`, `token`, `secret`, `private_key`, or AWS-style access key pattern in the generated code (run a regex scan over file contents fetched separately). | Self-Review section F |
| `UncertaintyHonestyAssertion` | If `uncertainty_flags` is non-empty, the harness records the case as `LOOP_BACK` not `PASS`. This is correct behavior, not a failure — the assertion exists to make sure the skill doesn't hide ambiguity. | Procedure step 1 |

## Adding a new case

1. Pick the next numeric prefix: `002-`, `003-`, …
2. Write `NNN-<name>.input.json` — must validate against `schemas/input.json`.
3. Write `NNN-<name>.expected.json` — must validate against `schemas/output.json`.
4. Document the case purpose in a one-line comment at the top of the file
   (use a JSON-with-comments parser, or a sibling `.md` if strict JSON is
   required).
5. Re-run the suite.

## What a passing run looks like

```
ok   001-simple-handler   schema=PASS audit=N/A idempotency=PASS coverage=PASS secrets=PASS uncertainty=PASS
```

Any `FAIL`, `LOOP_BACK`, or `HUMAN_QUEUE` line is actionable and printed
with the full assertion diff.
