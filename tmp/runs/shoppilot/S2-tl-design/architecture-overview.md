# ShopPilot — architecture overview (S2 TL Design)

> Component map, event catalog, tech stack, NFR mapping, and load-bearing decisions for the ShopPilot MVP, derived
> from the S1 BA pack. Diagrams: [`diagrams/shoppilot-architecture.drawio`](diagrams/shoppilot-architecture.drawio)
> (HLD) and [`diagrams/shoppilot-erd.drawio`](diagrams/shoppilot-erd.drawio) (ERD).

## Bounded contexts

Split by **epic workstream** (never tech layer). Four contexts + one cross-cutting concern:

| Context | Epic | Owns | Key invariants |
|---|---|---|---|
| **Auth** | EPIC-AUTH | Customer credentials, sessions, refresh-token families | no account enumeration · atomic refresh rotation · replay → family revoke |
| **Inventory** | EPIC-INVENTORY | Stock (available/reserved/sold), reservations, TTL | never negative · last-item race → exactly one winner · 30-min TTL release |
| **Checkout** | EPIC-CHECKOUT | Cart, server-side totals, coupon, mock payment | server-computed total · idempotent confirm · provider-replay dedup · no PAN/CVV |
| **Order** | EPIC-ORDER | Orders, frozen snapshots, fulfillment state machine, shipment | own-order isolation · immutable snapshot · forward-only transitions |
| **Audit** *(cross-cutting)* | all | Append-only audit trail keyed by `audit_id` | every state-change audited · never logs PII / tokens / PAN |

## Component map

| Service | Aggregates | Datastore | Sync deps (HTTP) | Consumes (events) | Emits (events) |
|---|---|---|---|---|---|
| `auth-service` | auth, session | MySQL + Redis | — | — | `auth.login`, `auth.refresh`, `auth.logout` |
| `inventory-service` | stock, reservation | MySQL | — | `order.payment_captured` (→ sold/release), `order.cancelled` (→ release) | `stock.reserved`, `stock.released`, `stock.adjusted` |
| `checkout-service` | cart, checkout, coupon, payment | MySQL | → `inventory-service` (reserve), → `order-service` (create) | — | `order.created`, `order.payment_captured` |
| `order-service` | order, shipment | MySQL | — | `order.payment_captured` (→ paid/failed) | `order.status_changed` |
| `web` | storefront, admin | — | → all four services (per S3 contracts) | — | — |

> `component_map.dependencies[]` reference contract names only (no orphan deps). The authoritative machine form is
> the `tl-design.json` `component_map` produced by the full S2 skill — this table is the human-readable mirror.

## Primary flows

- **Login (AUTH-01/02):** `web → auth-service` → access (15-min) + refresh (14-day) tokens; refresh rotates
  atomically, replay revokes the family. Every attempt → `auth.*` audit (generic failure message, no enumeration).
- **Checkout confirm (CHECKOUT-01 + INVENTORY-01):** `web → checkout-service /confirm` (idempotency key) →
  server-computes `total = subtotal − coupon + shipping`, re-validates coupon → **sync** `inventory reserve`
  (atomic, race-safe) → **sync** `order create` (awaiting-payment, snapshots frozen) → emits `order.created`.
- **Payment (CHECKOUT-02):** `web → checkout-service /capture` (mock) → `payment.provider_callback` deduped on
  provider event id → emits `order.payment_captured {success|failure|timeout}` →
  `order-service` consumes (→ paid / payment-failed / payment-timeout, creates shipment on success) and
  `inventory-service` consumes (→ reserved becomes sold, or released).
- **Tracking & fulfillment (ORDER-01/02):** `web → order-service /orders/:id` (own-order isolation, frozen snapshot);
  admin transitions paid→packing→shipped(tracking required)→delivered, forward-only, idempotent → `order.status_changed`.
- **Stock admin (INVENTORY-02):** `web(admin) → inventory-service /adjust` (mandatory reason; reject below reserved) → `stock.adjusted`.

## Event catalog

