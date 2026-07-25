---
name: researching-ba-problem-space
version: 2.0.0
description: Run BA problem-space discovery after S0 request normalization and BEFORE the BA brief is elaborated — investigate the problem, frame opportunities, surface assumptions and the four product risks (value, usability, feasibility, viability), and map the banking regulatory regimes in play — producing a discovery artifact that a named human decides on before the brief node runs. Use when asked to research the problem space before the brief, decide whether this is the right thing to build, do product discovery, frame the opportunity and risks, or map the regulatory regime for an initiative. AI drafts; a human decides. Do NOT use to structure a known requirement into a brief or stories (use eliciting-banking-brief or scoping-ba-intake). Do NOT use to design the architecture (use designing-tech-lead-handoff). Do NOT use to write code or run compliance enforcement.
stage_type: analyze
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: enhanced, pii_handling: redact, tier_default: T1, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 240
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Researching the BA Problem Space

## Purpose

Decide *whether the right thing is being built* before the brief is elaborated.
In the composite S1, discovery runs **after S0 has normalized the request and
before `ba-research` writes the brief**: problem framing, opportunity mapping,
assumption/risk surfacing, and banking regulatory-regime mapping — an AI-drafted
artifact that a **named human decides on** (only `proceed` releases the brief
node).

## When to use this skill

- Use when: a normalized request needs discovery before anyone writes a brief or
  stories.
- Use when: asked to "do product discovery", "frame the opportunity + risks", or
  "map the regulatory regime" for an initiative.
- Do NOT use: to structure a known requirement (`eliciting-banking-brief` /
  `scoping-ba-intake`), to design architecture (`designing-tech-lead-handoff`), or
  to write code / enforce compliance.

## Input contract

`schemas/input.json` is **ENFORCED** — the engine validates the ASSEMBLED payload
against it before this stage runs (fail-closed, exactly like output validation);
it documents the POST-adapter payload assembled at stage `s1-discovery`. Required: `raw_request` and `requester` (from the workflow
input), `normalized_request` (picked from the completed S0 intake stage), and the
engine-injected `idempotency_key`. Optional engine-injected: `upstream_artifacts`,
`loop_back_feedback`. `normalized_request` is **always present** (S0 has already
run) — its presence never signals a failure. Never echo real PII; redact as
`PII:REDACTED:CLASS=...`.

**Example (validates against schemas/input.json):**

```json
{
  "raw_request": "A single Thai merchant wants its own B2C storefront where customers self-serve the full purchase journey.",
  "requester": "shoppilot-demo",
  "normalized_request": "Build a single-merchant Thai-market B2C storefront plus admin back office covering browse, cart, checkout, payment, fulfilment and tracking.",
  "idempotency_key": "req-2026-07-12-shoppilot-001"
}
```

## Output contract

Validate against `schemas/output.json`: `problem_framing`, `assumptions[]`
(`{statement, risk_type, confidence, de_risk}`), `regulatory_regimes[]` (may be
`[]` = none identified — but always present), `recommendation`
(`proceed|needs-work|do-not-build`), and `audit_id`; `opportunities[]` optional.
On `proceed` the schema enforces **four-risk completeness**: at least four
assumptions, at least one per risk class, each with a `de_risk` step.

`handoff_to_intake` is optional and legal **only when both the top-level and the
nested recommendation are `proceed`**. It is advisory-only seeding for the brief
node: the consumer may seed pending-citation rows or a tier *floor*, but never
suppress a detector, lower a tier, or satisfy a citation — an absent handoff is
**byte-identical** for the brief. Blocked/failed discoveries carry a
`failure_state` (`{failure_code: RB-01|RB-02|RB-03, message, remediation}` plus
optional `blockers[]`/`open_questions[]`), a `needs-work`/`do-not-build`
recommendation, and never a handoff.

