# Route Map — ShopPilot

Routes derived from the BA brief (`../../S1b-ba-brief/`). The **Implements** column cites real BA
story IDs from `INDEX.json`; no story IDs are invented. There is no frontend spec, so this route table
is BA-derived (P2: confirm against the UX team's route list when it arrives).

| Route | Screen | Auth | Tab? | Implements BA stories | Notes |
|---|---|---|---|---|---|
| `/register` | Register | public | no | EPIC-AUTH (register scope) | No dedicated story; in EPIC-AUTH scope ("register with unique email"). |
| `/login` | Login | public | no | STORY-AUTH-01 | Generic invalid-credentials message (no account enumeration). |
| `/` | Product catalog | public | yes (home) | — (browse precondition for EPIC-CHECKOUT) | **UX route without a dedicated BA story** — see Gaps. |
| `/products/:sku` | Product detail | public | no | — (browse precondition) | **UX route without a dedicated BA story** — see Gaps. |
| `/cart` | Cart | customer | yes (cart) | — (cart precondition for STORY-CHECKOUT-01) | **UX route without a dedicated BA story** — see Gaps. |
| `/checkout` | Checkout | customer | no | STORY-CHECKOUT-01 | Server-computed total; coupon re-validated at confirm; idempotent confirm. |
| `/checkout/payment` | Payment | customer | no | STORY-CHECKOUT-02 | Mock provider success/failure/timeout; provider-replay-safe. |
| `/orders` | Order list | customer | yes (orders) | STORY-ORDER-01 | Own-data-only; lists the signed-in customer's orders. |
| `/orders/:orderNo` | Order detail / tracking | customer | no | STORY-ORDER-01 | Frozen price snapshot; status timeline; tracking number when shipped. |
| `/admin/orders` | Admin fulfillment | admin | n/a | n/a (internal) — STORY-ORDER-02 | Back-office; out of customer-UX scope. |
| `/admin/inventory` | Admin stock | admin | n/a | n/a (internal) — STORY-INVENTORY-02 | Back-office; out of customer-UX scope. |

Background (no screen): **STORY-AUTH-02** (silent refresh-token rotation) runs in the client/session
layer — referenced in `screens/EPIC-AUTH/stories/` but has no standalone route.

## Gaps

**UX routes without a BA story (flag for BA):**
- `/` (product catalog), `/products/:sku` (product detail), `/cart` (cart) — implied by the checkout
  flow but the brief has no dedicated browse/cart story. Surface as P2 for BA to confirm scope.

**BA stories without UX coverage (intentional — back-office/internal, not gaps):**
- STORY-ORDER-02 (admin fulfillment state machine) — admin route `/admin/orders`.
- STORY-INVENTORY-01 (stock reservation lifecycle / last-item race) — system/server behavior, no screen.
- STORY-INVENTORY-02 (admin stock adjustment) — admin route `/admin/inventory`.
