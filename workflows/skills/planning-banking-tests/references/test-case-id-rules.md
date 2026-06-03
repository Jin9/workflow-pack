# Test Case ID Rules — `planning-banking-tests` v1.0.0

> Loaded by `SKILL.md` at **Steps 4, 6, 7**. Sibling docs: `coverage-rubric.md`, `anti-patterns.md`, `markdown-rendering-spec.md`.

---

## 1. Purpose

This document defines the canonical identifier patterns for test artifacts emitted by `planning-banking-tests`. IDs are the trace primitives that connect a BA Gherkin scenario, banking-grade row, NFR target, regulator dependency, or PII field to the QA test that exercises it. Determinism in ID assignment is load-bearing for Validation Scenario 1 (re-run determinism) and AP-Q8 traceability enforcement (`anti-patterns.md`).

This spec covers three ID families: functional test cases (TC), NFR tests (NFR), and compliance tests (COMP). Coverage-gap IDs and other secondary identifiers are out of scope here and defined in `schemas/output.json`.

---

## 2. TC ID pattern

**Pattern**: `^TC-[A-Za-z0-9_.-]+-[0-9]{3}$`

Composition: `TC-{story_id}-{seq:03d}` where:

1. `{story_id}` is the literal value of the parent BA `stories[].id`. The skill must not transform the story id (no case change, no slug, no truncation). If the brief carries a story id `STORY-CART-CHECKOUT-2`, the test case id is `TC-STORY-CART-CHECKOUT-2-001`.
2. `{seq}` is a zero-padded three-digit sequence, starting at **001 per story**. The sequence is monotonic and **never reused** within a story even when a test is deleted in a later iteration (see Section 6).
3. The id must match the regex above; SKILL.md Step 4 validates every test case id and AP-Q8 (`anti-patterns.md`) emits P1 on any mismatch.
4. The `{story_id}` segment in the id must equal `test_cases[i].story_id` literally. Mismatch is AP-Q8.

Three-digit sequence is sufficient for 999 tests per story; a story exceeding 999 indicates upstream scope error and must be flagged at Step 6.

---

## 3. NFR ID pattern

**Pattern**: `^NFR-[A-Za-z0-9_.-]+-(perf|sec|a11y|reliab|obs|data)-[0-9]{3}$`

Composition: `NFR-{scope_id}-{kind}-{seq:03d}` where:

1. `{scope_id}` is the epic id when the NFR is epic-scoped, or the literal `INITIATIVE` when initiative-scoped.
2. `{kind}` is one of the six fixed NFR families: `perf` (performance / latency / throughput), `sec` (security non-functional), `a11y` (accessibility), `reliab` (reliability / SLO / error budget), `obs` (observability / logging / metrics), `data` (data-quality / retention / freshness).
3. `{seq}` is zero-padded three-digit, starting at **001 per (scope_id, kind) pair**.

Example: `NFR-EPIC-CART-CHECKOUT-perf-001` is the first performance NFR scoped to the cart-checkout epic. The kit's first accessibility NFR for the catalog epic is `NFR-EPIC-CATALOG-a11y-001`.

The six-kind enum is closed at v1.0.0. New kinds require a minor version bump.

---

## 4. Compliance ID pattern

**Pattern**: `^COMP-[A-Z0-9_]+-[0-9]{3}$`

Composition: `COMP-{regulator_code}-{seq:03d}` where:

1. `{regulator_code}` is the literal value of `regulatory_dependencies[].code` from the BA brief, restricted to uppercase letters, digits, and underscores. The skill does **not** invent regulator codes; if BA carries `PDPA-TH-2019`, the renderer must convert to `PDPA_TH_2019` (hyphens replaced with underscores) to satisfy the pattern. The mapping is recorded in `processing_metadata.audit_trace` so the reverse lookup is unambiguous.
2. `{seq}` is zero-padded three-digit, starting at **001 per regulator_code**.

