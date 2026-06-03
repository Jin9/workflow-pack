# Architecture-smells self-audit (scaffold-v1.1 §5 + §3.10)

A discipline gate, not optional. Run BEFORE L3 sign-off (Procedure step 11) and
the per-Orchestrator check at step 7. Each failed check requires either
(a) revision to remove the smell, or (b) an explicit ADR naming the smell as a
knowing trade-off. Record each as an `architecture_smells[]` entry
(`status: pass|fail`, `resolution: revised|adr|n/a`, `adr_ref` when adr). An
unresolved `fail` downgrades `output_type` to `partial_design`.

## L3 architecture-smells checklist (10 items — copy verbatim, scaffold §5)

```
- [ ] No Orchestrator contains business logic (validation, decision rules, calculations)
- [ ] No single service controls multiple domains' Aggregates
- [ ] Events used as facts only, not as commands ("EventX happened" not "do X")
- [ ] No Domain waits for another Domain to emit (no hidden orchestration)
- [ ] No shared library contains business meaning (utilities only)
- [ ] No Domain Processor knows journey/flow logic
- [ ] No Adapter carries domain semantics (protocol translation only)
- [ ] Process Events emitted only from Orchestrators (verified against §3 Orchestrator catalog)
- [ ] Domain Events emitted only from Domain Processors (verified against §6 Domain Processor design)
- [ ] No `if event.x then send command y` pattern (use saga/orchestrator instead)
```

## Per-Orchestrator smells checklist (5 items — scaffold §3.3.10)

```
- [ ] No `if cart.subtotal > X then Y` (business logic in Orchestrator)
- [ ] No direct DB writes from this Orchestrator (Aggregate ownership)
- [ ] No "wait for EventC" hidden-orchestration pattern
- [ ] Events emitted are Process Events only (`*.journey.*`), not Domain Events
- [ ] All commands issued return success/failure semantics (sync); no async commands
```
