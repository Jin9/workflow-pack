# 2026-06-10 — spec_to_drawio.py 0.2.1: multi-service context bands (L2 unreadable fix)

The `designing-tech-lead-handoff` generator silently assumed **one service per bounded
context** on the L2 tab: all services in a context band were placed at the same
`(L2_SVC_X, svc_y)` (datastores/externals had index staggers; services had none). The new
`workflows-ui-binding-architecture.drawio` (5 services in `office-sim`, 2 in
`pipeline-data-plane`) rendered as an unreadable pile.

Fix (skill 0.2.0 → **0.2.1**), three contained changes in `scripts/spec_to_drawio.py`:

1. **Service stacking** — services in a band stack at `svc_pitch = L2_SVC_H + 60`
   (clearance for the bottom labels); `band_h`/`svc_y` reformulated via `svc_block` so
   single-service bands are **byte-identical** to 0.2.0.
2. **Channel fold** — service↔service gutter channels keep the two legacy slots
   (`+0/+14`); channels ≥2 fold left so they never enter the service column.
3. **Dense-bundle labels** — when a page has >2 service↔service edges, labels spread
   along their edges (`mxGeometry x` −0.5…+0.5) and get `labelBackgroundColor=#ffffff`
   so channel lines can't strike through text. Sparse specs (≤2) keep legacy bytes.

Verified: regenerating the committed ShopPilot
`S2-tl-design/diagrams/shoppilot-architecture.drawio` under 0.2.1 is **byte-identical**
(`cmp`) — no drift for the run artifact or its console-embedded SVG. Binding diagram
gates: double-build deterministic, offline-clean, no-overlap; L1/L2/L3 visually verified
via draw.io CLI PNG export. Pins synced: SKILL.md `version: 0.2.1`,
`delivery-pipeline.yaml` `skill_version: "0.2.1"`,
`tests/cases/001-ecommerce-checkout.expected.json`, `dashboard-data.json` S2 skill string
(bundle respliced via `roundtripping-dashboard-data-contract`; only the `c7f43bda` DATA
entry changed; lossless re-extract). Binding spec also trimmed (shorter L3 process note +
shorter runtime edge labels).
