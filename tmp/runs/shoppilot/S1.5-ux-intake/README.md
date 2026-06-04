# S1.5 · UX Intake

| | |
|---|---|
| **Owner** | Tech Lead |
| **Skill** | `generate-ux-pack 0.1.0` |
| **Tier / Gate** | T2 · `async` (L2 peer; queue `ux-intake-pending`) |
| **Consumes → Emits** | `ba.brief` → `ux.pack` |
| **Input** | `epic · stories` (from `../S1b-ba-brief/`) |
| **Output contract** | `output.json` (skill `ux_pack` shape) + the `ux-design-c3f8a1d2/` pack |
| **Human-view** | `ux-pack-maturity-report.md` (markdown today; HTML viewer planned) |
| **SDLC phase** | Requirements & Design |
| **Status** | ✅ produced (2026-06-04) · maturity **1 (basic)** · status `draft` |

Produced by applying `generate-ux-pack 0.1.0` to the **BA brief only** (no UX-team drop was available),
so brand tokens and all Thai microcopy are honest `TBD-*` with P1 findings. Feeds S2 (TL Design) and
S4b (Frontend Impl) — **S2 is not run in this session.**

## Files

```
output.json                  the node contract (ux_pack; maturity 1; P1/P2 findings)
ux-pack-maturity-report.md   human-view review doc (verdict, findings, coverage)
ux-design-c3f8a1d2/          the pack:
  README.md  tokens.json  route-map.md  component-inventory.md  microcopy.json
  screen-states.md  form-validation.md  responsive-spec.md  accessibility-spec.md
  flows/     (4 customer journeys, Mermaid)
  screens/   (EPIC-AUTH, EPIC-CHECKOUT, EPIC-ORDER — customer-facing)
```

## Caveats

- **Honest run, no UX drop.** The skill is designed to consume a UX-team drop (frontend spec + bundled
  prototype). Those were absent, so visual/brand/Thai-copy fields are `TBD-*` (4 P1 findings) and the
  maturity is **1 (basic)**, not implementation-ready. No fabrication.
- **Boundary-schema gap.** `workflows/delivery-pipeline.yaml` names `schemas/ux-intake.json` for this
  node, but that file does **not exist** in `workflows/schemas/`. Validation here is against the skill's
  own `workflows/skills/generate-ux-pack/schemas/output.json` (the `ux_pack` branch). Authoring the
  boundary schema is a pipeline follow-up.
- **Back-office stories** (STORY-ORDER-02, STORY-INVENTORY-01/02) have no customer screens by design —
  listed in `output.json:ba_stories_without_ux_coverage`, not gaps.
