---
name: running-performance-load-test
version: 0.2.1
description: >
  Drive a pre-prod performance/load test against a staging or UAT target and
  emit a budget-backed PASS, FAIL, or ERROR gate from real runner metrics — p95,
  p99, error rate, and throughput measured by a load runner, never asserted by an
  agent. Use when asked to run a load or performance test, drive virtual users
  against staging or UAT, check p95 or p99 latency and error rate against a
  budget, or produce the pre-prod performance gate. Runs in a sandbox via a load
  runner and recommends or gates only; it never shifts traffic or changes config.
  Do NOT use to design SLIs or SLOs or latency budgets (the Tech-Lead design owns
  those via designing-tech-lead-handoff). Do NOT use to validate live production SLOs after a deploy (use
  validating-production-slo). Do NOT use for canary-vs-baseline rollout analysis
  (use analyzing-canary-rollout) or to tune or fix the system under test.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: detailed, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
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
- Do NOT use: to design SLIs/SLOs/budgets (`designing-tech-lead-handoff` owns SLI/SLO design), to validate
  live production SLOs post-deploy (`validating-production-slo`), for the
  canary-vs-baseline comparison (`analyzing-canary-rollout`), or to tune the SUT.

## Input contract

`schemas/input.json` is **ENFORCED** — the engine validates the ASSEMBLED payload
against it before this stage runs (fail-closed, exactly like output validation);
it documents the POST-adapter payload assembled at stage `perf-load-test`. Required: `totals` and `verdict` picked from `qa-validate`
(**the QA verdict — a prerequisite, never load evidence and never this stage's
verdict**) and the engine-injected `idempotency_key`. Optional:
`performance_test_context` from the workflow input — the runner context
(`load_profile`, `budget` with upper-bound p95/p99/error-rate thresholds and the
lower-bound `throughput_min_rps`, `target_env`, `target_kind: staging|uat`,
non-secret `runner_profile_ref`). Live runner mode without a context is
`needs-input`; replay needs none. Optional engine-injected: `upstream_artifacts`,
`loop_back_feedback`.

**Example (validates against schemas/input.json):**

```json
{
  "totals": {"planned": 24, "executed": 24, "passed": 24, "failed": 0, "blocked": 0},
  "verdict": "PASS",
  "performance_test_context": {"load_profile": {"vus": 50, "duration": "10m"}, "budget": {"p95_ms": 800, "error_rate_max": 0.01, "throughput_min_rps": 40}, "target_env": "staging", "target_kind": "staging"},
  "idempotency_key": "req-2026-07-12-shoppilot-001"
}
```

## Procedure

1. **Bind the budget, don't re-derive it** (`references/perf-load.md`): take the
   `performance_test_context.budget` thresholds as authored; configure them as
   runner thresholds (a failed threshold exits the runner non-zero). Semantics:
   p95/p99/error-rate are upper bounds (observed >= threshold breaches);
   throughput is a lower bound (observed < threshold breaches). Entry: context +
   target. Exit: a runnable load spec.
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
   unreadable; `FAIL` if any threshold breaches OR `sample_adequate` is false
   (window/sample too short — banking default: uncertain is not a clean pass,
   and inadequacy is recorded in `limitations[]`); else `PASS` with
   `within_budget` true and `sample_adequate` true.
6. **Emit** the verdict with execution provenance (Output contract): `execution`
   records `runner` (a real run, with runner/evidence_ref/report_sha256) vs
   `replay` (byte-verbatim reference corpus — no load ran). Stop — a controller
   or human decides promotion; this skill does not shift traffic or change
   config.

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR), `metrics`
(`p95` + `error_rate` required numeric on PASS/FAIL; `p99`/`throughput` optional
runner-supplied extras — never fabricated), `within_budget`, `breaches[]`
(non-null numeric `observed`/`budget`), `sample_adequate` (+ `limitations[]`
required when false), `execution` (provenance), and `audit_id`. Conditionals:
PASS ⇒ within_budget true + zero breaches + adequate sample; FAIL ⇒
within_budget false + (a breach ∨ inadequate sample); ERROR ⇒ within_budget
false + non-empty `errors[]`.

`audit_id` (live): `UUIDv5(HOUSE_NS, "perf-load-test:{idempotency_key}")`,
`HOUSE_NS = uuid5(NAMESPACE_URL, "https://squad-delivery/audit")` — distinct
from the engine's per-attempt audit id.

**Example (validates against schemas/output.json):**

```json
{
  "verdict": "PASS",
  "metrics": {"p95": 540, "error_rate": 0.001},
  "within_budget": true,
  "breaches": [],
  "sample_adequate": true,
  "execution": {"mode": "replay", "target_source": "reference-corpus"},
  "audit_id": "75470a1b-97c3-56c5-832c-f4e00b7a245a"
}
```

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| PL-01 | live runner mode with no performance_test_context | `needs-input` (no fabricated run) | human supplies the context |
| PL-02 | load run could not execute / report unreadable | `ERROR` | human-queue |
| PL-03 | a threshold breaches budget | `FAIL` + breaches[] | route to fixer / human review |
| PL-04 | window or sample too short to be significant | `FAIL` + sample_adequate false + limitations[] | human review |

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
