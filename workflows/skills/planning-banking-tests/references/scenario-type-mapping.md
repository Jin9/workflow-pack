# Scenario-Type Mapping (v1.0)

## Purpose

This reference provides the deterministic mapping from a BA brief's
`acceptance_criteria[].scenario_type` value to the QA test plan's
`test_cases[].test_type` and `test_cases[].pyramid_level` defaults. It is
loaded at SKILL.md Step 4 on every run, regardless of tier. Every
acceptance criterion in the brief must resolve through this table; failing
that, the run emits a `failure_shape` output with reason
`unmapped_scenario_type`. The mapping is the load-bearing decoder between
BA-stage Gherkin scenarios and the QA-stage test roster, and its row count
and version are recorded in `processing_metadata` for audit
reconstruction.

## The mapping table

| scenario_type                        | test_type            | default_pyramid_level | naming_convention                              | notes |
|--------------------------------------|----------------------|------------------------|-------------------------------------------------|-------|
| `happy`                              | `functional`         | `unit` + `integration` | `TC-{STORY}-HP-{NNN}`                           | Emit two test cases per happy scenario: one pure-logic unit test and one integration test exercising the realistic adapter path. The unit case is mandatory; the integration case is mandatory when the scenario crosses a process boundary (DB, HTTP, queue). |
| `error`                              | `functional_negative`| `unit` + `integration` | `TC-{STORY}-ERR-{NNN}`                          | Errors must assert the precise error code, the user-visible message, and the absence of partial state. When the error path includes a compensating action, link the case to the corresponding `banking_grade_reversibility` test by `scenario_ref`. |
| `edge_case`                          | `functional_edge`    | `unit`                  | `TC-{STORY}-EDGE-{NNN}`                         | Boundary inputs (empty, max-length, off-by-one, locale-mixed). Default unit-level; promote to integration only when the edge depends on storage semantics (e.g., collation, decimal precision). |
| `banking_grade_audit`                | `audit`              | `integration`           | `TC-{STORY}-AUD-{NNN}`                          | Asserts a `workflow.stage.completed` (or domain-equivalent) event was emitted with the expected hashes, retention class, and 7-year horizon. Integration-level is the default because audit emission is rarely pure logic. |
| `banking_grade_idempotency`          | `idempotency`        | `integration`           | `TC-{STORY}-IDEM-{NNN}`                         | Replay-once and replay-many assertions, keyed by `idempotency_key`. The test must demonstrate that the second invocation returns the cached prior result without re-executing the side effect. |
| `banking_grade_authz`                | `security_authz`     | `integration`           | `TC-{STORY}-AUTHZ-{NNN}`                        | Asserts that the deny path returns the correct status code (403 vs 404 disambiguation) and that no information-leak side effect occurred. Promote to E2E only when the authz decision threads a UI flow that itself carries the leak risk. |
| `banking_grade_reversibility`        | `compensation`       | `integration`           | `TC-{STORY}-REV-{NNN}`                          | Asserts that the compensating action fully restores state and that the compensation event itself is auditable. Pairs with the upstream `banking_grade_audit` test by `scenario_ref`. |
| `banking_grade_tipping_off`          | `compliance_authz`   | `integration`           | `TC-{STORY}-TIPOFF-{NNN}`                       | Extension placeholder. Not observed as a direct `scenario_type` in the e-commerce-v5 holdout; surfaces in that holdout through `banking_grade_concerns` rows. When emitted by a future BA brief as a direct scenario_type, route here. |
| `banking_grade_notification`         | `notification`       | `integration`           | `TC-{STORY}-NOTIF-{NNN}`                        | Extension placeholder. Asserts a regulator- or customer-facing notification was emitted with the correct payload, channel, and retry policy. Not observed in the holdout as a direct scenario_type. |

The seven primary rows are validated against the 16 stories of the
e-commerce-v5 holdout, where every acceptance criterion resolves to
exactly one of those types. The two extension rows are reserved for
future briefs and are not emitted by v1.0.0 unless the brief carries the
corresponding type verbatim.

