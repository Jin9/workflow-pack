# Production SLO validation — burn-rate, ACA, boundary

Grounded in the ResearchVault: automated canary/post-deploy analysis queries
**live SLIs vs declarative thresholds** over a bake window and emits
Pass/Marginal/Fail → promote/hold/rollback, and the analysis layer **consumes
rather than re-derives** the SLI/SLO definitions ("the analysis layer cannot
exceed the resolution of the telemetry it queries"); the multi-window
multi-burn-rate alert recipe is the standard error-budget gate. See
`[[literature/deployment-delivery/canary-deployment]]` and
`[[literature/observability-reliability/slo-sli-design]]`.

## Bind, don't re-derive

Use the `slo_defs` exactly as authored by `observability-design`. This skill does
not invent SLIs, targets, or alert rules; it measures against them.

## Multi-window burn-rate

For each SLO, compute error-budget burn over a fast window and a slow window
(e.g. 1h and 6h). A fast-burn breach is urgent (rollback); a slow-burn elevation
is a hold. Respect the SLI's good/valid ratio shape (availability, latency,
freshness, durability).

## Verdict policy

- **Fail → rollback** — any SLO breaches its fast-burn threshold.
- **Marginal → hold** — elevated slow burn, a window too short to be significant,
  or a telemetry gap. Route to a human gate.
- **Pass → promote** — every SLO within budget across the bake window.

## Boundary

Recommends/gates only — a release controller (Argo Rollouts AnalysisTemplate,
Flagger MetricTemplate, OpenSLO criteria) or a human executes promote/hold/
rollback. SLO authoring is `observability-design`; the rollout-time
canary-vs-baseline comparison is `analyzing-canary-rollout`; a firing incident is
`incident-response`.
