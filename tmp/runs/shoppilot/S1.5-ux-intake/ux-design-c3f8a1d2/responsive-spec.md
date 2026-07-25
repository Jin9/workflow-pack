# Responsive Spec — ShopPilot

No frontend spec was supplied, so the device intent is **derived** and one decision is flagged TBD.

## Targets & breakpoints
- **Primary target:** 390×844 (iPhone 14) — mobile-first storefront.
- **Mobile range:** 360×640 → 430×932 (fluid).
- **Desktop:** `TBD-confirm-with-UX` — the BA brief describes a "web storefront" (so desktop is
  plausibly in scope) but gives no desktop layout intent. **Do not assume mobile-only**; confirm with
  the UX team. Surfaced as a P2 finding.

## Per-breakpoint behavior (mobile)
- Single-column flow; bottom nav (`nav.tab.*`) fixed.
- OrderSummary sticky above the primary action on `/checkout` and `/checkout/payment`.
- Product grid: 2 columns at ≥390px, 1 column below.

## Touch targets
- Minimum **44×44px** for all interactive elements (WCAG 2.5.5 / 2.5.8); applies to Button,
  StatusBadge actions, nav tabs, and the password show/hide toggle.

## Safe area
- Respect iOS notch / home-indicator and Android nav-bar insets (`env(safe-area-inset-*)`); bottom nav
  and sticky CTAs must not be occluded.

## Webview vs standalone
- `TBD-confirm-with-UX` — whether the storefront runs in an in-app webview affects safe-area and back-gesture handling.