## Mapping versioning

Every test case emitted by this skill must carry, inside its parent
`processing_metadata` block, the field
`scenario_mapping_table_version: "1.0"`. The version is bound at run
time, not at schema time, so that an audit re-run against a future
mapping table version can be cleanly distinguished from the original
run. The version field is opaque to the schema and is intentionally
typed as a free-form string in `output.json` so that v1.1 can publish
"1.1" or "2.0" without a schema migration.

When two BA briefs produced under different mapping table versions are
diffed in audit, the version field is the first column inspected;
unequal versions void any test-case-level diff at the routing layer.

## Edge cases and disambiguation

A single Gherkin scenario in a BA brief may carry implicit multiple
classification. The disambiguation rules are:

1. The brief's `acceptance_criteria[].scenario_type` is authoritative
   for the primary mapping. The cell value is a single scalar, never an
   array.
2. When the same scenario is also referenced by a row in
   `banking_grade_concerns` (e.g., a `happy` scenario also marked as
   `banking_grade_audit_applies: true` at the story level), the skill
   emits two distinct test cases — one functional and one audit — and
   links them by sharing the same `scenario_ref` value. The
   `scenario_ref` field is the join key for audit reconstruction.
3. When a scenario carries a regulator code in
   `regulatory_dependencies` AND a `banking_grade_*` flag, the skill
   emits a third test case in `compliance_tests[]` whose
   `linked_test_case_ids[]` references the functional and banking-grade
   cases. Compliance tests are never the only output for such a
   scenario; the underlying functional or banking-grade case must
   exist independently.
4. When the brief contains a scenario whose `scenario_type` is not in
   the table above, the skill emits a `failure_shape` output with
   `failure_reason: "unmapped_scenario_type"` and the offending value
   in `failure_details.unmapped_value`. The skill does not silently
   discard nor heuristically reclassify.
5. When a scenario carries `scenario_type: edge_case` but the edge
   depends on storage or wire semantics (decimal precision, JSON null
   vs absent, charset collation), the mapping promotes
   `default_pyramid_level` from `unit` to `integration`. This
   promotion is recorded in the test case's `pyramid_promotion_reason`
   field for audit.

## Anti-patterns

See `anti-patterns.md` for the full list. Three anti-patterns apply
directly to this mapping:

- **AP-Q1** — Renaming `scenario_type` values to fit a preferred
  taxonomy. The brief's vocabulary is authoritative; the mapping
  table is the only legitimate site for transformation.
- **AP-Q2** — Collapsing a `happy` and a `banking_grade_audit`
  scenario into one combined test case to reduce roster size. This
  destroys the audit-reconstruction join and is rejected at
  validation.
- **AP-Q8** — Emitting a test case at a pyramid level lower than the
  default (e.g., demoting a `banking_grade_idempotency` integration
  case to a unit case with a mock) without recording
  `pyramid_demotion_reason` and a reviewer approval reference.

## When this table changes

The mapping table is versioned independently of the SKILL.md major
version, but follows a parallel discipline:

1. Adding a new row (new `scenario_type` observed in a future brief)
   is a **minor bump** (1.0 → 1.1) provided no existing row's
   `test_type` or `default_pyramid_level` changes. The two extension
   placeholders above are pre-allocated for the two most likely
   additions and may be activated by a minor bump.
2. Changing an existing row's `test_type` or `default_pyramid_level`
   is a **major bump** (1.0 → 2.0) because it alters the historical
   audit interpretation of every prior run.
3. Removing a row is always a **major bump** and requires a written
   deprecation notice in the SKILL.md `CHANGELOG` block at least one
   minor version in advance.
4. Renaming the `scenario_mapping_table_version` field key in
   `processing_metadata` is forbidden inside the v1.x series; rename
   is permitted only at the schema major boundary.

Every change to this table must update both this document and the
matching cross-link in `SKILL.md` Step 4. The renderer asserts that
the version string emitted in `processing_metadata` matches the
version recorded at the top of this file; a mismatch fails the run.
