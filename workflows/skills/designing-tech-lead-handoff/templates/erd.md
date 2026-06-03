# ERD Template (per microservice)

**Parent:** [`../templates.md`](../templates.md)
**Owner role:** [Tech-Designer](../roles.md) · **`template_version`:** 0.1.0

One ERD MD per microservice. The user's philosophy: 1 Domain → ≥1 microservice → ≥1 aggregate boundary → ≥1 table. The ERD captures the third arrow (aggregate boundary → table) per service.

**File location:** `<workflow_root>/design/components/<svc>/erd.md`

Pairs with the `tables[]` field in `td.json` (which is high-level) — this MD is the full picture: columns, indexes, constraints, relationships, invariants.

---

## Required sections

1. `# ERD — <Service Name>`
2. `## Schema owner` — name + Postgres schema (e.g., `inventory` service owns the `inventory` schema)
3. `## Aggregate boundaries` — list each aggregate this service contains; one paragraph per
4. `## Tables` — one section per table:
   - Columns: name, type, NULL/NOT NULL, default, comment
   - Primary key
   - Indexes (incl. partial indexes)
   - Constraints (CHECK, UNIQUE, FK)
   - Owner aggregate
5. `## Relationships` — narrative + ASCII / mermaid ER diagram
6. `## Invariants` — bullet list of business rules guaranteed at the data layer (e.g., "no negative stock", "one default address per user", "order.status only writable by Order service")
7. `## Concurrency model` — lock-order pin, optimistic vs pessimistic locking choices, expected hot rows
8. `## Migration history` — table: migration file, what it adds, when applied
9. `## Snapshot vs live-source policy` — for any column that snapshots data from another service (e.g., `order_items.priceSnapshot` from Catalog), explain why and how it's frozen
10. `## Change log`

---

## File shape (example — inventory service from dry-run #1)

```markdown
# ERD — Inventory Service

## Schema owner

- Service: `inventory`
- Postgres schema: `inventory`
- Default `search_path`: `inventory, public`

## Aggregate boundaries

This service contains two aggregates:

- **StockLevel** (root: `stock_levels.sku`) — the source of truth for current quantity per SKU.
- **Reservation** (root: `reservations.id`) — a transient hold on stock, created by Checkout, committed/released by event consumers + sweeper.

Future split: if reservation throughput exceeds 1k qps OR sweeper backlog > 10k expired rows / tick, the Reservation aggregate splits into its own microservice; the StockLevel aggregate stays.

## Tables

### `stock_levels`

| Column | Type | Null | Default | Comment |
|---|---|---|---|---|
| sku | TEXT | NOT NULL | — | PK |
| available_qty | INT | NOT NULL | 0 | sellable inventory |
| reserved_qty | INT | NOT NULL | 0 | held by open reservations |
| sold_qty | INT | NOT NULL | 0 | committed via payment.completed |
| version | INT | NOT NULL | 0 | OPTLOCK counter |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | |

- **PK:** `sku`
- **Indexes:** none beyond PK; reads are point-lookups by sku.
- **Constraints:**
  - `CHECK (available_qty >= 0)`
  - `CHECK (reserved_qty >= 0)`
  - `CHECK (sold_qty >= 0)`
- **Owner aggregate:** StockLevel.

### `reservations`

| Column | Type | Null | Default | Comment |
|---|---|---|---|---|
| id | UUID | NOT NULL | — | PK (uuidv7) |
| order_id | UUID | NOT NULL | — | FK to order.orders.id (cross-service ref; no FK enforced — schema isolation) |
| sku | TEXT | NOT NULL | — | FK to stock_levels.sku (within-schema FK enforced) |
| qty | INT | NOT NULL | — | reserved units |
| status | TEXT | NOT NULL | 'RESERVED' | enum: RESERVED, COMMITTED, RELEASED, EXPIRED |
| expires_at | TIMESTAMPTZ | NOT NULL | NOW() + INTERVAL '15 min' | TTL anchor |
| released_at | TIMESTAMPTZ | NULL | NULL | set when status moves off RESERVED |
| release_reason | TEXT | NULL | NULL | enum: PAYMENT_FAILED, PAYMENT_EXPIRED, ORDER_CANCELLED, EXPIRED, ADMIN_FORCE |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | |

- **PK:** `id`
- **Indexes:**
  - `INDEX(order_id, sku)` — lookup-by-order-and-sku for state-driven consumers.
  - `INDEX(status, expires_at) WHERE status = 'RESERVED'` — sweeper scan.
- **Constraints:**
  - `CHECK (status IN ('RESERVED', 'COMMITTED', 'RELEASED', 'EXPIRED'))`
  - `FK (sku) REFERENCES stock_levels(sku)`.
- **Owner aggregate:** Reservation.

### `outbox_events`, `consumed_events`, `idempotency_keys`, `stock_adjustments`

(Detail tables analogous to above; omitted here for brevity in the example.)

## Relationships

```
stock_levels (sku PK)
   ▲
   │ FK (sku)
   │
