# QA execution loop, coverage, flaky handling, human layer

Grounded in the ResearchVault: an autonomous QA agent runs a **Plan-Act-Verify**
loop that writes AND executes tests and validates against the codebase, measures
run-system line/branch coverage, surfaces and reduces flaky tests, and catches
live defects via a CI/Playwright runner — and a $6M production loss when
AI-passed tests masked defects is exactly why this execution gate must feed a
human verification layer. See `[[literature/agent-orchestration/autonomous-qa-agents]]`.

## Plan-Act-Verify

For each roster item: set up state → execute against the running target via the
CI/test runner → verify the observed end-state (not an HTTP 200, not an LLM
claim). Record real pass/fail with evidence.

## Run-system coverage

Read line/branch coverage from the runner report on the running system. Never
report a self-declared coverage number; if coverage cannot be measured, say so
and do not infer a pass.

## Flaky handling

Re-run suspect items a bounded number of times; if results differ, mark the item
`flaky` and exclude it from a PASS — a flaky green is not a pass. Report flaky
items for stabilization.

## Gate policy (banking default)

- `ERROR` — suite could not execute against the target.
- `FAIL` — any required item failed, `signoff_criteria` unmet, OR results are
  masked/uncertain (uncertain → fail in regulated contexts).
- `PASS` — all required items pass on real runner evidence with coverage met.

## Human verification layer

The verdict **feeds a named human** sign-off; this skill never auto-approves.
Failures route to `progressive-bug-hunter` (diagnosis) — the executor does not
fix code. Single-level execution (unit/integration/e2e) is delegated to the
dedicated execution skills; this skill orchestrates the roster + verdict.