`audit_id` (live derivation): `UUIDv5(HOUSE_NS, "s1-discovery:{idempotency_key}")`
with `HOUSE_NS = uuid5(NAMESPACE_URL, "https://squad-delivery/audit")` —
independent of optional inputs, distinct from the engine's per-attempt audit id
in `events.jsonl`. Reference-corpus ids predate this formula and are
grandfathered; never rewrite recorded provenance.

**Example (validates against schemas/output.json):**

```json
{
  "problem_framing": "Customers of a single Thai merchant cannot self-serve the full purchase journey; staff mediate every order by phone.",
  "assumptions": [
    {"statement": "Customers prefer self-serve checkout to phone orders", "risk_type": "value", "confidence": "medium", "de_risk": "interview 5 repeat customers"},
    {"statement": "A Thai-language storefront is usable without training", "risk_type": "usability", "confidence": "medium", "de_risk": "hallway test the checkout prototype"},
    {"statement": "Stock reservation can be enforced with the current inventory data", "risk_type": "feasibility", "confidence": "high", "de_risk": "spike the reservation flow against the stock table"},
    {"statement": "Order volume justifies the build cost within a year", "risk_type": "viability", "confidence": "low", "de_risk": "model break-even from last year's order data"}
  ],
  "regulatory_regimes": ["PDPA B.E. 2562: lawful basis per field, breach-notification path", "PCI-DSS v4.0: stay out of cardholder-data scope via PSP tokenization"],
  "recommendation": "proceed",
  "audit_id": "34932efa-fa8c-5bc6-bc78-5da0d97fce34"
}
```

## Procedure

1. **Frame the problem** (`references/discovery-method.md`): what problem, for
   whom, why now — opportunity, not solution. Entry: the normalized request.
   Exit: a problem framing.
2. **Map opportunities** (opportunity-solution-tree style): candidate opportunities
   and the outcomes they serve; do not jump to a solution.
3. **Surface assumptions + the four risks** — value, usability, feasibility,
   viability — each as a testable assumption with a confidence and a way to
   de-risk (spike/interview/data). On `proceed`, all four classes must be
   covered (schema-enforced).
4. **Map regulatory regimes** in play (KYC / AML / sanctions / PCI-DSS / data
   residency / PDPA) and flag any that gate the initiative; a hard blocker is
   never auto-resolved — it routes to the governance human queue (RB-02).
5. **Recommend** `proceed` / `needs-work` / `do-not-build`, with the rationale.
   AI drafts; a **named human decides** at the review gate — only `proceed`
   releases the brief node.
6. **Emit** the discovery artifact (Output contract). On `proceed`, optionally
   populate `handoff_to_intake` (advisory seeding); on `needs-work` /
   `do-not-build`, emit `failure_state` where a failure code applies and never
   a handoff. The engine nests the picked fields under `discovery` in the brief
   node's input (see `references/discovery-method.md` for the real payload
   shape).

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| RB-01 | `normalized_request` vacuous / unusable (its mere presence is normal — S0 always ran) | required fields + `failure_state` + `needs-work` | human review |
| RB-02 | regulatory hard-blocker | required fields + `failure_state` + `needs-work`/`do-not-build` | human-queue (governance) — never auto-resolved |
| RB-03 | insufficient context to frame the problem | required fields + `failure_state` (with `open_questions[]`) + `needs-work` | human review |

A failure artifact still validates: the four required top-level fields are always
emitted (empty arrays where honest), plus `failure_state`; never a handoff.

## Constraints

- DO NOT structure stories/acceptance criteria — that is the brief node's job
  downstream.
- DO NOT decide; AI drafts the discovery, a named human decides at the gate.
- DO NOT echo or persist real PII; work at the problem/regime level.
- DO NOT recommend a solution architecture — frame the problem, not the build.
- DO NOT route "back to intake" — S0 has already completed when this stage runs.
- Advisory-only handoff: seeding may add work for the brief, never remove or
  weaken it; absent handoff must remain byte-identical for the consumer.

## References

| Need | Reference |
|------|-----------|
| Problem framing, opportunity-solution-tree, four risks, regulatory mapping, the real handoff payload shape | `references/discovery-method.md` |
