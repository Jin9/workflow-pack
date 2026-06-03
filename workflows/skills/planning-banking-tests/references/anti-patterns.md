# QA Anti-Patterns AP-Q1 through AP-Q12 — `planning-banking-tests` v1.0.0

> Loaded by `SKILL.md` at **Steps 5, 6, 8, 11, 12**. Sibling docs: `coverage-rubric.md`, `markdown-rendering-spec.md`, `test-case-id-rules.md`.

---

## 1. Purpose

This document catalogues the twelve QA anti-patterns that the skill must detect and refuse, mitigate, or downgrade. Each anti-pattern is a known failure mode in BA-brief-to-test-plan translation, drawn from banking-grade QA practice. The skill is expected to actively scan its own draft output against this list before Step 12 (render). An anti-pattern hit at P1 severity blocks the run; at P2 it produces a conditional-go exception; at P3 it produces an informational entry in `08-coverage-gaps.md`.

This list is closed at v1.0.0. New anti-patterns require a minor version bump and a corresponding update to `coverage-rubric.md` and SKILL.md.

---

## 2. How to use this document

Every anti-pattern entry below has the same five fields:

1. **Name** — the AP code and short title.
2. **Description** — the failure mode in one paragraph.
3. **Detection signal** — the exact, mechanically-checkable signal the skill uses to detect the pattern in its own draft output.
4. **Mitigation** — the action the skill takes when the signal fires.
5. **Severity** — P1 / P2 / P3 per the rubric in `coverage-rubric.md` Section 5.

Detection runs in three places in the skill flow:

- **Step 5 (test design)** — APs Q1, Q2, Q10, Q11, Q12 are checked against draft test cases.
- **Step 6 (coverage scan)** — APs Q3, Q4, Q6, Q9 are checked against the assembled plan.
- **Step 8 (compliance + NFR pass)** — APs Q7, Q11 are checked against compliance tests and test data specs.
- **Step 11 (rubric apply)** — AP Q5 is checked against the proposed rubric application.
- **Step 12 (render gate)** — every AP is re-checked; any P1 hit fails the render and emits a `failure_shape` output.

---

## 3. AP-Q1 — Generating test code instead of test plan

1. **Name**: AP-Q1 — Test-code-from-test-plan substitution.
2. **Description**: The skill emits executable test code (e.g., a Jest `describe`/`it` block, a pytest function, a Cypress spec, a Karate feature file) inside the test plan. The skill's charter is **test design**, not authoring; code generation is a separate skill (`test-code-from-gherkin`).
3. **Detection signal**: Any fenced `code_block` in the rendered markdown whose info-string is a programming language (`javascript`, `python`, `java`, `gherkin`, `feature`, ...). The audit-trace renderer also scans `output.json` for any string field whose value contains lines starting with `function `, `def `, `it(`, `describe(`, `Scenario:` outside the BA `scenario_name` field.
4. **Mitigation**: Refuse the run. Emit `failure_shape` with `failure_state: "scope-violation"` and `escalate_to_skill: "test-code-from-gherkin"`. Do **not** silently strip the code — the LLM call must be re-run with a tighter system prompt because the code's presence indicates upstream prompt drift.
5. **Severity**: P1.

---

## 4. AP-Q2 — Implementation-detail tests

1. **Name**: AP-Q2 — Asserting against implementation instead of observable behavior.
2. **Description**: A test case's expected assertion names a private function, internal class, or SQL query rather than a user-visible state change, response payload, audit event, or notification.
3. **Detection signal**: `test_cases[i].expected_assertions[j]` contains substrings such as `function called`, `method invoked`, `query executed`, `private method`, `internal function`, `class instantiated`, `module imported`, or matches the regex `\\b[a-z][a-zA-Z0-9_]*\\.[a-z][a-zA-Z0-9_]*\\(\\)` where the receiver is not a documented public interface from the BA brief.
4. **Mitigation**: Rephrase the assertion to observe one of: (a) returned response payload, (b) database state delta, (c) audit-event emission, (d) outbound notification, (e) UI state. The skill re-drafts the test case in place and records the rewrite in the audit trace.
5. **Severity**: P2.

---

## 5. AP-Q3 — Single-tier QA across multi-epic briefs

