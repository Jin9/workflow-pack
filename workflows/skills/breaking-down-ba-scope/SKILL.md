---
name: breaking-down-ba-scope
version: 1.0.0
description: Break a normalized requirement into the business-decoupled epic and story SKELETON that a BA, a developer and a tester review together before anyone writes acceptance criteria - grouping epics by business dependency, cataloguing the business rules, the domain entities and their state machines and the end-to-end flows, and escalating governance gaps as P1 blockers. This IS the delivery pipeline's ba-breakdown stage (S1b). Use when asked to break scope into epics and stories, group epics by business dependency, extract the business rules or domain model before detailed stories, map end-to-end business flows, or prepare the three-amigos review pack. Do NOT use to write acceptance criteria, Gherkin or banking-grade rows (use elaborating-user-stories, after the gate). Do NOT use for problem-space discovery (use researching-ba-problem-space), request normalization (use scoping-ba-intake), technical design (use designing-tech-lead-handoff) or code. PII-bearing input is redacted at preflight, never echoed.
stage_type: analyze
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: enhanced, pii_handling: redact, tier_default: T2, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 150
max_retries_recommended: 2
fallback: human-queue
recommended_temperature: {T1: 0.1, T2: 0.3, T3: 0.5}
compatibility: claude-code, codex, opencode
---

# Skill: Breaking Down BA Scope

## Purpose

Produce the **breakdown pack** — the epic and story skeleton, the business-rule
catalogue, the domain model and the end-to-end business flows — that a BA, a
developer and a tester review **together** before anyone writes a single
acceptance criterion.

Two things make this stage worth its own node. First, the epics it produces are
grouped by **business dependency** rather than by system area, so an epic is
something a business audience can receive value from. Second, everything
downstream is expensive: elaborating stories, designing, and building against a
backlog whose shape is wrong is the most costly rework in the pipeline. The
skeleton is cheap to argue with; the elaborated brief is not.

The skill **surfaces** defects and never silently repairs them. Silent repair
launders ambiguity into shipped requirements and destroys audit reconstruction.

## When to use this skill

- Use when: scope must be broken into epics and stories before detail is written.
- Use when: asked to group epics by business dependency, catalogue the business
  rules, model the domain entities and their state machines, or map the
  end-to-end business flows.
- Use when: preparing the pack for a three-amigos (BA plus developer plus tester)
  review session.
- Do NOT use: to write acceptance criteria, Gherkin or banking-grade rows — that
  is `elaborating-user-stories`, and it runs only after the gate agrees.
- Do NOT use: for problem-space discovery (`researching-ba-problem-space`) or
  request normalization (`scoping-ba-intake`).
- Do NOT use: for technical design (`designing-tech-lead-handoff`) or code.

## Input contract

`schemas/input.json` is **ENFORCED** — the engine validates the assembled payload
against it before the stage runs, fail-closed, exactly as it validates output.
The schema documents the real post-adapter payload assembled at stage
`ba-breakdown`.

Required: `raw_request`, `requester`, `normalized_request` (the PII-redacted
string from S0 intake), `idempotency_key` (engine-injected).

Optional, both **advisory and add-only**:

- **`scope`** — the trimmed S0 scope contract (business goal, in and out of
  scope, quantified non-functional requirements, open questions, assumptions,
  risk flags). It bounds what is in play. It may never invent a rule, discharge a
  detector, or lower a tier.
- **`discovery`** — the typed handoff from `s1-discovery`, delivered after that
  stage's human gate. It may **raise** a tier floor, **seed** absent-stakeholder
  rows, and **seed** pending regulatory-citation leads. It may never suppress a
  detector, lower a tier, satisfy a citation, or replace `raw_request`. An absent
  `discovery` is byte-identical to discovery-present-but-empty behaviour.

Also optional and engine-injected: `upstream_artifacts`, and `loop_back_feedback`
carrying the three-amigos reviewers' findings on a returned breakdown.

Idempotency extends to the tuple `(raw_request, scope, discovery)`. A cache keyed
on `idempotency_key` alone is a bug.

**Example (validates against `schemas/input.json`):**

