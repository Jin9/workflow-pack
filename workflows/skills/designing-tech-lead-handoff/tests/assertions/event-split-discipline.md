# Assertion — event-split discipline

On a `design` output:

- Every event referenced anywhere (`l4_specs[].events_emitted[]`,
  `orchestrators[]` content) appears in EXACTLY ONE of
  `event_catalog.domain_events` or `event_catalog.process_events`.
- `domain_events[]` are emitted only by Domain Processors (have
  `emitting_aggregate` + `emitting_service`); `process_events[]` are emitted
  only by Orchestrators (`emitting_orchestrator` matches an `orchestrators[]`
  `orchestrator_id`) and match `^[a-z]+\.journey\.[a-z]+$`.
- Every `l4_specs[].command.name` does NOT match `Submit*|Process*|Handle*|Manage*`.
- Every event name matches `{domain}.{subject}.{verb}` (3 dot-segments) and
  carries no technical verb (`*.processed|*.handled|*.managed`).
- Every event has ≥1 known consumer; an event with none → a
  `coverage_gaps[]` `contract_without_consumer` entry exists.

FAIL ⇒ block the offending L4 from `ready-for-implementation` and downgrade to
`partial_design` (FM-TL-05).
