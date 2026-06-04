# ADR-001 — Polyrepo, one service per bounded context

**Status:** Accepted

**Context:** Four epic workstreams (Auth, Inventory, Checkout, Order) with distinct invariants + a cross-cutting Audit concern.

**Decision:** One repo/deployable per context; no shared DB; communicate via sync HTTP (system-internal) + async Kafka events.

**Consequences:** Independent deploy/scale and clear ownership; cost is cross-service contracts (mitigated by ADR-008 outbox) and no cross-context transactions (ADR-004).
