# S7 · Prod Validation — validating-production-slo

**Skill:** `validating-production-slo 0.1.0` · **gate:** sync (L3, On-call / Release Manager — named rollback
decision) · **status:** ▶ simulated.

Validates the live release against the declared SLOs (multi-window burn-rate) and emits a
`promote | hold | rollback` verdict — the named rollback decision.

## Artifacts
- **`smoke-slo.json`** — the contract (`workflows/schemas/smoke-slo.json`; skill
  `validating-production-slo/schemas/output.json`): **verdict `promote`**, **grade `Pass`**,
  `per_slo[]` (availability 99.97% · order-confirm p95 540ms · error-rate 0.1% · 0 double-charge — all
  `within_budget`), `window` (30m + 6h burn-rate), `audit_id`.

> The built skill's `verdict` **is** the YAML's `slo_verdict` and encodes the `rollback_decision`
> (promote = no rollback); the speculative YAML fields predate the built skill (OI-003).
