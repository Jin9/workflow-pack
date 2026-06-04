# ADR-006 — Cross-cutting, append-only audit keyed by audit_id

**Status:** Accepted

**Context:** Banking-grade traceability: every state change must be reconstructable; PII/tokens/PAN must never leak.

**Decision:** Each service writes its own append-only audit `{event, actor, ts, before, after, outcome, audit_id}` and publishes to a shared audit topic. `audit_id` is the correlation + Kafka partition key end-to-end.

**Consequences:** Full reconstruction + tamper evidence; retention 5y (order/financial, Revenue Code) / 1y (auth/stock). Redaction enforced in the logging layer (see observability spec).