```json
{
  "raw_request": "A single Thai merchant wants a B2C storefront plus an admin back office covering browse, cart, checkout, mock payment and delivery tracking. Free shipping over 1500 THB. Stock must never oversell.",
  "requester": "Khun Pim (Product Manager)",
  "normalized_request": "Build a single-merchant Thai-market B2C storefront plus an admin back office covering browse, cart, checkout, payment, fulfilment and tracking.",
  "idempotency_key": "req-2026-07-12-shoppilot-001"
}
```

## Procedure

Eleven ordered steps. Each line is the imperative action plus its load-bearing
markers; the binding sub-rules, thresholds and field names live per-step in the
references named in parentheses.

1. **Preflight — strip ground-truth, detect source type, score input quality.**
   Fail closed on strip failure (FM-12). Input too thin to break down at all
   yields `state: needs-clarification` (FM-01) — never a fabricated epic.
   (`references/governance-detectors.md`)
2. **Classify and redact PII.** Never echo an actual value; substitute
   `[PII:REDACTED:CLASS=NRIC]` before analysis writes anything, and raise the P1
   alert (FM-13). Classification is recorded per field in step 7, not in a
   separate inventory. (`references/governance-detectors.md`)
3. **Recognize regulator citations.** Resolved versus unresolved; unresolved on
   T1 blocks (FM-04). A discovery-seeded lead is not a citation.
   (`references/governance-detectors.md`)
4. **Extract stakeholders and run the Legal-absence gate.** Never collapse roles;
   weight by authority mode; enumerate the absent-but-implied with
   `engagement_required_for`. Always emit `legal_status`; anything other than
   `present` on regulatory scope raises a P1 `legal_absent_on_regulatory` with
   `blocks: true` (FM-05). Compliance is not Legal. Run the tipping-off scan over
   every customer-facing string (FM-06). (`references/governance-detectors.md`)
5. **Group epics by business dependency.** Apply the three tests — independently
   valuable, own success metric, no mandatory business dependency on a sibling —
   and **merge** any candidates that fail the third. Enablers such as
   authentication and stock reservation are never epics; they become stories
   inside the epic they enable. Record every folded candidate in
   `decoupling.merged_from`; `sibling_dependencies` must end empty.
   (`references/epic-and-story-breakdown.md`)
6. **Catalogue the business rules.** One row per rule, stated once with concrete
   values and a stable `RULE-DOMAIN-NN` id and a source reference. A rule whose
   value the source leaves vague is emitted with `open: true` and a linked open
   question — never omitted. (`references/rules-domain-flows.md`)
7. **Model the domain.** Entities, their `key_fields` with a forced `pii_class`,
   their lifecycle states and the legal transitions between them with the rule
   that guards each. Personal data is declared here, once, at the field.
   Irreversible transitions that move money or external state need a
   `compensating_action`. The glossary lives here too.
   (`references/rules-domain-flows.md`)
8. **Map the end-to-end business flows.** One file per journey: one primary
   actor, a trigger, numbered steps citing entities and rules and stories,
   decision points that each cite the rule deciding them, and at least two
   outcomes. A branch no rule can be cited for is an undocumented rule — add the
   rule. (`references/rules-domain-flows.md`)
9. **Emit story skeletons.** What and why only: card, one-line `intent`,
   `rule_refs`, `flow_refs`, `entity_refs`, MoSCoW priority, sizing,
   dependencies. **No acceptance criteria and no banking-grade rows** — writing
   them before the gate agrees is precisely the rework this stage prevents. Every
   non-spike story references at least one rule.
   (`references/epic-and-story-breakdown.md`)
10. **Infer tier per epic and run the assembly gates.** Tier per epic, never per
    file. A discovery `tier_signal` is a floor: `effective_tier = max(inferred,
    tier_floor, tier_signal)`; a raise of one step or more over the supplied hint
    sets `inferred_higher_than_manual` and requires a human override (AP-1.3).
    Then run FM-01, FM-04, FM-05, FM-06, FM-11, FM-12, FM-13 and the FM-14 count
    consistency checks, and set `state` and `blocks_elaboration`.
    (`references/governance-detectors.md`)
