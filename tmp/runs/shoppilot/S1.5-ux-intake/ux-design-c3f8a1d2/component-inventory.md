# Component Inventory — ShopPilot

No frontend spec §6 was supplied, so this inventory is **derived from the screens the BA stories
require**. Visual variants/props are `TBD-needs-UX-input`; accessibility behavior is specified because
it follows from WCAG AA + the story acceptance criteria.

## Button (atom)
- **Purpose:** primary/secondary actions (login, confirm order, pay, retry).
- **Variants:** TBD-needs-UX-input (brand / dark / light / ghost expected).
- **States:** idle, hover, active, focused, disabled, loading.
- **Accessibility:** role `button`; Enter/Space activate; visible focus ring (≥3:1 vs background);
  loading state sets `aria-busy="true"` and disables re-submit; min touch target 44×44.
- **Banking-grade:** contains-PII no; customer-facing yes.
- **Used by screens:** login, register, checkout, payment, order-detail.

## TextField (atom)
- **Purpose:** single-line input (email, name, phone, coupon, address).
- **Variants:** TBD-needs-UX-input.
- **States:** idle, focused, filled, error, disabled.
- **Accessibility:** programmatic `<label>` association; error text linked via `aria-describedby`;
  `aria-invalid="true"` on error; never rely on color alone (icon + text).
- **Banking-grade:** contains-PII yes (email/phone/address); customer-facing yes.
- **Used by screens:** login, register, checkout.

## PasswordField (atom)
- **Purpose:** credential entry.
- **States:** idle, focused, error, show/hide toggle.
- **Accessibility:** toggle is a labelled `button` (`aria-pressed`); SR label "show/hide password".
- **Banking-grade:** contains-PII yes (credential); customer-facing yes.
- **Carve-out:** no client-side regex on password rules (server-side only — see `form-validation.md`).
- **Used by screens:** login, register.

## StatusBadge (atom)
- **Purpose:** order status (awaiting-payment, paid, payment-failed, packing, shipped, delivered, cancelled).
- **Accessibility:** status conveyed by text + icon, not color alone; semantic colors from `tokens.json`
  (all AA on white).
- **Banking-grade:** contains-PII no; customer-facing yes.
- **Used by screens:** orders, order-detail.

## ProductCard (composite)
- **Purpose:** catalog item (image, name, price, add-to-cart).
- **Variants/props:** TBD-needs-UX-input.
- **Accessibility:** card is a single tab stop linking to detail; add-to-cart is a separate labelled button.
- **Banking-grade:** contains-PII no; customer-facing yes.
- **Used by screens:** product catalog, product detail.

## OrderSummary (composite)
- **Purpose:** server-computed totals (subtotal, coupon, shipping, net total) at checkout.
- **Accessibility:** total uses a live region (`aria-live="polite"`) so recomputation is announced;
  amounts are real text, not images.
- **Banking-grade:** contains-PII yes (shipping address snapshot); customer-facing yes.
- **Used by screens:** checkout, order-detail.

## Toast / InlineAlert (composite)
- **Purpose:** transient success / error / info messages (payment result, coupon invalid).
- **Accessibility:** errors `role="alert"` (assertive); success `aria-live="polite"`.
- **Banking-grade:** contains-PII no; customer-facing yes.
- **Used by screens:** checkout, payment, login.

## Icons
Icon set is `TBD-needs-UX-input` (no spec icon list). Every icon MUST carry an `aria-label` or be
`aria-hidden="true"` when decorative — enforce in `accessibility-spec.md`.
