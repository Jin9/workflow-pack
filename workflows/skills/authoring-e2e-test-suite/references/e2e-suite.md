# E2E suite — deriving scenarios from journeys, runner integration, flaky rate, gate

Grounded in the ResearchVault: a requirement-to-test pipeline turns user journeys
and stories into executable end-to-end scenarios, and the UAT/regression strategy
runs them against a running system for SIT/UAT. The runner is the source of truth;
the agent derives scenarios and reports real results, never a self-claimed pass.

## Deriving scenarios from journeys

For each journey or story, derive an executable end-to-end scenario: explicit
setup, ordered steps, and assertions tied to the journey's acceptance criteria.
Each scenario records `steps_total` and, after the run, `steps_failed`.

## E2E runner integration

Execute each scenario against `target_env` through the CI/test runner using an
e2e/browser driver. Verify the observed end-state of the journey — not an HTTP 200
and not an LLM claim. Record per-scenario pass/fail with reproduction evidence.

## Flaky-rate handling

Re-run suspect scenarios a bounded number of times. If results differ across runs,
mark the scenario `flaky` and exclude it from a PASS — a flaky green is not a
pass. Compute `flaky_rate` as the fraction of scenarios surfaced as flaky and
report them for stabilization.

## Gate policy (banking default)

- `ERROR` — the suite could not execute against the target.
- `FAIL` — any journey/assertion failed, any scenario is flaky, OR results are
  masked/uncertain (uncertain is a fail in regulated contexts).
- `PASS` — 0 journey/assertion failures AND no flaky scenario, all on real runner
  evidence.

## Human verification layer

The verdict feeds a named human sign-off; this skill never auto-approves. Failures
route to `progressive-bug-hunter` for diagnosis — the executor does not fix code.

## Sources

- [[literature/product-requirements/requirement-to-test-pipeline|Requirement-to-test pipeline]]
- [[literature/product-requirements/uat-regression-testing-strategy|UAT/Regression testing strategy]]
- [[literature/agent-orchestration/autonomous-qa-agents|Autonomous QA agents]]
- Web: playwright.dev (end-to-end testing and retries for flaky tests) · oneuptime.com
