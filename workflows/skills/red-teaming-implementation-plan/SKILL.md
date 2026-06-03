---
name: red-teaming-implementation-plan
version: 0.1.0
description: >
  Adversarially red-team an implementation plan or Tech-Lead design BEFORE any
  code is written, then issue a machine-readable PROCEED, REVISE, or BLOCK
  verdict with severity-ranked findings. Use when asked to red-team an
  implementation plan, adversarially review a plan before building, check
  whether a plan is safe to fan out to per-component work, or critique a
  Tech-Lead design before code. Runs as a critic separate from the plan's
  author (a generator is never its own critic), states a steelman of the plan
  first, and applies reviewer-bias mitigation. Do NOT use to review a code diff
  or pull request (use the built-in code review or pr-design-review). Do NOT use
  for deep security threat-modeling (use reviewing-software-security). Do NOT use
  to author or revise the plan itself.
stage_type: review
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: enhanced, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 120
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Red-Teaming the Implementation Plan

## Purpose

Stress-test a Tech-Lead design / implementation plan against the requirements it
must satisfy and against the ways plans fail, **before** the expensive fan-out to
per-component implementation. Emit a single, severity-ranked, machine-readable
verdict that a workflow engine gates on. Read-only: this skill critiques a plan;
it never writes the plan, the code, or the fix.

## When to use this skill

- Use when: a plan / TL-design artifact has been produced and the next step would
  be to fan out into implementation, and you want an adversarial gate first.
- Use when: asked to "red-team", "adversarially review", or "stress-test" a plan,
  or to decide whether a plan is "safe to fan out".
- Do NOT use: to review emitted code, a diff, or a PR (that is the built-in code
  review / `pr-design-review`).
- Do NOT use: for full security threat-modeling (hand off to `reviewing-software-security`).
- Do NOT use: to write or revise the plan (the planning/design skill owns that).

## Input contract

Validate against `schemas/input.json`. Required: `plan` (the TL design /
implementation plan), `idempotency_key`. Optional: `ba_brief` (the epic + stories
the plan must satisfy — needed for criteria-coverage findings), `author_model`
(the model that authored the plan), `tier` (T1|T2|T3, default T2). Stop with a
`needs-input` note if `plan` is empty or unparseable.

**Heterogeneity rule:** the critic must not be the same model instance that
authored the plan. If `author_model` equals the running model, record it in
`bias_checks` and lower `confidence`; a stronger or different reviewer is
preferred (see `references/red-team-lenses.md`).

## Procedure

1. **Steelman first.** Before looking for flaws, write the strongest honest case
   FOR the plan (`steelman`). This counters reviewer self-preference and
   reject-by-default bias. Entry: a parsed plan. Exit: one paragraph.
2. **Sweep the attack lenses.** Walk every lens in
   `references/red-team-lenses.md` (requirements, architecture, contract, data,
   security-handoff, operability, cost, testability). For each real weakness emit
   one finding `{id: RT-n, severity, category, claim, evidence, recommendation}`.
   Tie each finding to evidence in the plan or a missing requirement from
   `ba_brief`; do not flag style or speculation.
3. **Apply bias mitigation.** Re-read each finding and drop or downgrade any that
   are hallucinated, position/verbosity-driven, or unfalsifiable. Record which
   mitigations you applied in `bias_checks`.
4. **Decide the verdict** per the policy in `references/red-team-lenses.md`:
   **BLOCK** if any `high` finding sits on a required path; **REVISE** if there
   are `medium` findings but no blocking `high`; **PROCEED** if only `low`
   findings remain. Set `confidence` (0–1); lower it for thin evidence or a
   non-heterogeneous reviewer.
5. **Emit** the structured verdict (see Output contract). Stop. Routing of REVISE
   back to the planner / BLOCK to a human is the engine's job, not this skill's.

## Output contract

Validate against `schemas/output.json`: `verdict` (PROCEED|REVISE|BLOCK),
`findings[]`, `steelman`, `confidence`, `bias_checks[]`, and `audit_id` (carried
for the pipeline handoff trace). Findings carry stable `RT-n` ids so a later run
can diff them.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| RTP-01 | `plan` empty / unparseable | no verdict | needs-input → human-queue |
| RTP-02 | reviewer == author_model | verdict + lowered confidence | note in bias_checks |
| RTP-03 | `ba_brief` absent | verdict without criteria-coverage findings | flag the coverage gap |
| RTP-04 | cannot reach a defensible verdict | `fallback` | human-queue |

## Constraints

- DO NOT author or edit the plan, the code, or the fix — critique only.
- DO NOT approve a plan the same agent authored without recording the conflict.
- DO NOT invent file paths, requirement ids, or CWE references; cite only what is
  present in `plan` / `ba_brief`.
- DO NOT escalate style/taste to a blocking finding.

## References

| Need | Reference |
|------|-----------|
| Attack lenses, steelman rule, bias mitigation, verdict policy | `references/red-team-lenses.md` |
