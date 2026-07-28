---
name: elaborating-user-stories
version: 1.0.0
description: Elaborate an APPROVED epic and story breakdown into implementation-ready stories - rule-anchored Gherkin acceptance criteria, the seven force-evaluated banking-grade rows, a systematic edge-case sweep derived from the business-rule catalogue and the domain state machines, and the hidden-requirements frame sweep. This IS the delivery pipeline's ba-research stage, running only after the three-amigos gate agrees the breakdown. Use when asked to write acceptance criteria or Gherkin for agreed stories, elaborate a story skeleton into a ready story, derive edge cases from business rules or a state machine, or produce the TL-ready brief. Do NOT use to create or regroup epics, invent stories, or edit the rule catalogue (use breaking-down-ba-scope, which runs before the gate). Do NOT use for problem-space discovery (use researching-ba-problem-space), technical design (use designing-tech-lead-handoff), test execution or code. PII is redacted, never echoed.
stage_type: analyze
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: enhanced, pii_handling: redact, tier_default: T2, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 180
max_retries_recommended: 2
fallback: human-queue
recommended_temperature: {T1: 0.1, T2: 0.3, T3: 0.5}
compatibility: claude-code, codex, opencode
---

# Skill: Elaborating User Stories

## Purpose

Turn an **agreed** story skeleton into a story a developer can build and a tester
can verify: Gherkin acceptance criteria anchored to catalogued business rules, a
systematic edge-case sweep derived from those rules and from the domain state
machines, the seven force-evaluated banking-grade rows, and the ten-frame
hidden-requirements sweep.

The stage is deliberately narrow. It does not decide what the epics are, which
stories exist, or what the business rules say — a BA, a developer and a tester
settled all of that at the three-amigos gate. Elaboration adds depth **inside**
an agreed shape. That constraint is what makes the depth affordable: nothing
written here is at risk of being thrown away because the backlog was wrong.

The skill **surfaces** defects and never silently repairs them.

## When to use this skill

- Use when: an approved breakdown needs acceptance criteria and banking-grade
  evaluation written.
- Use when: asked to derive edge cases systematically from business rules or from
  an entity state machine, rather than by inspiration.
- Use when: producing the Tech-Lead-ready brief and its epic and story ref-chain.
- Do NOT use: to create, merge or regroup epics, to invent a story, or to add or
  edit a rule — that is `breaking-down-ba-scope`, and its output was reviewed at
  a gate. Editing it here voids that review.
- Do NOT use: for problem-space discovery (`researching-ba-problem-space`) or
  request normalization (`scoping-ba-intake`).
- Do NOT use: for technical design (`designing-tech-lead-handoff`), test
  execution, or code.

## Input contract

`schemas/input.json` is **ENFORCED** — the engine validates the assembled payload
before the stage runs, fail-closed. It documents the real post-adapter payload
assembled at stage `ba-research`.

Required: `raw_request`, `requester`, `normalized_request`, `idempotency_key`,
and **`breakdown`** — the approved pack with its ref-chain already hydrated:
`epics[]`, `stories[]` (skeletons), `rules{rules[]}`, `domain{entities[]}`,
`flows[]`, plus the governance roll-up.

Optional `amigos_verdict` carries the recorded gate decision: the verdict, the
named approvers one per required role, any `conditions` the reviewers attached,
and open questions they resolved in the session. Conditions are **binding
input** — a condition is elaborated like a rule, and a scenario written to
satisfy one is tagged `derived_from: amigos_condition`.

**Two preconditions are re-checked fail-closed** even though the engine gate
already enforces them: `breakdown.state` must be `ready-for-amigos`, and
`breakdown.blocks_elaboration` must be false. A skill that trusts its caller is a
skill that can be invoked wrongly.

**Example (validates against `schemas/input.json`):**

