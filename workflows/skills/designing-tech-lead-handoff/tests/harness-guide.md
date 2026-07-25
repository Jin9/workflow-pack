# Test harness guide — designing-tech-lead-handoff

> Named `harness-guide.md` (NOT `README.md`): `scripts/quick_validate.py`
> `BANNED_DOCS` refuses any skill folder containing `README.md` at any depth.

## What the cases assert

`designing-tech-lead-handoff` is generative — output is NOT byte-comparable. Cases
assert **structure and invariants**, not exact bytes:

1. `cases/001-*.input.json` validates against `schemas/input.json`.
2. Running the skill on it produces JSON that validates against
   `schemas/output.json` (`oneOf` → `design` for a clean ready-for-tl brief).
   The skill is the **system-design blueprint** only — per-service API specs,
   per-story L4 specs, and the event catalog are out of scope.
3. The invariant docs under `assertions/` hold on that output.
4. `cases/001-*.expected.json` is a **shape skeleton** (required top-level keys
   + minimal valid sub-shapes), not a fixture for equality — use it to drive
   key-presence / type assertions only.

## Assertions (run all; each is a gate)

- `assertions/layer-presence-completeness.md` — every context has a
  layer-presence row with a non-"following the pattern" rationale; every
  Orchestrator cites ≥1 of the 3 signals.
- `assertions/contract-completeness.md` — `component_map.components[].dependencies`
  resolve to `api_contracts.contracts[].contract_name`; no vague
  `idempotency_rules`/`failure_modes`; async contracts name a partition key.
- `assertions/downstream-consumability.md` — `api_contracts` + `component_map`
  satisfy the field selections the backend/frontend implement+review stages
  declare in `delivery-pipeline.yaml`.
- `assertions/ba-def-drift.md` — the inlined BA `definitions` in
  `schemas/input.json` are byte-faithful to the live
  `eliciting-banking-brief/schemas/output.json`.

## Follow-up

A case derived from the real `integration/examples/ecommerce-v9/output-15e221f4/output.json`
(208KB, multi-epic) is a follow-up; `001` is a compact single-epic brief
sufficient for shape assertions (see `audit/RATIONALE.md §5`).
