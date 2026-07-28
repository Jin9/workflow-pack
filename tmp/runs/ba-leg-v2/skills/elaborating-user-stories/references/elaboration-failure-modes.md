# Elaboration failure modes

Binding rules for Procedure step 7. Codes carry over from the predecessor skill
unchanged so the fleet vocabulary and the audit trail survive the split. The
codes that belong to the breakdown stage (FM-04, FM-05, FM-12, FM-14) are not
this skill's and are not repeated here — they fired before the three-amigos gate.

## Preconditions this stage re-checks fail-closed

The engine's gate already enforces both; the skill checks them again because a
skill that trusts its caller is a skill that can be invoked wrongly.

- **`breakdown.state` must be `ready-for-amigos`.** Any other value →
  `failure_code: breakdown_not_agreed`, emit nothing.
- **`breakdown.blocks_elaboration` must be false.** A P1 governance gap reaching
  this stage means something upstream was relaxed → `governance_p1_unresolved`,
  emit nothing. Do not elaborate around a blocker; do not downgrade it.

## The gates

| Code | Condition | Result |
|---|---|---|
| **FM-01** | composite linguistic quality of the written criteria below 5.0 | `needs-work`, `untestable_criteria` — refuse handoff rather than ship criteria a tester cannot automate |
| **FM-02** | an unresolved P1 in compliance, tipping-off, retention, audit schema, personal-data class, regulatory citation or dual approval | `blocked` |
| **FM-06** | a forbidden tipping-off term reached a customer-facing string in a written scenario | `blocked`, substitute the approved phrase, set `legal_signoff_required` |
| **FM-11** | any emitted file fails its schema | emit nothing; never a malformed pack |
| **FM-13** | personal data would reach the output | `pii_echo_blocked`, auto-redact |
| **FM-15** | hidden-requirements sweep coverage is `partial` or `skipped` | downgrade to `needs-work` plus a P2 open question recording the gap (FM-02 takes precedence) |
| **FM-16** | a story whose `banking_grade_concerns.idempotency.status` is `applies` carries no `banking_grade_idempotency` scenario | hard schema failure — enforced by `schemas/story-sidecar.json` and re-checked here |
| **FM-17** | Frame 4 activated and a required sub-topic is uncovered | `coverage_score: partial` plus a P2 open question |
| **FM-18** | `rule_coverage.uncovered_rule_ids` is non-empty | `needs-work` — a referenced rule with no derived scenario is an untested rule |
| **FM-19** | `rule_coverage.open_rule_ids` is non-empty | `needs-work`, `open_rule_blocks_story` — a story cannot be ready against a rule whose value nobody has decided |

FM-18 and FM-19 are new with this skill. They exist because the breakdown now
makes rules countable, so "did we test every rule" became a question with an
answer instead of a matter of opinion.

## Per-story mandatory scenario floor

Every non-spike story carries at least three acceptance criteria, and among them
at least one of each:

1. a `happy` scenario;
2. an `error`, `edge_case`, `boundary`, `replay`, `race`, `partial_failure`,
   `illegal_transition` or `wrong_actor` scenario;
3. a `banking_grade_*` scenario.

Missing the third on a state-changing or notifying story is an automatic
INVEST-Testable failure (AP-8.4), not a style note.

## The seven forced banking-grade rows

`pii_fields`, `audit_events`, `idempotency`, `reversibility`, `authn_authz`,
`regulatory`, `tipping_off` — all seven present on every story, each with a
`status` and a `justification` of at least ten characters. A `not_applicable`
row must cite the workflow class that makes it inapplicable.

**This is the depth that does not get trimmed.** The reports around it got
shorter; the forced evaluation did not. An empty row is FM-11, a hard failure.

Where the domain model already answers the question, use it: a story touching an
entity whose fields carry a `pii_class` other than `none` cannot honestly write
`pii_fields: not_applicable`.

## Definition of Ready

The predecessor emitted eight booleans that were true in every recorded output.
They are replaced by `dor: pass | fail` plus `dor_failures[]`, required and
non-empty only when the verdict is `fail`.

This loses nothing: a schema that already enforces Gherkin format, the happy and
error and banking-grade floor, priority, dependencies and sizing is asserting
those same eight facts structurally. Recording them a second time as booleans
that can never be false is ceremony, and ceremony in an audit trail is worse than
absent — it looks like evidence.

## State

- `ready-for-tl` — no P1 gap, no uncovered or open rule, sweep coverage
  `complete`. Schema-enforced.
- `needs-work` — content-complete but a gate above failed; carries
  `failure_state`.
- `blocked` — a P1 governance gap is unresolved; carries `failure_state`.

## Cross-references

- `references/rule-anchored-edge-cases.md` — FM-18 and FM-19's coverage ledger
- `references/hidden-requirements-frames.md` — FM-15 and FM-17
- `references/anti-patterns.md` — AP-8.2, AP-8.4 and the full catalogue
- `references/gherkin-templates.md` — the banking-grade scenario templates
