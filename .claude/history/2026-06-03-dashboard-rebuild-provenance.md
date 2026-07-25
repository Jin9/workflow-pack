# 2026-06-03 — Dashboard scripted-rebuild provenance (aside)

**Dashboard scripted-rebuild provenance (2026-06-03).** The first scripted rebuild via `roundtripping-dashboard-data-contract` re-encoded the DATA module's formatting once (zero data/render change, proven by post-merge deep-equality); rebuilds are byte-deterministic thereafter. The manual decode/splice path still applies to the **render** module (`c022aabb…`), which the skill does not touch; RENDER-module/CSS/layout edits are out of the skill's scope.
