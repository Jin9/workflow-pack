---
story_id: EPIC-ORDER-02
context_id: order
command: AdvanceFulfillment (sync_http, idempotency_required: true, key: order_id+target_state)
events_emitted: [order.status.changed (domain)]
api_spec_endpoint_ref: "order-service POST /admin/orders/:orderNo/transition"
spec_status: ready-for-implementation
---

# L4 — EPIC-ORDER-02 · Advance fulfillment (admin)

- **Command:** `AdvanceFulfillment` → order aggregate; paid→packing→shipped(tracking required)→delivered.
- **Idempotency:** guarded by current-state precondition; re-submit no-ops; forward-only.
- **Events:** `order.status.changed` (domain, via outbox) → inventory (release on cancel) + notification.
- **Invariants:** illegal backward transition rejected; shipped requires tracking; admin role only; before/after audited.
- **AC ref:** STORY-ORDER-02 (back-office; no customer screen).
