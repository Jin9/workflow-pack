# API Spec (Request/Response)

This document lists all HTTP paths from router/router.go with request/response payloads derived from handler structs.

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

## Endpoints

### POST /api/v1/platform/checkout/confirm

Confirms a checkout. The server computes the order total from the trusted cart (the client never supplies a total), re-validates any coupon, then synchronously reserves stock and creates the order (ADR-007), appends `order.purchase.created` to the transactional outbox (ADR-008), and audits `order.confirmed` (ADR-006). The whole flow is replay-safe via the client idempotency key (ADR A2): a repeated key returns the stored response.

Request:

```json
{
  "cartId": "string (required)",
  "address": "string (required)",
  "coupon": "string (optional)",
  "idempotencyKey": "string (required, uuid)"
}
```

Response data:

```json
{
  "orderId": "string",
  "totalMinor": 0
}
```

Outcomes:

| Condition | HTTP | Code |
|---|---|---|
| Confirmed (or idempotent replay) | 200 | `SUCCESS` |
| Validation error (missing/invalid field) | 400 | `BAD_REQUEST` |
| Coupon expired or unknown | 400 | `BAD_REQUEST` |
| Out of stock | 400 | `BAD_REQUEST` |
| Auth required | 401 | `UNAUTHORIZED` |
| Unexpected error | 500 | `INTERNAL_ERROR` |

### POST /api/v1/platform/checkout/capture

Captures an authorized payment for an order. Deduped on `providerEventId` (a replayed webhook returns the prior outcome). The claimed `amount` is validated against the server-recorded order total before any payment call. A deterministic mock PSP performs the capture (no PAN/CVV is ever accepted or stored). On success, appends `order.payment.captured` to the outbox (ADR-008) and audits `order.payment.captured` (ADR-006).

Request:

```json
{
  "orderId": "string (required, uuid)",
  "providerEventId": "string (required)",
  "amount": 0
}
```

Response data:

```json
{
  "orderId": "string",
  "amountMinor": 0,
  "captured": true
}
```

Outcomes:

| Condition | HTTP | Code |
|---|---|---|
| Captured (or idempotent replay) | 200 | `SUCCESS` |
| Validation error (missing/invalid field) | 400 | `BAD_REQUEST` |
| Amount mismatch (rejected) | 400 | `BAD_REQUEST` |
| Payment declined | 400 | `BAD_REQUEST` |
| Payment timeout | 503 | `SERVICE_UNAVAILABLE` |
| Unexpected error | 500 | `INTERNAL_ERROR` |

## Audit events emitted

- `order.confirmed`
- `order.payment.captured`

## Outbox events appended (ADR-008)

- `order.purchase.created` (on confirm)
- `order.payment.captured` (on capture)

## Naming conventions

- **Routes**: `/api/v1/<domain>/<aggregate>/<action>` — `<domain>` = API namespace (e.g. `platform`), `<aggregate>` = the `app/` package, `<action>` = verb. e.g. `POST /api/v1/platform/checkout/confirm`.
- **Kafka events**: `<DOMAIN>_<AGGREGATE>_<ACTION>` in UPPER_SNAKE, mirroring the route segments (event `<action>` is usually past tense). e.g. `PLATFORM_CHECKOUT_CONFIRMED`.

Full conventions live in `.github/skills/implementing-go-template-requirements/`.
