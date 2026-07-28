# Rules, domain model and flows

Binding rules for Procedure steps 6, 7 and 8 — the three catalogues that carry the
analytical depth. Schemas: `schemas/rules.json`, `schemas/domain.json`,
`schemas/flow.json`.

## Why these exist

Previously a business rule such as "shipping is free at or above 1500 THB,
otherwise 60 THB" existed only inside the prose of one acceptance criterion in
one story. Three consequences followed: the rule could not be found without
reading every story; a second story restating it could drift from the first with
nothing detecting the contradiction; and the Tech Lead received no entity model
or state machine to design against.

Stating each fact once, with an id, and referencing it from the stories that
honour it is simultaneously **deeper** (rules, entities, states and flows are now
first-class and countable) and **smaller** (each fact appears once instead of
being paraphrased in every story that touches it).

## RULES.json — the business-rule catalogue

One row per rule. A rule is a statement that constrains behaviour and could be
independently right or wrong.

**Extraction order.** Sweep the raw request for: numeric thresholds and their
units; anything expressing eligibility ("only if", "customers who"); every
calculation; every allowed and forbidden state change; every authorisation
statement ("only an admin may"); every constraint framed as "must" or "must not".

**Id.** `RULE-{DOMAIN}-NN`, where `DOMAIN` is the business area the rule governs
(`CHECKOUT`, `STOCK`, `REFUND`), dense from 01 per domain. The domain token is
independent of epic ids: a rule may be referenced by stories in more than one
epic, which is precisely why it is not stored inside an epic.

**`statement`** — one testable sentence with the concrete values in it. If the
source says "a reasonable delay" the value is unknown: still create the rule,
set `open: true`, link an `open_question_ref`. An open rule is visible and
countable; a rule silently omitted because its value was vague is not.

**`type`** — the enum decides what the elaboration stage will sweep for. Getting
it right matters:

| Type | Means | Elaboration derives |
|---|---|---|
| `calculation` | A value is computed from inputs | Boundary and rounding cases |
| `eligibility` | Something is allowed for some subjects | In, out and edge-of-set cases |
| `threshold` | A numeric boundary changes behaviour | At, just below and just above |
| `state-transition` | An entity may move between states | The illegal-transition case |
| `constraint` | An invariant that must always hold | The violation attempt |
| `authorization` | A role gates an action | The wrong-actor case |

`state-transition` rules must name their entity in `applies_to_entities` —
schema-enforced, because the elaboration sweep walks from the entity's state
machine back to the rule.

**`source_ref`** — where in the raw request the rule comes from. A rule with no
source is an assumption. Assumptions are legitimate but they are recorded as open
questions, not laundered into the catalogue as facts.

## DOMAIN.json — entities, state machines, fields, glossary

One row per business entity: something the business names, whose data persists,
and which a business person would recognise. Not a table, not a service.

**States and transitions.** An entity with a lifecycle carries `states[]` and
`transitions[]`; schema-enforced together — declaring states without transitions
describes a lifecycle nobody can enter or leave. Each transition carries a
`trigger` and, where a rule decides it, a `guard` naming the `RULE-*` id. Mark
`reversible: false` on any transition that moves money or external state, and
give it a `compensating_action` — a false-and-uncompensated transition raises
`compensating_action_missing`.

**Fields and PII.** `key_fields[]` carries one row per field the business cares
about, each with a forced `pii_class`. This **replaces the old standalone
pii_inventory table**: personal data is declared where the field is defined,
once, instead of re-listed inside every story that touches it. Any class other
than `none` requires `lawful_basis` and `masking` (schema-enforced).

`pii_class: none` is a decision, not a default. An entity holding customer data
whose every field is `none` raises `pii_class_missing` — the successor to AP-4.1.

**Retention.** Any entity holding personal or financial data needs `retention`
with its source. Absent, raise `retention_policy_unstated`.

**Glossary.** Terms live here rather than in a separate file: a domain term is
almost always an entity, a state or a field, and separating them produced two
lists that disagreed.

## FLOW-NAME.json — end-to-end business flows

One file per journey. A journey is one primary actor moving from a trigger to an
outcome, crossing however many stories it takes.

**`actor`** — exactly one primary actor. A flow that switches primary actor
halfway is two flows; connect them with a `goes_to` naming the other `FLOW-*` id.

**`steps[]`** — at least two, sequentially numbered, each naming its actor and
action, and citing the entities, rules and stories it touches. The `story_refs`
are what turn an unordered story set into a path.

**`decision_points[]`** — every branch, each citing at least one `RULE-*` id
(schema-enforced). This constraint is the useful one: **a branch nobody can cite
a rule for is an undocumented business rule**. When the sweep finds one, add the
rule (usually `open: true`) rather than deleting the branch.

**`outcomes[]`** — at least two, schema-enforced. A flow with only a success
outcome has not been analysed for failure. Give each outcome the `entity_state`
the primary entity lands in, matching a state in `DOMAIN.json`.

## The three cross-checks

Run these before emitting; each failure is a real gap, not a formatting nit.

1. **Every rule is referenced.** A rule no story and no decision point references
   is either a missing story or a rule that does not belong to this scope.
2. **Every decision point cites a rule.** Enforced by schema; listed here because
   the fix is to add the rule, never to drop the branch.
3. **Every flow outcome maps to an entity state.** An outcome landing in a state
   the domain model does not declare means the state machine is incomplete.

Record the counts in `count_check`. The three-amigos report leads with them.

## Cross-references

- `references/epic-and-story-breakdown.md` — how stories reference these catalogues
- `references/governance-detectors.md` — the PII, retention and citation gaps
  these files raise