11. **Write the one human report.** Emit `breakdown.md` — the three-amigos agenda,
    two pages, derived from the pack and byte-deterministic. It is the only
    human-facing document this stage produces.
    (`references/breakdown-report-spec.md`)

## Output contract

The stage artifact is a **pack of small files under a thin INDEX**, not one large
document. `INDEX.json` conforms to `schemas/output.json`; each referenced file
conforms to its own schema. Consumers dereference `epics[].file`,
`story_files[].file` and `flows[].file` exactly as the ba-brief ref-chain is
hydrated today.

```
INDEX.json              manifest + governance roll-up  (schemas/output.json)
EPIC-NAME.json          one per epic                   (schemas/epic.json)
STORY-PREFIX-NN.json    one per story skeleton         (schemas/story-skeleton.json)
RULES.json              the business-rule catalogue    (schemas/rules.json)
DOMAIN.json             entities, states, fields, glossary (schemas/domain.json)
FLOW-NAME.json          one per business flow          (schemas/flow.json)
breakdown.md            the three-amigos agenda        (references/breakdown-report-spec.md)
```

**`state`** is the gate signal: `ready-for-amigos` releases the three-amigos
review; `blocked` carries at least one P1 governance gap and a `failure_state`;
`needs-clarification` means the input could not be broken down at all.
`blocks_elaboration` is true whenever any gap carries `blocks: true` — and no
verdict at the gate can clear it. A named human resolves the gap.

**Nothing is inlined that has its own file.** The rule text lives in `RULES.json`
and stories cite its id; the entity lives in `DOMAIN.json` and stories cite its
id. This is what lets the pack carry more analysis in fewer bytes than the brief
it replaces.

**Provenance id.** Required top-level `audit_id`, producer-stamped and
deterministic: `UUIDv5(HOUSE_NS, "ba-breakdown:{idempotency_key}")` with
`HOUSE_NS = uuid5(NAMESPACE_URL, "https://squad-delivery/audit")`. `RULES.json`
and `DOMAIN.json` carry the same value. It is independent of the optional `scope`
and `discovery` inputs, and distinct from both `discovery.audit_id` (recorded in
`upstream_refs.discovery_audit_id`) and the engine's per-attempt execution id.
Never rewrite a recorded provenance value.

**Example (validates against `schemas/output.json`):**

```json
{
  "audit_id": "0f1b2c3d-4e5f-5a6b-8c9d-0e1f2a3b4c5d",
  "stage": "ba-breakdown",
  "state": "ready-for-amigos",
  "produced_by": "breaking-down-ba-scope 1.0.0",
  "idempotency_key": "req-2026-07-12-shoppilot-001",
  "scope_kind": "multi-epic",
  "epics": [
    {
      "id": "EPIC-STOREFRONT-PURCHASE",
      "file": "EPIC-STOREFRONT-PURCHASE.json",
      "title": "A customer can buy something end to end",
      "story_prefix": "PURCHASE",
      "story_ids": ["STORY-PURCHASE-01"]
    }
  ],
  "story_files": [
    {
      "id": "STORY-PURCHASE-01",
      "epic_id": "EPIC-STOREFRONT-PURCHASE",
      "file": "STORY-PURCHASE-01.json",
      "title": "Customer checks out at a server-computed total",
      "priority": "Must"
    }
  ],
  "flows": [
    { "id": "FLOW-CUSTOMER-PURCHASE", "file": "FLOW-CUSTOMER-PURCHASE.json", "name": "Customer purchase journey" }
  ],
  "rules_file": "RULES.json",
  "domain_file": "DOMAIN.json",
  "stakeholders": [
    { "role": "Legal Counsel", "name_or_team": "Khun Somchai", "status": "present", "raci": "A" },
    { "role": "Data Protection Officer", "status": "absent", "engagement_required_for": "per-field lawful basis on customer data" }
  ],
  "legal_status": "present",
  "governance_gaps": [],
  "open_questions": [
    {
      "id": "OQ-1",
      "severity": "P2",
      "question": "Does a coupon re-validated at confirm reprice the order or reject it outright?",
      "for": "dev",
      "related_rule_ids": ["RULE-CHECKOUT-02"]
    }
  ],
  "blocks_elaboration": false,
  "count_check": { "epics": 1, "stories": 1, "rules": 3, "entities": 2, "flows": 1, "open_questions": 1 },
  "human_report": "breakdown.md",
  "upstream_refs": {
    "source_artifacts": ["ecommerce_mvp_business_only.gap-closed.md"],
    "discovery_audit_id": "9d4e1f8a-2c07-4b63-a5e9-6f1b0c3d8e24"
  }
}
```

