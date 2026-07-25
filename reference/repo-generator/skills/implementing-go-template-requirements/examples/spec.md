# Example Spec — Invoice (single-endpoint reference)

A minimal example of the requirement document the
`implementing-go-template-requirements` skill consumes. It demonstrates the spec
format with exactly one HTTP endpoint and one Kafka consumer. Copy this into a
generated repo's root `spec.md` and feed an item to the skill, e.g.
"implement spec.md item 1".

## Response envelope (all JSON responses)

```json
{
  "code": "SUCCESS",
  "message": "SUCCESS",
  "data": {},
  "traceId": "string (optional)"
}
```

Error responses use the same envelope with `code`/`message` indicating the error
and `data` null. HTTP status codes are set per handler.

## Naming conventions

- **Routes**: `/api/v1/<domain>/<aggregate>/<action>` (e.g. `POST /api/v1/platform/invoice/create`).
- **Kafka events**: `<DOMAIN>_<AGGREGATE>_<ACTION>` UPPER_SNAKE (e.g. `PLATFORM_PAYMENT_SETTLED`).

Full conventions live in `.github/skills/implementing-go-template-requirements/`.

## 1. Invoice / Create

### Request

**Endpoint**: `POST /api/v1/platform/invoice/create`

```json
{
  "orderId": "uuid (required)",
  "amount": "number (required, > 0)",
  "currency": "string (required, ISO-4217)"
}
```

### Response

**Success (200 OK)**:
```json
{
  "code": "SUCCESS",
  "message": "SUCCESS",
  "data": { "invoiceId": "uuid", "status": "PENDING" },
  "traceId": "string (optional)"
}
```

**Error (400 / 500)**:
```json
{
  "code": "BAD_REQUEST | INTERNAL_ERROR",
  "message": "human-readable error",
  "data": null,
  "traceId": "string (optional)"
}
```

## 2. Kafka Events

### PLATFORM_PAYMENT_SETTLED (consumed)

**Payload**:
```json
{
  "invoiceId": "uuid (required)",
  "paidAt": "string (required, RFC3339)"
}
```

**Consumer action**: look up the invoice by `invoiceId` and set its status to
`PAID`. Idempotent — re-delivery of the same event is a no-op if already `PAID`.
