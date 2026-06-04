# checkout-service — API spec (v1.0)

Changelog: v1.0 — initial.

| Method | Path | Contract | Auth | Notes |
|---|---|---|---|---|
| POST | `/checkout/confirm` | `checkout.confirm` | customer | client idempotency key; server-computed total; coupon re-validated; sync reserve+create |
| POST | `/checkout/capture` | `checkout.capture` | customer | mock PSP; dedupe on provider event id; amount==server total |

Calls (system_internal): `inventory.reserve`, `inventory.release`, `order.create`.
Emits (via outbox, ADR-008): `order.purchase.created`, `order.payment.captured`. PCI boundary; no PAN/CVV stored.
