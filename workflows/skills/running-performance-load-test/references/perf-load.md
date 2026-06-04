# Performance load testing — runner thresholds, budget binding, boundary

Grounded in the ResearchVault: a pre-prod load test drives a declared load
profile against a staging/UAT target and judges it against a **declared
performance budget**, consuming the budget rather than re-deriving it ("the
analysis cannot exceed the resolution of the telemetry it queries"). A load
runner encodes each budget line as a pass/fail **threshold** that fails the run
(and CI) on breach, so the gate is mechanical, not asserted. See
`[[literature/observability-reliability/slo-sli-design]]` and
`[[literature/platform-devops/platform-reliability-scorecard]]`.

## Bind the budget, don't re-derive it

Use the `budget` thresholds exactly as authored by `observability-design`. This
skill does not invent latency targets, error budgets, or scenarios; it measures
against them. Typical budgets: p95 under 300-500 ms and error rate under 1% for
an interactive API; tighter for a payment path.

## Runner thresholds are the gate

In a runner such as k6, each budget line is a `threshold` (e.g. `http_req_duration:
p(95)<500`, `http_req_failed: rate<0.01`). A failed threshold makes the runner
**exit non-zero**, which fails CI. The verdict is read from the runner summary —
never from an agent claim about how the run "looked". If the run cannot complete
or the summary is missing, that is an `ERROR`, not a pass.

## Metric reading

Read `p95`, `p99`, `error_rate`, and `throughput` from the runner report on the
staging/UAT target. A breach is recorded when observed is outside budget (p95 at
or above target, error_rate at or above budget). Collect breaches into
`breaches[]` with observed-vs-budget so a human can see the gap.

## Gate policy (banking default)

- `ERROR` — the load run could not execute against the target, or metrics are
  unreadable.
- `FAIL` — any threshold breaches, OR the window/sample is too short to be
  statistically meaningful (uncertain → fail in regulated contexts).
- `PASS` — every thresholded metric is within budget over a sufficient window,
  with `within_budget` true.

## Boundary

Recommends/gates only — a controller or a named human decides promotion. The
skill runs in a sandbox against a non-production target; it never shifts traffic,
scales, or changes config. Budget/SLO authoring is `observability-design`;
post-deploy live SLO validation is `validating-production-slo`; the rollout-time
canary-vs-baseline comparison is `analyzing-canary-rollout`.

## Sources

Vault: [[literature/observability-reliability/slo-sli-design|SLO/SLI design]] · [[literature/platform-devops/platform-reliability-scorecard|Platform reliability scorecard]] · [[literature/deployment-delivery/progressive-delivery|Progressive delivery]]

Web: grafana.com (k6 thresholds are pass/fail criteria that fail CI on breach) · oneuptime.com
