# Screen States — ShopPilot

One section per **customer** route in `route-map.md`. Each state names the components it renders
(see `component-inventory.md`) and the microcopy keys it uses (see `microcopy.json`). Admin routes
(`/admin/*`) are back-office and out of customer-UX scope.

## `/login`
- **Idle:** TextField (email), PasswordField, Button (`common.action.login`). Title `screen.login.title`.
- **Empty:** n/a (form screen).
- **Loading:** Button → loading state, `common.status.loading`, form disabled (`aria-busy`).
- **Error:** InlineAlert `screen.login.error-state` ("Email or password is incorrect" — identical for unknown-email and wrong-password, STORY-AUTH-01). Field errors `field.email.error-required`, `field.password.error-required`.
- **Success:** redirect to `/` (or return route); no PII echoed.
- **Auth-required:** n/a (public).

## `/register`
- **Idle:** TextField (name, email, phone), PasswordField, Button (`common.action.register`). Title `screen.register.title`.
- **Loading:** Button loading; `common.status.loading`.
- **Error:** `field.email.error-format`, `field.phone.error-format`, `error.validation`.
- **Success:** account created → `/login` or auto-login.
- **Auth-required:** n/a (public).

## `/` (product catalog)
- **Idle:** grid of ProductCard; nav tabs (`nav.tab.home/cart/orders/profile`). Title `screen.products.title`.
- **Empty:** `common.status.no_results`.
- **Loading:** ProductCard skeletons; `common.status.loading`.
- **Error:** InlineAlert `error.network` / `error.server`.

## `/products/:sku` (product detail)
- **Idle:** product info + Button (`common.action.add_to_cart`).
- **Loading:** skeleton; `common.status.loading`.
- **Error:** `error.server`.
- **Out-of-stock:** add-to-cart disabled (final enforcement is at confirm — STORY-INVENTORY-01).

## `/cart`
- **Idle:** line items + OrderSummary + Button (`common.action.checkout`). Title `screen.cart.title`.
- **Empty:** `screen.cart.empty-state` ("Your cart is empty").
- **Loading:** `common.status.loading`.
- **Auth-required:** prompt to `/login` if logged out before checkout.

## `/checkout`
- **Idle:** OrderSummary (server-computed: subtotal − coupon + shipping), TextField (address, coupon), Button (`common.action.confirm`). Title `screen.checkout.title`.
- **Loading:** Button loading; idempotent confirm — duplicate taps return the same order (STORY-CHECKOUT-01).
- **Error — coupon:** `field.coupon.error-expired` ("This coupon is no longer valid"); no order created, no stock reserved.
- **Error — out of stock:** `error.out-of-stock` at confirm (last-item race resolved server-side, STORY-INVENTORY-01).
- **Error — validation:** `error.validation`.
- **Success:** order created in awaiting-payment → `/checkout/payment`.
- **Auth-required:** redirect to `/login` (`error.session-expired` if session lapsed).

## `/checkout/payment`
- **Idle:** OrderSummary (read-only) + Button (`common.action.pay`). Title `screen.payment.title`.
- **Loading / processing:** `screen.payment.processing-state`; provider-replay-safe (duplicate callback applies once, STORY-CHECKOUT-02).
- **Error:** `error.payment-declined`, `error.payment-timeout` + Button (`common.action.retry`); reserved stock released.
- **Success:** order → paid; `common.status.success`; → `/orders/:orderNo`.

## `/orders`
- **Idle:** list of orders with StatusBadge + Button (`common.action.track_order`). Title `screen.orders.title`. Own-data-only (STORY-ORDER-01).
- **Empty:** `screen.orders.empty-state` ("No orders yet").
- **Loading:** `common.status.loading`.
- **Auth-required:** redirect to `/login`.

## `/orders/:orderNo`
- **Idle:** OrderSummary (frozen price snapshot), StatusBadge (`order.status.*`), status timeline, tracking number when shipped. Title `screen.order-detail.title`. Button `common.action.back`.
- **Error — not owner:** access denied, no order data disclosed (own-data-only).
- **Loading:** `common.status.loading`.
- **Auth-required:** redirect to `/login`.
