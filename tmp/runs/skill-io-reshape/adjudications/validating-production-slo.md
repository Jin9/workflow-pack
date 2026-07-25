# Adjudication — validating-production-slo (S7 prod-validate, replay-bound, receipt-based)

Source: codex/validating-production-slo.md · exit=0 (landed on the 00:13 mop-up). Verified: input.json
requires phantom slo_defs/live_metrics vs the real pick (release-handoff.receipt_id + injected — the
canary/smoke receipt pattern); corpus smoke-slo.json = {verdict promote, grade Pass, per_slo[4] rows
{name, target, observed, burn_rate, judgement}, window, audit_id} — NO execution, NO receipt_id, and
per_slo rows carry bare numbers with no unit/comparison (target 800 vs 99.9 vs 0 — scale is implicit);
grade/verdict are independent enums (Pass+rollback validates today); window optional; per_slo has no
minItems.

| F# | Sev | Verdict | Rationale / modified form |
|----|-----|---------|---------------------------|
| F1 | blocker | **ACCEPT** | input.json ← stub (receipt_id + idempotency_key + injected; ADVISORY marker); slo_defs/live_metrics/bake_window/tier retired; receipt resolves through a read-only deployment/observability registry into the approved SLO policy + telemetry; unavailable policy/telemetry ⇒ needs-input. doc → brk; 0.1.0 → 0.2.0 + pin. |
| F2 | blocker | **ACCEPT** | execution{mode, target_source} REQUIRED (fleet shape; runner ⇒ +runner/evidence_ref/report_sha256; replay ⇒ reference-corpus) in skill+boundary+YAML; sim gains replay provenance; requires_capabilities: [code_execution, sandbox_network_access] added (live mode reads a telemetry backend). |
| F3 | major | **ACCEPT** | Top-level receipt_id REQUIRED, echoed unchanged — binds the SLO evidence to the release it validated (mirrors the smoke gate); corpus echoes the run's own s6["receipt_id"]. |
| F4 | major | **ACCEPT** | House audit_id formula documented (prod-validate:{idempotency_key}); corpus id grandfathered; NO engine equality enforcement this pass (that stays on the follow-up ledger). |
| F5 | major | **ACCEPT** | grade/verdict pairing enforced (oneOf: Pass↔promote · Marginal↔hold · Fail↔rollback — today Pass+rollback validates); rollback requires a breaching row; promote requires all rows within_budget. Corpus Pass/promote/all-within-budget valid. |
| F6 | major | **ACCEPT** | window REQUIRED non-empty (skill+boundary+YAML) — the normalized summary of every fast/slow window actually evaluated, not a display note. Corpus supplies it. |
| F7 | major | **ACCEPT** | per_slo minItems 1; rows require name/target/observed/burn_rate/judgement (name non-empty, target non-null); observed/burn_rate nullable ONLY for insufficient telemetry (F9); burn_rate ≥ 0. Corpus 4 rows conform. |
| F8 | major | **ACCEPT** | Rows require unit + comparison (gte|lte|eq) so target/observed share an explicit scale (today 99.9, 800 and 0 sit side by side, meaning nothing without them). Corpus derived HONESTLY from its own row semantics: availability percent/gte · latency ms/lte · error-rate percent/lte · incidents count/eq. |
| F9 | major | **ACCEPT** | judgement enum += insufficient_data (skill + boundary) + per-row reason: insufficient_data ⇒ non-empty redacted reason ∧ null observed/burn_rate; partial/low-resolution telemetry maps to Marginal/hold; a wholly missing SLI series stays needs-input with NO verdict artifact (fail-closed — never a fabricated pass). |
| F10 | minor | **ACCEPT** | Dead refs: analyzing-canary-rollout kept (real); observability-design → "the SLO-authoring workflow"; incident-response → "the incident-response process" (no such skills exist). |

Version: 0.1.0 → 0.2.0 + YAML pin. Boundary required = [verdict, receipt_id, grade, per_slo, window,
execution, audit_id] == YAML (R3). Closes the LAST baseline lint finding → ratchet 0.
