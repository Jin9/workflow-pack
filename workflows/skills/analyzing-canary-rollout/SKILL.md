---
name: analyzing-canary-rollout
version: 0.1.0
description: >
  Compare a canary against its baseline across multiple windows with a statistical
  non-inferiority test and emit a promote, hold, or rollback recommendation from
  real metric series — never an agent assertion, and never weak-evidence promotion.
  Use when asked to analyze a canary rollout, compare canary vs baseline metrics,
  decide promote or hold or rollback during a progressive deploy, or run
  Kayenta-style or Argo-Rollouts-style canary analysis. Runs in a sandbox over
  supplied metric series and recommends only; it never shifts traffic itself. An
  inadequate sample or a window too short to be significant yields hold, never
  promote. Do NOT use for post-deploy SLO burn-rate validation (use
  validating-production-slo). Do NOT use to actually shift, scale, or roll back
  traffic, or to author the rollout config.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: detailed, pii_handling: none, tier_default: T1, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
expected_duration_p95_seconds: 300
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Analyzing a Canary Rollout

## Purpose

Judge whether a **canary** is non-inferior to its **baseline** during a
progressive deploy by comparing their metric series over **multiple windows** with
a statistical test (Kayenta / Argo Rollouts style), and emit a promote / hold /
rollback recommendation. The judgement is read from real series, not asserted; and
weak evidence (inadequate sample, too few windows) yields `hold`, never `promote`.
It recommends only — it never shifts, scales, or rolls back traffic itself.

## When to use this skill

- Use when: a progressive/canary deploy is in flight and the canary must be
  statistically compared against baseline to decide promote/hold/rollback.
- Use when: asked to "analyze the canary", "compare canary vs baseline", or "run
  Kayenta/Argo-Rollouts-style canary analysis".
- Do NOT use: for post-deploy SLO burn-rate validation (`validating-production-
  slo`), to shift/scale/roll back traffic, or to author the rollout config.

## Input contract

Validate against `schemas/input.json`. Required: `canary_metrics`,
`baseline_metrics`, `idempotency_key`. Optional: `windows` (default 3),
`success_threshold` (default 0.95), `tier`. Stop with `needs-input` if either
metric set is missing or has no comparable series.

## Procedure

1. **Pair the series** (`references/canary-analysis.md`): match each canary metric
   to its baseline counterpart over the requested `windows`. Entry: both metric
   sets. Exit: paired per-metric series. The analysis cannot exceed the data's
   resolution.
2. **Test non-inferiority per metric and window** using a statistical comparison
   (e.g. Mann-Whitney with a non-inferiority margin), classifying each metric
   `pass` / `marginal` / `fail`. Judgements come from the test, **never an
   LLM-asserted call**.
3. **Check sample adequacy.** If a metric's sample is too small or a window too
   short to be significant, mark `sample_adequate` false — weak evidence cannot
   support a promotion.
4. **Aggregate windows.** Count `windows_passed`; require success in at least
   `success_threshold` (default 0.95) of metric-windows across all `windows`
   (default 3) AND `sample_adequate` true.
5. **Decide the verdict:** `rollback` if any metric clearly regresses (fails the
   non-inferiority test); `hold` if evidence is weak — `sample_adequate` false,
   too few windows, or success below threshold (banking default: never promote on
   weak evidence); `promote` only when success is at least the threshold over all
   windows AND the sample is adequate.
6. **Emit** the verdict (Output contract). Stop — a release controller or human
   acts on it; this skill does not shift traffic.

## Output contract

Validate against `schemas/output.json`: `verdict` (promote|hold|rollback),
`per_metric[]{name,baseline,canary,judgement}`, `sample_adequate` (bool),
`windows_passed` (integer), and `audit_id`.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| CR-01 | missing/incomparable metric sets | no verdict | needs-input → human-queue |
| CR-02 | a metric clearly regresses | `rollback` | controller rollback |
| CR-03 | inadequate sample / too few windows / below threshold | `hold` | human gate |
| CR-04 | success at/above threshold over all windows + adequate sample | `promote` | controller promote |

## Constraints

- DO NOT promote on weak evidence — inadequate sample or short windows → `hold`.
- DO NOT emit a judgement not backed by the statistical test; uncertain → hold.
- DO NOT shift, scale, or roll back traffic — recommend only.
- DO NOT author or alter the rollout config or its metric definitions.
- DO NOT echo real PII in metric labels or evidence; redact as
  [PII:REDACTED:CLASS=...].

## References

| Need | Reference |
|------|-----------|
| Multi-window non-inferiority, sample adequacy, threshold aggregation, verdict policy, boundary | `references/canary-analysis.md` |