## Failure modes

Codes carry over from the predecessor skill unchanged, so the fleet vocabulary
and the audit trail survive the split. Full detection, output shape and
escalation per code: `references/governance-detectors.md`.

| Code | Trigger | Result |
|---|---|---|
| FM-01 | input too thin to break down | `needs-clarification`, `empty_or_minimal_input` |
| FM-04 | regulator named, citation unresolved, T1 scope | P1 gap, `blocked` |
| FM-05 | Legal absent or mentioned-only on regulatory scope | P1 gap, `blocked` |
| FM-06 | forbidden tipping-off term in a customer-facing string | P1 gap, safe phrase, `blocked` |
| FM-11 | any emitted file fails its schema | emit nothing; never a malformed pack |
| FM-12 | ground-truth strip failed | `needs-clarification`, do not proceed |
| FM-13 | personal data would reach the output | `needs-clarification`, auto-redact |
| FM-14 | count or cross-reference inconsistency | schema error |

Undecidable epic grouping — the three tests cannot be resolved from the source —
yields `scope_kind: ambiguous` plus a P2 open question addressed to the PM, not a
guess. The three-amigos session is the right place to settle it.

## Constraints

- DO NOT write acceptance criteria, Gherkin, or banking-grade concern rows. The
  gate exists between this stage and the stage that writes them.
- DO NOT create an epic for an enabler. Authentication, inventory reservation,
  notification and audit logging are stories inside the epic they enable.
- DO NOT split an epic on a technical layer. Frontend, backend, API and database
  are not value axes (AP-7.1).
- DO NOT restate a rule inside a story. Cite the `RULE-*` id.
- DO NOT emit a story with no `rule_refs` unless it is a spike.
- DO NOT let `discovery` or `scope` suppress a detector, lower a tier, or satisfy
  a citation. They add; they never subtract.
- DO NOT echo real PII anywhere — in the pack, the report or an example.
- DO NOT auto-resolve a P1 governance gap, and do not relax the gate to make a
  run go green. A named human clears it.
- DO NOT put timestamps, model names, durations or token counts in any emitted
  file. The pack must be byte-deterministic for identical input.

## References

Progressive disclosure — load only what the step needs.

- `references/governance-detectors.md` — preflight, PII, citations, stakeholders,
  the Legal-absence gate, the tipping-off scan, and the assembly gates
  (steps 1–4, 10).
- `references/epic-and-story-breakdown.md` — the three decoupling tests, merging,
  the story cap and value-axis splitting, story-skeleton field rules, MoSCoW
  (steps 5, 9).
- `references/rules-domain-flows.md` — how to build and cross-check the rule
  catalogue, the domain model and the flow files (steps 6–8).
- `references/breakdown-report-spec.md` — the two-page three-amigos agenda:
  section order, the ASCII flow rendering, and what must never appear (step 11).
- `references/anti-patterns.md` — the full anti-pattern catalogue; AP-1.3, AP-2.3,
  AP-3.2, AP-5.1 and AP-7.1 are the ones this stage enforces (steps 4, 5, 10).
- `references/non-tipping-vocabulary.md` — approved phrases and forbidden terms
  (step 4, on a forbidden-term hit).
- `references/job-story-decision-tree.md` — job story versus classic user story
  when the format choice is ambiguous (step 9).

## Human approval gate

**Stop after emitting.** This stage's output goes to a **three-amigos review**: a
named BA, a named developer and a named tester. Verdicts are `agreed`,
`split-stories`, `descope` and `needs-rework`; only `agreed` releases story
elaboration, and anything else returns the breakdown here with the reviewers'
findings attached.

The agent drafts the breakdown. It never records the verdict, never approves its
own pack, and never clears a P1 governance gap — including when doing so is the
only thing standing between the run and a green result.