```json
{
  "raw_request": "Free shipping over 1500 THB. Stock must never oversell. A double-clicked confirm must not create two orders.",
  "requester": "Khun Pim (Product Manager)",
  "normalized_request": "Build a single-merchant Thai-market B2C storefront plus an admin back office covering browse, cart, checkout, payment, fulfilment and tracking.",
  "idempotency_key": "req-2026-07-12-shoppilot-001",
  "breakdown": {
    "audit_id": "0f1b2c3d-4e5f-5a6b-8c9d-0e1f2a3b4c5d",
    "state": "ready-for-amigos",
    "blocks_elaboration": false,
    "epics": [{ "id": "EPIC-STOREFRONT-PURCHASE", "title": "A customer can buy something end to end" }],
    "stories": [{ "id": "STORY-PURCHASE-01", "epic_id": "EPIC-STOREFRONT-PURCHASE", "rule_refs": ["RULE-CHECKOUT-01"] }],
    "rules": { "rules": [{ "id": "RULE-CHECKOUT-01", "type": "threshold", "statement": "Shipping is free at or above 1500 THB, otherwise 60 THB." }] },
    "domain": { "entities": [{ "id": "ENTITY-ORDER", "states": ["awaiting-payment", "paid"] }] },
    "flows": [{ "id": "FLOW-CUSTOMER-PURCHASE" }]
  },
  "amigos_verdict": {
    "verdict": "agreed",
    "approvers": [
      { "role": "ba-lead", "name": "Khun Pim" },
      { "role": "dev-lead", "name": "Khun Anan" },
      { "role": "qa-lead", "name": "Khun Ratree" }
    ]
  }
}
```

## Procedure

Seven ordered steps. Binding sub-rules live per-step in the references named in
parentheses.

1. **Check the preconditions and carry the pack forward.** Verify
   `breakdown.state` and `blocks_elaboration`; copy each epic and each story
   skeleton forward without changing its `id`, `card`, `intent`, `rule_refs`,
   `priority` or `sizing`. Carry `rules_file`, `domain_file` and `flows` refs on
   the manifest so the Tech Lead, the contract stage and QA planning receive them.
   (`references/elaboration-failure-modes.md`)
2. **Write the acceptance criteria from the source and the rules.** Rewrite every
   stated behaviour as `Given` / `When` / `Then` with concrete values. `Given`
   names concrete state and actor; `When` is a **single** trigger — an `and`
   chain is two scenarios (AP-8.2); `Then` is an observable outcome, never "is
   happy" or "works correctly". Each scenario derived from a catalogued rule
   carries that `rule_ref`; every scenario carries `derived_from`.
   (`references/gherkin-templates.md`, `references/invest-checklist.md`)
3. **Detect residual ambiguity in what the source says.** Run the eight ambiguity
   detectors over every text segment and assign severity. Anti-patterns compose —
   never deduplicate across detectors. (`references/ambiguity-patterns.md`)
4. **Run the rule-anchored edge-case sweep.** For each referenced rule derive the
   cases its `type` demands — at, below and above a threshold; rounding and zero
   on a calculation; in, out and edge on eligibility; the violation attempt on a
   constraint; the wrong actor on an authorization — plus replay, race and
   partial-failure where the story's shape calls for them. For each referenced
   entity with states, write the **illegal-transition** case. Record every
   decision in `edge_case_ledger`, including what was judged not applicable and
   why. (`references/rule-anchored-edge-cases.md`)
5. **Force-evaluate the seven banking-grade rows.** `pii_fields`,
   `audit_events`, `idempotency`, `reversibility`, `authn_authz`, `regulatory`,
   `tipping_off` — all seven on every story, each with a status and a
   justification of at least ten characters. Use the domain model rather than
   guessing: a story touching a field whose `pii_class` is not `none` cannot
   write `pii_fields: not_applicable`. An irreversible transition needs its
   `compensating_action`. (`references/elaboration-failure-modes.md`)
6. **Run the hidden-requirements sweep.** Apply the ten frames to catch what the
   source does not say at all — as distinct from step 3, which catches what it
   says ambiguously. Each finding lands in `open_questions[]` with
   `provenance: hidden_frame_sweep` and its frame number, or in
   `assumptions_made[]` with a `default_revisit_trigger` when a defensible
   default exists. (`references/hidden-requirements-frames.md`,
   `references/frame-rule-data.json`)
