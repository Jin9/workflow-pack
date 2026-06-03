# Orchestrator scaffold — how to think about it (scaffold-v1.1 §3)

The fill-in shape is `templates/orchestrator.md`. This file is the *reasoning*
guide for step 7.

- **Instantiate only with a cited signal.** multi-Aggregate / compensation /
  temporal (see `canonical-architecture-layers.md`). The instantiation
  justification section (template §2) is the gate.
- **Slug names the journey, not the implementation:** `orch-checkout`,
  `orch-fulfillment` — never `orch-service-x`.
- **State machine is journey-level**, distinct from any Aggregate's domain
  state machine. Use `stateDiagram-v2` with explicit `[*] -->` and `--> [*]`.
- **Commands out, events in.** The Orchestrator issues commands to Domain
  Processors (sync, success/failure semantics — no async commands) and reacts
  to Domain Events. It never writes a DB or owns an Aggregate.
- **Process Events are sole-sourced here.** `<ctx>.journey.{started,
  completed,failed}` — emitted ONLY by this Orchestrator, never by a Domain
  Processor.
- **Compensation is the documented exception.** Under failure≠rollback, list
  each trigger → compensating command and *why compensation not retry*;
  absence means rely on retry/inquiry.
- **Run the 5-item smells self-audit** (`architecture-smells.md`) before
  sign-off; business logic in the Orchestrator is the cardinal smell ("answers
  'what's next?' never 'is this correct?'").
