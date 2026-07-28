# Assertion — BA shape drift (hydrated sidecars)

`schemas/input.json` no longer inline-copies BA definitions: the hydrated
`epics[]` / `stories[]` shapes are OWNED by `elaborating-user-stories`
(`schemas/epic-sidecar.json`, `schemas/story-sidecar.json`) and referenced by
bare skill name — the engine hydrates the manifest refs into those exact
rendered objects at assembly time (engine/mapping.py `_hydrate_ba_research`).

Assertion: the test fixture's `epics[]`/`stories[]` entries validate against
the live sidecar schemas (same `required`, `properties`, id `pattern`s:
epic `^EPIC-[A-Z0-9-]+$`, story `^STORY-[A-Z0-9-]+-\d+$`). The pipeline pins
the BA skill EXACTLY (no caret ranges — supply-chain rule), so drift appears
only on a deliberate BA bump; this check is the sync obligation.

Procedure: validate `tests/cases/*.input.json` `epics[0]` and `stories[0]`
against the sidecar schemas; any structural delta ⇒ FAIL with the drifted
shape named (action: re-render the fixture from a real hydrated payload and
re-review).
