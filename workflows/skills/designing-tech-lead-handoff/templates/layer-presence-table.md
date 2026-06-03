# Per-Context Layer-Presence Table (scaffold-v1.1 §2.3)

**File location:** part of `<workflow_root>/design/architecture/L2-DOMAIN.md`

The L2 document MUST include this table. Absence of layer-presence rationale is
incomplete L2. The Gateway is the project-wide shared LB+Kong+token-plugin; no
context owns a custom Gateway. The rationale column is mandatory — "following
the pattern" is NOT a valid rationale.

| Context | Gateway | Orchestrator | Domain Processor | Adapter | Rationale |
|---|---|---|---|---|---|
| `<ctx>` | shared | `—` or `✓ (orch-<slug>)` | `✓` or `—` | `—` or `✓ (adapt-<slug>)` | Why these layers; cite the Orchestrator instantiation signal (multi-Aggregate / compensation / temporal) when an Orchestrator is present, or state which of the 3 signals are absent when it is not. |

Rules:

- Instantiate an Orchestrator only when ≥1 of the 3 signals fires
  (multi-Aggregate coordination / compensation required / temporal control);
  name it `orch-<purpose-slug>` and cite the signal in the rationale.
- Default routing when no signal fires: Gateway → Domain Processor directly
  (single-Aggregate ops, simple validations, queries, CRUD).
- An Orchestrator with no citable signal is an architecture smell (remove it);
  a flow with a signal that routes direct to a Domain Processor is the missing
  Orchestrator smell.
