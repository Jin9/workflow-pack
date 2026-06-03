# Backend unit execution — runner integration, coverage, flaky handling, gate

Grounded in the ResearchVault: an autonomous QA agent executes tests against the
codebase and measures real coverage rather than asserting a pass, which is the
discipline this unit gate enforces for the backend leg. The runner is the source
of truth; the agent orchestrates and reports.

## Stage and run

Load `backend_artifacts` and stand up the sandbox `target_env`. Compile and run
the backend unit suite (e.g. `go test` with coverage) through the CI/test runner.
Record per-test pass/fail with a concrete reproduction command, never an HTTP 200
and never an LLM claim.

## Line coverage from the runner

Read measured line coverage from the runner report (e.g. the coverage profile),
not a self-declared number. If coverage cannot be measured, set
`coverage_measured` to null, say so, and do not infer a pass — an unmeasurable
coverage is treated as below threshold.

## Flaky handling

Re-run suspect tests a bounded number of times. If results differ across runs,
mark the test flaky and exclude it from a PASS — a flaky green is not a pass.
Report flaky tests for stabilization rather than passing them by luck.

## Gate policy (banking default)

- `ERROR` — the suite could not execute against the sandbox.
- `FAIL` — any unit test failed, measured coverage is under the threshold
  (default 0.80), coverage is unmeasurable, OR results are masked/uncertain
  (uncertain is a fail in regulated contexts).
- `PASS` — `failed` is 0 AND measured line coverage is at least the threshold,
  all on real runner evidence.

## Human verification layer

The verdict feeds a named human sign-off; this skill never auto-approves. Failures
route to `progressive-bug-hunter` for diagnosis — the executor does not fix code.

## Sources

- [[literature/capabilities/test-generation-capability|Test Generation Capability]]
- [[literature/agent-orchestration/autonomous-qa-agents|Autonomous QA agents]]
- [[literature/agent-orchestration/agentic-cicd|Agentic CI/CD]]
- Web: grafana.com (k6 thresholds as a runner-measured gate) · oneuptime.com
