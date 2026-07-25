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

## Naming conventions

- **Routes**: `/api/v1/<domain>/<aggregate>/<action>` — `<domain>` = API namespace (e.g. `platform`), `<aggregate>` = the `app/` package, `<action>` = verb. e.g. `POST /api/v1/platform/product/create`.
- **Kafka events**: `<DOMAIN>_<AGGREGATE>_<ACTION>` in UPPER_SNAKE, mirroring the route segments (event `<action>` is usually past tense). e.g. `PLATFORM_PRODUCT_CREATED`.

Full conventions live in `.github/skills/implementing-go-template-requirements/`.

## Endpoints

### POST `/api/v1/platform/inventory/reserve` (system_internal)

Holds stock for an in-flight order. Idempotent on `confirmId`: a repeated `confirmId` returns the existing reservation without decrementing stock again (ADR-004). Each item is decremented atomically (ADR-002).

Request:

```json
{
  "confirmId": "uuid (required)",
  "items": [
    { "sku": "string (required)", "qty": "int > 0 (required)" }
  ]
}
```

Success `200` data:

```json
{ "reservationId": "string", "expiresAt": "RFC3339 (now + 30m)" }
```

Errors: `400 BAD_REQUEST` on insufficient stock or invalid body; `404 NOT_FOUND` on an unknown SKU. Emits audit `stock.reserved`.

### POST `/api/v1/platform/inventory/release` (system_internal)

The SAGA compensation / TTL-expiry target. Returns a reservation's held stock to available and marks it released. Idempotent: an already-released reservation is a no-op success.

Request:

```json
{ "reservationId": "uuid (required)", "reason": "string (required)" }
```

Success `200` data:

```json
{ "reservationId": "string", "status": "released" }
```

Errors: `404 NOT_FOUND` on an unknown reservation. Emits audit `stock.released`.

### POST `/api/v1/platform/inventory/adjust` (admin)

Sets a SKU's absolute available count (manual stock correction). Enforces `available >= reserved`.

Request:

```json
{ "sku": "string (required)", "newAvailable": "int (required, may be 0)", "reason": "string (required)" }
```

Success `200` data:

```json
{ "sku": "string", "newAvailable": "int" }
```

Errors: `400 BAD_REQUEST` when `newAvailable` is below the reserved hold; `404 NOT_FOUND` on an unknown SKU. Emits audit `stock.adjusted`.

## Consumed events

### `order.status.changed`

Emitted by the order service. Payload:

```json
{ "orderId": "uuid (required)", "reservationId": "uuid (required)", "status": "string (required)" }
```

On a cancellation status the inventory releases the reservation via the idempotent release path (ADR-004). Any other status is an acknowledged no-op.
