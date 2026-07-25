# 2026-07-12/13 — Fleet-wide skill I/O contract reshape (31/31)

**What:** every skill in the workspace (28 pipeline + 3 tooling) had its input/output contract
reshaped, brainstormed per-skill with Codex `gpt-5.6-sol` at max effort (**advisory only** — Claude
adjudicated every finding and recorded a verdict). In place on `main`, one always-green commit per
chunk. Staging + full evidence: `tmp/runs/skill-io-reshape/` (`report.md` is the completion report;
`adjudications/<skill>.md` holds a verdict per finding; `codex/` holds the raw consults with a
PROVENANCE line each; `gates/` holds the gate-stack log per commit).

## Numbers

- **263 findings** ruled on: 225 ACCEPT · 32 ACCEPT-MODIFIED · **6 REJECT** (no silent drops).
- **33 always-green commits**; contract-drift lint **68 → 0**, with **0 new findings** ever introduced.
- pytest 38/38 and the `_sim` replay oracle green at every commit; end-to-end: a fresh 27-stage replay
  completes and `engine validate-run` passes **27/27** under the new contracts.

## What changed structurally

1. **Input contracts became true.** All 27 pipeline `schemas/input.json` now describe the **POST-adapter
   payload** the engine actually assembles (picks + `NESTED_HANDOFF` nesting + ba-research hydration +
   injected `idempotency_key`/`upstream_artifacts`/`loop_back_feedback`), each carrying an explicit
   `ADVISORY` marker. Nearly every one had drifted into fiction, declaring envelopes (`plan`,
   `ba_brief`, `design_document`, `code_under_review`, `target`, `source_ref`, `load_profile`, `slo_defs`)
   that **no stage ever sends**.
2. **Two deterministic lints now hold the line, BLOCKING at zero** (`workflows/scripts/`):
   `check_contract_consistency.py` (picks ⊆ producer `required_fields` · picks ∈ consumer input schema ·
   boundary `required` == YAML `required_fields` · flat-merge collisions · workflow bookend ·
   compensation refs) and `check_contract_examples.py` (every fenced example in a contract section
   validates against its schema — prose can no longer drift).
3. **Execution provenance is contractual.** Every replay-capable gate emits
   `execution{mode, target_source, …}`; a replayed artifact can no longer masquerade as a real scan.
4. **`audit_id` fleet-wide** with one house derivation — `UUIDv5(HOUSE_NS, "<stage-id>:{idempotency_key}")`,
   `HOUSE_NS = uuid5(NAMESPACE_URL, "https://squad-delivery/audit")`. Reference-corpus ids stay
   **grandfathered**: recorded provenance is never rewritten.
5. **S0 lost its exemption.** `scoping-ba-intake` had no schemas at all; both were authored from the real
   artifact, `intake` was removed from the engine's `SKILL_SCHEMA_EXEMPT`, and the oracle now
   dual-validates it. Only `ba-research` (a ref-chain manifest) remains exempt.
6. **Workflow `metadata.version` 2.5.0 → 3.0.0** (fleet-wide breaking reshape); `gates.yaml` + the corpus
   run-plan resynced.

## Real bugs found and fixed (not just hygiene)

- **Review-verdict collision (engine):** `qa-plan` picked `verdict` from *both* code reviews and the flat
  merge kept only the frontend's — **the backend review verdict was silently lost**. Fixed via
  `NESTED_HANDOFF` (each nests under its own key); an executable plan now requires both to approve.
- **`severity_floor` suppression vector (reviews):** a P1 floor hid P2 findings while the engine forwards
  *only emitted findings* to regeneration → a blind remediation loop. Removed.
- **Unqualified GREEN from 1/12 gates** (review console): now `INCOMPLETE` with evidence accounting.
- **Destroy-the-input paths in all three tooling skills**, plus a **destructive drift check prescribed in
  the roundtripping skill's own checklist** (re-extract over the edited contract) — the safe read-only
  `build.py --verify` already existed, undocumented.
- **Offline gate scanned only the shell** (contract viewer) — forbidden lexemes in *data* reached the
  saved file unscanned.
- **`scope_kind` conditionals unsatisfiable** (eliciting) — failure shapes could not validate at all.
- **`normalized_request` typed as an object** in eliciting's input while producer, boundary and corpus all
  emit a **string**.
- **T1/T3 latent live bug** — schema demanded object-typed `failures`; the live script executor emits
  strings, so every live FAIL would have failed validation.
- **Grade/verdict could contradict** (prod-SLO): `Pass` + `rollback` validated cleanly. Now paired by
  schema.
- **Routing docs contradicting `engine/policies.py`** (red-team, both reviews): promised `loop_back →
  design` / "BLOCK aborts" edges that do not exist.

## Principled rejections (recorded)

Corpus provenance rewrites (×3) · a maturity-3 hard stop that would permanently redline the live-proven
replay leg · required tl `frontend_quality_policy` / `backend_implementation_handoff` (topology cascade —
ledgered as detailed-design follow-ups) · stripping the named approver from receipts (named-human
accountability is a design invariant) · every request to fabricate data (synthetic latencies, p99,
per-case results, retroactive rubric traces). Where a value could be **honestly derived** from the run's
own bytes, it was — real file counts, real `STORY-*` ids, the run's own receipt id.

## Engine follow-up ledger (recorded, NOT implemented this pass)

`from_stage` alias syntax · runtime **input** validation through the adapter · `audit_id` equality
enforcement · terminal workflow artifact assembly · `ba-research` INDEX exemption removal · run-snapshot
schema digests · **script-executor artifact enrichment (T1/T3)** then flip the optional live fields to
required · compensation trigger threads the resolving human · `backend_implementation_handoff` + tl
`frontend_quality_policy` detailed-design stages · QA `test_results` flip with GAP-05.
