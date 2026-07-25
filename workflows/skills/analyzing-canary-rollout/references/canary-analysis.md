# Canary analysis — multi-window non-inferiority, sample adequacy, boundary

Grounded in the ResearchVault: progressive/canary delivery automates a
**promote-or-rollback** decision from a statistical comparison of the canary
against a baseline over **multiple windows** — Kayenta (Spinnaker) and Argo
Rollouts AnalysisTemplates score each metric against a non-inferiority margin and
gate the rollout, never trusting a single point. The skill consumes the metric
series rather than authoring the rollout. See
`[[literature/deployment-delivery/canary-deployment]]` and
`[[literature/deployment-delivery/progressive-delivery]]`.

## Pair the series

Match each canary metric to its baseline counterpart over the requested windows.
Compare like-for-like under the same conditions (same traffic shape) so the only
difference is the new version. The analysis cannot exceed the data's resolution.

## Multi-window non-inferiority

For each metric and window, run a statistical test (e.g. Mann-Whitney with a
non-inferiority margin) asking *is the canary no worse than the baseline by more
than the margin?* Classify `pass` / `marginal` / `fail`. A single good window is
not enough — the decision is aggregated across windows (default 3). Judgements
come from the test, not an agent's read of the numbers.

## Sample adequacy gate

If a metric's sample is too small, or a window too short to be statistically
significant, the evidence is **weak**. Set `sample_adequate` false. Weak evidence
can never support a promotion — it forces `hold`.

## Threshold aggregation

Count `windows_passed`. Promotion requires success in at least
`success_threshold` (default 0.95) of metric-windows across all windows AND an
adequate sample. Anything less is a `hold`.

## Verdict policy (banking default)

- `rollback` — a metric clearly regresses (fails non-inferiority).
- `hold` — weak evidence: `sample_adequate` false, too few windows, or success
  below threshold. Route to a human gate. Never promote on weak evidence.
- `promote` — success at or above the threshold over all windows with an adequate
  sample.

## Boundary

Recommends only — a release controller (Argo Rollouts, Flagger) or a named human
shifts traffic; this skill never shifts, scales, or rolls back. Post-deploy SLO
burn-rate validation is `validating-production-slo`; rollout config authoring is
out of scope.

## Sources

Vault: [[literature/deployment-delivery/canary-deployment|Canary deployment]] · [[literature/deployment-delivery/progressive-delivery|Progressive delivery]] · [[literature/observability-reliability/slo-sli-design|SLO/SLI design]]

Web: argo-rollouts.readthedocs.io (Kayenta-style multi-window canary analysis, Mann-Whitney non-inferiority, automated promote-or-rollback) · grafana.com (metric queries)
