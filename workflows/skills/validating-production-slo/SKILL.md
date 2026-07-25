---
name: validating-production-slo
version: 0.2.0
description: >
  Validate a live production release against its declared SLOs by querying live
  SLIs over a bake window, evaluating multi-window burn-rate, and emitting a
  promote, hold, or rollback recommendation with a Pass, Marginal, or Fail grade.
  Use when asked to validate production SLOs after a deploy, check live SLIs
  against thresholds, decide if prod is healthy enough to promote or roll back,
  or run post-release SLO validation. It consumes the SLI/SLO definitions rather
  than authoring them, and recommends/gates only — it never shifts traffic or
  changes alerts. Do NOT use to design SLIs, SLOs, dashboards, or alerts (the
  SLO-authoring workflow owns those). Do NOT use for the rollout-time
  canary-vs-baseline comparison (use analyzing-canary-rollout). Do NOT use for a
  firing incident (that is the incident-response process).
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: enhanced, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
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
- Do NOT use: to author SLIs/SLOs/dashboards (the SLO-authoring workflow owns
  them), for the rollout-time canary comparison (`analyzing-canary-rollout`), or
  for a firing incident (the incident-response process).

## Input contract

`schemas/input.json` is **ENFORCED** — the engine validates the ASSEMBLED payload
against it before this stage runs (fail-closed, exactly like output validation);
it documents the POST-adapter payload assembled at stage `prod-validate`. Required: `receipt_id` (picked from release-handoff — the S6
deployment receipt) and the engine-injected `idempotency_key`. Optional
engine-injected: `upstream_artifacts`, `loop_back_feedback`.

**Receipt resolution:** resolve `receipt_id` through the read-only deployment /
observability registry into the release's target, its **approved SLO policy**
(definitions + targets), and the telemetry series. Targets are consumed, never
re-derived. Missing approved policy or unavailable telemetry is `needs-input` —
never a fabricated verdict.

**Example (validates against schemas/input.json):**

```json
{
  "receipt_id": "RCPT-shoppilot-20260607-0001",
  "idempotency_key": "req-2026-07-12-shoppilot-001"
}
```

## Procedure

1. **Bind SLIs to SLOs** (`references/prod-slo-validation.md`): resolve the
   receipt into the approved SLO policy and its telemetry; do not re-derive
   targets. Every row records its `unit` and `comparison` (gte|lte|eq) so
   `target` and `observed` share an explicit scale. Entry: a resolved receipt.
   Exit: per-SLO series. The analysis cannot exceed the telemetry's resolution.
2. **Evaluate the error budget** with a multi-window, multi-burn-rate recipe
   (fast + slow windows) per SLO; classify within / approaching / breaching.
3. **Grade.** `Fail` if any SLO breaches its fast-burn threshold; `Marginal` if a
   slow burn is elevated or the window is short; `Pass` if all SLOs are within
   budget over the bake window.
4. **Map grade → recommendation:** Pass → `promote`; Marginal → `hold` (human
   gate); Fail → `rollback`.
5. **Emit** the verdict with the receipt binding and execution provenance
   (Output contract): `receipt_id` echoes the input unchanged, and `execution`
   records `runner` (a real observation window: runner + evidence_ref +
   report_sha256) vs `replay` (byte-verbatim reference corpus — **no telemetry
   was read**). Stop — a named human / controller executes; this skill does not
   shift traffic or change alerts.

## Output contract

Validate against `schemas/output.json`. Required: `verdict`
(promote|hold|rollback), `receipt_id` (echoed unchanged), `grade`
(Pass|Marginal|Fail), `per_slo[]` (≥1 row; each requires `name`, `target`,
`unit`, `comparison`, `observed`, `burn_rate`, `judgement`), `window` (the
normalized summary of EVERY fast/slow burn window actually evaluated — the
decision basis, not a display note), `execution`, and `audit_id`.

**Grade and verdict pair exactly** (schema-enforced): `Pass`↔`promote` (every row
`within_budget`) · `Marginal`↔`hold` · `Fail`↔`rollback` (at least one
`breaching` row). A `judgement` of `insufficient_data` requires a redacted
`reason` and null `observed`/`burn_rate`; partial or low-resolution telemetry
grades `Marginal`/`hold`, while a wholly missing SLI series is `needs-input`
with **no verdict artifact**.

`audit_id` (live): `UUIDv5(HOUSE_NS, "prod-validate:{idempotency_key}")`,
`HOUSE_NS = uuid5(NAMESPACE_URL, "https://squad-delivery/audit")` — distinct
from the engine's per-attempt audit id; corpus ids grandfathered.

**Example (validates against schemas/output.json):**

```json
{
  "verdict": "promote",
  "receipt_id": "RCPT-shoppilot-20260607-0001",
  "grade": "Pass",
  "per_slo": [
    {"name": "availability", "target": 99.9, "observed": 99.97, "burn_rate": 0.2, "unit": "percent", "comparison": "gte", "judgement": "within_budget"}
  ],
  "window": "30m + 6h multi-window burn-rate, post-deploy",
  "execution": {"mode": "replay", "target_source": "reference-corpus"},
  "audit_id": "a20f2de4-cda9-5762-92b5-b1ead082baf5"
}
```

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| PS-01 | unknown receipt / no approved SLO policy / SLO without a live SLI series | `needs-input`, NO verdict artifact | human-queue |
| PS-02 | fast-burn breach | `rollback` | controller rollback |
| PS-03 | elevated slow burn / short window | `hold` | human gate |
| PS-04 | telemetry gap / low resolution on SOME rows | `Marginal`/`hold` + `insufficient_data` rows carrying a redacted `reason` | human review |

## Constraints

- DO NOT author or alter SLIs/SLOs, dashboards, or alerts — consume them only.
- DO NOT shift traffic, promote, or roll back — recommend only.
- DO NOT return Pass on a window too short to be significant.
- DO NOT invent SLOs, thresholds, units, or observations absent from the
  approved policy and its telemetry — an unmeasurable row is `insufficient_data`
  with a reason, never a guessed number.
- DO NOT emit a grade/verdict pair the schema forbids (Pass must promote, Fail
  must roll back) — the verdict follows the evidence, never the reverse.

## References

| Need | Reference |
|------|-----------|
| Multi-window burn-rate, ACA, consume-not-derive, verdict policy, boundary | `references/prod-slo-validation.md` |
