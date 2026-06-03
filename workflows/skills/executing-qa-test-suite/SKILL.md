---
name: executing-qa-test-suite
version: 0.1.0
description: >
  Execute a planned QA test roster against a running system, measure
  run-system coverage, surface flaky tests, catch live defects, and emit a
  results-backed PASS, FAIL, or ERROR QA gate that feeds a human verification
  layer. Use when asked to execute the QA test suite, run the planned test
  roster on the running system, produce the QA pass/fail gate with evidence, or
  measure run-system coverage. Runs in a sandbox via a CI/test runner and routes
  failures to a fixer rather than fixing them. Do NOT use to design the test plan
  (use planning-banking-tests). Do NOT use to run a single test level in
  isolation (use the unit/integration/e2e execution skills). Do NOT use to write
  or fix tests or production code.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: detailed, pii_handling: none, tier_default: T1, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 900
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Executing the QA Test Suite

## Purpose

Run the QA roster produced by `planning-banking-tests` against a running system
and emit a results-backed sign-off gate — the **execution** stage that the design
stage deliberately leaves out (it "produces test plans, not test code; never
measures coverage on running systems"). Measures real coverage, surfaces flaky
tests, catches live defects, and hands the verdict to a human verification layer.
Never writes or fixes code.

## When to use this skill

- Use when: a `qa-plan` / test roster exists and must be executed on a running
  system to produce a pass/fail QA gate with evidence.
- Use when: asked to "execute the QA suite", "run the roster", or "produce the QA
  sign-off with coverage".
- Do NOT use: to design the plan (`planning-banking-tests`), to run one level in
  isolation (the unit/integration/e2e execution skills), or to fix code.

## Input contract

Validate against `schemas/input.json`. Required: `test_roster` (the planned
suite), `target_env` (the running system/sandbox to test), `idempotency_key`.
Optional: `signoff_criteria`, `tier`. Stop with `needs-input` if no roster or no
reachable target.

## Procedure

1. **Plan-Act-Verify** (`references/qa-execution-loop.md`): for each roster item,
   execute against `target_env` via the CI/test runner, capturing real results —
   never an LLM-asserted pass. Entry: a roster + target. Exit: per-item results.
2. **Measure run-system coverage** from the runner report (line/branch), not a
   self-declared figure.
3. **Surface flaky tests** by bounded re-run; mark non-deterministic items rather
   than passing them by luck.
4. **Collect live defects** with reproduction evidence; classify by severity.
5. **Apply the gate:** `FAIL` on any failed required item or unmet
   `signoff_criteria`; `ERROR` if the suite could not run; else `PASS`. Banking
   default: a masked/uncertain result is a fail, not a pass.
6. **Emit** the verdict (Output contract). Stop — failures route to a fixer; the
   gate feeds a **human verification layer**, never auto-approves.

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR),
`totals{executed,passed,failed,skipped}`, `coverage_measured`, `flaky[]`,
`defects[]{severity,summary,repro}`, and `audit_id`.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| QE-01 | no roster / unreachable target | no verdict | needs-input → human-queue |
| QE-02 | suite cannot execute | `ERROR` | human-queue |
| QE-03 | required item fails | `FAIL` + defects[] | route to progressive-bug-hunter |
| QE-04 | flaky/non-deterministic results | verdict + flaky[] | flag for human verification |

## Constraints

- DO NOT write, edit, or fix tests or production code — execute and report only.
- DO NOT emit a pass not backed by runner results; uncertain → fail (banking).
- DO NOT auto-approve; the gate feeds a named human verification layer.
- DO NOT run outside the sandbox or reach the network beyond the target env.

## References

| Need | Reference |
|------|-----------|
| Plan-Act-Verify loop, runner integration, run-system coverage, flaky handling, human layer | `references/qa-execution-loop.md` |
