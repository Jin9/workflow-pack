# Assertion — contract completeness

On a `design` output:

- Every `component_map.components[].dependencies[]` string resolves to some
  `api_contracts.contracts[].contract_name`. An orphan dependency ⇒ structural
  failure (FM-TL-03), downgrade to `partial_design`.
- No contract has a content-free `idempotency_rules` (reject literal
  `"Idempotent"`, `"Idempotent."`, empty-ish) — it must state key shape +
  scope + TTL + collision behavior.
- No contract has `failure_modes: ["Various"]` / single unenumerable entry —
  must enumerate distinct error codes + resulting system state.
- Every `semantics: async` contract names a partition key in `payload_shape`
  (e.g. a `key` field) and a concrete `ordering_guarantees` (NOT "Best effort"
  / "n/a" for async).
- `component_map.components[].complexity != standard` ⇒ `complexity_rationale`
  present and non-empty.

FAIL ⇒ `partial_design` with a per-contract `blocking_findings[]` entry
(FM-TL-04).
