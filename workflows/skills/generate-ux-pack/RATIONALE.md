# RATIONALE — generate-ux-pack

The TL Design scaffold pack v1.1 (`integration/stages/2-tl-design/tl-design-scaffold-v1.1.md`) mandates `tokens.json` + `route-map.md` as the UX input contract for Stage 2. Before this skill existed, the contract was unowned: the dev-bootstrap-kit noted "ux-intake-audit skill deferred" and Stage 2/4b had no upstream producer for design tokens or route maps.

This skill closes that gap. It wraps the v1.1 generator prompt (`references/generate-prompt.md`) — a battle-tested artifact factory that emits 9 contract files (README, tokens, route-map, components, microcopy, screen-states, form-validation, responsive-spec, accessibility-spec) plus flows + per-epic screens. The pack is the structured drop TL Design and `implement-frontend-feature` consume downstream.

Banking-grade discipline lives in the prompt body: bilingual TH/EN, tipping-off vocabulary scan, WCAG contrasts computed (not asserted), no invented PII, BA cross-reference verification, honest TBDs over fabricated completeness. The skill is v0.1.0 — wraps an existing, working prompt into the squad-lab skill contract. Independent test cases and an `ux-intake-audit` companion skill are future work.

Pipeline placement: `ux-intake` stage in `delivery-pipeline.yaml`, between `ba-analyze` and `tl-design`. `frontend-implement` also consumes its `tokens_path`, `route_map_path`, `component_inventory_path`, `microcopy_path` as first-class inputs.
