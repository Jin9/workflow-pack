# Connectivity — ShopPilot

| From | To | Kind | Contract | Notes |
|---|---|---|---|---|
| web | auth-service | sync | `auth.login`, `auth.refresh` | tokens in body; never localStorage |
| web | checkout-service | sync | `checkout.confirm`, `checkout.capture` | client idempotency key on confirm |
| web | order-service | sync | `order.get`, `order.transition` | own-data-only; admin transitions |
| web | inventory-service | sync | `inventory.adjust` | admin only |
| checkout-service | inventory-service | sync (system_internal) | `inventory.reserve`, `inventory.release` | atomic reserve at confirm |
| checkout-service | order-service | sync (system_internal) | `order.create` | idempotent on confirm id |
| checkout-service | mock-psp | sync (external) | capture | tokenized; PCI boundary |
| order-service | mock-courier | sync (external) | tracking | shipment on paid |
| checkout-service | Kafka | async (outbox) | `order.purchase.created`, `order.payment.captured` | partition key audit_id |
| order-service | Kafka | async (outbox) | `order.status.changed` | consumed by inventory + notification |
| inventory-service | Kafka | async (outbox) | `stock.unit.reserved/released`, `stock.level.adjusted` | audit |
| inventory-service | Kafka | consume | `order.payment.captured`, `order.status.changed` | reserved→sold / release on cancel |
| order-service | Kafka | consume | `order.payment.captured` | →paid/failed/timeout |

All sync calls are mTLS intra-cluster; all event flows pass through a per-service transactional outbox (ADR-008).
