# Event catalog — Domain vs Process split (scaffold-v1.1 §6.4 + §7)

The catalog at `design/architecture/02-event-catalog.md` has TWO sections,
reflecting the golden rule. A single event MUST classify into exactly one.
Events that resist classification are an architecture smell (usually an
Orchestrator leaking into business decisions, or a Domain Processor acting as
a coordinator).

## Section A — Domain Events

Emitted ONLY by Domain Processors. Represent business facts. Owner = the
Aggregate that produced the fact. Table columns: Event name | Emitting
Aggregate | Emitting service | Consumers | Key field | Ordering | Retention |
Idempotency strategy.

## Section B — Process Events

Emitted ONLY by Orchestrators. Represent journey/flow progression. Owner = the
Orchestrator. Table columns: Process Event name | Emitting Orchestrator |
Consumers | Key field | Retention | Sequence position. Process Event names are
`<ctx>.journey.<verb>`.

## Naming discipline (§6.4 — validated at L4 generation, step 12)

- **Commands** imperative, business intent. MUST NOT match `Submit*`,
  `Process*`, `Handle*`, `Manage*` (DDD anti-list).
- **Events** past-tense `{domain}.{subject}.{verb-past}`. MUST NOT contain
  technical verbs (`*.processed`, `*.handled`, `*.managed`).
- A violation blocks the offending L4 from `ready-for-implementation` and
  downgrades `output_type` to `partial_design` (FM-TL-05).

## Cross-references (§7.5)

Each event links to the L4 spec (Domain Events) or Orchestrator file (Process
Events) that emits it, and every L4/Orchestrator that consumes it. Bidirectional
linkage is mandatory; an event with no identified consumer is a candidate for
removal → `coverage_gaps[]` `contract_without_consumer`.

## Schema evolution (§7.4)

Backward-compatible additions append to the current version. Renames /
removals / type changes require a version bump + dual-publish window.