7. **Run the assembly gates and emit.** FM-01, FM-02, FM-06, FM-11, FM-13, FM-15,
   FM-16, FM-17, and the two new coverage gates FM-18 (an uncovered rule) and
   FM-19 (an open rule). Set `dor` per story, compute `rule_coverage`, set
   `state`, and emit the ref-chain.
   (`references/elaboration-failure-modes.md`)

## Output contract

A pack of small files under a thin INDEX. `INDEX.json` conforms to
`schemas/output.json`; each sidecar conforms to its own schema.

```
INDEX.json                    manifest + coverage ledgers  (schemas/output.json)
EPIC-NAME.json                one per epic                 (schemas/epic-sidecar.json)
STORY-PREFIX-NN-slug.json     one per story                (schemas/story-sidecar.json)
```

`RULES.json`, `DOMAIN.json` and the `FLOW-*.json` files are **referenced, not
copied**: they belong to the breakdown pack, they passed the gate there, and a
second copy would drift from the first.

**Boundary compatibility is deliberate.** The required set — `epics`,
`story_files`, `governance_gaps`, `state`, `audit_id` — and the item shapes are
unchanged from the predecessor skill, so splitting the old single stage into
breakdown plus elaboration is invisible to all five downstream consumers. The
`audit_id` formula is likewise unchanged:
`UUIDv5(HOUSE_NS, "ba-research:{idempotency_key}")` with `HOUSE_NS =
uuid5(NAMESPACE_URL, "https://squad-delivery/audit")`, so recorded corpus
provenance stays valid. The breakdown's own id is recorded in
`upstream_refs.breakdown_audit_id`, never reused.

**Two coverage ledgers make the depth checkable.** `rule_coverage` counts rules
referenced, rules with at least one derived scenario, the uncovered remainder,
state transitions and illegal-transition cases. `hidden_requirements_sweep`
records frames applied, skipped with reasons, and the coverage score.
`ready-for-tl` requires both to be clean — schema-enforced, not merely asserted.

**No human report.** The run-level delivery-review console renders this pack; the
one short markdown report in the BA leg is the breakdown's three-amigos agenda,
written before the gate, where a human decision actually depends on it.

**Example (validates against `schemas/output.json`):**

```json
{
  "audit_id": "a1b2c3d4-5e6f-5a7b-8c9d-0e1f2a3b4c5e",
  "stage": "ba-research",
  "state": "ready-for-tl",
  "produced_by": "elaborating-user-stories 1.0.0",
  "idempotency_key": "req-2026-07-12-shoppilot-001",
  "epics": [
    {
      "id": "EPIC-STOREFRONT-PURCHASE",
      "file": "EPIC-STOREFRONT-PURCHASE/EPIC-STOREFRONT-PURCHASE.json",
      "title": "A customer can buy something end to end",
      "story_ids": ["STORY-PURCHASE-01"]
    }
  ],
  "story_files": [
    {
      "id": "STORY-PURCHASE-01",
      "epic_id": "EPIC-STOREFRONT-PURCHASE",
      "file": "EPIC-STOREFRONT-PURCHASE/STORY-PURCHASE-01-customer-checks-out.json",
      "title": "Customer checks out at a server-computed total",
      "priority": "Must"
    }
  ],
  "rules_file": "../S1b-breakdown/RULES.json",
  "domain_file": "../S1b-breakdown/DOMAIN.json",
  "flows": [
    { "id": "FLOW-CUSTOMER-PURCHASE", "file": "../S1b-breakdown/FLOW-CUSTOMER-PURCHASE.json", "name": "Customer purchase journey" }
  ],
  "governance_gaps": [],
  "rule_coverage": {
    "rules_total": 3,
    "rules_covered": 3,
    "uncovered_rule_ids": [],
    "transitions_total": 4,
    "illegal_transition_cases": 4,
    "open_rule_ids": []
  },
  "hidden_requirements_sweep": {
    "frames_applied": [1, 2, 4, 5, 6, 9, 10],
    "frames_skipped": [3, 7, 8],
    "frames_skipped_reasons": { "3": "no monetary policy content beyond the catalogued rules", "7": "no external system in scope", "8": "single market, single language" },
    "total_findings": 9,
    "coverage_score": "complete"
  },
  "count_check": { "epics": 1, "stories": 1, "acceptance_criteria": 6, "open_questions": 2 },
  "upstream_refs": {
    "breakdown_audit_id": "0f1b2c3d-4e5f-5a6b-8c9d-0e1f2a3b4c5d",
    "amigos_approvers": ["Khun Pim (ba-lead)", "Khun Anan (dev-lead)", "Khun Ratree (qa-lead)"]
  }
}
```

