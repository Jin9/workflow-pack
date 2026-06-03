# Assertion — Tree Shape

## Scope

Applied to test cases 001, 002, 005 (success or partial output_type). Test cases 003, 004 use the failure-tree shape.

## What's tested

Output directory layout matches `references/markdown-rendering-spec.md` exactly.

## Required files (success / partial shape)

Tree under `test-plan-{idem8}/`:

- `README.md` present
- `output.json` present and parses as JSON
- `00-STRATEGY.md` through `10-audit-trace.md` all present (11 top-level docs)
- `epics/` directory present
- Per epic in `epics/EPIC-{NAME}/`: `EPIC-test-plan.md` + `stories/` directory
- Per story in `epics/EPIC-{NAME}/stories/`: one file matching pattern `{story-slug}-test-plan.md`

## Required files (failure shape — cases 003, 004)

- `README.md` (carries failure banner)
- `output.json` (with `failure_state` populated)
- `FAILURE.md` (translated failure description)
- NO `00-STRATEGY.md` through `10-audit-trace.md`
- NO `epics/`

## Pass criterion

`find test-plan-{idem8}/ -type f | sort` matches the expected listing exactly. No extra files. No missing files. Compare against `expected/tree-listing.txt`.

## Verification command

```
find runs/<case-id>/test-plan-*/ -type f | sort > runs/<case-id>/actual-listing.txt
diff -u expected/<case-id>-tree-listing.txt runs/<case-id>/actual-listing.txt
```

Pass if `diff` returns exit code 0.

## What failure means

- Missing top-level doc → renderer skipped a section; likely a regression in `render_test_plan_tree.py`.
- Extra files → renderer leaked auxiliary output; should not happen as renderer is pure.
- Missing per-story file → renderer failed to iterate `stories[]` sorted, or `output.json` is missing a story the schema claimed.
