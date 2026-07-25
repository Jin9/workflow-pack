# ADR-003 — Order owns immutable price/items/address snapshots

**Status:** Accepted

**Context:** A placed order must never drift when the catalog price/name later changes (STORY-ORDER-01).

**Decision:** At `order.create`, copy price, line items, and shipping address into the order row as an immutable snapshot. Order reads serve the snapshot, not live catalog data.

**Consequences:** Trustworthy tracking + dispute trail; small storage duplication. Address snapshot is PII (encrypt at rest; own-data-only).
