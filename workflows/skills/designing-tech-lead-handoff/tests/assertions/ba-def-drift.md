# Assertion — BA definition drift

`schemas/input.json` `definitions` (Epic, Story, Stakeholder,
AcceptanceCriterion, BankingGradeRow, GovernanceGap, Translations) are
**inline-copied** from `ba-squad/skills/eliciting-banking-brief/schemas/output.json`
`definitions` (value-handoff; no cross-file `$ref` because no artifact-handoff
skill exists yet — GAP-03).

Assertion: each inlined definition is structurally equal to the corresponding
definition in the live BA output schema (same `required`, `properties`,
`enum`, `pattern`, `oneOf`/`allOf`). The pipeline pins the BA skill at
`^1.4.0`, so a BA bump to `1.5.x` can drift these — this check is the sync
obligation flagged in `audit/RATIONALE.md §6 (R4)`.

Procedure: load both schemas, compare the named subtrees; any structural delta
⇒ FAIL with the drifted definition named (action: re-sync the inline copy and
re-review).
