# Assertion — Scenario-Mapping Determinism

## Scope

Test cases 001, 002. Not meaningful on failure shapes.

## What's tested

Running the skill twice on the same input with the same `idempotency_key` produces byte-identical canonicalized output.

## Procedure

```
# Run 1
qa-skill run --input tests/cases/001-ecommerce-multi-epic.input.json --out runs/001/r1
# Run 2 — identical input
qa-skill run --input tests/cases/001-ecommerce-multi-epic.input.json --out runs/001/r2

# Canonicalize: sort JSON keys, mask volatile fields
jq -S 'del(.processing_metadata.generated_at, .processing_metadata.run_id,
           .processing_metadata.duration_ms, .processing_metadata.tokens_used,
           .frontmatter.created_at)' runs/001/r1/output.json > runs/001/r1.canon.json
jq -S 'del(.processing_metadata.generated_at, .processing_metadata.run_id,
           .processing_metadata.duration_ms, .processing_metadata.tokens_used,
           .frontmatter.created_at)' runs/001/r2/output.json > runs/001/r2.canon.json

# Compare
diff -u runs/001/r1.canon.json runs/001/r2.canon.json
diff -ur runs/001/r1/test-plan-*/ runs/001/r2/test-plan-*/
```

Mask rules applied via a regex pass before diff:
- `\d{4}-\d{2}-\d{2}T[0-9:.+Z-]+` → `<TS>`
- `sha256:[a-f0-9]{64}` → `sha256:<H>`
- `run_[a-z0-9]+` → `run_<ID>`

## Pass criterion

`diff` exit code 0 on both the canonicalized JSON and the rendered tree. Zero lines of text difference after masking.

## What failure means

- JSON differs but tree from a frozen `output.json` is stable → upstream bug: LLM is non-deterministic at temp=0.3. Mitigation: response cache (see R1 in `audit/phases/phase-a1-skill-genesis.md`).
- JSON identical but tree differs → renderer is non-deterministic. Bug in `scripts/render_test_plan_tree.py`: dict iteration order, unsorted JSON, or missing key sort. Hard failure; must fix before ship.

## Severity

Hard gate. Banking-grade non-negotiable #3 (determinism). Cannot ship v1.0.0 if this fails.
