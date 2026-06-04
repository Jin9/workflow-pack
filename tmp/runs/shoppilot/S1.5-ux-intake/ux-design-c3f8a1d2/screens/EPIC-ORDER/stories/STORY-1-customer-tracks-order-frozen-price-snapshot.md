---
ux_story_id: UX-ORDER-1
ba_story_id: STORY-ORDER-01
related_route: /orders/:orderNo
screen_states_ref: ../../../screen-states.md#ordersorderno
microcopy_keys_used: [screen.orders.title, screen.orders.empty-state, screen.order-detail.title, common.action.track_order, common.action.back, order.status.AWAITING_PAYMENT, order.status.PAID, order.status.PACKING, order.status.SHIPPED, order.status.DELIVERED, order.status.CANCELLED]
---

# Customer tracks an order with a frozen price snapshot

## Layout
```mermaid
flowchart TD
    A[/orders: list + order.status.* badges/] --> B[common.action.track_order]
    B --> C[/orders/:orderNo: screen.order-detail.title/]
    C --> D[OrderSummary frozen snapshot]
    D --> E[status timeline + tracking if SHIPPED]
    C --> F[common.action.back]
```

## State-by-state
See `../../../screen-states.md` (`/orders`, `/orders/:orderNo`). Own-data-only; a non-owner request
is denied with no data disclosed. The order shows the **price snapshot** taken at creation even after
the catalog price changes.

## Microcopy keys used
`screen.orders.title`, `screen.orders.empty-state`, `screen.order-detail.title`, `common.action.track_order`, `common.action.back`, `order.status.AWAITING_PAYMENT`, `order.status.PAID`, `order.status.PACKING`, `order.status.SHIPPED`, `order.status.DELIVERED`, `order.status.CANCELLED`.

## Components
StatusBadge, OrderSummary, Button (`../../../component-inventory.md`).

## Edge cases
- Catalog price changes after purchase → order detail unchanged (snapshot).
- Non-owner → access denied, no order data leaked.
- Status changes are admin-driven (STORY-ORDER-02) and announced to the SR on this screen.

## Accessibility
Status transitions announced; address PII visible to owner/admin only.

## Open questions
- TBD-extract-from-prototype: Thai status labels, timeline visual.
