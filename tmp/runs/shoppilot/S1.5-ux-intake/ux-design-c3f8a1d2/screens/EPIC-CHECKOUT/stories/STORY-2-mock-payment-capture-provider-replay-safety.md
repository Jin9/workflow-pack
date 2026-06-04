---
ux_story_id: UX-CHECKOUT-2
ba_story_id: STORY-CHECKOUT-02
related_route: /checkout/payment
screen_states_ref: ../../../screen-states.md#checkoutpayment
microcopy_keys_used: [screen.payment.title, screen.payment.processing-state, common.action.pay, common.action.retry, common.action.cancel, error.payment-declined, error.payment-timeout, common.status.success]
---

# Mock payment capture with provider-replay safety

## Layout
```mermaid
flowchart TD
    A[Title: screen.payment.title] --> B[OrderSummary read-only]
    B --> C[Button: common.action.pay]
    C --> D[screen.payment.processing-state]
    D --> E{provider result}
    E -- success --> F[common.status.success → /orders/:orderNo]
    E -- declined --> G[error.payment-declined + retry/cancel]
    E -- timeout --> H[error.payment-timeout + retry/cancel]
```

## State-by-state
See `../../../screen-states.md` (`/checkout/payment`). No card data collected (PSP/mock; PCI scope-excluded).
Duplicate provider callback applies once.

## Microcopy keys used
`screen.payment.title`, `screen.payment.processing-state`, `common.action.pay`, `common.action.retry`, `common.action.cancel`, `error.payment-declined`, `error.payment-timeout`, `common.status.success`.

## Components
OrderSummary, Button, Toast/InlineAlert (`../../../component-inventory.md`).

## Edge cases
- Failure/timeout → reserved stock released (see `../../../flows/payment-failure-recovery.md`).
- Captured amount must equal the server total.
- Late/duplicate callback → applied once (idempotent on provider event id).

## Accessibility
Processing state announced (`aria-live`); failure `role="alert"` (assertive); retry/cancel are 44×44 targets.

## Open questions
- TBD-confirm-with-UX: whether payment is an in-app screen or a PSP-hosted redirect (affects safe-area/back handling).
