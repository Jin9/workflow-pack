---
story_id: EPIC-INVENTORY-01
context_id: inventory
command: ReserveStock (sync_http, idempotency_required: true, key: confirm_id)
events_emitted: [stock.unit.reserved (domain), stock.unit.released (domain)]
api_spec_endpoint_ref: "inventory-service POST /inventory/reserve"
spec_status: ready-for-implementation
---

# L4 — EPIC-INVENTORY-01 · Reserve stock (last-item race)

- **Command:** `ReserveStock` → stock aggregate; atomic conditional decrement; 30-min TTL.
- **Idempotency:** keyed on confirm id; retry reserves once.
- **Events:** `stock.unit.reserved` on hold; `stock.unit.released` on TTL/failure/timeout/cancel (domain, via outbox).
- **Invariants:** never negative; last-item race → exactly one winner; resolved at confirm not payment.
- **AC ref:** STORY-INVENTORY-01 (system-driven; no customer screen).
