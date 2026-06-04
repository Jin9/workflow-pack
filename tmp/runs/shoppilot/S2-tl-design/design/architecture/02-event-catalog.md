# Event Catalog — ShopPilot (split: domain / process)

Async over Kafka, at-least-once + idempotent consumers = effectively-once. Partition key = `audit_id`
(per-run FIFO). Names are 3-part past-tense `{domain}.{subject}.{verb}`.

## Section A — Domain Events (emitted by aggregates / Domain Processors)

| Event | Aggregate | Service | Consumers | Key | Retention |
|---|---|---|---|---|---|
| `auth.session.issued` | session | auth-service | audit | audit_id | 1y |
| `auth.session.rotated` | session | auth-service | audit | audit_id | 1y |
| `auth.family.revoked` | session | auth-service | audit | audit_id | 1y |
| `order.purchase.created` | order | checkout-service | order-service, audit | audit_id | 5y |
| `order.payment.captured` | order | checkout-service | order-service, inventory-service, audit | audit_id | 5y |
| `order.status.changed` | order | order-service | inventory-service, notification, audit | audit_id | 5y |
| `stock.unit.reserved` | stock | inventory-service | audit | audit_id | 1y |
| `stock.unit.released` | stock | inventory-service | audit | audit_id | 1y |
| `stock.level.adjusted` | stock | inventory-service | audit | audit_id | 5y |

## Section B — Process Events (emitted by Orchestrators)

None. No standalone Orchestrator is instantiated — checkout's multi-aggregate + compensation +
temporal concerns are handled by a transactional outbox + TTL-bounded compensation (see
`ADRs/ADR-007-*` and `ADRs/ADR-008-*`). Revisit if a second cross-context journey appears.
