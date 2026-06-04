---
story_id: EPIC-CHECKOUT-01
context_id: checkout
command: ConfirmOrder (sync_http, idempotency_required: true, key: client_idempotency_key)
events_emitted: [order.purchase.created (domain)]
api_spec_endpoint_ref: "checkout-service POST /checkout/confirm"
spec_status: ready-for-implementation
---

# L4 — EPIC-CHECKOUT-01 · Confirm order at a server-computed total

- **Command:** `ConfirmOrder` → checkout aggregate; server-computes `total = subtotal − coupon + shipping`; re-validates coupon; sync `inventory.reserve` then `order.create`.
- **Idempotency:** client idempotency key; duplicate confirm returns the same order; no second order/reservation (now crash-safe via ADR-008 outbox + idempotent `order.create`).
- **Events:** `order.purchase.created` (domain, via outbox).
- **Invariants:** client total never trusted; coupon expired → neutral error, no order; out-of-stock at confirm.
- **AC ref:** STORY-CHECKOUT-01.
