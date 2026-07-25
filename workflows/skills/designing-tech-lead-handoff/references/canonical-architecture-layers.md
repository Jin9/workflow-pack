# Canonical architecture layers (scaffold-v1.1 §2)

Every system in this house style is four layers. Every context conforms even
when not all layers are populated.

## The four layers

**Gateway** — single technical entry point per project (NOT per-context).
LB + Kong + token-verify plugin + standard observability. Responsibilities:
Auth / Routing / Rate Limit / Observability. Must NOT contain business logic,
journey/flow logic, domain decisions, or payload-content-based routing.
Scaffold treatment: one paragraph in L2; no per-context Gateway document.

**Orchestrator (Process Manager)** — coordinates multi-step journeys.
Instantiated only when justified. Coordinates steps, tracks journey progress,
handles retries/timeouts/compensation, communicates via commands and events
only. Must NOT validate business rules, decide business correctness, or own
Aggregates. Key principle: *"the Orchestrator answers 'what's next?' but never
'is this correct?'"* In this system-design blueprint an Orchestrator is
**identified** as a process-manager component (recorded in the layer-presence
table + an ADR + a `process_aggregates[]` entry on the L3 diagram page); its
detailed state-machine spec is a separate detailed-design concern, out of scope
here.

**Domain Processor** — owns business correctness via Aggregates. Business rules
and invariants, Aggregate ownership, state transitions, emits Domain Events.
Must NOT know journey/flow logic or control other domains. A microservice may
host multiple Aggregates; each Aggregate has its own commands and owns its
events. Covered by L3-TECHNICAL-STRATEGY.md per context.

**Protocol Adapter** — anti-corruption layer for external partners.
Legacy/external integration, protocol handling (HTTP/SOAP/MQ/gRPC), retry /
circuit breaker / auth. Must NOT contain business logic or carry domain
semantics. Documented inside L3 "external dependencies"; per-adapter scaffold
only when non-trivial.

## Orchestrator instantiation criteria

Orchestrators are NOT instantiated by default. Instantiate only when ≥1 fires:

- **Signal 1 — Multi-Aggregate coordination.** The flow touches ≥2 Aggregates
  (within or across contexts).
- **Signal 2 — Compensation required.** ≥1 step needs a compensating action
  when a downstream step fails (journey-level, not Aggregate-level).
- **Signal 3 — Temporal control needed.** Explicit timeouts, scheduled
  retries, or step delays.

**Default when no signal fires:** Gateway → Domain Processor directly
(single-Aggregate ops, simple validations, queries, CRUD).

**Smell:** an Orchestrator with no citable signal is unjustified (remove it);
a flow with a signal that routes direct to a Domain Processor is the missing
Orchestrator. Both are caught by the §5 architecture-smells gate.

## Per-context layer-presence declaration

The L2 document MUST include the layer-presence table
(`templates/layer-presence-table.md`). Absence of rationale is incomplete L2;
"following the pattern" is not a valid rationale.
