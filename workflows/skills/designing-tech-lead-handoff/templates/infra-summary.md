# Infra Summary Template

**Parent:** [`../templates.md`](../templates.md)
**Owner role:** [Tech-Lead](../roles.md) · **`template_version`:** 0.1.0

A human-readable MD listing every runtime component the workflow ships with. Sits at the front of the design subtree as the operator's mental model.

**File location:** `<workflow_root>/design/architecture/infra-summary.md`

Pairs with [`./infra-topology.md`](./infra-topology.md) (ASCII diagram) and [`./connectivity.md`](./connectivity.md) (request/event flow).

---

## Fields (rendered as MD sections, not frontmatter)

- `## Services` — table: name, language/runtime, port, ownership (which EPIC, which microservice it implements), `complexity` from `tl-components.json`
- `## Databases` — table: name, engine + version, schema owner (= service name), tables (high-level count; full ERD in per-service erd.md)
- `## Caches` — table: name, engine + version, used by, eviction policy
- `## External / MAP APIs` — table: name, vendor, used by, endpoint, auth method (env var name only — never the secret)
- `## Message Bus` — table: broker (Kafka/Redpanda/etc.), topics summary (full catalog in events.md), ordering guarantees
- `## Observability` — table: log aggregator, metrics scraper, trace collector, dashboards, alerts
- `## Deployment topology` — paragraph: where does this run? (docker-compose for local; K8s namespace for SIT/UAT/PRD; cloud provider)

---

## File shape

```markdown
# Infra Summary — <Workflow Name>

Generated: 2026-05-07
Tech-Lead: Claude Opus 4.7 xHigh

See also: [topology](./infra-topology.md) · [connectivity](./connectivity.md) · [events](./events.md)

---

## Services

| Name | Runtime | Port | Owns | Complexity |
|---|---|---:|---|---|
| identity | Go 1.23 + Gin | 8081 | EPIC_AUTH (registration, login, refresh, profile, addresses) | standard |
| catalog | Go 1.23 + Gin | 8082 | EPIC_CATALOG (products, categories) | standard |
| inventory | Go 1.23 + Gin | 8083 | EPIC_INVENTORY (stock levels, reservations, sweeper) | complex |
| cart | Go 1.23 + Gin | 8084 | EPIC_CART (cart line items, fan-out cart.read) | standard |
| checkout | Go 1.23 + Gin | 8085 | EPIC_CHECKOUT (orchestrator: cart→catalog→inventory→order→payment) | complex |
| order | Go 1.23 + Gin | 8086 | EPIC_ORDER (state machine, sole writer of order.status) | complex |
| payment | Go 1.23 + Gin | 8087 | EPIC_PAYMENT (mock intent, dedup'd callback) | complex |
| frontend-web | Next.js 14 + TS + Tailwind | 3000 | EPIC_FRONTEND (customer journey UI) | complex |

## Databases

| Name | Engine | Schema owner | Table count | Notes |
|---|---|---|---:|---|
| identity_db | PostgreSQL 16 | identity service | 3 | users, addresses, refresh_tokens |
| catalog_db | PostgreSQL 16 | catalog service | 5 | products (NUMERIC price), categories, product_images, status_history, outbox_events |
| inventory_db | PostgreSQL 16 | inventory service | 6 | stock_levels (CHECK >=0), reservations, stock_adjustments, outbox_events, consumed_events, idempotency_keys |
| cart_db | PostgreSQL 16 | cart service | 3 | carts, cart_items (UNIQUE merge), cart_clear_idempotency |
| checkout_db | PostgreSQL 16 | checkout service | 2 | idempotency_keys (INSERT-ON-CONFLICT race-safe), saga_log |
| order_db | PostgreSQL 16 | order service | 6 | orders, order_items (immutable), status_history, outbox_events, consumed_events, admin_action_log |
| payment_db | PostgreSQL 16 | payment service | 3 | payment_intents, payment_callback_dedup, outbox_events |

> Per BA-locked decision: PostgreSQL only; pgx driver via `common/database`.

## Caches

| Name | Engine | Used by | Eviction |
|---|---|---|---|
| (none for MVP) | — | — | — |

> Cache deferred to v2; sweeper-driven invalidation TBD when added.

## External / MAP APIs

| Name | Vendor | Used by | Endpoint | Auth env var |
|---|---|---|---|---|
| (mock — no externals in MVP) | — | — | — | — |

## Message Bus

| Property | Value |
|---|---|
| Broker | Apache Kafka 3.x (Redpanda 23.x acceptable for local) |
| Topics | `ecom.order-state.events`, `ecom.inventory.events`, `ecom.catalog.events` |
| Partition strategy | per-orderId for order/payment/reservation events; per-sku for catalog product events |
| Retention | 7 days production, 1 day local |

> Full catalog: [events.md](./events.md)

## Observability

| Layer | Component | Notes |
|---|---|---|
| Logs | slog → stdout → Loki via Promtail | structured fields per `observability-spec.md` |
| Metrics | Prometheus scraping `/metrics` per service | standard HTTP metrics + per-domain counters |
| Traces | OpenTelemetry → Tempo (OTLP gRPC) | W3C `traceparent` propagation |
| Dashboards | Grafana | "p95 by endpoint", "error rate", "saga in-flight" |
| Alerts | Prometheus rules | error rate > 5% / 5min, p95 breach, saga stuck > 15min |

> Local stack: docker-compose snippet at `B2C E-Commerce Platform/observability/docker-compose.yml`.

## Deployment topology

Local: 7 backend services + frontend + Postgres-per-service + Kafka + observability stack via `docker-compose up`. SIT/UAT/PRD: Kubernetes; one deployment per service; one StatefulSet for Kafka and Postgres. Per `cross-cutting.persistence`, schema-per-service with no cross-service tables.
```

---

## Negative examples

### Negative #1 — Service table is content-thin

```markdown
## Services

| Name | Notes |
|---|---|
| identity | Auth service |
| catalog | Catalog service |
```

What Reviewer-L2 / Plan-Reviewer should catch:

1. `Runtime`, `Port`, `Owns`, `Complexity` columns missing — operators can't tell what runs where. Tag: `architecture_risk` (medium) → TL.
2. `Notes` paraphrases name — content-free.

### Negative #2 — External APIs hide auth or fabricate vendors

```markdown
## External / MAP APIs

| Name | Vendor | Auth |
|---|---|---|
| stripe | Stripe | API key in code |
```

What's wrong:

1. "API key in code" is a security finding by itself — secrets in code violates the run's locked decisions. Tag: `cross_component_security_issue` (high) → TL.
2. If Stripe isn't actually integrated (MVP runs mock payment), this is `unstated_assumption` (high) — TL hallucinated an integration.
