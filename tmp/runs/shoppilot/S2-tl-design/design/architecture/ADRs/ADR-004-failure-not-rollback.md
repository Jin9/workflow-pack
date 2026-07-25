# ADR-004 — Failure ≠ rollback (compensating events, not distributed transactions)

**Status:** Accepted

**Context:** Polyrepo, no shared DB (ADR-001); payment can fail/timeout after stock is reserved.

**Decision:** No distributed/2PC rollback. Failure paths emit compensating actions: payment failure/timeout/cancel → release reserved stock; unpaid reservations auto-release on the 30-min TTL.

**Consequences:** Simple, observable recovery; the only inconsistency window is "reserved but order-create/payment not yet settled", bounded by TTL and closed by ADR-008 (idempotent retry + outbox).
