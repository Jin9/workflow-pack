---
name: running-performance-load-test
version: 0.1.0
description: >
  Drive a pre-prod performance/load test against a staging or UAT target and
  emit a budget-backed PASS, FAIL, or ERROR gate from real runner metrics — p95,
  p99, error rate, and throughput measured by a load runner, never asserted by an
  agent. Use when asked to run a load or performance test, drive virtual users
  against staging or UAT, check p95 or p99 latency and error rate against a
  budget, or produce the pre-prod performance gate. Runs in a sandbox via a load
  runner and recommends or gates only; it never shifts traffic or changes config.
  Do NOT use to design SLIs or SLOs or latency budgets (use observability-design).
  Do NOT use to validate live production SLOs after a deploy (use
  validating-production-slo). Do NOT use for canary-vs-baseline rollout analysis
  (use analyzing-canary-rollout) or to tune or fix the system under test.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: detailed, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
expected_duration_p95_seconds: 900
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Running a Performance Load Test

## Purpose

Exercise a release in a **pre-prod environment** (staging / UAT) under a declared
load profile and decide whether its measured latency and error behaviour stay
inside a declared budget — emitting a results-backed PASS / FAIL / ERROR gate.
Metrics come from a real load runner (k6, Gatling, Locust) where each threshold
is a pass/fail criterion; the skill consumes the budget rather than authoring it,
and recommends or gates only. It never shifts traffic, scales, or changes config.

## When to use this skill

- Use when: a build is deployed to staging/UAT and must be load-tested against a
  declared budget before promotion.
- Use when: asked to "run the load test", "check p95/p99 under load", or "produce
  the pre-prod performance gate with evidence".
- Do NOT use: to design SLIs/SLOs/budgets (`observability-design`), to validate
  live production SLOs post-deploy (`validating-production-slo`), for the
  canary-vs-baseline comparison (`analyzing-canary-rollout`), or to tune the SUT.

## Input contract

Validate against `schemas/input.json`. Required: `load_profile` (VUs / duration /
scenario), `budget` (p95, p99, error-rate targets), `target_env` (the staging/UAT
target), `idempotency_key`. Optional: `tier`. Stop with `needs-input` if the
profile, the budget, or a reachable non-production target is missing.

## Procedure

1. **Bind the budget, don't re-derive it** (`references/perf-load.md`): take the
   `budget` thresholds as authored; configure them as runner thresholds (a failed
   threshold exits the runner non-zero). Entry: profile + budget + target. Exit:
   a runnable load spec.
2. **Run the load profile** against `target_env` via the load runner, capturing
   the run report. Metrics are read from the runner summary — **never an
   LLM-asserted number**. The analysis cannot exceed the runner's resolution.
3. **Read measured metrics** from the report: `p95`, `p99`, `error_rate`,
   `throughput`. If the run could not complete or the report is missing, that is
   an `ERROR`, not a pass.
4. **Evaluate against the budget.** For each thresholded metric, mark a breach
   when observed is outside budget (e.g. p95 at or above target, error_rate at or
   above budget). Collect breaches into `breaches[]`.
5. **Apply the gate:** `ERROR` if the run could not execute or metrics are
   unreadable; `FAIL` if any threshold breaches OR the window/sample is too short
   to be significant (banking default: uncertain is not a clean pass); else
   `PASS` with `within_budget` true.
6. **Emit** the verdict (Output contract). Stop — a controller or human decides
   promotion; this skill does not shift traffic or change config.

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR),
`metrics{p95,p99,error_rate,throughput}`, `within_budget` (bool),
`breaches[]{metric,observed,budget}`, and `audit_id`.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| PL-01 | missing profile/budget/target | no verdict | needs-input → human-queue |
| PL-02 | load run could not execute / report unreadable | `ERROR` | human-queue |
| PL-03 | a threshold breaches budget | `FAIL` + breaches[] | route to fixer / human review |
| PL-04 | window or sample too short to be significant | `FAIL` + note | human review |

## Constraints

- DO NOT author or alter budgets, SLIs, or SLOs — consume them only.
- DO NOT emit a pass not backed by runner metrics; uncertain → fail (banking).
- DO NOT run against production, shift traffic, scale, or change config.
- DO NOT auto-approve promotion; the gate feeds a named human decision.
- DO NOT echo real PII in evidence or logs; redact as [PII:REDACTED:CLASS=...].

## References

| Need | Reference |
|------|-----------|
| Runner thresholds, budget binding, metric reading, gate policy, boundary | `references/perf-load.md` |
