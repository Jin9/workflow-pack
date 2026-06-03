---
name: validating-production-slo
version: 0.1.0
description: >
  Validate a live production release against its declared SLOs by querying live
  SLIs over a bake window, evaluating multi-window burn-rate, and emitting a
  promote, hold, or rollback recommendation with a Pass, Marginal, or Fail grade.
  Use when asked to validate production SLOs after a deploy, check live SLIs
  against thresholds, decide if prod is healthy enough to promote or roll back,
  or run post-release SLO validation. It consumes the SLI/SLO definitions rather
  than authoring them, and recommends/gates only — it never shifts traffic or
  changes alerts. Do NOT use to design SLIs/SLOs, dashboards, or alerts (use
  observability-design). Do NOT use for the rollout-time canary-vs-baseline
  comparison (use analyzing-canary-rollout). Do NOT use for a firing incident
  (use incident-response).
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: enhanced, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 180
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Validating Production SLOs

## Purpose

Decide whether a live release is healthy against its **declared SLOs** by
measuring live SLIs over a bake window and evaluating multi-window burn-rate,
then recommend promote / hold / rollback. This is the active post-deploy
validation loop (S7) that `observability-design` does not own (it stops at the
design artifact + alert recipe). Consumes SLO definitions; recommends/gates only.

## When to use this skill

- Use when: a release is live and you need a post-deploy SLO verdict over a bake
  window.
- Use when: asked to "validate prod SLOs", "check burn-rate", or "promote/hold/
  rollback on live signals".
- Do NOT use: to author SLIs/SLOs/dashboards (`observability-design`), for the
  rollout-time canary comparison (`analyzing-canary-rollout`), or for a firing
  incident (`incident-response`).

## Input contract

Validate against `schemas/input.json`. Required: `slo_defs` (the declared
SLIs/SLOs + targets), `live_metrics` (windowed observations), `idempotency_key`.
Optional: `bake_window`, `tier`. Stop with `needs-input` if an SLO has no live
SLI series.

## Procedure

1. **Bind SLIs to SLOs** (`references/prod-slo-validation.md`): use the supplied
   definitions; do not re-derive targets. Entry: defs + metrics. Exit: per-SLO
   series. The analysis cannot exceed the telemetry's resolution.
2. **Evaluate the error budget** with a multi-window, multi-burn-rate recipe
   (fast + slow windows) per SLO; classify within / approaching / breaching.
3. **Grade.** `Fail` if any SLO breaches its fast-burn threshold; `Marginal` if a
   slow burn is elevated or the window is short; `Pass` if all SLOs are within
   budget over the bake window.
4. **Map grade → recommendation:** Pass → `promote`; Marginal → `hold` (human
   gate); Fail → `rollback`.
5. **Emit** the verdict (Output contract). Stop — a controller/human executes;
   this skill does not shift traffic or change alerts.

## Output contract

Validate against `schemas/output.json`: `verdict` (promote|hold|rollback),
`grade` (Pass|Marginal|Fail), `per_slo[]{name,target,observed,burn_rate,judgement}`,
`window`, and `audit_id`.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| PS-01 | SLO without live SLI | no verdict | needs-input → human-queue |
| PS-02 | fast-burn breach | `rollback` | controller rollback |
| PS-03 | elevated slow burn / short window | `hold` | human gate |
| PS-04 | telemetry gap / low resolution | `hold` + note | human review |

## Constraints

- DO NOT author or alter SLIs/SLOs, dashboards, or alerts — consume them only.
- DO NOT shift traffic, promote, or roll back — recommend only.
- DO NOT return Pass on a window too short to be significant.
- DO NOT invent SLOs or thresholds absent from `slo_defs`.

## References

| Need | Reference |
|------|-----------|
| Multi-window burn-rate, ACA, consume-not-derive, verdict policy, boundary | `references/prod-slo-validation.md` |
