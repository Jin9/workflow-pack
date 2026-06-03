# Infra Topology Template (ASCII)

**Parent:** [`../templates.md`](../templates.md)
**Owner role:** [Tech-Lead](../roles.md) · **`template_version`:** 0.1.0

A pixel/ASCII rendering of the runtime topology in a single fenced code block. Companion to [`./infra-summary.md`](./infra-summary.md). The user explicitly asked for "pixel design in MD" — this template gives Tech-Lead the canonical shape.

**File location:** `<workflow_root>/design/architecture/infra-topology.md`

---

## Required sections

1. `# Topology — <Workflow Name>`
2. `## Layers` — short paragraph naming each layer (gateway, processor, data, observability) and what runs there.
3. `## Diagram` — fenced code block, ASCII only, no Unicode beyond the standard box-drawing set used in `README.md`.
4. `## Legend` — explains arrow types (`──▶` sync HTTP, `==▶` async event, `╌╌▶` cron / system-internal).

---

## Diagram conventions

- **Boxes:** services, databases, queues, infra components.
- **Arrows:**
  - `──▶` — synchronous HTTP request
  - `==▶` — async Kafka event (publishes onto a topic)
  - `╌╌▶` — system-internal call (cron sweeper, scheduled job, in-process invocation)
- **Top-down ordering by data-flow:** entrypoints (frontend, gateway) at top; services in the middle; data stores + bus + observability at bottom.
- **Group boxes** (gateway, services, data) with thin frames; use whitespace to separate groups.
- **One topology = one big diagram.** Don't split into multiple diagrams; the goal is one screen the operator can scan.

---

## File shape (example, drawn from the dry-run #1 reference architecture)

```markdown
# Topology — ShopPilot MVP (B2C E-Commerce)

## Layers

- **Edge / UI** — Next.js (Server Components + route handlers; HttpOnly cookies; CSP).
- **Processor** — 7 Go/Gin microservices behind no API gateway in MVP (the Next.js route handlers play that role).
- **Data** — PostgreSQL per service (schema-per-service); Kafka bus for cross-service events.
- **Observability** — slog → Loki; Prometheus → Tempo (OTLP); Grafana for dashboards.

## Diagram

```
                   ┌──────────────────────────┐
                   │        Customer          │
                   │        (browser)         │
                   └─────────────┬────────────┘
                                 │ HTTPS
                                 ▼
                   ┌──────────────────────────┐
                   │  Next.js (frontend-web)  │
                   │  - SSR + RSC pages       │
                   │  - /api/proxy/* handlers │
                   │  - withAuth (6-step)     │
                   │  - Idempotency-Key gen   │
                   └─────────────┬────────────┘
                                 │ POST /api/v1/<svc>/<agg>/<action> (Bearer JWT or X-Internal-Secret)
        ┌───────────┬────────────┼────────────┬───────────┬───────────┐
        ▼           ▼            ▼            ▼           ▼           ▼
   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
   │identity│  │catalog │  │inventory│ │ cart   │  │checkout│  │ order  │
   │ :8081  │  │ :8082  │  │ :8083   │ │ :8084  │  │ :8085  │  │ :8086  │
   └───┬────┘  └───┬────┘  └────┬───┘  └───┬────┘  └───┬────┘  └───┬────┘
       │           │            │           │           │           │
       ▼           ▼            ▼           ▼           ▼           ▼
   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
   │identity│  │catalog │  │inventory│ │ cart   │  │checkout│  │ order  │
   │  _db   │  │  _db   │  │  _db    │ │  _db   │  │  _db   │  │  _db   │
   └────────┘  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘
                                                                      │
                                                                      │ ──▶ POST /api/v1/payment/intent/create (X-Internal-Secret)
                                                                      ▼
                                                                 ┌────────┐
                                                                 │payment │
                                                                 │ :8087  │
                                                                 └───┬────┘
                                                                     ▼
                                                                 ┌────────┐
                                                                 │payment │
                                                                 │  _db   │
                                                                 └────────┘

      ════════════════════ Kafka: ecom.order-state.events ════════════════════
                                       │
                ┌──────────────────────┼──────────────────────┐
                │ payment ══▶          │       order ══▶      │
                │ payment.completed    │ order.cancelled       │
                ▼                      ▼                       ▼
           ┌────────┐             ┌────────┐              ┌────────┐
           │ order  │             │inventory│            │inventory│
           │consumer│             │consumer │            │consumer │
           └────────┘             └────────┘             └────────┘
              (state-driven; reads current state via FOR UPDATE)

      ════════════════════ Kafka: ecom.inventory.events ════════════════════
                inventory ══▶ events.reservation.expired ──▶ order consumer

         ╌╌▶ inventory.sweeper (every 30s, FOR UPDATE SKIP LOCKED, batch 200)
         ╌╌▶ payment.expiry-sweeper (every 60s, FOR UPDATE SKIP LOCKED)
         ╌╌▶ outbox-relay (every 5s per service)
```

## Legend

- `──▶` synchronous HTTP request
- `══▶` async Kafka event (per-orderId or per-sku partition key)
- `╌╌▶` system-internal cron / sweeper

```

---

## Negative examples

### Negative #1 — Multiple disconnected diagrams

A topology MD with three separate diagrams (one for sync, one for async, one for sweepers) violates the "one screen" rule. Reviewer-L2 catches: `cross_component_maintainability_issue` (low → advisory) — operator can't see the whole picture.

### Negative #2 — Boxes without ports / paths

```
   ┌────────┐     ┌────────┐
   │identity│ ──▶ │catalog │
   └────────┘     └────────┘
```

What's missing: ports, route shape, auth requirement. The diagram is decorative not informational. Reviewer-L2: `architecture_risk` (medium) — operator can't infer the connectivity from the diagram alone.
