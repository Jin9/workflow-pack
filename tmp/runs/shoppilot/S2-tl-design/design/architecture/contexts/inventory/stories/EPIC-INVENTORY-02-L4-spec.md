---
story_id: EPIC-INVENTORY-02
context_id: inventory
command: AdjustStock (sync_http, idempotency_required: false)
events_emitted: [stock.level.adjusted (domain)]
api_spec_endpoint_ref: "inventory-service POST /admin/inventory/adjust"
spec_status: ready-for-implementation
---

# L4 — EPIC-INVENTORY-02 · Adjust stock (admin)

- **Command:** `AdjustStock` → stock aggregate; receive/count/write-off with a mandatory reason.
- **Idempotency:** none (each adjustment is a distinct intentional entry), but guarded by a precondition.
- **Events:** `stock.level.adjusted` (domain, via outbox) with before/after.
- **Invariants:** may not reduce available below currently reserved; admin role only; reason mandatory; audited.
- **AC ref:** STORY-INVENTORY-02 (back-office; no customer screen).
