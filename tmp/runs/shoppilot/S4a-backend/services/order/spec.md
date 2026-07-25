# API Spec (Request/Response)

This document lists all HTTP paths from router/router.go with request/response payloads derived from handler structs.

## Order domain (`app/order/`)

Routes are grouped under `/api/v1/platform/order`. The order aggregate freezes an
immutable snapshot at confirmation (ADR-003), advances through a forward-only
state machine, enforces own-data-only reads, and emits an append-only audit trail
(ADR-006) plus a transactional outbox row on each admin-driven status change (ADR-008).

State machine (forward-only): `awaiting_payment → paid → packing → shipped → delivered`,
plus terminal failure/abort states `payment_failed`, `payment_timeout`, `cancelled`
(cancelled is reachable until the order ships). Backward, self, skip-ahead, and
out-of-terminal transitions are rejected. The pure validator is `canTransition(from, to)`
in `service_transition.go`.

### POST /api/v1/platform/order  (system_internal)

Confirm an order. Idempotent on `confirmId`: a repeat call returns the existing
order with no duplicate create or audit.

Request:

```json
{
  "confirmId": "uuid (required)",
  "snapshot": {
    "customerId": "string (required)",
    "items": [{ "sku": "string", "name": "string", "quantity": 1, "priceMinor": 1000 }],
    "totalMinor": 1000,
    "address": "string (required)"
  }
}
```

Response data: `{ orderNo, state, confirmId, snapshot }`. New orders start in
`awaiting_payment` and emit the `order.confirmed` audit event. 400 on invalid payload.

### GET /api/v1/platform/order/:orderNo  (customer)

Own-data-only read. The caller identity is taken from the `X-Member-ID` header and
must equal the order's `customerId`.

- 200 → `{ orderNo, state, trackingNo?, snapshot }`
- 403 when the requester is not the owner
- 404 when the order does not exist

### POST /api/v1/platform/order/:orderNo/transition  (admin)

Advance the order through the forward-only state machine. Admin-only: the caller
role is read from the `X-Role` header and must be `admin`.

Request: `{ "targetState": "string (required)", "trackingNo": "string (optional)" }`.

- 200 → `{ orderNo, state, trackingNo? }`; emits `order.status.changed` audit + outbox row
- 400 on a backward/illegal transition, or on `shipped` without a `trackingNo`
- 403 when the caller is not an admin
- 404 when the order does not exist

### Kafka consumer: order.payment.captured

Order **consumes** `order.payment.captured` (emitted by checkout) and advances the
order out of `awaiting_payment`: `success → paid`, `failure → payment_failed`,
`timeout → payment_timeout`. Idempotent — an order already past `awaiting_payment`
is a no-op ack. Payload: `{ orderId (uuid), outcome (success|failure|timeout), amountMinor }`.
Wired as `routes["order.payment.captured"] = h.OnPaymentCaptured` in `router/subscriber.go`.

---

## Response envelope (all JSON responses)

Responses are wrapped by the common response envelope. Successful responses include:

```json
{
  "code": "SUCCESS",
  "message": "SUCCESS",
  "data": {},
  "traceId": "string (optional)"
}
```

Error responses use the same envelope with `code`/`message` indicating the error and `data` omitted or null. HTTP status codes are set per handler.

## Naming conventions

- **Routes**: `/api/v1/<domain>/<aggregate>/<action>` — `<domain>` = API namespace (e.g. `platform`), `<aggregate>` = the `app/` package, `<action>` = verb. e.g. `POST /api/v1/platform/product/create`.
- **Kafka events**: `<DOMAIN>_<AGGREGATE>_<ACTION>` in UPPER_SNAKE, mirroring the route segments (event `<action>` is usually past tense). e.g. `PLATFORM_PRODUCT_CREATED`.

Full conventions live in `.github/skills/implementing-go-template-requirements/`.
