# Screens — EPIC-CHECKOUT (Server-side checkout and mock payment)

- **BA epic:** EPIC-CHECKOUT (`../../../../S1b-ba-brief/EPIC-CHECKOUT/EPIC-CHECKOUT.json`)
- **Related routes:** `/checkout`, `/checkout/payment` (preceded by `/cart`)
- **Stakeholder note:** PM (Khun Pim, A), Merchant Owner (Khun Wirat, A), Compliance (Khun Niran, C).
- **Customer-journey position:** the revenue path — after auth + cart, before orders.

## Stories
- `stories/STORY-1-customer-checks-out-server-computed-total.md` ← BA STORY-CHECKOUT-01
- `stories/STORY-2-mock-payment-capture-provider-replay-safety.md` ← BA STORY-CHECKOUT-02
