# Assertion — Budget Envelope

## Scope

Test case 001 (full holdout, ~169KB output.json input). Required SLA check before ship.

## What's tested

Wall-clock and dollar cost of one run on the holdout fit the T2 envelope: cost ≤ $1.50/run, p95 wall-clock ≤ 5 min, max single-run cost ≤ $2.00.

## Procedure

```
# Run 5 times to compute p95 wall-clock + median cost
for i in $(seq 1 5); do
  /usr/bin/time -l qa-skill run \
    --input tests/cases/001-ecommerce-multi-epic.input.json \
    --emit-metrics runs/bench-$i/metrics.json \
    --out runs/bench-$i/
done

# Compute aggregate metrics from frozen pricing table
python tools/cost.py runs/bench-*/metrics.json \
  --pricing-table references/model-pricing.json \
  --report runs/bench-summary.json
```

Pricing table must be frozen at design time (e.g., `references/model-pricing-2026-04.json`) so the assertion is reproducible across re-runs.

## Pass criterion

- **Median cost ≤ $1.50/run** (design budget $1.15 + 30% slack)
- **p95 wall-clock ≤ 300s** (5 minutes)
- **Max single-run cost ≤ $2.00** (hard ceiling — fail if exceeded)
- **Token budget**: ≤ 120k prompt + ≤ 30k completion at T2

## What failure means

- Median cost > $1.50 but < $2.00 → prompt is fat; trim reference files or move guidance behind conditional loading.
- p95 > 5 min → single LLM call is too long-context for the chosen model; either upgrade or split (which would force re-opening ADR #8).
- Max > $2.00 → design is structurally over-budget; re-baseline T2 or re-evaluate monolithic.

## Severity

Hard gate. v1.0.0 must pass this scenario before release. If it fails on the actual holdout, the design brief's monolithic assumption is invalidated and we re-open Step 3 cost analysis.
