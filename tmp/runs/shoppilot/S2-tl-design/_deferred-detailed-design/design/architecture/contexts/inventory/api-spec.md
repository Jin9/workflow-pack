# inventory-service — API spec (v1.0)

Changelog: v1.0 — initial.

| Method | Path | Contract | Auth | Notes |
|---|---|---|---|---|
| POST | `/inventory/reserve` | `inventory.reserve` | system_internal | atomic conditional decrement; keyed on confirm id; 30-min TTL |
| POST | `/inventory/release` | `inventory.release` | system_internal | compensating; idempotent on reservation id |
| POST | `/admin/inventory/adjust` | `inventory.adjust` | admin | mandatory reason; reject below reserved |

Consumes: `order.payment.captured` (reserved→sold / release), `order.status.changed` (cancel→release).
Emits: `stock.unit.reserved`, `stock.unit.released`, `stock.level.adjusted`. Stock never negative.
