# UX input contract (scaffold-v1.1 §8)

The `ux-intake-audit` skill is deferred — the TL validates the UX drop manually
at steps 1 and 13.

## Required artifacts (the drop, §8.1)

`tokens.json` (REQUIRED), `route-map.md` (REQUIRED), `microcopy.json`
(REQUIRED), `screen-states.md` (REQUIRED), plus `component-inventory.md`,
`form-validation.md`, `responsive-spec.md`, `accessibility-spec.md`, `flows/`,
`screens/` (per epic). The skill receives paths: `tokens_path`,
`route_map_path` (both gate the run if missing — `BLOCK-UX-CONTRACT`),
`component_inventory_path` (optional).

- **tokens.json** — W3C Design Tokens draft format. Mandatory categories:
  color (brand/text/background/semantic), spacing, typography, radius, shadow,
  motion, breakpoint. `$extensions.contrast` is non-standard but lets the
  implementation skill refuse AA-failing combinations.
- **route-map.md** — table: Route | Screen | Auth | Implements BA stories.
  Every UX route maps to ≥1 BA story; every customer-facing BA story maps to
  ≥1 route.

## Manual acceptance checklist (§8.4 — step 13)

```
- [ ] tokens.json exists and validates against W3C Design Tokens format
- [ ] route-map.md exists and every customer-facing BA story is covered
- [ ] microcopy.json exists and customer-facing strings pass non-tipping-vocabulary scan
- [ ] Each customer-facing BA story has a corresponding screen-state spec
- [ ] form-validation.md covers every form field with locale rules where applicable
```

## Coverage gaps (non-blocking, FM-TL-08)

Route↔story mismatches are surfaced as `coverage_gaps[]`
(`ba_story_without_ux_route` / `ux_route_without_ba_story`) — surfaced, not
fatal. The run still produces a `design` output; the gap is a finding for the
PO/UX owner.