1. **Name**: AP-Q3 — Uniform pyramid across heterogeneous epics.
2. **Description**: The skill applies a single test-pyramid split (e.g., 70/20/10 unit/integration/e2e) across every epic, ignoring that different epics carry different `test_tier` values and different banking-grade footprints.
3. **Detection signal**: For a multi-epic brief (`scope_kind == "multi-epic"`), all entries in `epics[].pyramid_allocation` are identical. Equivalently: `len(distinct(epics[*].pyramid_allocation)) == 1` when `len(epics) > 1`.
4. **Mitigation**: Re-derive the pyramid per epic using `epics[].test_tier` and `pyramid-allocation-rules.md`. T1 epics carry more unit + integration; T3 epics carry more smoke.
5. **Severity**: P2.

---

## 6. AP-Q4 — Flaky-test acceptance

1. **Name**: AP-Q4 — Accepting flakes without quarantine.
2. **Description**: A test whose historical pass rate is between 80% and 95% is left in the active suite without a quarantine policy. Such tests poison the signal-to-noise ratio of CI.
3. **Detection signal**: `test_cases[i].historical_pass_rate` is present and falls in the half-open interval `[0.80, 0.95)` **and** `test_cases[i].quarantine_policy` is absent or null.
4. **Mitigation**: Emit `quarantine_policy` with `quarantined_at` set to the run timestamp, `fix_by` set to run timestamp + 14 days (T1) / 30 days (T2) / 60 days (T3), and `owner` set to the test's `owner`. Move the test out of `smoke_subset` if it was included.
5. **Severity**: P2.

---

## 7. AP-Q5 — Coverage-target obsession

1. **Name**: AP-Q5 — Treating line coverage % as a quality signal.
2. **Description**: The plan references line coverage, branch coverage, or statement coverage % as a sign-off criterion. Line coverage measures code reachability, not behavior correctness; banking-grade QA weights scenario + banking-grade coverage instead.
3. **Detection signal**: Any string in `coverage_matrix`, `signoff_criteria`, `qa_readiness_checklist`, or rendered markdown matching `(line|branch|statement)\\s*coverage` followed within 40 characters by a number + `%`.
4. **Mitigation**: Strip the percentage target. Replace with a reference to `coverage-rubric.md` Section 3 thresholds (scenario / banking-grade / NFR / compliance / PII). Record the rewrite in audit trace with `mitigation: "AP-Q5"`.
5. **Severity**: P1.

---

## 8. AP-Q6 — Mock-against-mock contract tests

1. **Name**: AP-Q6 — Contract tests whose provider side is a local fake.
2. **Description**: A contract test (consumer-driven or provider-driven) targets a local mock instead of a documented provider contract artifact or a sandbox-provider environment. Such tests cannot detect real upstream contract drift.
3. **Detection signal**: `test_cases[i].test_type == "contract"` **and** the test's `environment_ref` resolves to an environment with `kind == "local-mock"` or `kind == "stub"` **and** no `contract_source` field references either a TL Design contract artifact ID or a sandbox provider URL.
4. **Mitigation**: Source the contract from the TL Design contract artifact (`tl_design_ref`) or a sandbox-provider environment. If neither is available, emit a coverage gap (P2) and downgrade the test from `contract` to `integration-stub` with a note.
5. **Severity**: P2.

---

## 9. AP-Q7 — Real PII in test fixtures

1. **Name**: AP-Q7 — Production-shaped PII values in synthesized test data.
2. **Description**: A test data fixture contains a value that matches a PII pattern (e.g., real-looking Thai national ID, real phone number, real email) and lacks a test marker.
3. **Detection signal**: For every `test_data_specs[i].fixture_value`: if value matches any PII regex (Thai-NID `^\\d{13}$`, phone `^\\+?66\\d{9}$`, email `^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$`, name field, address) **and** does **not** contain a test marker (`+test`, `.test`, `example.com`, `example.co.th`, `TEST_`, `0000000000000`), flag it.
4. **Mitigation**: Regenerate the fixture from `test-data-design.md` synthesis rules. Replace email with `<role>+test-<seq>@example.co.th`, phone with `+66800000<seq:03>`, Thai-NID with the synthesizer's reserved range. Record the regeneration in audit trace.
5. **Severity**: P1.

---

## 10. AP-Q8 — Traceability loss

1. **Name**: AP-Q8 — Test case IDs that hide their BA provenance.
2. **Description**: A test case's ID does not embed both `story_id` and a scenario reference, breaking the BA-to-QA trace chain.
3. **Detection signal**: `test_cases[i].id` does not match the pattern `^TC-[A-Za-z0-9_.-]+-[0-9]{3}$` **or** the `{story_id}` segment of the id does not equal `test_cases[i].story_id` literally **or** `test_cases[i].scenario_ref` is empty/null.
4. **Mitigation**: Enforce the ID pattern from `test-case-id-rules.md`. Re-assign the id using sorted-iteration sequencing; record the prior (invalid) id in audit trace for traceability.
5. **Severity**: P1.

