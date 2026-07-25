# Integration / SIT execution — runner integration, teardown, defect capture, gate

Grounded in the ResearchVault: system integration testing runs against a wired-up
SIT environment, and the environment strategy (SIT/UAT/PRD) requires that test
environments are stood up and torn down cleanly so a run cannot leak state into
the next. The runner is the source of truth; the agent orchestrates and reports.

## Stage and run

Load `test_roster` (or derive runs from `artifacts`) and stand up the sandbox
`target_env` with its service dependencies. Run the integration suite through the
CI/test runner. Record per-flow pass/fail with a concrete reproduction command,
verifying observed end-state — never an HTTP 200 and never an LLM claim.

## Teardown verification

After the run, confirm the sandbox tears down cleanly: no leaked fixtures, open
connections, or residual data. Record `teardown_ok`. A dirty teardown is an
exception — it does not pass — because leaked state corrupts later runs and hides
defects.

## Defect capture

Collect integration defects with reproduction evidence and classify by severity.
Surface non-deterministic flows rather than passing them by luck.

## Gate policy (banking default)

- `ERROR` — the suite could not execute against the sandbox.
- `FAIL` — any integration flow failed, OR results are masked/uncertain
  (uncertain is a fail in regulated contexts).
- `FAIL` + `teardown_ok=false` — a dirty teardown escalates as an exception even
  if all flows passed.
- `PASS` — `failed` is 0 AND `teardown_ok` is true, all on real runner evidence.

## Human verification layer

The verdict feeds a named human sign-off; this skill never auto-approves. Failures
route to `progressive-bug-hunter` for diagnosis — the executor does not fix code.

## Sources

- [[literature/platform-devops/environment-strategy-sit-uat-prd|Environment strategy: SIT/UAT/PRD]]
- [[literature/agent-orchestration/autonomous-qa-agents|Autonomous QA agents]]
- [[literature/agent-orchestration/agentic-cicd|Agentic CI/CD]]
- Web: oneuptime.com · grafana.com (k6 thresholds as a runner-measured gate)
