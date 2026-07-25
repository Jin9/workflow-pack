---
name: planning-banking-tests
version: 2.0.0
description: Convert the hydrated BA brief (eliciting-banking-brief, exact-pinned in the pipeline) into a structured QA test plan covering every Gherkin scenario, banking-grade concern, NFR target, regulatory dependency, and compliance requirement. Emits canonical output.json plus deterministic markdown tree. Use when implementing Stage 4c Test Design after BA Stage 1 completes. Use when QA needs a per-story test roster derived from a structured brief. Use when sign-off criteria must be derived from BA governance gaps. Do NOT use to generate runnable test code, measure coverage on running systems, file defects, or substitute for TL Design.
stage_type: analyze
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: enhanced, pii_handling: redact, tier_default: T2, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 60
max_retries_recommended: 2
fallback: human-queue
recommended_temperature: {T1: 0.1, T2: 0.3, T3: 0.5}
tier_review_levels: {T1: [L0, L1, L2], T2: [L0, L1, L2], T3: [L0, L1]}
compatibility: claude-code, codex, opencode
---

# Planning Banking Tests

## Purpose

Convert a completed BA brief into a structured test plan covering every Gherkin scenario, banking-grade concern, NFR target, regulatory dependency, and compliance requirement defined in the brief. Output is a canonical `output.json` consumed by the downstream test-code-generation and QA-sign-off steps, plus a deterministic markdown tree for human review.

The skill produces **test plans, not test code**. It surfaces coverage gaps and untestable specifications; it never silently invents test data, mock contracts, or assertion thresholds.

## When to use this skill

- Use when: test design must run after a BA brief completes (`output_type ∈ {brief, blocked_partial_brief}`).
- Use when: QA needs a per-story test roster grounded in BA `acceptance_criteria` + `banking_grade_concerns`.
- Use when: Sign-off criteria must be derived from `governance_gaps` + `regulatory_dependencies` + tier policy.
- Do NOT use when: generating executable test code (defer to the test-code-generation step).
- Do NOT use when: measuring coverage on running systems (downstream of execution).
- Do NOT use when: filing defects (a later pipeline concern).
- Do NOT use when: selecting test framework (deferred to code-generation step).

## Input contract

ADVISORY — documents the assembled stage input; the engine validates workflow input
and stage OUTPUTS only (engine/validation.py). Validate against `schemas/input.json`.
Required: `epics` + `stories` (engine-hydrated sidecar objects; `story_files` refs
retained), `governance_gaps`, `backend_review` + `frontend_review` (engine-NESTED —
each producer's `verdict` under its own key so the flat merge can no longer discard
one; an executable `test_plan` requires BOTH to be `approve`), and
`idempotency_key` (engine-injected). Optional engine-injected: `upstream_artifacts`
(resolve `["ba-research"]` → the INDEX manifest → its `brief_file` for the
canonical-brief-only fields: `blocks_tl_handoff`, `ba_compliance_checklist`,
`regulatory_dependencies`, `pii_inventory`, open questions, assumptions, glossary;
resolution failure = the defined input-incomplete failure), `loop_back_feedback`.
The legacy standalone `ba_brief_ref` XOR `ba_brief_inline` interface is retired.

**Example (validates against schemas/input.json):**
```json
{
  "epics": [{ "id": "EPIC-CHECKOUT", "title": "Checkout" }],
  "story_files": [{ "epic": "EPIC-CHECKOUT", "file": "EPIC-CHECKOUT/STORY-CHECKOUT-01.json" }],
  "stories": [{ "id": "STORY-CHECKOUT-01", "epic_id": "EPIC-CHECKOUT", "title": "Customer pays" }],
  "governance_gaps": [],
  "backend_review": { "verdict": "approve" },
  "frontend_review": { "verdict": "approve" },
  "idempotency_key": "3f6c0b2e-7a41-4d9b-9c2a-8e5b1f0a4d22"
}
```

## Output contract

