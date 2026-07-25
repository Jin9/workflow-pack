# ADR-008 — Transactional outbox + idempotent order.create retry

**Status:** Accepted (added in the S2.5 loop-back revision, round 1 → round 2)

**Context:** Round-1 plan-review (S2.5) returned **REVISE** on finding RT-2: with sync orchestration (ADR-007) and no outbox, a crash after `inventory.reserve` succeeds but before `order.create`/event-publish leaves an orphan reservation and an at-risk event, and dual writes (DB + Kafka) are not atomic.

**Decision:** (1) Each producing service writes domain events to a **transactional outbox** in the same DB transaction as the state change; a relay publishes to Kafka at-least-once. (2) `order.create` and `checkout.capture` are **idempotent on the confirm/provider id** so checkout can safely retry after a crash. (3) Orphan reservations still auto-release on TTL (ADR-004) as the backstop.

**Consequences:** Closes the dual-write gap and the partial-failure window from RT-2; consumers must be idempotent (already required). Adds an outbox table + relay per producing service. Round-2 plan-review → **PROCEED**.
