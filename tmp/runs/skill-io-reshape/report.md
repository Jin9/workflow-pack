# Fleet-wide skill I/O contract reshape — completion report

**Mode:** skillify Refactor (fleet) · **Scope:** all 31 skills (28 pipeline + 3 tooling)
**Method:** Codex `gpt-5.6-sol` @ max effort — one fleet consult + 31 per-skill consults, **advisory only**;
Claude adjudicated every finding and recorded a verdict. **Edit mode:** in place on `main`, one
always-green commit per chunk.

> Status: **COMPLETE — 31/31 skills applied.** The contract-drift lint reports **0 findings** across all
> 27 stages and all 28 schema'd skills, and both lints are now **BLOCKING by default**.

## Headline numbers

| Metric | Value |
|---|---|
| Skills reshaped | **31 / 31** (28 pipeline + 3 tooling) |
| Codex consults adjudicated | **31** per-skill + 1 fleet |
| Findings ruled on | **273** — 235 ACCEPT · 32 ACCEPT-MODIFIED · 6 REJECT (no silent drops) |
| Always-green commits | **33** (each passed the full gate stack before landing) |
| Contract-drift lint | **68 → 0** findings, **0 new** ever introduced · both lints now **BLOCKING** |
| Engine tests | 38/38 green throughout — **and `intake` is no longer schema-exempt** |
| Replay oracle | ALL PASS throughout (corpus regenerated, byte-deterministic) |
| End-to-end | fresh 27-stage replay `done` · `validate-run` **27/27 ALL PASS** · audit chain OK |

## What changed structurally

1. **Input contracts became true.** All 27 pipeline `schemas/input.json` were rewritten to the
   **POST-adapter payload** the engine actually assembles (picks + `NESTED_HANDOFF` nesting + ba-research
   hydration + injected `idempotency_key`/`upstream_artifacts`/`loop_back_feedback`), each carrying an
   explicit `ADVISORY` marker. They had drifted into fiction: most declared envelopes (`plan`, `ba_brief`,
   `design_document`, `code_under_review`, `target`, `source_ref`, `load_profile`…) that **no stage ever
   sends**.
