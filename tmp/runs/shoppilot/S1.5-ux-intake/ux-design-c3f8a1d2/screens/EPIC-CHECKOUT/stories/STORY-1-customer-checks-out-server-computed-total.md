---
ux_story_id: UX-CHECKOUT-1
ba_story_id: STORY-CHECKOUT-01
related_route: /checkout
screen_states_ref: ../../../screen-states.md#checkout
microcopy_keys_used: [screen.checkout.title, field.address.label, field.coupon.label, field.coupon.error-expired, common.action.confirm, error.out-of-stock, error.validation, common.status.loading]
---

# Customer checks out at a server-computed total

## Layout
```mermaid
flowchart TD
    A[Title: screen.checkout.title] --> B[OrderSummary: subtotal − coupon + shipping]
    B --> C[TextField: field.address.label]
    C --> D[TextField: field.coupon.label]
    D --> E[Button: common.action.confirm]
    E --> F{server validation}
    F -- coupon expired --> G[field.coupon.error-expired]
    F -- out of stock --> H[error.out-of-stock]
    F -- ok --> I[order awaiting-payment → /checkout/payment]
```

## State-by-state
See `../../../screen-states.md` (`/checkout`). Total is **server-computed** (client total never trusted);
coupon re-validated at confirm; confirm is idempotent (duplicate tap → same order).

## Microcopy keys used
`screen.checkout.title`, `field.address.label`, `field.coupon.label`, `field.coupon.error-expired`, `common.action.confirm`, `error.out-of-stock`, `error.validation`.

## Components
OrderSummary, TextField, Button, InlineAlert (`../../../component-inventory.md`).

## Edge cases
- Example: subtotal 1200 + coupon WELCOME100 (−100) + shipping 60 = **1160 THB** (AC).
- Coupon expired during browsing → neutral `field.coupon.error-expired`; no order, no reservation.
- Last-item race → `error.out-of-stock` at confirm.

## Accessibility
OrderSummary total is an `aria-live="polite"` region (recomputation announced). Address is PII —
snapshotted into the order, redacted in non-order logs.

## Open questions
- TBD-extract-from-prototype: Thai strings, brand styling, address sub-field layout.
