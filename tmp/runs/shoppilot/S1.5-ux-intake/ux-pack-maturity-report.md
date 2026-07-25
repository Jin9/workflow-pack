# UX-Pack Maturity Report — ShopPilot (S1.5 · ux-intake)

> Human-view for the `ux-intake` node. Skill `generate-ux-pack 0.1.0`. Contract: `output.json`.
> Pack: `ux-design-c3f8a1d2/`. **Refreshed 2026-06-07 for the maturity-2 full-run simulation.**

## Verdict

| | |
|---|---|
| **Maturity level** | **2 — draft** (0 skeleton · 1 basic · 2 draft · 3 ready-for-implementation) |
| **Status** | `ready-for-audit` |
| **Why 2, not 3** | brand tokens + Thai microcopy now concrete (P1s resolved), but the pack is still **BA-derived** — no UX-team frontend spec / prototype yet (tracked as P2). Maturity 3 needs a UX-team source. |
| **Why ≥ 2** | clears the **S4b frontend gate** (RT-4: UX maturity ≥ 2), unblocking the frontend leg + the FE gates (T3 unit, T4 a11y). |
| **Gate** | async-peer (L2 · Tech Lead), non-blocking; queue `ux-intake-pending`. |

## What changed at maturity 2 (simulation enrichment)

- `UX-P1-BRAND-TBD` → **resolved**: `tokens.json` brand `primary #0B5FD8` (5.63:1 on white, AA) /
  `secondary #E8590C`, with `radius`, font-family and motion filled.
- `UX-P1-TH-MICROCOPY-TBD` → **resolved**: every `th` string in `microcopy.json` is concrete Thai
  (tipping-off-clean).
- `UX-P1-NO-FRONTEND-SPEC`, `UX-P1-NO-PROTOTYPE` → **downgraded to P2**: BA-derived pack accepted at
  maturity-2 (draft); UX-team source still required for maturity 3.

So `p1_findings` is now empty; `p2_findings` carries the two downgraded items plus the original P2s
(`UX-P2-FIGMA-TBD` · `UX-P2-CONTACT-TBD` · `UX-P2-DESKTOP-INTENT` · `UX-P2-ROUTES-NO-BA-STORY`).

## Artifact checklist (11 present)

✅ README.md ✅ tokens.json ✅ route-map.md ✅ component-inventory.md ✅ microcopy.json
✅ screen-states.md ✅ form-validation.md ✅ responsive-spec.md ✅ accessibility-spec.md
✅ flows/ (4) ✅ screens/ (3 customer epics)

## Coverage vs the BA brief (4 epics / 8 stories)

| BA story | Customer-facing? | UX screen |
|---|---|---|
| STORY-AUTH-01 | yes | EPIC-AUTH/STORY-1 |
| STORY-AUTH-02 | yes (session) | EPIC-AUTH/STORY-2 |
| STORY-CHECKOUT-01 | yes | EPIC-CHECKOUT/STORY-1 |
| STORY-CHECKOUT-02 | yes | EPIC-CHECKOUT/STORY-2 |
| STORY-ORDER-01 | yes | EPIC-ORDER/STORY-1 |
| STORY-ORDER-02 | no (admin) | — intentional internal scope |
| STORY-INVENTORY-01 | no (system) | — intentional internal scope |
| STORY-INVENTORY-02 | no (admin) | — intentional internal scope |

**Customer coverage: 5/5.** The 3 uncovered stories are back-office/internal by design (listed in
`output.json:ba_stories_without_ux_coverage`), not gaps.

**UX routes without a BA story:** `/`, `/products/:sku`, `/cart` (browse/cart implied by checkout — flagged P2 for BA).

## Banking / quality gates

- Tipping-off scan: clean (e-commerce; no AML/SAR vocabulary).
- PII: only fake example values (`customer+test@shoppilot.test`, `081-234-5678`).
- WCAG: derived text/semantic colors pass AA on white; brand contrast now computed (AA).
- No card data in UX scope (PSP/mock; PCI excluded).

## Next step (to reach maturity 3)

Re-run `generate-ux-pack` with a real `frontend_spec_path` + `prototype_html_path` to clear the two P2
"no UX-team source" items and re-gate to maturity 3 (ready-for-implementation).