---

## 11. AP-Q9 — Authoring tests for unresolved open questions

1. **Name**: AP-Q9 — Concrete targets where BA still has an OQ.
2. **Description**: A test asserts a specific numeric or boolean value where the BA brief has an unresolved `open_questions[]` entry governing that value. Such a test will pass or fail arbitrarily depending on which side of the OQ is later resolved.
3. **Detection signal**: For each test case, scan `expected_assertions[j]` for numeric literals. For each literal, check whether the originating BA `success_criterion` or `scenario` references an `open_questions[]` entry whose `status != "resolved"`. If yes, the test is asserting against an unresolved OQ.
4. **Mitigation**: Set the test's `target` to the literal string `"TBD pending OQ-N"` where N is the open-question id. Populate `test_cases[i].blocking_oqs[]` with the OQ ids. Add the test to `coverage_gaps[]` with severity tied to the OQ's `blocks_*` flag.
5. **Severity**: P2 (P1 if the OQ has `blocks_qa_execution: true`).

---

## 12. AP-Q10 — Conflating Dev / QA test ownership

1. **Name**: AP-Q10 — Owner-role drift between pyramid levels.
2. **Description**: Integration or e2e tests are assigned to `Dev` ownership, or unit tests are assigned to `SDET` ownership. The kit's role contract is: **Dev owns unit tests; SDET owns integration + e2e; SDET-Security owns security tests; SDET-Perf owns performance tests; Compliance owns compliance tests.**
4. **Detection signal**: `test_cases[i].pyramid_level == "integration" | "e2e"` and `test_cases[i].owner == "Dev"`; or `pyramid_level == "unit"` and `owner` in `{"SDET", "SDET-Security", "SDET-Perf"}`.
5. **Mitigation**: Re-assign owner per the role contract above. Record the reassignment in audit trace. If the brief explicitly justifies a deviation, retain the assignment but emit a P3 informational gap.
6. **Severity**: P2.

---

## 13. AP-Q11 — Tipping-off in test plan copy

1. **Name**: AP-Q11 — AML / fraud-flow tests whose copy tips off the subject.
2. **Description**: A test description for an AML, fraud, sanctions, or suspicious-activity flow contains language that, if leaked or rendered in a UI, would inform the subject that they are flagged — violating tipping-off prohibitions under Thai AMLO and analogous regimes.
3. **Detection signal**: `test_cases[i].description` or `expected_assertions[j]` contains both (a) a flag/AML/suspicious vocabulary token (`AML`, `suspicious`, `flag`, `flagged`, `sanctions`, `STR`, `SAR`, `frozen`) **and** (b) a tipping-off verb phrase (`tell customer`, `inform customer`, `notify customer`, `display to customer`, `show to user`, `email customer`).
4. **Mitigation**: Rephrase to non-tipping vocabulary (`record internal audit event`, `notify ops queue`, `escalate to compliance reviewer`). Require Legal / Compliance review and set `reviewer_role: "Legal"`. Emit a P2 gap until reviewed.
5. **Severity**: P2 (P1 if the offending text is on a customer-facing surface in the test).

---

## 14. AP-Q12 — Audit assertions without payload schema

1. **Name**: AP-Q12 — "Audit emitted" assertions that don't enumerate fields.
2. **Description**: A test asserts that an audit event was emitted but does not name the required payload fields. Such assertions pass when an empty or malformed audit row is written, defeating the audit trail's purpose.
3. **Detection signal**: `test_cases[i].expected_assertions[j]` contains `audit event emitted`, `audit fired`, `audit logged`, or `audit record created` **and** does **not** enumerate the seven standard audit fields.
4. **Mitigation**: Rewrite the assertion to enumerate the seven standard fields: `event`, `actor`, `ts`, `before`, `after`, `reason`, `idem_key`. Add context-specific fields where the BA brief names them (`pii_subject_id`, `regulator_code`, `monetary_amount`, ...). Record the rewrite in audit trace.
5. **Severity**: P2.

---

## 15. Cross-references

- SKILL.md Steps 5, 6, 8, 11, 12 — detection invocation points.
- `coverage-rubric.md` Section 5 — severity-to-signoff mapping.
- `test-case-id-rules.md` — AP-Q8 enforcement rules.
- `test-data-design.md` — AP-Q7 synthesis rules.
- `compliance-test-patterns.md` — AP-Q11 tipping-off templates.
