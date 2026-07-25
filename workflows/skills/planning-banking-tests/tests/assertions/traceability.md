# Assertion — Traceability

## Scope

Test cases 001, 002. Applied after coverage-completeness passes.

## What's tested

Every test plan artifact traces back to a real BA brief element. No orphan tests; no hallucinated story / scenario / regulator / PII field references.

## Per-case assertions

1. **Every test_case.story_id resolves to a BA story.**
   ```
   jq -r '.test_cases[].story_id' output.json | sort -u > tc_story_refs.txt
   jq -r '.stories[].id' brief/output.json | sort -u > brief_story_ids.txt
   comm -23 tc_story_refs.txt brief_story_ids.txt   # expect empty (every TC story_id appears in brief)
   ```

2. **Every test_case.scenario_ref resolves to a real Gherkin scenario in that story.**
   ```
   # For each TC, lookup brief.stories[story_id].acceptance_criteria[].scenario_name; must contain TC.scenario_ref
   ```

3. **Every NFR test references a real epic.** `nfr_tests[].epic_id` ⊆ `epics[].id`.

4. **Every nfr_tests[].metric or blocking_oq references real data.** Either `metric` text appears in brief `success_criteria[]` for that epic, OR `blocking_oqs[]` reference real OQ IDs from the brief.

5. **Every compliance_test.regulator_code is in BA.** `compliance_tests[].regulator_code` ⊆ `regulatory_dependencies[].code`.

6. **Every test_data_specs.pii_field_ref is in BA.** `test_data_specs[].pii_field_refs[*]` ⊆ `pii_inventory[].field`.

7. **No invented thresholds.** Scan `expected_assertions[].description` for numeric values; ensure each numeric value either appears verbatim in BA `success_criteria[]` OR the test carries `blocking_oqs[]` (AP-Q9 enforced).

## Pass criterion

All 7 assertions pass. Hard gate on (1), (5), (6); soft gate on others (warning if violated, P2 coverage gap emitted by skill).

## What failure means

- TC references unknown story → renderer / SKILL.md mis-routed; story_id was mis-spelled.
- Invented numeric threshold → AP-Q9 violation. Skill prompt is silently resolving OQs.
- Compliance test for unnamed regulator → skill is hallucinating regulatory scope. Hard refuse; SKILL.md Step 7 broken.
