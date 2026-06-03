---
name: researching-ba-problem-space
version: 1.0.0
description: >
  Run upstream BA problem-space discovery BEFORE intake — investigate the problem,
  frame opportunities, surface assumptions and the four product risks (value,
  usability, feasibility, viability), and map the banking regulatory regimes in
  play — producing a discovery artifact that seeds a human review gate and hands
  off into requirement intake. Use when asked to research the problem space before
  intake, decide whether this is the right thing to build, do product discovery,
  frame the opportunity and risks, or map the regulatory regime for an initiative.
  AI drafts; a human decides. Do NOT use to structure a known requirement into a
  brief or stories (use eliciting-banking-brief or scoping-ba-intake). Do NOT use
  to design the architecture (use designing-tech-lead-handoff). Do NOT use to
  write code or run compliance enforcement.
stage_type: analyze
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: enhanced, pii_handling: minimal, tier_default: T1, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 240
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Researching the BA Problem Space

## Purpose

Decide *whether the right thing is being built* before the squad commits to
intake. The BA pipeline begins at intake (`scoping-ba-intake` /
`eliciting-banking-brief`), which assumes discovery is done; this skill fills the
upstream gap — problem framing, opportunity mapping, assumption/risk surfacing,
and banking regulatory-regime mapping — as an AI-drafted artifact that a human
decides on, then hands into intake.

## When to use this skill

- Use when: an initiative/problem is raw and you need discovery before writing a
  brief or stories.
- Use when: asked to "do product discovery", "frame the opportunity + risks", or
  "map the regulatory regime" for an initiative.
- Do NOT use: to structure a known requirement (`eliciting-banking-brief` /
  `scoping-ba-intake`), to design architecture (`designing-tech-lead-handoff`), or
  to write code / enforce compliance.

## Input contract

Validate against `schemas/input.json`. Required: `initiative` (the raw problem /
opportunity statement), `idempotency_key`. Optional: `context` (market/user
notes), `tier`. If the input is already a structured requirement, stop with a
note to use intake instead. Never echo real PII.

## Procedure

1. **Frame the problem** (`references/discovery-method.md`): what problem, for
   whom, why now — opportunity, not solution. Entry: a raw initiative. Exit: a
   problem framing.
2. **Map opportunities** (opportunity-solution-tree style): candidate opportunities
   and the outcomes they serve; do not jump to a solution.
3. **Surface assumptions + the four risks** — value, usability, feasibility,
   viability — each as a testable assumption with a confidence and a way to
   de-risk (spike/interview/data).
4. **Map regulatory regimes** in play (KYC / AML / sanctions / PCI-DSS / data
   residency) and flag any that gate the initiative; escalate a hard blocker.
5. **Recommend** proceed-to-intake / needs-discovery-work / do-not-build, with the
   rationale. AI drafts; a **human decides** at the review gate.
6. **Emit** the discovery artifact (Output contract). On `recommendation: proceed`,
   populate `handoff_to_intake` so the composite S1 chain can thread discovery into
   intake; on `needs-work`/`do-not-build`, or on RB-01 (input already structured),
   emit no handoff. See `references/discovery-method.md` for the field map and the
   orchestrator merge recipe.

## Output contract

Validate against `schemas/output.json`: `problem_framing`, `opportunities[]`,
`assumptions[]{statement,risk_type,confidence,de_risk}`, `regulatory_regimes[]`,
`recommendation` (proceed|needs-work|do-not-build), and `audit_id`. On `proceed`,
also emit the optional `handoff_to_intake` block — a typed handoff
(`{audit_id, recommendation, tier_signal, stakeholder_hints[], opportunity_detail[]}`)
consumed field-for-field by `eliciting-banking-brief`'s `input.discovery`. `audit_id`
inside the handoff MUST equal the top-level `audit_id` (one audit identity across the
chain). The handoff is advisory: intake may seed but never suppress its own findings.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| RB-01 | input already a structured requirement | note | route to intake |
| RB-02 | regulatory hard-blocker | artifact + blocker | human-queue (governance) |
| RB-03 | insufficient context to frame | partial + open questions | human review |

## Constraints

- DO NOT structure stories/acceptance criteria — that is intake's job downstream.
- DO NOT decide; AI drafts the discovery, a named human decides at the gate.
- DO NOT echo or persist real PII; work at the problem/regime level.
- DO NOT recommend a solution architecture — frame the problem, not the build.

## References

| Need | Reference |
|------|-----------|
| Problem framing, opportunity-solution-tree, four risks, regulatory mapping, hand-off | `references/discovery-method.md` |
