# Smoke testing — critical-path probes, end-state checks, boundary

Grounded in the ResearchVault: post-deploy verification starts with a small,
fast **smoke / sanity** check on the golden critical paths before wider exposure —
it confirms the release is *up and reachable on what matters*, distinct from the
full QA suite, SLO burn-rate validation, and canary analysis. The skill consumes
the probe set rather than authoring it. See
`[[literature/deployment-delivery/progressive-delivery]]` and
`[[literature/deployment-delivery/blue-green-deployment]]`.

## Bind the probes

Take the supplied critical-path probes as the golden set. This skill does not
invent paths; it runs the declared probes against the live release. Keep it
small and fast — smoke is a sanity gate, not coverage.

## End-state, not HTTP 200

For each probe, verify the observed **end-state** matches expectation (a real
journey outcome), not merely a 2xx status. A 200 with the wrong body is red.
Capture `latency_ms` from the probe runner alongside the green/red result.

## Results from the runner

Read `green` and `latency_ms` per probe from the probe runner — never assert a
green the runner did not produce. If no probe could run against the target, that
is an `ERROR`, not a pass.

## Gate policy (banking default)

- `ERROR` — the probe set could not execute against the live target.
- `FAIL` — any probe red, OR the run was too sparse to be a meaningful sanity
  check (uncertain → fail in regulated contexts).
- `PASS` — every probe green on real runner evidence, with `all_green` true.

## Boundary

Reports only — a release controller or named human acts on a red gate (hold /
roll back); the skill never shifts traffic or changes config. The full roster is
`executing-qa-test-suite`; post-deploy SLO burn-rate is `validating-production-
slo`; the rollout-time canary-vs-baseline comparison is
`analyzing-canary-rollout`.

## Sources

Vault: [[literature/deployment-delivery/progressive-delivery|Progressive delivery]] · [[literature/deployment-delivery/blue-green-deployment|Blue-green deployment]] · [[literature/observability-reliability/slo-sli-design|SLO/SLI design]]

Web: oneuptime.com (post-deploy smoke / synthetic probes) · grafana.com (k6 probe scripting)