## Failure modes

Full detection, output shape and escalation: `references/elaboration-failure-modes.md`.

| Code | Trigger | Result |
|---|---|---|
| FM-01 | criteria a tester could not automate | `needs-work`, `untestable_criteria` |
| FM-02 | unresolved P1 governance item | `blocked` |
| FM-06 | tipping-off term in a customer-facing string | `blocked`, safe phrase, legal sign-off |
| FM-11 | any emitted file fails its schema | emit nothing |
| FM-13 | personal data would reach the output | `pii_echo_blocked`, auto-redact |
| FM-15 | frame-sweep coverage partial or skipped | `needs-work` plus a P2 question |
| FM-16 | idempotency applies but no replay scenario | hard schema failure |
| FM-17 | Frame 4 sub-topic uncovered | `partial` plus a P2 question |
| FM-18 | a referenced rule has no derived scenario | `needs-work` |
| FM-19 | a story references a still-open rule | `needs-work`, `open_rule_blocks_story` |

Precondition failures — `breakdown_not_agreed` and `governance_p1_unresolved` —
emit nothing at all. Elaborating around a blocker is worse than not elaborating.

## Constraints

- DO NOT create, merge, regroup or rename an epic. The gate agreed the shape.
- DO NOT invent a story, and do not drop one. A story the reviewers agreed on
  that cannot be elaborated is an open question, not a silent deletion.
- DO NOT add or edit a business rule. If the sweep reveals uncovered behaviour,
  raise an open question against the breakdown.
- DO NOT restate a rule as prose inside a scenario. Cite `rule_ref` and use its
  values; two copies drift.
- DO NOT guess a value for a rule the breakdown marked open. Surface the block.
- DO NOT write `not_applicable` on a banking-grade row without a justification
  that names the workflow class making it inapplicable.
- DO NOT pad the sweep. A derived case that duplicates another's observable
  behaviour is recorded as not applicable with that reason, not written twice.
- DO NOT emit an all-true checklist. Definition of Ready is a verdict plus its
  failures; ceremony in an audit trail looks like evidence.
- DO NOT echo real PII anywhere, including examples.
- DO NOT put timestamps, model names, durations or token counts in any emitted
  file. The pack is byte-deterministic for identical input.

## References

Progressive disclosure — load only what the step needs.

- `references/elaboration-failure-modes.md` — preconditions, the ten gates, the
  mandatory scenario floor, the seven forced rows, Definition of Ready, and
  `state` (steps 1, 5, 7).
- `references/rule-anchored-edge-cases.md` — the derivation table per rule type,
  the state-machine illegal-transition case, open rules, and the coverage ledger
  (step 4).
- `references/gherkin-templates.md` — scenario format and the banking-grade
  scenario templates (steps 2, 5).
- `references/invest-checklist.md` — per-letter rules and the testability
  self-check (step 2).
- `references/ambiguity-patterns.md` — the eight ambiguity types with severity
  (step 3).
- `references/hidden-requirements-frames.md` — the ten elicitation-gap frames
  with activation triggers, severity floors and caps (step 6).
- `references/frame-rule-data.json` — runtime source of truth for Frame 4
  sub-topic coverage; drift against the frames document is caught by
  `scripts/check_frame_rule_data_drift.py` (step 6).
- `references/anti-patterns.md` — the full catalogue; AP-8.2 and AP-8.4 are the
  ones this stage enforces (steps 2, 7).

## Human approval gate

**Stop after emitting.** The brief goes to the BA lead for review, and the Tech
Lead's pre-flight requires `state: ready-for-tl`.

The agent never records the verdict, never approves its own brief, and never
clears a P1 governance gap or an open rule to make a run go green. A named human
does both.
