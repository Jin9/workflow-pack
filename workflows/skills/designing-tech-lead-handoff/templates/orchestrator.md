# Orchestrator Template (scaffold-v1.1 §3)

**Owner role:** Tech-Lead · Emitted only when an Orchestrator is instantiated
(≥1 of the 3 signals: multi-Aggregate / compensation / temporal).

**File location:** `<workflow_root>/design/architecture/contexts/{ctx}/orchestrators/{orchestrator-id}.md`

`{orchestrator-id}` = `orch-{purpose-slug}` (slug describes the journey, not
the implementation), e.g. `orch-checkout`, `orch-fulfillment`.

---

## Frontmatter

```yaml
---
artifact_type: tl-orchestrator
orchestrator_id: orch-<slug>
context_id: <ctx>
journey_name: "<one-line journey description from start to terminal state>"
project_id: <PROJECT-ID>
brief_id: <EPIC-...>
workload_tier: T1 | T2 | T3
instantiation_signals: [multi_aggregate, compensation, temporal]   # subset, ≥1
aggregates_coordinated: [<Aggregate>, ...]
process_events_emitted:
  - <ctx>.journey.started
  - <ctx>.journey.completed
  - <ctx>.journey.failed
domain_events_consumed:
  - <domain>.<subject>.<verb-past>
commands_issued:
  - <CommandName> (to <ctx> Domain Processor)
timeout_seconds: <int>
compensation_required: true | false
retry_policy: <time-based-delay | batch-inquiry | selective-replay>
created_at: <ISO-8601>
created_by: designing-tech-lead-handoff-<version>
---
```

## Content sections (11, all required)

1. **Journey definition.** Two paragraphs: what journey this coordinates from
   start to terminal state; explicit terminal states (success / failure /
   timeout / compensated).
2. **Instantiation justification.** Cite which of the 3 signals apply and why.
   This is the gate that prevents unjustified Orchestrators.
3. **State machine.** Mermaid `stateDiagram-v2` — the Orchestrator's own
   journey-level state machine, distinct from any Aggregate's domain state
   machine. Explicit `[*] -->` initial and `--> [*]` terminals.
4. **Commands issued.** Table: Command name | Target Aggregate | Target service
   | Transport | Timeout | On failure.
5. **Process Events emitted.** This Orchestrator is the sole source of these
   Process Events. Table: Process Event name | Emitted on | Schema ref |
   Consumers | Retention.
6. **Domain Events consumed.** Table: Domain Event | Source Aggregate | Source
   service | Triggers state transition.
7. **Retry and timeout policy.** Per-step retry semantics, per-step timeout,
   total journey timeout; reference the L3 §6.5 retry pattern.
8. **Compensation actions.** Per failure≠rollback, compensation is the
   EXCEPTION that MUST be explicitly listed; absence means no compensation
   (rely on retry/inquiry instead). State the trigger → compensating command
   and why compensation rather than retry.
9. **Must NOT clauses.** Verbatim per principles doc, for this Orchestrator:
   does not validate business rules; does not decide business correctness;
   does not own Aggregates; contains no business logic.
10. **Architecture smells check.** Self-audit before sign-off:
    - [ ] No `if cart.subtotal > X then Y` (business logic in Orchestrator)
    - [ ] No direct DB writes from this Orchestrator (Aggregate ownership)
    - [ ] No "wait for EventC" hidden-orchestration pattern
    - [ ] Events emitted are Process Events only (`*.journey.*`), not Domain Events
    - [ ] All commands issued return success/failure semantics (sync); no async commands
11. **Open questions.** P2 questions remaining at Orchestrator design level
    (retry tuning, timeout values, compensation completeness).