2. **Two new deterministic lints** (`workflows/scripts/`) hold the line: `check_contract_consistency.py`
   (picks ⊆ producer `required_fields`; picks ∈ consumer input schema; boundary `required` == YAML
   `required_fields`; flat-merge collisions; workflow bookend; compensation refs) and
   `check_contract_examples.py` (every fenced example in a contract section validates against its schema —
   so prose can't drift again).
3. **Execution provenance is now contractual.** Every gate that can run in replay emits
   `execution{mode, target_source, …}` — a replayed artifact can no longer masquerade as a real scan.
4. **audit_id fleet-wide**, with one documented house derivation:
   `UUIDv5(HOUSE_NS, "<stage-id>:{idempotency_key}")`. Corpus ids stay **grandfathered** — recorded
   provenance is never rewritten.
5. **S0 lost its exemption.** `scoping-ba-intake` was the last skill with no schemas at all; both were
   authored from the real artifact, `intake` was removed from the engine's `SKILL_SCHEMA_EXEMPT`, and the
   oracle now dual-validates it. Only `ba-research` (a ref-chain manifest) remains exempt.

## Real bugs the pass found and fixed

| Bug | Where | Impact |
|---|---|---|
| **Review-verdict collision** — qa-plan picked `verdict` from *both* code reviews; the flat merge kept only the frontend's | `engine/mapping.py` | The backend review verdict was **silently lost**. Fixed via `NESTED_HANDOFF` (both nest under their own key); an executable plan now requires both to approve. |
| **`severity_floor` suppression vector** | review-backend/frontend | A `P1` floor hid P2 findings while the engine forwards *only emitted findings* to regeneration → a blind remediation loop. Removed. |
| **Unqualified GREEN from 1/12 gates** | delivery-review console | One green gate + 11 missing rendered as GREEN. Now `INCOMPLETE` with per-gate evidence accounting. |
| **Destroy-the-input paths (×3)** | all 3 tooling skills | `-o` pointing at the source silently destroyed it. Guarded + atomic writes everywhere. |
| **A destructive drift check in the docs** | roundtripping | The skill's own checklist told the agent to re-extract *over* the edited contract. Now `build.py --verify` (read-only — it already existed, undocumented). |
| **Offline gate scanned only the shell** | contract-debug-viewer | Forbidden lexemes in *data* reached the saved file unscanned. Now neutralized + the final bytes are scanned. |
| **`scope_kind` conditionals unsatisfiable** | eliciting-banking-brief | Failure shapes could not validate at all. |
| **`normalized_request` typed as an object** | eliciting input schema | Producer, boundary and corpus all emit a **string** — a cross-skill contradiction. Unified. |
| **T1/T3 latent live bug** | unit-test gates | Schema demanded object-typed `failures`; the live script executor emits strings → every live FAIL would have failed validation. |
| **Traversal in a path pattern** | generate-ux-pack | `..` slipped through a pattern **I** had written earlier in this pass; Codex caught it. |
| **Routing docs contradicting the engine** | red-teaming, both reviews | Docs promised `loop_back → design` / "BLOCK aborts"; no such edge exists (`engine/policies.py`). Corrected to the real routes. |
| **`Pass` + `rollback` validated cleanly** | validating-production-slo | grade and verdict were independent enums. Now paired by schema (Pass↔promote · Marginal↔hold · Fail↔rollback), and per-SLO rows carry `unit`+`comparison` — without them `99.9`, `800` and `0` sat side by side meaning nothing. |

## Principled rejections (recorded, not silently dropped)

- **Corpus provenance rewrites** (×3 consults) — grandfathered `audit_id`s are recorded history; the house
  formula is documented for *live* derivations only.
- **Maturity-3 hard stop** (implement-frontend) — would permanently redline the live-proven replay leg.
- **Required tl `frontend_quality_policy` / `backend_implementation_handoff`** — topology cascade; ledgered
  as detailed-design follow-ups instead.
- **Stripping the named approver** from receipts — named-human accountability is a design invariant.
- **Fabricated data** — synthetic latencies, p99/throughput, per-case results, retroactive rubric traces:
  refused. Where a value could be *honestly derived* from the run's own bytes, it was (real file counts,
  real story ids, the run's own receipt id).

## Verification (evidence in `gates/`)

Every commit passed, before landing: `quick_validate.py` + `check_links.py` (per touched skill) ·
`check_contract_examples.py --strict` · `pytest engine/tests -q` (38) · `_sim/validate.py` (the replay
oracle) · `check_contract_consistency.py --strict` against the ratchet baseline.

End-to-end (`gates/e2e-verification.log`): fresh full replay → terminal `done`, 27/27 artifacts ·
`engine validate-run` **27/27 ALL PASS** (the engine's own dual-schema validator, under the new
`required_fields`) · `engine verify-audit` chain OK.

## Engine follow-up ledger (recorded, deliberately NOT implemented this pass)

1. `from_stage` alias syntax (would let a consumer disambiguate the `files_generated` collision structurally).
2. Runtime **input** validation through the adapter (the input schemas are now true enough to enforce).
3. `audit_id` equality enforcement across the chain.
4. Terminal workflow artifact assembly.
5. `ba-research` INDEX exemption removal (the last one).
6. Run-snapshot schema digests.
7. **Script-executor artifact enrichment (T1/T3)** — then flip the optional live fields to required.
8. Compensation trigger threads the resolving human.
9. `backend_implementation_handoff` + tl `frontend_quality_policy` detailed-design stages.
10. QA `test_results` flip together with GAP-05 (execution node).

## Per-skill adjudication ledger

| Skill | Findings | ACCEPT | MODIFIED | REJECT |
|---|---:|---:|---:|---:|
| analyzing-canary-rollout | 8 | 7 | 1 | 0 |
| authoring-e2e-test-suite | 8 | 6 | 2 | 0 |
| befe-contract-design | 8 | 7 | 1 | 0 |
| contract-testing-pact | 9 | 7 | 2 | 0 |
| designing-tech-lead-handoff | 9 | 7 | 1 | 1 |
| eliciting-banking-brief | 10 | 10 | 0 | 0 |
| executing-backend-unit-tests | 9 | 5 | 4 | 0 |
| executing-frontend-unit-tests | 8 | 6 | 2 | 0 |
| executing-integration-tests | 7 | 7 | 0 | 0 |
| executing-qa-test-suite | 8 | 7 | 1 | 0 |
| generate-ux-pack | 8 | 8 | 0 | 0 |
| handoff-revoke | 8 | 6 | 2 | 0 |
| handoff-to-deploy | 9 | 7 | 1 | 1 |
| implement-backend-feature | 8 | 6 | 1 | 1 |
| implement-frontend-feature | 9 | 4 | 3 | 2 |
| planning-banking-tests | 10 | 9 | 1 | 0 |
| red-teaming-implementation-plan | 10 | 10 | 0 | 0 |
| rendering-contract-debug-viewer | 10 | 9 | 1 | 0 |
| rendering-delivery-review-console | 9 | 8 | 1 | 0 |
| researching-ba-problem-space | 9 | 7 | 1 | 1 |
| review-backend-code | 10 | 9 | 1 | 0 |
| review-frontend-code | 10 | 8 | 2 | 0 |
| roundtripping-dashboard-data-contract | 10 | 9 | 1 | 0 |
| running-accessibility-tests | 9 | 9 | 0 | 0 |
| running-performance-load-test | 10 | 10 | 0 | 0 |
| running-sast-security-gate | 8 | 8 | 0 | 0 |
| running-smoke-tests | 6 | 5 | 1 | 0 |
| scanning-appsec-pipeline-gate | 8 | 7 | 1 | 0 |
| scoping-ba-intake | 9 | 8 | 1 | 0 |
| validating-banking-implementation | 9 | 9 | 0 | 0 |
| validating-production-slo | 10 | 10 | 0 | 0 |

Full rationale per finding: `adjudications/<skill>.md`. Raw consults: `codex/<skill>.md` (+ `.log` with a
PROVENANCE line and a `manifest.jsonl` row per dispatch).


## Closing state (P3 + P4)

- Both contract lints flipped **BLOCKING by default** (`--advisory` reports only; `--strict` kept as a
  no-op alias). They hold at **0 findings**.
- Workflow `metadata.version` **2.5.0 → 3.0.0** (fleet-wide breaking reshape); `gates.yaml` + the corpus
  run-plan resynced.
- `dashboard-data.json` + the bundle + `delivery-pipeline-flow.drawio` refreshed: dead field names
  (`go_files`/`tsx_files` → `files_generated`) and 22 stale skill-version strings. Bundle rebuilt through
  the roundtripping skill — `--verify` in sync, render module + 15 fonts byte-identical.
- `CLAUDE.md` current-state prose synced; history entry
  `.claude/history/2026-07-12-skill-io-reshape.md` + index line added.
