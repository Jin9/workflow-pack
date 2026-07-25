---
story_id: EPIC-CHECKOUT-02
context_id: checkout
command: CaptureMockPayment (sync_http, idempotency_required: true, key: provider_event_id)
events_emitted: [order.payment.captured (domain)]
api_spec_endpoint_ref: "checkout-service POST /checkout/capture"
spec_status: ready-for-implementation
---

# L4 — EPIC-CHECKOUT-02 · Capture mock payment (replay-safe)

- **Command:** `CaptureMockPayment` → checkout aggregate; calls mock PSP via `client_psp` gateway.
- **Idempotency:** dedupe on provider event id; duplicate callback applies once; captured amount must equal server total.
- **Events:** `order.payment.captured {success|failure|timeout}` (domain, via outbox) → order + inventory consume.
- **Invariants:** no PAN/CVV stored (PCI boundary); failure/timeout releases stock (ADR-004).
- **AC ref:** STORY-CHECKOUT-02.
