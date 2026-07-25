# S1.5 · UX Intake

| | |
|---|---|
| **Owner** | Tech Lead |
| **Skill** | `generate-ux-pack 0.1.0` |
| **Tier / Gate** | T2 · `async` (L2 peer; queue `ux-intake-pending`) |
| **Consumes → Emits** | `ba.brief` → `ux.pack` |
| **Output contract** | `output.json` (skill `ux_pack` shape) + the `ux-design-c3f8a1d2/` pack |
| **Human-view** | `ux-pack-maturity-report.md` + the Delivery Review Console (`../delivery-review.html`) |
| **Status** | ✅ produced (2026-06-04) · **▶ bumped to maturity 2 (draft)** for the full-run simulation (2026-06-07) |

Originally produced from the **BA brief only** at **maturity 1** (no UX-team drop). For the full S0→S7 run
simulation it was **enriched to maturity 2** so the S4b frontend leg clears its gate (RT-4: UX maturity ≥ 2).

## Maturity-2 simulation enrichment (what changed)

- `output.json`: `maturity_level` **1 → 2**, `status` `draft → ready-for-audit`.
- `ux-design-c3f8a1d2/tokens.json`: brand `primary`/`secondary` now concrete hex with **computed WCAG
  contrast** (resolves `UX-P1-BRAND-TBD`); `radius`, default font-family and motion duration filled.
- `ux-design-c3f8a1d2/microcopy.json`: every `th` value now concrete Thai (resolves
  `UX-P1-TH-MICROCOPY-TBD`); still tipping-off-clean.
- The two remaining "no UX-team source" findings (`UX-P1-NO-FRONTEND-SPEC`, `UX-P1-NO-PROTOTYPE`) were
  **downgraded to P2** — a BA-derived pack is accepted at **maturity-2 (draft)** for the MVP; a UX-team source
  is still required to reach maturity 3. So `p1_findings` is now empty.

This is a **documented simulation enrichment** of a previously-real artifact, not a fresh skill run.

## Files

```
output.json                  the node contract (ux_pack; maturity 2; p1_findings: []; p2_findings)
ux-pack-maturity-report.md   human-view review doc (refreshed for maturity 2)
ux-design-c3f8a1d2/          the pack:
  README.md  tokens.json  route-map.md  component-inventory.md  microcopy.json
  screen-states.md  form-validation.md  responsive-spec.md  accessibility-spec.md
  flows/     (4 customer journeys)
  screens/   (EPIC-AUTH, EPIC-CHECKOUT, EPIC-ORDER — customer-facing)
```

## Notes

- **Boundary schema now exists.** `output.json` validates against **both** the skill's
  `generate-ux-pack/schemas/output.json` (`ux_pack` branch) **and** the boundary
  `workflows/schemas/ux-intake.json` (`maturity_level` integer 0–3).
- **Back-office stories** (STORY-ORDER-02, STORY-INVENTORY-01/02) have no customer screens by design —
  listed in `output.json:ba_stories_without_ux_coverage`, not gaps.
