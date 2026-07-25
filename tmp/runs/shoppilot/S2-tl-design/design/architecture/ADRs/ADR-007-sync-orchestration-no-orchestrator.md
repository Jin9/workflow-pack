# ADR-007 — Sync orchestration in checkout-service, no standalone Orchestrator

**Status:** Accepted

**Context:** The checkout journey touches multiple aggregates (stock + order), needs compensation (release on failure), and has a temporal element (TTL) — the three signals the house style uses to instantiate an Orchestrator. The architecture-smells self-audit flags "no Orchestrator" as a deviation.

**Decision:** For the single-merchant MVP with exactly one cross-context journey, do **not** stand up a separate Orchestrator service. `checkout-service` orchestrates the reserve→create path with synchronous, idempotent calls.

**Consequences (and why it's safe):** Avoids premature infrastructure for one journey. The partial-failure window (reserve succeeds, order-create fails) is the cost — bounded by the reservation TTL (ADR-004) and **closed by ADR-008** (idempotent `order.create` retry + transactional outbox). **Revisit** if a second cross-context journey appears → promote to a real Orchestrator. Recorded in `architecture_smells` as `fail → resolution: adr (ADR-007)`.