Validated by `schemas/output.json`. Discriminated `output_type ∈ {test_plan, blocked_test_plan, partial_test_plan, failure_shape}`: executable/partial plans require ≥1 `test_cases` entry + `signoff_criteria` + the BA-derived metadata; blocked/failure plans carry EMPTY `test_cases` + explicit no-go `signoff_criteria` and only input-derived identifiers (they intentionally fail qa-validate's const guards, so execution can never start from them). Trace keys join the hydrated sidecars exactly (`^EPIC-[A-Z0-9-]+$`, `^STORY-[A-Z0-9-]+-\d+$`; `scenario_ref` = story id + upstream scenario name). Compliance rows round-trip the BA brief: `regulator` + `regulator_code` verbatim from `regulatory_dependencies`, `template_key` as the separate normalized lookup slug. Optional typed `processing_metadata.audit_trace` + `facet_firing_log` (live plans SHOULD emit; requiring them against the frozen corpus would fabricate retroactive rubric traces — flip ledgered). `audit_id` is required — producer-stamped, deterministic: UUIDv5(HOUSE_NS, "qa-plan:{idempotency_key}") for live derivations (corpus ids sim-convention, grandfathered). Markdown tree rendered by `scripts/render_test_plan_tree.py` (pure Python, no LLM). See `references/markdown-rendering-spec.md` for tree shape.

**Example (validates against schemas/output.json — failure variant):**
```json
{
  "output_type": "failure_shape",
  "blocks_qa_execution": true,
  "frontmatter": {
    "test_plan_id": "TP-shoppilot-001",
    "idempotency_key": "3f6c0b2e-7a41-4d9b-9c2a-8e5b1f0a4d22",
    "workload_tier": "T2", "created_at": "2026-07-12",
    "created_by": "planning-banking-tests 2.0.0", "status": "blocked"
  },
  "test_cases": [],
  "signoff_criteria": { "tier": "T2", "go_conditions": [], "conditional_go_conditions": [], "no_go_conditions": ["BA brief could not be loaded — no basis for a plan"] },
  "processing_metadata": { "scenario_mapping_table_version": "1.0.0", "pyramid_allocation_rules_version": "1.0.0" },
  "failure_state": { "failure_code": "ba_brief_not_found", "message": "ba-research manifest brief_file did not resolve (TM-01).", "remediation": "Re-run ba-research or fix the manifest brief_file ref." },
  "audit_id": "50012a63-945d-513f-b7eb-33edae948cba"
}
```

## Procedure

### Step 1 — Pre-flight + brief validation

Consume the hydrated `epics`/`stories` directly. Resolve `upstream_artifacts["ba-research"]` → the INDEX manifest → `brief_file`, and validate the canonical brief before reading its brief-only fields. Verify `backend_review.verdict` and `frontend_review.verdict` are both `approve`. Refuse with:

- `failure: ba_brief_not_found` if the manifest/brief cannot be resolved (TM-01, input-incomplete).
- `failure: ba_brief_invalid` if schema fails (TM-02).
- `blocked_test_plan` if `blocks_tl_handoff: true` (TM-03) OR `ba_compliance_checklist.definition_of_ready_met: false` (TM-04).
- On `partial_brief`, emit `partial_test_plan` covering only complete epics.

### Step 2 — Inventory BA artifacts

Build internal model from `output.json`: per-epic list, per-story list, scenarios per story, banking-grade rows with `banking_grade_concerns.<concern>.status == "applies"` per story, NFR targets per epic (from `success_criteria`), regulators (from `regulatory_dependencies`), PII fields (from `pii_inventory`), governance gaps (from `governance_gaps`), OQs by story (from `open_questions[].related_story_ids`), assumptions by story (from `assumptions_made[].related_story_ids`).

### Step 3 — Tier inheritance + override resolution

Per epic, inherit `inferred_tier` from BA brief. Apply `tier_hint` override per `references/tier-aware-test-policy.md`. Record per-epic decisions in `processing_metadata.tier_decisions`. Multi-epic briefs carry heterogeneous tiers — never collapse to one test tier (AP-Q3 in `references/anti-patterns.md`).

### Step 4 — Scenario → test-type mapping

Load `references/scenario-type-mapping.md`. For each Gherkin scenario in each story, deterministically map `scenario_type` → `test_type`. Each mapped case carries `mapping_table_version: "1.0"` for audit reconstruction. Generate test case IDs per `references/test-case-id-rules.md`.

### Step 5 — Pyramid allocation

Load `references/pyramid-allocation-rules.md`. Apply allocation rules per tier and per scenario type. Identify smoke subset (1 test per Must-priority story, target wall-clock <30s each). Apply AP-Q5 (no coverage-target obsession).

### Step 6 — NFR test derivation

Load `references/nfr-derivation.md`. For each epic's `success_criteria[]`, derive perf/load/reliability tests. For each PII field, derive security/authz tests. For customer-facing stories, derive accessibility tests. Where a target depends on an unresolved BA OQ, emit `target: "TBD pending OQ-N"` and `blocking_oqs[]` — apply AP-Q9 (no assumed defaults).

### Step 7 — Compliance test derivation

Load `references/compliance-test-patterns.md`. For each `regulatory_dependencies[].code`, load matching template (PDPA-TH-2019, TRC-VAT-7PCT, CCA-TH-LOG-90D, CPA-TH-DISCLOSURE for Thai e-commerce; extensible). Where `citation_status: pending`, emit test cases with `compliance_scope_blocked: true` and link the governance gap. Apply AP-Q11 (no tipping-off vocabulary in test copy).

### Step 8 — Test data design

Load `references/test-data-design.md`. From BA `pii_inventory[]`, generate synthetic fixture rules per PII category. Preserve bilingual surface forms (Thai/English) from BA glossary. Define time-anchored seeds. Enforce AP-Q7 (no real PII, no production data).

### Step 9 — Environment scoping

For each test case, identify env requirements (mocks, real services, concurrency primitives, time control). Group tests by env. If `environment_inventory_ref` provided, validate every test has a feasible env; else emit `environment_dependency` findings.

### Step 10 — Execution DAG construction

For each test case, derive `depends_on_test_cases[]` from BA `story.dependencies.depends_on`. Add pre-test setup edges (env provisioning, fixture loading). Identify parallelizable groups (no shared env state). Identify critical-path order (banking_grade_* and Must-priority first). Emit as nodes + edges in JSON; render in `06-execution-order.md`.

### Step 11 — Coverage rubric evaluation

Load `references/coverage-rubric.md`. Per story: every AC scenario has ≥1 test case; every `banking_grade_applies` row has corresponding test; ≥1 happy + ≥1 error + ≥1 banking_grade_*. Per tier: rubric thresholds met. Per regulator: coverage scope set. Per PII field: data spec + authz test present. Gaps → `coverage_gaps[]` with severity P1/P2/P3 + required action + escalation target.

### Step 12 — Failure-mode evaluation + output assembly

Evaluate gates per `references/anti-patterns.md` TM-01 to TM-12 (see Failure Modes below). Coverage gap count > 0: `partial_test_plan` if all P2/P3, `blocked_test_plan` if any P1. TL Design dependencies > 0: record in `tl_design_dependencies[]` (do not block — test plan still useful).

Emit canonical JSON conforming to `schemas/output.json`. Invoke `scripts/render_test_plan_tree.py --input output.json --output-dir test-plan-{idem8}/` to render markdown tree per `references/markdown-rendering-spec.md`. For failure shapes, emit reduced 3-file tree (README + output.json + FAILURE.md).

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| TM-01 | BA brief path invalid | `failure: ba_brief_not_found` | Re-invoke with correct path |
| TM-02 | BA `output.json` fails schema | `failure: ba_brief_invalid` + validation_errors | Fix BA brief / regenerate |
| TM-03 | `blocks_tl_handoff: true` | `blocked_test_plan` | Resolve BA governance gaps |
| TM-04 | `definition_of_ready_met: false` | `blocked_test_plan` | Resolve BA DoR failures |
| TM-05 | banking_grade_applies row has no matching scenario | `coverage_gap` P1, escalate BA | BA defect or manual enhancement |
| TM-06 | NFR target needed but no `success_criteria[]` metric | `nfr_target_unresolved` linked to OQ | BA OQ resolution required |
| TM-07 | Regulator with `citation_status: pending` | `compliance_test_scope_blocked` finding | Legal/Compliance engagement |
| TM-08 | This skill's own output fails schema | `schema_validation_failure` | Bug in renderer; retry with fix |
| TM-09 | TL Design ref invalid / schema mismatch | Continue without TL Design; warning | Re-invoke with correct ref |
| TM-10 | Environment inventory malformed | Continue without env inventory; warning | Fix env inventory; retry |
| TM-11 | `tier_hint` looser than BA-inferred tier | `tier_downgrade_warning`, require override | Confirm or remove override |
| TM-12 | Tipping-off violation in proposed test copy | Refuse; require Legal sign-off | Rephrase to non-tipping vocabulary |

## Anti-patterns

See `references/anti-patterns.md` for AP-Q1 through AP-Q12 with detection patterns and mitigations. Critical: AP-Q1 (no test code generation), AP-Q9 (no invented thresholds for unresolved OQs), AP-Q11 (no tipping-off in test plan copy), AP-Q12 (audit assertions must enumerate the 7 standard fields plus context-specific fields).

## Validation

- [ ] Frontmatter `name` matches folder name `planning-banking-tests`.
- [ ] `schemas/input.json` and `schemas/output.json` both draft-07 valid.
- [ ] Re-running with same `idempotency_key` produces byte-identical output (after canonicalization: sorted JSON keys + masked timestamps).
- [ ] Every BA Gherkin scenario in the holdout has ≥1 mapped test case.
- [ ] Every `banking_grade_applies` row has corresponding test case with matching `tags`.
- [ ] Every regulator in BA `regulatory_dependencies[]` appears as ≥1 `compliance_tests[].regulator_code`.
- [ ] Every PII field appears in ≥1 `test_data_specs[].pii_field_refs`.
- [ ] Determinism: re-run delta is exactly zero after canonicalization (5 validation scenarios specified in `tests/assertions/`).

## References

| Need | Reference |
|---|---|
| Map scenario_type to test_type and pyramid level | `references/scenario-type-mapping.md` |
| Decide pyramid allocation per test case | `references/pyramid-allocation-rules.md` |
| Apply tier-specific gates and sign-off rules | `references/tier-aware-test-policy.md` |
| Generate per-regulator compliance tests | `references/compliance-test-patterns.md` |
| Derive NFR tests from BA success criteria | `references/nfr-derivation.md` |
| Design synthetic fixtures from PII inventory | `references/test-data-design.md` |
| Evaluate coverage against the rubric | `references/coverage-rubric.md` |
| Detect and avoid anti-patterns | `references/anti-patterns.md` |
| Render the markdown tree deterministically | `references/markdown-rendering-spec.md` |
| Assign test case / NFR / compliance IDs | `references/test-case-id-rules.md` |
| QA-role boundaries preserved for v1.1+ fan-out | `references/v1.1-role-boundaries.md` |
