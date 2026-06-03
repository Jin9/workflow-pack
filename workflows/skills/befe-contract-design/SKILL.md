---
name: befe-contract-design
version: 0.1.0
description: >
  Design the two-sided backend/frontend shared contract for parallel development —
  a design-first OpenAPI/AsyncAPI single source of truth, generated client types,
  a consumer mock/stub so the frontend is unblocked before the backend exists,
  list/pagination conventions, BFF-per-client shaping, and the frontend
  state-binding contract (loading/empty/error/optimistic). Use when asked to
  design the BE/FE contract, design a two-sided API contract for parallel
  frontend and backend development, set up the consumer mock plus provider
  contract, or define the shared OpenAPI source of truth. It composes
  api-contract-design (backend endpoint) with the frontend consumption side. Do
  NOT use to design only a single backend-exposed endpoint (use api-contract-design).
  Do NOT use to execute contract tests (use contract-testing-pact). Do NOT use to
  validate a tool/agent schema for breaking changes (use universal-spec-validator).
stage_type: design
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: enhanced, pii_handling: minimal, tier_default: T2, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 180
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Backend/Frontend Contract Design

## Purpose

Design the **shared, two-sided** contract so backend and frontend can build in
parallel without drift. `api-contract-design` covers the backend-exposed endpoint
only; this skill composes it with the frontend-consumption side — a single
machine-readable source of truth, generated client types, a consumer mock that
unblocks the frontend before the backend exists, and the FE state-binding
contract. Designs the contract; it does not execute contract tests or validate
schemas.

## When to use this skill

- Use when: a BE↔FE seam needs a shared contract that lets both sides develop in
  parallel.
- Use when: asked to "design the BE/FE contract", "set up the consumer mock +
  provider contract", or "define the shared OpenAPI source of truth".
- Do NOT use: for a single backend endpoint (`api-contract-design`), to run
  contract tests (`contract-testing-pact`), or to validate tool/agent schemas
  (`universal-spec-validator`).

## Input contract

Validate against `schemas/input.json`. Required: `stories` (the behavior the
contract must serve), `idempotency_key`. Optional: `api_contracts` (backend
endpoints from `designing-tech-lead-handoff` / `api-contract-design`),
`client_classes` (web/mobile for BFF shaping), `tier`. Stop with `needs-input` if
there is no behavior to contract.

## Procedure

1. **Establish the source of truth** (`references/two-sided-contract.md`):
   design-first OpenAPI (sync) / AsyncAPI (events) that clients, mocks, and tests
   all share. Reuse `api_contracts` where present rather than re-deriving. Entry:
   stories. Exit: a contract spec.
2. **Define list/pagination + error conventions** (cursor/keyset, `has_more` /
   `next_cursor`, enumerated errors with client action).
3. **Generate client types + a consumer mock/stub** so the frontend can build and
   test against the contract before the backend is ready (parallel dev).
4. **Shape BFF-per-client** where client classes differ (web vs mobile).
5. **Specify the FE state-binding contract** — loading / empty / error /
   optimistic states per operation.
6. **Emit** the contract artifact (Output contract). Defer the breaking-change
   gate to `universal-spec-validator` and contract execution to
   `contract-testing-pact`; this skill designs only.

## Output contract

Validate against `schemas/output.json`: `contract_spec` (ref/inline OpenAPI/
AsyncAPI), `client_types`, `mock_plan`, `list_conventions`, `bff`,
`fe_state_binding`, and `audit_id`.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| BC-01 | no behavior to contract | no artifact | needs-input → human-queue |
| BC-02 | conflicting backend api_contracts | artifact + conflict note | route to TL design |
| BC-03 | money/PII operation without idempotency | artifact + blocking note | human review |

## Constraints

- DO NOT execute contract tests or validate schemas — design only (compose, do
  not duplicate, `api-contract-design` + `universal-spec-validator`).
- DO NOT omit idempotency on money-moving operations.
- DO NOT invent endpoints absent from the stories / `api_contracts`.
- Stop at a human sign-off gate before the contract is treated as published.

## References

| Need | Reference |
|------|-----------|
| Design-first SoT, generated types, consumer mock, conventions, BFF, FE state-binding | `references/two-sided-contract.md` |
