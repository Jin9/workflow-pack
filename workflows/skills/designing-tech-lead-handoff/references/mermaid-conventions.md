# Mermaid conventions (scaffold-v1.1 §9)

## Primary diagram types

- **`sequenceDiagram`** — multi-actor flows; default for L4 sequence diagrams
  when 2+ services or actors are involved.
- **`stateDiagram-v2`** — Aggregate state machines, Orchestrator journey state
  machines.
- **`erDiagram`** — data model in `contexts/{ctx}/data-model.md` (see
  `templates/erd.md`).
- **`flowchart`** — fallback only when sequence and state don't fit; avoid
  when either would work (it reads worst at scale).

## Sequence diagram style

- One participant per service/actor; do not collapse services into one box.
- `->>` sync request, `-->>` sync response, `->` async (event emit).
- Annotate transport when not obvious (`sync HTTP`, `async Kafka`).
- Note boxes for important state changes: `Note over PAY: persist payment row`.

## State diagram style

- `stateDiagram-v2` (not legacy `stateDiagram`).
- Explicit initial `[*] --> initial: label` and terminal `state --> [*]`.
- Compound states allowed for nested journeys; flatten if depth > 2.
- Transition labels are events or conditions, not implementation details.

## Runtime / deployment

Mermaid is inadequate for runtime topology in this house style. Emit ASCII
`infra-topology.md` (one fenced block, one screen — see
`templates/infra-topology.md`).

The consolidated architecture / HLD / ER / DDD-boundary view is the **one
exception** to "Mermaid only": it is emitted as a single offline 4-tab
`.drawio` (L1–L4) — but **only** via the deterministic generator
`scripts/spec_to_drawio.py` from `architecture.spec.json` (see
`references/drawio-architecture-conventions.md`, step 8.5). **Never hand-author
`.drawio` XML.**
