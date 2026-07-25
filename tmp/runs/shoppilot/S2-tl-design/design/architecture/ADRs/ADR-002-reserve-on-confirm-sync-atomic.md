# ADR-002 — Reserve-on-confirm, synchronous + atomic

**Status:** Accepted

**Context:** The last-item race (STORY-INVENTORY-01) must resolve to exactly one winner, at confirm time, never at payment.

**Decision:** `checkout.confirm` makes a synchronous, idempotent `inventory.reserve` call performing an atomic conditional decrement (`available = available - n WHERE available >= n`). Reservation carries a 30-min TTL.

**Consequences:** Deterministic single winner; stock never negative. Reserve is keyed on the confirm/order id so a retry reserves once. Unpaid reservations auto-release on TTL (ADR-004).
