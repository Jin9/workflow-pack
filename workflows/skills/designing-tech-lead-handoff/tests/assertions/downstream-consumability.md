# Assertion — downstream consumability

`delivery-pipeline.yaml` wires designing-tech-lead-handoff outputs into four stages. On a
`design` output, assert each selected field exists with a consumable shape:

- `backend-implement.input.from_stage.designing-tech-lead-handoff: [api_contracts, component_map]`
  → both present, `api_contracts` is the tech-lead-contracts shape,
  `component_map` is the tech-lead-components shape.
- `backend-review.input.from_stage.designing-tech-lead-handoff: [api_contracts]` → present.
- `frontend-implement.input.from_stage.designing-tech-lead-handoff: [api_contracts, component_map]`
  → both present.
- `frontend-review.input.from_stage.designing-tech-lead-handoff: [api_contracts]` → present.
- Stage `required_fields: [component_map, api_contracts, audit_id]` ⊆ the
  emitted top-level keys; `audit_id` is a uuid.

> Known residual (NOT asserted here — out of scope, GAP-03): the
> `implement-backend-feature`/`implement-frontend-feature` skills' own
> `schemas/input.json` require `design_document`(string)+`target_package`, not
> these objects. Bridging that is the future `artifact-handoff` skill's job;
> `l4_specs[].content` is the `design_document` source. See
> `audit/RATIONALE.md §6`.
