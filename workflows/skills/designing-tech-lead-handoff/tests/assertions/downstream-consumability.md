# Assertion — downstream consumability

`delivery-pipeline.yaml` wires tl-design output into SIX consumer stages. On a
`design` output, assert each picked field exists with a consumable shape:

- `plan-review` picks `[component_map, api_contracts]` → both present;
  `api_contracts` is the tech-lead-contracts shape, `component_map` the
  tech-lead-components shape.
- `contract-design` picks `[component_map, api_contracts]` → both present
  (befe-contract-design 0.2.0 requires exactly these).
- `backend-implement` picks `[component_map, api_contracts]` → both present.
- `frontend-implement` picks `[component_map, api_contracts]` → both present.
- `backend-review` picks `[api_contracts]` → present.
- `frontend-review` picks `[api_contracts]` → present.
- Stage `required_fields: [component_map, api_contracts, audit_id]` ⊆ the
  emitted top-level keys; `audit_id` is a uuid (house derivation:
  UUIDv5(HOUSE_NS, "tl-design:{idempotency_key}")).

The consumers' own `schemas/input.json` files describe the POST-adapter
payload (flat picks + engine-injected keys) as of the skill-io-reshape pass —
the old `design_document`/`target_package` envelope dialect is retired.
