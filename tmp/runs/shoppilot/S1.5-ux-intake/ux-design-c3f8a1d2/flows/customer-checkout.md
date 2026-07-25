---
flow_id: customer-checkout
related_epics: [EPIC-CHECKOUT, EPIC-INVENTORY]
related_stories: [STORY-CHECKOUT-01, STORY-CHECKOUT-02, STORY-INVENTORY-01]
---

# Flow — Customer Checkout (happy path)

Browse → add to cart → checkout (server-computed total) → mock payment success.

```mermaid
sequenceDiagram
    actor C as Customer
    participant P as /products/:sku
    participant Cart as /cart
    participant CO as /checkout
    participant Pay as /checkout/payment
    participant API as Order/Stock/Payment API
    C->>P: add to cart
    C->>Cart: review items
    C->>CO: confirm (address, coupon, idempotency-key)
    CO->>API: compute total server-side (subtotal − coupon + shipping)
    API->>API: re-validate coupon; reserve stock (atomic, TTL 30m)
    API-->>CO: order created (awaiting-payment) with reserved stock
    Note over CO,API: duplicate confirm returns same order (STORY-CHECKOUT-01)
    C->>Pay: pay now
    Pay->>API: mock provider capture (amount == server total)
    API-->>Pay: success — order PAID, reserved→sold, shipment + notification
    Note over Pay,API: duplicate provider callback applies once (STORY-CHECKOUT-02)
    Pay-->>C: success → /orders/:orderNo
```

## Screen-by-screen
1. **`/` , `/products/:sku`** — browse, `common.action.add_to_cart`.
2. **`/cart`** — OrderSummary, `common.action.checkout`; empty → `screen.cart.empty-state`.
3. **`/checkout`** — server-computed OrderSummary (e.g. 1200 − 100 coupon + 60 shipping = 1160 THB), `common.action.confirm`.
4. **`/checkout/payment`** — `common.action.pay`; `screen.payment.processing-state`; success → order detail.

## Edge cases
- Coupon expired during browsing → `field.coupon.error-expired`; no order, no reservation.
- Last unit taken by a concurrent buyer → `error.out-of-stock` at confirm (exactly one winner, STORY-INVENTORY-01).
- Double-click confirm → same order returned (idempotency key).
- Client total tampered → ignored; server total authoritative.

## Cross-references
- Screens: `../screens/EPIC-CHECKOUT/stories/STORY-1-customer-checks-out-server-computed-total.md`, `STORY-2-mock-payment-capture-provider-replay-safety.md`
- Failure path: `payment-failure-recovery.md`
- States: `../screen-states.md` (`/cart`, `/checkout`, `/checkout/payment`)
