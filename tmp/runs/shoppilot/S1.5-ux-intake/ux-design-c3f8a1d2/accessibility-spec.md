# Accessibility Spec — ShopPilot (WCAG 2.1 AA)

## Target
WCAG 2.1 **AA** (derived; the BA discovery/§20 names keyboard-usable, responsive, human-readable
messages). Cross-references `tokens.json`, `component-inventory.md`, `responsive-spec.md`.

## Color contrast (computed from `tokens.json`)
| Token | vs white | AA | AAA |
|---|---|---|---|
| text.primary `#1A1A1A` | 17.40:1 | ✅ | ✅ |
| text.secondary `#595959` | 7.00:1 | ✅ | ✅ |
| text.tertiary `#6E6E6E` | 5.10:1 | ✅ (normal) | ❌ |
| semantic.success `#197A3D` | 5.39:1 | ✅ | ❌ |
| semantic.warning `#8A5300` | 6.33:1 | ✅ | ❌ |
| semantic.error `#B3261E` | 6.54:1 | ✅ | ❌ |
| semantic.info `#1A5FB4` | 6.29:1 | ✅ | ❌ |
| **brand.primary** | **uncomputable** | **TBD** | **TBD** | 

> **P1 (UX-P1-BRAND-TBD):** brand colors are absent (no spec/prototype), so brand-on-background
> contrast **cannot be verified**. Recompute and re-gate this table when the UX team supplies the palette.

Never convey state by color alone — pair semantic colors with text + icon (StatusBadge, InlineAlert).

## Focus order
Per screen, Tab order follows visual/reading order: header → primary content → form fields top-to-bottom
→ primary action → bottom nav. Modals trap focus; Escape closes and returns focus to the trigger.

## Keyboard
- Enter submits the focused form; Space/Enter activate Button.
- Escape closes modals/toasts.
- Password show/hide toggle reachable and operable by keyboard (`aria-pressed`).

## Screen-reader announcements
- Form errors: `role="alert"` (assertive) on the InlineAlert; each field error linked via `aria-describedby` + `aria-invalid`.
- Order total recomputation on `/checkout`: OrderSummary is an `aria-live="polite"` region.
- Payment progress/result on `/checkout/payment`: `screen.payment.processing-state` announced; success polite, failure assertive.
- Status transitions on `/orders/:orderNo`: announce new `order.status.*`.

## Icon ARIA labels
Every icon carries an `aria-label` or is `aria-hidden="true"` when decorative (icon set is
`TBD-needs-UX-input` in `component-inventory.md`).

## Touch targets
≥44×44px (see `responsive-spec.md`).

## Reduced motion
Honor `prefers-reduced-motion`: replace non-essential animation with instant state changes
(`tokens.json motion.duration` is `TBD-pending-UX-input`).

## Security-adjacent (banking-grade)
Auth tokens must not be placed in `localStorage` (XSS exfiltration risk) — use the session model from
the BA brief (short-lived access token + rotating refresh token, STORY-AUTH-01/02).