Examples: `COMP-PDPA_TH_2019-001`, `COMP-TRC_VAT_7PCT-001`, `COMP-CCA_TH_LOG_90D-001`, `COMP-CPA_TH_DISCLOSURE-001` — matching the four regulators present in the e-commerce-v5 holdout.

---

## 5. Sequence determinism

Sequence numbers are assigned by **sorted iteration**, never by LLM order. The deterministic ordering rules are:

1. **TC sequence** — iterate `acceptance_criteria[]` for the story in lexicographic ascending order of `scenario_name`. Within a single scenario producing multiple test cases (happy + error + banking-grade splits), iterate the pyramid level in fixed order `[unit, integration, e2e]` then `scenario_type` in fixed order `[happy, error, banking-grade]`. Assign `seq = 001, 002, ...` along this iteration.
2. **NFR sequence** — iterate `success_criteria[]` for the scope (epic or initiative) in lexicographic ascending order of `metric` name. Filter by `kind` (perf / sec / a11y / reliab / obs / data) and assign `seq = 001, 002, ...` per `(scope, kind)` partition.
3. **COMP sequence** — iterate `regulatory_dependencies[]` filtered by `regulator_code` in the order their sub-requirements appear in the brief, then `[DSAR, retention, breach, consent, disclosure, other]` in that fixed order, then alphabetical by sub-requirement title. Assign `seq = 001, 002, ...` per regulator.

LLM output order is **discarded** before assignment. The skill sorts, then numbers, then writes.

---

## 6. Re-run stability

Re-running the skill with the same input idempotency key on an unchanged brief must produce identical IDs. Re-running on an **edited** brief is governed by two rules:

1. **Additions never re-sequence prior IDs.** A new BA scenario added to a story whose existing tests are `TC-STORY-3-001` through `TC-STORY-3-005` is assigned `TC-STORY-3-006`, regardless of where the new scenario sorts lexicographically. The skill consults `prior_test_plan_ref` (optional input) and reserves all prior ids before assigning new ones.
2. **Deletions leave holes.** A scenario removed from the brief retires its TC id; the slot is not refilled. The audit trace records the retirement with `event: "tc-retired"` and `reason: "scenario-removed-from-brief"`.

When `prior_test_plan_ref` is absent, the skill assumes a clean run and assigns from `001`. The renderer does not silently re-sequence; if it detects a re-sequence (current id mismatches prior id for the same `scenario_ref`), it fails with `RENDERER_E_RESEQUENCE`.

---

## 7. Collision handling

1. **Across stories** — no collision is possible because the `{story_id}` segment is unique per story by BA contract.
2. **Within a story** — collision is prevented by sorted-iteration sequencing (Section 5). Two scenarios with identical `scenario_name` would be a BA-side authoring error and are caught at Step 4 input validation (BA scenario names must be unique per story).
3. **Across NFR scope/kind partitions** — no collision because `{scope_id}-{kind}` is the partition key.
4. **Across regulators** — no collision because `{regulator_code}` is the partition key.

If a collision is somehow observed at Step 6 (coverage scan), it is an internal-invariant failure and the skill emits `failure_shape` with `failure_state: "id-collision"` rather than attempting silent renumbering. Silent renumbering would break the audit trail and violate AP-Q8.

---

## 8. Cross-references

- SKILL.md Step 4 — input validation runs the regex from Sections 2 / 3 / 4.
- SKILL.md Step 6 — coverage scan checks AP-Q8 traceability and Section 7 collision invariant.
- SKILL.md Step 7 — execution-DAG assembly consumes IDs as edge endpoints.
- `anti-patterns.md` AP-Q8 — enforcement of these patterns at P1 severity.
- `markdown-rendering-spec.md` Section 7.5 — renderer behavior when IDs are missing.
- `coverage-rubric.md` Section 4 — per-story rules that drive TC count per scenario.
