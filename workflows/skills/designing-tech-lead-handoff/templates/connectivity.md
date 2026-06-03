# Connectivity Template

**Parent:** [`../templates.md`](../templates.md)
**Owner role:** [Tech-Lead](../roles.md) · **`template_version`:** 0.1.0

The end-to-end request and event flows. Operator's tracing aid: "where does request X go?" / "what fires when event Y lands?". Companion to [`./infra-summary.md`](./infra-summary.md) and [`./infra-topology.md`](./infra-topology.md).

The user explicitly asked for "frontend call gateway / gateway call service / service call API" wired up. This run has no API gateway — Next.js route handlers are the gateway.

**File location:** `<workflow_root>/design/architecture/connectivity.md`

---

## Required sections

1. `# Connectivity — <Workflow Name>`
2. `## Synchronous request flows` — table OR sequence-style block per spine path
3. `## Asynchronous event flows` — table per Kafka topic: producer → consumers → effect
4. `## System-internal flows` — sweepers, cron, in-process invocations
5. `## Auth boundaries` — which auth tier (none / customer JWT / admin JWT / internal-secret) gates each path
6. `## Failure modes` — what happens on a downstream error in each spine flow

---

## File shape

```markdown
# Connectivity — ShopPilot MVP

## Synchronous request flows

### Customer journey: browse → cart → checkout → simulate-payment → see paid

```
Browser
  │  GET / (Server Component)
  ▼
Next.js page → Next.js route handler `/api/proxy/catalog/category/list`
  │  POST → catalog:8082/api/v1/catalog/category/list
  ▼
Catalog service → SELECT FROM categories → returns JSON envelope
```

(Repeat per spine step.)

### Customer login

```
Browser → POST /api/proxy/identity/auth/login
       → Next.js route handler reads request body
       → POST identity:8081/api/v1/identity/auth/login
       → Identity validates + bcrypt.CompareHashAndPassword
       → Returns {accessToken, refreshToken, role}
       ← Next.js route handler sets HttpOnly cookies (access 15m, refresh 14d)
       ← Browser receives 200 + Set-Cookie headers
```

### Checkout commit (orchestrated)

```
Browser → POST /api/proxy/checkout/checkout/commit (Idempotency-Key header)
       → withAuth (6-step) attaches Bearer
       → POST checkout:8085/api/v1/checkout/checkout/commit

Step 1: Checkout → cart:8084/api/v1/cart/cart/read
Step 2: Checkout → identity:8081/api/v1/identity/profile/read (for buyerEmail)
Step 3: Checkout → catalog:8082/api/v1/catalog/product/detail (per item, parallel via errgroup)
Step 4: Checkout → inventory:8083/api/v1/inventory/reservation/create (X-Internal-Secret)
Step 5: Checkout → order:8086/api/v1/order/internal/create-from-checkout (X-Internal-Secret)
Step 6: Checkout → payment:8087/api/v1/payment/intent/create (X-Internal-Secret)
Step 7: Checkout → cart:8084/api/v1/cart/cart/clear-on-checkout (best-effort)

Returns {orderId, paymentIntentId, total, currency}
```

## Asynchronous event flows

### `ecom.order-state.events` (per-orderId partitioned)

| Event | Producer | Consumers | Consumer effect |
|---|---|---|---|
| `events.payment.completed` | payment | order, inventory | order: PENDING_PAYMENT → PAID; inventory: RESERVED → COMMITTED |
| `events.payment.failed` | payment | order, inventory | order: PENDING_PAYMENT → PAYMENT_FAILED; inventory: RESERVED → RELEASED |
| `events.payment.expired` | (sweeper-driven, NOT emitted by payment in MVP) | order, inventory | (deferred — see KNOWN_ISSUES) |
| `events.order.cancelled` | order | inventory | inventory: state-driven release per current reservation status |

### `ecom.inventory.events`

| Event | Producer | Consumers | Consumer effect |
|---|---|---|---|
| `events.reservation.expired` | inventory.sweeper | order | order: PENDING_PAYMENT → PAYMENT_EXPIRED |

### `ecom.catalog.events`

| Event | Producer | Consumers | Consumer effect |
|---|---|---|---|
| `events.product.created` | catalog | inventory | inventory: seed `stock_levels(sku)` row |

## System-internal flows

| Job | Cadence | Owner | Effect |
|---|---|---|---|
| inventory.reservation.sweep-expired | 30s | inventory | flips RESERVED + expired → EXPIRED; emits events.reservation.expired |
| payment.intent.expiry-sweeper | 60s | payment | flips REQUIRES_PAYMENT + expired → EXPIRED (no event) |
| outbox-relay | 5s per service | each service | drains outbox_events to Kafka; marks published_at |

## Auth boundaries

| Path | Auth tier | Notes |
|---|---|---|
| `/api/v1/identity/auth/register|login` | none | public |
| `/api/v1/identity/auth/refresh|logout` | (refresh token in body) | rotate jti in tx |
| `/api/v1/identity/profile/*` | customer JWT | `claims.sub == user_id` |
| `/api/v1/catalog/product/list|detail` | none | public |
| `/api/v1/catalog/product/create|update|soft-delete` | admin JWT | role=ADMIN |
| `/api/v1/inventory/stock/read|bulk-read` | customer JWT | |
| `/api/v1/inventory/stock/adjust` | admin JWT | |
| `/api/v1/inventory/reservation/create|release` | internal-secret | constant-time compare |
| `/api/v1/cart/*` | customer JWT | scoped by claims.sub |
| `/api/v1/checkout/*` | customer JWT + Idempotency-Key | |
| `/api/v1/order/list-mine|detail|cancel-mine` | customer JWT | scoped by owner |
| `/api/v1/order/list-admin|update-status-admin|cancel-on-checkout-failure` | admin JWT or internal-secret | |
| `/api/v1/order/internal/create-from-checkout` | internal-secret | constant-time compare |
| `/api/v1/payment/intent/create` | internal-secret | from Checkout |
| `/api/v1/payment/intent/simulate` | customer JWT + ownership check | |
| `/api/v1/payment/intent/callback` | HMAC-SHA256 signature | webhook only |

## Failure modes

| Spine flow | Failure | Compensation |
|---|---|---|
| Step 4 (reservation.create) fails | none — no state mutated | return error to client |
| Step 5 (order.create) fails after step 4 OK | Checkout calls inventory.reservation.release(orderId), 3 retries | on retry-exhaustion: log CRITICAL + saga DEGRADED; reservation TTL (15min) is the safety net |
| Step 6 (payment.intent.create) fails after step 5 OK | Checkout calls order.cancel-on-checkout-failure THEN inventory.reservation.release | same retry policy |
| Step 7 (cart.clear-on-checkout) fails after success | log warning; do NOT roll back order/payment | cart inconsistency is cosmetic for the test path |
| `events.payment.completed` consumer crashes | Kafka rebalance redelivers; consumed_events PK + state-driven guard prevents double-apply |
```

---

## Negative examples

### Negative #1 — Spine flow without auth boundary annotated

A connectivity doc that lists "Step 5: Checkout → order.create-from-checkout" without naming `X-Internal-Secret` leaves Reviewer-L2 unable to spot a secret-leak. Tag: `cross_component_security_issue` (medium) → TL.

### Negative #2 — Async event with no failure mode

```markdown
| events.payment.completed | payment | order | order transitions to PAID |
```

Missing: what happens if the consumer is down? What happens on partial commit? The doc claims a clean handoff but real-world Kafka has rebalance storms, late deliveries, and partial reads. Tag: `cross_component_error_propagation_issue` (medium) → TL.
