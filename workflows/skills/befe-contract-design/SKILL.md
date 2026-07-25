---
name: befe-contract-design
version: 0.2.0
description: Design the two-sided backend/frontend shared contract for parallel development — a design-first OpenAPI/AsyncAPI single source of truth, generated client types, a consumer mock/stub so the frontend is unblocked before the backend exists, list/pagination conventions, BFF-per-client shaping, and the frontend state-binding contract (loading/empty/error/optimistic). Use when asked to design the BE/FE contract, design a two-sided API contract for parallel frontend and backend development, set up the consumer mock plus provider contract, or define the shared OpenAPI source of truth. It elaborates the architecture-level interface contracts from designing-tech-lead-handoff into operation/event-level two-sided specs. Do NOT use to draft the architecture-level component/interface map itself (use designing-tech-lead-handoff). Do NOT use to execute contract tests (use contract-testing-pact). Do NOT use to validate a tool/agent schema for breaking changes (use universal-spec-validator).
stage_type: design
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: enhanced, pii_handling: redact, tier_default: T2, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 180
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Backend/Frontend Contract Design

## Purpose

Design the **shared, two-sided** contract so backend and frontend can build in
parallel without drift. Upstream, `designing-tech-lead-handoff` supplies
**architecture-level cross-component interfaces** (the connective tissue — not
endpoint specs); this skill elaborates them into operation/event-level contracts —
a single machine-readable source of truth, generated client types, a consumer mock
that unblocks the frontend before the backend exists, and the FE state-binding
contract. Designs the contract; it does not execute contract tests or validate
schemas.

## When to use this skill

- Use when: a BE↔FE seam needs a shared contract that lets both sides develop in
  parallel.
- Use when: asked to "design the BE/FE contract", "set up the consumer mock +
  provider contract", or "define the shared OpenAPI source of truth".
- Do NOT use: to draft the architecture-level interface map
  (`designing-tech-lead-handoff`), to run contract tests
  (`contract-testing-pact`), or to validate tool/agent schemas
  (`universal-spec-validator`).

## Input contract

ADVISORY — documents the assembled stage input; the engine validates workflow input
and stage OUTPUTS only (engine/validation.py). Validate against `schemas/input.json`.
Required: `api_contracts` (tl-design's architecture-level cross-component interface
contracts — to elaborate, not finished endpoint specs), `component_map` (providers/
consumers resolve against it), `idempotency_key` (engine-injected). Optional
engine-injected: `upstream_artifacts`, `loop_back_feedback`. Stop with
`needs-input` when method, path/channel, status/error, security, or payload detail
cannot be derived from the interfaces + component map without invention.

**Example (validates against schemas/input.json):**
```json
{
  "api_contracts": { "template_version": "1.0", "contracts": [] },
  "component_map": { "template_version": "1.0", "components": [] },
  "idempotency_key": "3f6c0b2e-7a41-4d9b-9c2a-8e5b1f0a4d22"
}
```

## Output contract

Validate against `schemas/output.json`: `contract_spec` `{summary,
documents[]{kind: openapi|asyncapi|contract-md, context, path}}` (paths are
producer-directory-relative; no absolute paths or traversal), `client_types`,
`mock_plan`, `list_conventions` (all required, non-empty), `bff`
(present-or-absent, never null — only when client classes differ),
`fe_state_binding` `{summary, states{loading,empty,error}, optimistic?,
documents[]?}`, optional `contract_files[]` manifest, optional `findings[]`
(BC-02/BC-03), and `audit_id` — producer-stamped, deterministic:
UUIDv5(HOUSE_NS, "contract-design:{idempotency_key}") with HOUSE_NS =
uuid5(NAMESPACE_URL, "https://squad-delivery/audit").

**Example (validates against schemas/output.json):**
```json
{
  "contract_spec": {
    "summary": "OpenAPI 3.1 per bounded context under be/.",
    "documents": [{ "kind": "contract-md", "context": "auth", "path": "be/auth.contract.md" }]
  },
  "client_types": "TS types via openapi-typescript.",
  "mock_plan": "Prism mock per OpenAPI.",
  "list_conventions": "Keyset pagination (has_more + next_cursor).",
  "fe_state_binding": {
    "summary": "loading=skeleton, empty=typed copy, error=microcopy key.",
    "states": { "loading": "skeleton", "empty": "typed copy", "error": "microcopy key" }
  },
  "audit_id": "cb921576-8648-5708-81f9-828c19ea708b"
}
```

## Procedure

1. **Elaborate the interfaces** (`references/two-sided-contract.md`): from each
   tl-design interface contract, derive operation/event-level detail — method,
   path/channel, status/error surface, security, payload — resolving providers
   and consumers against `component_map`. Design-first OpenAPI (sync) / AsyncAPI
   (events) that clients, mocks, and tests all share. Stop `needs-input` where
   detail cannot be derived without invention. Entry: api_contracts +
   component_map. Exit: a structured contract spec with per-context documents.
2. **Define list/pagination + error conventions** (cursor/keyset, `has_more` /
   `next_cursor`, enumerated errors with client action).
3. **Generate client types + a consumer mock/stub** so the frontend can build and
   test against the contract before the backend is ready (parallel dev).
4. **Shape BFF-per-client** where client classes differ (web vs mobile); omit
   `bff` entirely otherwise.
5. **Specify the FE state-binding contract** — loading / empty / error /
   optimistic states per operation, with per-context binding documents.
6. **Emit** the contract artifact (Output contract). Defer the breaking-change
   gate to `universal-spec-validator` and contract execution to
   `contract-testing-pact`; this skill designs only.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| BC-01 | interfaces/component map insufficient to derive detail | no artifact | needs-input → human-queue |
| BC-02 | conflicting upstream interface contracts | artifact + `findings[]` (blocking) | route to TL design |
| BC-03 | money/PII operation without idempotency | artifact + `findings[]` (blocking) | human review |

## Constraints

- DO NOT execute contract tests or validate schemas — design only (defer to
  `contract-testing-pact` + `universal-spec-validator`).
- DO NOT omit idempotency on money-moving operations.
- DO NOT invent endpoints absent from the stories / `api_contracts`.
- Stop at a human sign-off gate before the contract is treated as published.

## References

| Need | Reference |
|------|-----------|
| Design-first SoT, generated types, consumer mock, conventions, BFF, FE state-binding | `references/two-sided-contract.md` |
