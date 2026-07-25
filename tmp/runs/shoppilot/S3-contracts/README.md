# S3 · Contracts (BE/FE) — befe-contract-design

**Skill:** `befe-contract-design 0.1.0` · **gate:** auto (JSON-only autonomous stage) · **status:** ▶ simulated.

Designs the two-sided BE/FE contract from the S2 `api_contracts`: OpenAPI source of truth per bounded context,
generated client types, a consumer mock for parallel FE dev, list/pagination conventions, and the FE state
binding (loading / empty / error / optimistic) per operation.

## Artifacts
- **`befe-contracts.json`** — the contract (`workflows/schemas/befe-contracts.json`): `contract_spec`,
  `fe_state_binding`, `client_types`, `mock_plan`, `list_conventions`, `audit_id`. (The skill schema is
  `additionalProperties:false`, so per-context file refs are **not** inlined — the console scans `be/` + `fe/`.)
- **`be/{auth,checkout,order,inventory}.contract.md`** — per-context OpenAPI operation summaries derived from
  the S2 contracts (operation · semantics · request keys · failure modes).
- **`fe/{auth,checkout,order,inventory}.state-binding.md`** — per-context UI state bindings; money paths
  (confirm/capture) are never optimistic.

> The pipeline YAML's speculative `required_fields` `[api_paths, events, request_response]` predate the built
> skill (OI-003); this artifact follows the built `befe-contract-design` contract.
