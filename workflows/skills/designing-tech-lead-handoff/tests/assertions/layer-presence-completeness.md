# Assertion — layer-presence completeness

On a `design` output:

- The L2 artifact (carried in `infra_summary`/connectivity content or a
  dedicated L2 doc) contains a per-context layer-presence table.
- `processing_metadata.contexts_derived[]` is non-empty and every listed
  context appears in the table.
- Every table row has a Rationale cell that is NOT "following the pattern" /
  empty.
- For every `orchestrators[]` entry, `instantiation_signals` has ≥1 of
  `multi_aggregate | compensation | temporal`, and the same signal is cited in
  the context's rationale.
- No context routes a flow exhibiting a signal directly to a Domain Processor
  without an Orchestrator (missing-Orchestrator smell) — if intentional, an
  `architecture_smells[]` entry with `resolution: adr` + `adr_ref` exists.

FAIL ⇒ the skill must downgrade to `partial_design` (FM-TL-06) or revise.