Async over Kafka, **at-least-once + idempotent consumers = effectively-once**; partition key = `audit_id` (per-run
FIFO ordering). Dotted name = logical event; topic key = `<DOMAIN>_<AGGREGATE>_<ACTION>` (UPPER_SNAKE).

| Event | Topic key | Producer | Consumers |
|---|---|---|---|
| `order.created` | `SHOP_ORDER_CREATED` | checkout | order, (audit) |
| `order.payment_captured` | `SHOP_ORDER_PAYMENTCAPTURED` | checkout | order, inventory, (audit) |
| `order.status_changed` | `SHOP_ORDER_STATUSCHANGED` | order | (audit), notification |
| `stock.reserved` / `stock.released` / `stock.adjusted` | `SHOP_STOCK_*` | inventory | (audit) |
| `auth.login` / `auth.refresh` / `auth.logout` | `SHOP_AUTH_*` | auth | (audit) |

## Tech stack

- **Backend:** Go + **Gin** (HTTP) + **Kafka** (events) + **MySQL/RDS** (per-service DB) + **Redis** (sessions,
  rate-limit, cache). 4-layer DDD + CQRS house style (handlers → services → domain → access). `log/slog` only.
- **Frontend:** React/TS (**Next.js**, app router); typed API clients generated from the S3 contracts; design tokens from the S1.5 UX pack.
- **Integrations (mock for MVP):** mock PSP (tokenizes card; swappable for a real gateway — e.g. Omise), mock courier (tracking).
- **Per-repo:** Docker + GitLab CI; module path `gitlab.com/b2c-e-commerce-platform/platform/backend/<service>`; branch `develop`.

## NFR → design mapping

| NFR (from S1 stories) | Design response |
|---|---|
| **Idempotency** (double-click confirm, refresh, provider replay, reserve) | idempotency key on `/confirm`; single-use refresh rotation; provider-event-id dedup on capture; confirm-key dedup on reserve |
| **Concurrency / last-item race** | atomic conditional stock decrement at confirm; exactly one winner; stock never negative; resolved at confirm, not payment |
| **Reservation TTL** | 30-min hold; background sweep auto-releases; release also on payment fail/timeout/cancel |
| **Auditability** | append-only audit `{event, actor, ts, before, after, outcome, audit_id}` on every state-change; `audit_id` threads the run |
| **PII** (email, phone, name, address) | encrypt at rest; redact in logs (`<PII:REDACTED:CLASS=…>`); own-data-only access; PDPA B.E. 2562 lawful basis |
| **PCI-DSS v4.0** | no PAN/CVV stored; mock PSP tokenizes; payment context isolated to checkout-service |
| **Price integrity** | totals server-computed only; order freezes price/items/address snapshot at creation (no later catalog drift) |
| **State-machine integrity** | order transitions forward-only; shipped requires tracking; backward transitions rejected |

## Load-bearing decisions (ADR candidates)

1. **Polyrepo, one service per epic context** — independent deploy/scale; communicate via HTTP + Kafka; no shared DB.
2. **Reserve-on-confirm, synchronous + atomic** — the last-item race must be decided at confirm time (not payment),
   so reserve is a sync, idempotent call with an atomic stock decrement.
3. **Order owns immutable snapshots** — price/items/address copied into the order at creation; catalog changes never drift a placed order.
4. **Failure ≠ rollback** — payment failure/timeout/cancel **release** stock via compensating events; no implicit distributed rollback.
5. **Mock PSP behind a gateway interface** (`client_psp.go`) — keeps the PCI boundary clean and swap-in of a real PSP a one-adapter change.
6. **Audit is cross-cutting and append-only** — every service writes its own audit + publishes to a shared topic; tokens/PII/PAN never logged.

## Open questions (carried from S1, non-blocking)

- **OQ-1** — does the customer confirm delivery, or only the admin mark `delivered`? (affects `order` state machine; resolver: PM)
- **OQ-2** — abandoned-cart handling beyond the 30-day purge (notify vs silent)? (resolver: Marketing)
