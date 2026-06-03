# Assertion — Coverage Completeness

## Scope

Test cases 001 (full holdout), 002 (banking single-epic). Not applied to failure shapes (003, 004).

## What's tested

Every BA Gherkin scenario, banking-grade-applies row, NFR target, and compliance regulator from the brief is covered by ≥1 corresponding artifact in the test plan.

## Per-case assertions

1. **Every story has ≥1 test case.**
   ```
   jq -r '.stories[].story_id' output.json | sort -u > stories_with_plan.txt
   jq -r '.stories[].id' brief/output.json | sort -u > brief_stories.txt
   diff brief_stories.txt stories_with_plan.txt   # expect empty
   ```

2. **Every Gherkin scenario maps to ≥1 test case.**
   ```
   jq -r '.stories[].acceptance_criteria[].scenario_name' brief/output.json | sort -u > brief_scenarios.txt
   jq -r '.test_cases[].scenario_ref' output.json | sort -u > planned_scenarios.txt
   diff brief_scenarios.txt planned_scenarios.txt   # expect every brief_scenario present in planned (planned may be a superset)
   ```

3. **Every banking_grade_applies row has corresponding test case with matching tag.** For each `(story_id, concern)` where `banking_grade_concerns.<concern>.status == "applies"`, expect ≥1 test case with `story_id == that_story` AND `banking_grade_<concern>` in `tags[]`.

4. **Every NFR target either resolved OR linked to a blocking OQ.** For each `nfr_tests[].target` not literally "TBD pending OQ-N": ensure value is concrete. For each "TBD pending..." entry: ensure `blocking_oqs[]` non-empty.

5. **Every regulator covered.** `regulator_codes_in_brief = set(regulatory_dependencies[].code)` ⊆ `set(compliance_tests[].regulator_code)`.

6. **Every PII field referenced.** `pii_fields_in_brief = set(pii_inventory[].field)` ⊆ `union(test_data_specs[].pii_field_refs[])`.

## Pass criterion

All 6 assertions pass. AC coverage ≥ 100% (hard), banking-grade ≥ 100% (hard), NFR/regulator/PII ≥ 95% combined.

## What failure means

- Missing test case for a Gherkin scenario → AP-Q8 traceability loss, or BA brief has a scenario the skill didn't read.
- Missing banking_grade test → TM-05 should have fired; either renderer dropped a tag or coverage rubric was skipped.
- Missing regulator/PII coverage → AP-Q9 (skill assumed defaults or omitted scope).
