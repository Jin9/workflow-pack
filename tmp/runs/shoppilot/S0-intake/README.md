# S0 · Intake — scope sheet / run plan

**Skill:** `scoping-ba-intake 1.0.0` · **gate:** auto (Delivery Ops light sign-off) · **status:** ▶ simulated.

Turns the raw requirement into a typed **Scope Sheet** (business goal, in/out-scope, quantified NFRs, open
questions, assumptions, risk flags) wrapped with a run plan that seeds the pipeline.

## Artifacts
- **`run-plan.json`** — the boundary contract (`workflows/schemas/run-plan.json`): `normalized_request`,
  `run_plan` (tier floor T2, S0–S7 + T1–T12 span, the 8 human gates), `scope_sheet` (envelope + contract),
  `audit_id`. `scoping-ba-intake` has no JSON output schema of its own, so the boundary schema **is** the typed
  contract here (and it satisfies the YAML `required_fields` `[normalized_request, run_plan, audit_id]`).
- **`ecommerce_mvp_business_only.gap-closed.md`** — the `raw_request` (happy-path, all open questions +
  governance gaps closed).
- **`gap-closure-ledger.md`** — how each raw open question / governance gap was resolved.

The latency NFR is intentionally an **open question** (`OQ-1`): the spec says "fast" with no number — surfaced,
not guessed (per the skill's anti-pattern rule).
