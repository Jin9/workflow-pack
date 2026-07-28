# The rule-anchored edge-case sweep

Binding rules for Procedure step 4. This replaces the previous requirement of
"at least one error or edge acceptance criterion per story", which was satisfied
by whichever edge case happened to occur to whoever wrote the story.

## Why anchor on rules

An edge case is a place where a **rule** behaves differently near its boundary,
or where a **state machine** is asked to do something it must refuse. Both are
now enumerated in the breakdown pack: `RULES.json` lists every rule with a type,
and `DOMAIN.json` lists every entity's legal transitions. So the sweep can be
**derived** rather than improvised, and — more importantly — its coverage can be
**counted**. A rule with no derived case is a visible hole in `rule_coverage`,
not a silence.

The sweep does not replace judgement. It guarantees the floor.

## Part 1 — Derive from each rule

For every `RULE-*` id in the story's `rule_refs`, take the rule's `type` and
write the cases in its row. Each written scenario carries `derived_from:
rule_sweep` and the `rule_ref` it verifies.

| Rule type | Cases to derive |
|---|---|
| `threshold` | **at** the boundary; **just below**; **just above**. Three scenarios, because off-by-one at a threshold is the single most common business-logic defect. |
| `calculation` | a representative case with concrete inputs and the expected output; the **rounding or precision** case; the **zero or empty** case; any case where an input can be negative or absent. |
| `eligibility` | a subject clearly **in** the set; one clearly **out**; one at the **edge** of the defining predicate. |
| `state-transition` | the legal transition succeeding; the **illegal transition** being refused (see Part 2). |
| `constraint` | the invariant holding; an attempt that would **violate** it being rejected with the state unchanged. |
| `authorization` | the permitted actor succeeding; the **wrong actor** being refused; where relevant, the right actor in the wrong state. |

**Cross-cutting derivations** — apply on top of the type row when the condition
holds, regardless of rule type:

- **Replay.** The story changes state or sends a notification → write a `replay`
  or `banking_grade_idempotency` scenario: the same operation submitted twice
  produces one effect and returns the original result.
- **Race.** Two actors can reach the same rule concurrently on the same entity
  (stock, balance, seat, quota) → write a `race` scenario naming which one wins
  and what the loser observes.
- **Partial failure.** The story spans more than one system of record → write a
  `partial_failure` scenario: the first write succeeded, the second did not, and
  the business-visible outcome is stated.

## Part 2 — Derive from the state machine

For every entity in the story's `entity_refs` that declares `states`, take its
`transitions[]` from `DOMAIN.json`:

1. The transitions this story performs get a happy scenario each.
2. For each such transition, write **one `illegal_transition` scenario**: the
   entity sits in a state from which this transition is not declared, the trigger
   fires, and the expected behaviour is a refusal with the state unchanged and,
   where the entity is audited, an audit event recording the attempt.
3. A transition marked `reversible: false` that the story performs requires a
   `banking_grade_reversibility` scenario exercising its `compensating_action`.

The illegal-transition case is the one that reliably finds real defects, because
implementations tend to guard the transitions they were asked about and leave the
others open.

## Part 3 — Open rules

A rule the breakdown flagged `open: true` has no value to test against. Do not
invent one. Instead:

- Write the scenarios whose shape is knowable without the value, using the linked
  `OQ-n` id in place of the number.
- List the rule id in `rule_coverage.open_rule_ids`.
- The story cannot reach `ready-for-tl` while it references an open rule — the
  schema enforces this. Elaboration surfaces the block; it never guesses a
  threshold to clear it.

## Part 4 — The ledger

Every non-spike story carries `edge_case_ledger[]`: one row per referenced rule,
recording `cases_written` and — where a derivation genuinely does not apply —
`cases_not_applicable` with a `justification`.

A justification is a reason, not a restatement. "No race case: this rule is
evaluated inside the single-writer fulfilment console, so two actors cannot reach
it concurrently" is a justification. "Not applicable" is not.

The ledger is what makes the depth claim checkable. Without it, "we covered the
edge cases" is an assertion; with it, an auditor can count.

## Part 5 — What the sweep must not do

- **Do not pad.** A derived case that restates another case with different words
  is noise. If the boundary and the just-below case collapse into the same
  observable behaviour, write one and record the other as not applicable with
  that reason.
- **Do not migrate a rule into a scenario.** The scenario cites `rule_ref` and
  uses the rule's values; it never re-states the rule as prose. Two copies drift.
- **Do not invent a rule.** If the sweep reveals behaviour no rule covers, that
  is a finding for the breakdown, raised as an open question — not a new rule
  quietly added here. The rule catalogue is the breakdown's artifact and passed
  the three-amigos gate; editing it after the gate voids the review.

## Coverage ledger

Emit `rule_coverage` on the manifest:

- `rules_total` — rules referenced by at least one story in this brief.
- `rules_covered` — of those, how many have at least one derived scenario.
- `uncovered_rule_ids` — the difference. Must be empty for `ready-for-tl`.
- `transitions_total` / `illegal_transition_cases` — the state-machine half.
- `open_rule_ids` — rules still open. Must be empty for `ready-for-tl`.

## Cross-references

- `references/gherkin-templates.md` — the scenario format and the banking-grade
  scenario templates
- `references/invest-checklist.md` — the testability self-check every scenario
  must survive
- `references/elaboration-failure-modes.md` — FM-16 and the coverage gates
