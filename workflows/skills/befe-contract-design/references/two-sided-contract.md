# Two-sided BE/FE contract — source of truth, mock, conventions

Grounded in the ResearchVault: design-first OpenAPI/AsyncAPI as the single
machine-readable source of truth shared by clients, mocks, and tests; cursor/keyset
pagination with `has_more`/`next_cursor`; BFF-per-client-class shaping; and
consumer-driven contract testing as the CI drift guardrail. See
`[[literature/ddd-architecture/api-boundary-design]]`. Consumer-driven contracts
let the FE (consumer) and BE (provider) develop and deploy independently — the
consumer test generates a contract against a local mock so the FE is unblocked
before the BE exists. See `[[literature/ddd-architecture/contract-testing]]`.

## Single source of truth

Design-first: the OpenAPI (sync) / AsyncAPI (events) spec is authored first and
shared by clients, mocks, and tests. Reuse the backend endpoint design from
`api-contract-design` / `designing-tech-lead-handoff`; do not re-derive it.

## Parallel-dev enablers

- **Generated client types** from the spec (no hand-written drift).
- **Consumer mock/stub** so the frontend builds and tests against the contract
  before the backend is implemented.

## Conventions

- **Lists/pagination:** cursor/keyset with `has_more` / `next_cursor`.
- **Errors:** enumerated, each with a client action.
- **Idempotency:** required on money-moving operations.
- **BFF-per-client:** shape per client class (web/mobile/partner) where they
  differ, rather than one over-broad contract.

## FE state-binding

For each operation, specify the frontend states: loading, empty, error, and
optimistic-update behavior — so the consumption side is contracted, not improvised.

## Boundary (compose, don't duplicate)

This skill **designs** the two-sided contract. The breaking-change gate is
`universal-spec-validator`; contract **execution** (consumer pacts, provider
verification, can-i-deploy) is `contract-testing-pact`; a single backend endpoint
is `api-contract-design`. Stop at a human sign-off before the contract is
"published".
