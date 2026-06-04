# order-service — API spec (v1.0)

Changelog: v1.0 — initial.

| Method | Path | Contract | Auth | Notes |
|---|---|---|---|---|
| POST | `/orders` | `order.create` | system_internal | idempotent on confirm id; freezes price/items/address snapshot |
| GET | `/orders` | `order.get` | customer | own-data-only list |
| GET | `/orders/:orderNo` | `order.get` | customer | own-data-only; snapshot + status timeline |
| POST | `/admin/orders/:orderNo/transition` | `order.transition` | admin | forward-only; shipped requires tracking; idempotent |

Consumes: `order.payment.captured` (→paid/failed/timeout, shipment on success).
Emits (via outbox): `order.status.changed`. Sync to mock-courier for tracking.
