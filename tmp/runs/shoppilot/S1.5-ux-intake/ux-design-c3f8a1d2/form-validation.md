# Form Validation — ShopPilot

One section per form. Error messages reference microcopy keys in `microcopy.json`. Thai-locale rules
applied where relevant; banking-grade carve-outs called out.

## Login form — `/login`
Submit: `common.action.login`.

| Field | Type | Required | Client rule | Error (microcopy) | Submit-blocking |
|---|---|---|---|---|---|
| email | email | yes | non-empty | `field.email.error-required` | yes |
| password | password | yes | non-empty only | `field.password.error-required` | yes |

- **Auth error** is generic (`screen.login.error-state`) — identical for unknown-email vs wrong-password (no account enumeration, STORY-AUTH-01).
- **Carve-out (password):** server-side validation only — **no** client-side regex on password complexity (leaks policy). Client checks presence, not rules.

## Register form — `/register`
Submit: `common.action.register`.

| Field | Type | Required | Client rule | Error (microcopy) | Submit-blocking |
|---|---|---|---|---|---|
| name | text | yes | non-empty | `error.validation` | yes |
| email | email | yes | RFC-ish format; uniqueness server-side | `field.email.error-format` | yes |
| phone | tel | yes | Thai mobile `^0[0-9]{9}$` | `field.phone.error-format` | yes |
| password | password | yes | presence only (rules server-side) | `field.email.error-required`/server | yes |

- **Carve-out (email):** PII but customer-owned → no clipboard-copy block.
- **Carve-out (password):** server-side rule enforcement only.

## Checkout form — `/checkout`
Submit: `common.action.confirm`.

| Field | Type | Required | Client rule | Error (microcopy) | Submit-blocking |
|---|---|---|---|---|---|
| address | text | yes | non-empty; TH structure (sub-district / district / province / postal) | `error.validation` | yes |
| postal_code | text | yes | `^[0-9]{5}$` | `error.validation` | yes |
| coupon | text | no | format only; validity re-checked server-side at confirm | `field.coupon.error-expired` | no (invalid coupon ≠ block; surfaces neutral error) |

- **Totals** are server-computed (never trust a client total, STORY-CHECKOUT-01); coupon re-validated at confirm.
- **Out-of-stock** at confirm → `error.out-of-stock` (last-item race resolved server-side).
- **Idempotency:** confirm carries a client idempotency key; duplicate submit returns the same order.

## Payment — `/checkout/payment`
- **Payment fields are out of scope (PSP-hosted / mock provider)** — no PAN/CVV collected or stored
  (PCI scope-excluded, STORY-CHECKOUT-02). The screen only triggers the mock provider and renders
  success / `error.payment-declined` / `error.payment-timeout`.

## Thai-locale rule reference
- Mobile phone: `^0[0-9]{9}$`
- Postal code: `^[0-9]{5}$`
- National ID: 13-digit + checksum — **not collected** by ShopPilot (no KYC); listed for completeness only.
- Address: sub-district (tambon) / district (amphoe) / province (changwat) / postal code.
