# Frontend unit execution — runner integration, per-file coverage, flaky handling, gate

Grounded in the ResearchVault: an autonomous QA agent executes tests against the
codebase and reads real coverage rather than asserting a pass, which is the
discipline this unit gate enforces for the frontend leg. The runner is the source
of truth; the agent orchestrates and reports per file.

## Stage and run

Load `frontend_artifacts` and stand up the sandbox `target_env`. Run the frontend
unit suite (component/UI tests with coverage instrumentation) through the CI/test
runner. Record per-test pass/fail with a concrete reproduction command, never an
LLM claim.

## Per-file coverage from the runner

Read measured coverage per file from the runner report, not a self-declared
number. If a file's coverage cannot be measured, record it as null, say so, and
do not infer a pass — an unmeasurable file is treated as below threshold.

## Flaky handling

Re-run suspect tests a bounded number of times. If results differ across runs,
mark the test flaky and exclude it from a PASS — a flaky green is not a pass.
Report flaky tests for stabilization rather than passing them by luck.

## Gate policy (banking default)

- `ERROR` — the suite could not execute against the sandbox.
- `FAIL` — any unit test failed, any file's measured coverage is under the
  threshold (default 0.80), a file is unmeasurable, OR results are
  masked/uncertain (uncertain is a fail in regulated contexts).
- `PASS` — `failed` is 0 AND every file's measured coverage is at least the
  threshold, all on real runner evidence.

## Human verification layer

The verdict feeds a named human sign-off; this skill never auto-approves. Failures
route to `progressive-bug-hunter` for diagnosis — the executor does not fix code.

## Sources

- [[literature/capabilities/test-generation-capability|Test Generation Capability]]
- [[literature/agent-orchestration/autonomous-qa-agents|Autonomous QA agents]]
- [[literature/agent-orchestration/agentic-cicd|Agentic CI/CD]]
- Web: grafana.com (k6 thresholds as a runner-measured gate) · oneuptime.com
