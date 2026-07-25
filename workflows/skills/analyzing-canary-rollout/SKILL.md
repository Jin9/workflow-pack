---
name: analyzing-canary-rollout
version: 0.2.0
description: Compare a canary against its baseline across multiple windows with a statistical non-inferiority test and emit a promote, hold, or rollback recommendation from real metric series — never an agent assertion, and never weak-evidence promotion. Use when asked to analyze a canary rollout, compare canary vs baseline metrics, decide promote or hold or rollback during a progressive deploy, or run Kayenta-style or Argo-Rollouts-style canary analysis. Resolves the deploy receipt to live rollout telemetry through the read-only deployment registry, runs in a sandbox, and recommends only; it never shifts traffic itself. An inadequate sample or a window too short to be significant yields hold, never promote. Do NOT use for post-deploy SLO burn-rate validation (use validating-production-slo). Do NOT use to actually shift, scale, or roll back traffic, or to author the rollout config.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: detailed, pii_handling: none, tier_default: T1, tier_adaptable: [T1, T2, T3]}
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

ADVISORY — documents the assembled stage input; the engine validates workflow input
and stage OUTPUTS only (engine/validation.py). Validate against `schemas/input.json`.
Required: `receipt_id` (the release-handoff receipt), `idempotency_key`
(engine-injected). Optional engine-injected: `upstream_artifacts`,
`loop_back_feedback`. Analysis parameters are procedural defaults, not inputs:
`windows` = 3, `success_threshold` = 0.95. Stop with `needs-input` if the receipt
is unknown, no rollout is associated with it, or approved metric definitions are
missing.

**Example (validates against schemas/input.json):**
```json
{
  "receipt_id": "RCPT-shoppilot-20260607-0001",
  "idempotency_key": "3f6c0b2e-7a41-4d9b-9c2a-8e5b1f0a4d22",
  "upstream_artifacts": { "release-handoff": "../S6-deploy/handoff-receipt.json" }
}
```

## Output contract

Validate against `schemas/output.json`: `verdict` (promote|hold|rollback),
`per_metric[]{name,judgement}` (optional `baseline`/`canary` summaries and
`test_evidence` — live runner-backed analyses SHOULD emit them), `sample_adequate`
(bool), `windows_passed` (integer; the optional `analysis` roll-up resolves its
denominators), and `audit_id`. Schema-enforced invariants: an inadequate sample or
a failing metric can never coexist with `promote`; `rollback` requires at least one
failing metric. `audit_id` is producer-stamped and deterministic —
UUIDv5(HOUSE_NS, "canary-analysis:{idempotency_key}") with HOUSE_NS =
uuid5(NAMESPACE_URL, "https://squad-delivery/audit") — independent of optional
inputs and distinct from the engine's per-attempt execution audit id.

**Example (validates against schemas/output.json):**
```json
{
  "verdict": "promote",
  "per_metric": [
    { "name": "error-rate", "judgement": "pass" },
    { "name": "p95-latency", "judgement": "pass" }
  ],
  "sample_adequate": true,
  "windows_passed": 3,
  "audit_id": "dd6bb7ca-df1e-5a06-87d4-6c15383c8136"
}
```

## Procedure

1. **Resolve the receipt** through the read-only deployment/rollout registry:
   verify the release is `handed_off`, identify the canary and baseline cohorts,
   bind the approved metric definitions, and retrieve three aligned comparison
   windows. Unknown receipt, absent rollout, or missing metric definitions →
   `needs-input`; partial or underpowered telemetry → `hold`.
2. **Pair the series** (`references/canary-analysis.md`): match each canary metric
   to its baseline counterpart over the `windows` (default 3). Entry: resolved
   telemetry. Exit: paired per-metric series. The analysis cannot exceed the
   data's resolution.
3. **Test non-inferiority per metric and window** using a statistical comparison
   (e.g. Mann-Whitney with a non-inferiority margin), classifying each metric
   `pass` / `marginal` / `fail`. Judgements come from the test, **never an
   LLM-asserted call**. Record `test_evidence` when the runner exports it.
4. **Check sample adequacy.** If a metric's sample is too small or a window too
   short to be significant, mark `sample_adequate` false — weak evidence cannot
   support a promotion.
5. **Aggregate windows.** Count `windows_passed`; require success in at least
   `success_threshold` (default 0.95) of metric-windows across all windows AND
   `sample_adequate` true. Emit the `analysis` roll-up so the numerator has its
   denominators.
6. **Decide the verdict:** `rollback` if any metric clearly regresses (fails the
   non-inferiority test); `hold` if evidence is weak — `sample_adequate` false,
   too few windows, or success below threshold (banking default: never promote on
   weak evidence); `promote` only when success is at least the threshold over all
   windows AND the sample is adequate.
7. **Emit** the verdict (Output contract). Stop — a release controller or human
   acts on it; this skill does not shift traffic.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| CR-01 | unknown receipt / no rollout / missing metric definitions | no verdict | needs-input → human-queue |
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
