# Assertion — Open-Question Dependency Tracking

## Scope

Test case 001 (holdout has 51 OQs). Test case 002 (banking single-epic; expect fewer OQs).

## What's tested

For every unresolved BA OQ that affects a test (threshold, contract detail, etc.), the affected test references it via `blocking_oqs[]`. No silent assumption of defaults (AP-Q9 enforced).

## Per-case assertions

1. **Every OQ-related test has `blocking_oqs[]` populated.**
   ```
   # OQs with severity P1 or P2 from BA brief
   jq '[.open_questions[] | select(.severity=="P1" or .severity=="P2")] | length' brief/output.json
   # Test cases AND nfr_tests with blocking_oqs[] non-empty
   jq '[.test_cases[], .nfr_tests[] | select(.blocking_oqs and (.blocking_oqs | length) > 0)] | length' output.json
   ```

2. **Every blocking_oq reference resolves to a real BA OQ.**
   ```
   jq -r '.test_cases[].blocking_oqs[]?, .nfr_tests[].blocking_oqs[]?' output.json | sort -u > test_oqs.txt
   jq -r '.open_questions[].id' brief/output.json | sort -u > brief_oqs.txt
   comm -23 test_oqs.txt brief_oqs.txt   # expect empty (no invented OQ refs)
   ```

3. **NFR tests targeting "TBD pending OQ-N" have non-empty `blocking_oqs[]`.**
   ```
   jq '[.nfr_tests[] | select(.target | test("TBD pending OQ-"))] |
     map(select((.blocking_oqs | length) == 0))' output.json
   # Expect [] (every TBD has a blocker recorded)
   ```

4. **No test asserts a numeric threshold whose source OQ is unresolved.** Cross-check: if `expected_assertions[].description` contains a number that appears as a target in an OQ marked unresolved, the test must also carry `blocking_oqs[]` pointing at that OQ.

5. **Coverage gaps referencing OQs use correct severity.** Any `coverage_gap.type == "missing-nfr-target"` should map back to a real OQ blocking it.

## Pass criterion

All 5 assertions pass. Hard gate on (3) and (4) — AP-Q9 violation if either fails.

## What failure means

- TBD target without `blocking_oqs` → skill omitted the OQ link; AP-Q9 risk.
- Invented numeric threshold → skill silently assumed defaults; AP-Q9 violated; refuse and fix prompt.
- blocking_oq reference to unknown OQ → traceability loss; SKILL.md Step 2 didn't index OQs properly.