reservations (id PK, order_id, sku)
   ▲
   │ logical-FK (order_id) — to order.orders.id
   │ NOT enforced (schema isolation; cross-service refs are by ID only)
   ▼
order.orders (foreign schema; not in this ERD)
```

## Invariants

- **No negative quantities:** `available_qty + reserved_qty + sold_qty` is non-decreasing under normal operation; per-row CHECK constraints + tx-level guards in handlers + pre-UPDATE checks on adjust.
- **Reserved + sold conservation:** total physical inventory = `available_qty + reserved_qty + sold_qty`. The sweeper preserves this by always swapping `reserved_qty -= qty` with `available_qty += qty` in one tx.
- **Reservation TTL:** every RESERVED row has `expires_at = created_at + 15min`. Sweeper enforces.
- **Status monotonicity:** RESERVED → {COMMITTED, RELEASED, EXPIRED}. Terminal states never transition back.

## Concurrency model

- **Lock order pin:** `stock_levels(sku)` FIRST, THEN `reservations(id)`. Multi-SKU calls lock SKUs in lexicographic order. Documented at every lock point.
- **Optimistic vs pessimistic:** pessimistic via `SELECT ... FOR UPDATE` on stock_levels and reservations. `version` column on stock_levels for optimistic check on adjust path (reads acquire `FOR UPDATE`, but the version field exists for cross-service audit).
- **Hot rows:** highly-trafficked SKUs (top sellers); per-SKU lock contention is the throughput ceiling. Mitigation: shard hot SKUs across multiple stock-level rows if needed (deferred to v2).

## Migration history

| Migration | Adds | Applied |
|---|---|---|
| `001_stock_levels.up.sql` | `stock_levels` table + CHECK constraints | initial |
| `002_reservations.up.sql` | `reservations` table + indexes | initial |
| `003_stock_adjustments.up.sql` | `stock_adjustments` audit table | initial |
| `004_outbox_events.up.sql` | `outbox_events` for events.reservation.expired | initial |
| `005_consumed_events.up.sql` | `consumed_events` for consumer dedup | initial |
| `006_idempotency_keys.up.sql` | `idempotency_keys` for reservation.create | initial |

## Snapshot vs live-source policy

This service owns no snapshot columns — all data is live source-of-truth for stock state. (Compare `order.order_items.priceSnapshot` which IS a snapshot from Catalog — see Order service ERD.)

## Change log

| Date | Author | Change |
|---|---|---|
| 2026-05-07 | Tech-Designer (Opus 4.7 xHigh) | Initial ERD; lock-order pin documented |
```

---

## Negative examples

### Negative #1 — ERD lacking constraints / invariants

```markdown
## Tables

### stock_levels

| Column | Type |
|---|---|
| sku | TEXT |
| available_qty | INT |
| reserved_qty | INT |
| sold_qty | INT |
```

What Reviewer-L1 catches:

1. No PK named, no NOT NULL, no defaults, no CHECK constraints. The "no negative stock" invariant is purely vibes-based without `CHECK (available_qty >= 0)`. Tag: `latent_bug` (high) — at the schema level.
2. No `Indexes`, no `Owner aggregate`, no `Relationships` — fails schema-doc completeness.

### Negative #2 — Cross-service FK enforced at DB layer

```markdown
- FK (order_id) REFERENCES order.orders(id)
```

What's wrong:

1. Cross-service FK violates schema isolation (per `cross-cutting.persistence`'s schema-per-service rule). If Order's schema is in another database, this FK is broken; if same database, it couples deploy lifecycles. Tag: `architecture_risk` (high) → TL or `cross_component_data_flow_issue` at L2.
2. Cross-service refs MUST be by ID (UUID) only, NOT enforced at the DB layer. Note the rule clearly in the ERD.
