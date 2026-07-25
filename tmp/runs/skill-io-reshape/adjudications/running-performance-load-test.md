# Adjudication — running-performance-load-test (T9 perf-load-test, replay-bound)

Source: codex/running-performance-load-test.md · exit=0. Verified: input.json models phantom
load_profile/budget/target_env vs the real picks (qa-validate.totals + verdict + injected); corpus gate =
{verdict PASS, metrics{p95, error_rate}, within_budget true, breaches [], audit_id} — NO execution, NO
sample_adequate; sim gate() at simulate.py:692 confirmed; delivery-pipeline-input.json already carries
the contract_test_context / integration_test_context precedent for optional runner contexts.

| F# | Sev | Verdict | Rationale / modified form |
|----|-----|---------|---------------------------|
| F1 | blocker | **ACCEPT** | input.json ← stub (totals + verdict shaped from executing-qa-test-suite + injected; input verdict documented as the QA verdict, never the perf verdict; ADVISORY marker). Runner fields relocate to performance_test_context (F2). doc → brk; 0.1.0 → 0.2.0 + pin. |
| F2 | major | **ACCEPT** | Optional workflow-input performance_test_context {load_profile, budget, target_env, target_kind staging\|uat, runner_profile_ref?} (strict; additive to delivery-pipeline-input.json — same pattern as contract/integration contexts) + from_workflow_input pick. Live runner mode without it ⇒ needs-input; replay unaffected. QA totals/verdict documented as prerequisites, not load evidence. |
| F3 | major | **ACCEPT** | execution{mode runner\|replay, target_source} REQUIRED (replay-bound stage, T6 pattern); runner mode conditionally requires runner + run-relative evidence_ref + 64-hex report_sha256; skill+YAML+boundary lockstep; sim gains {"mode":"replay","target_source":"reference-corpus"}. |
| F4 | major | **ACCEPT** | breaches promoted required (corpus has []); if/then: PASS ⇒ within_budget true + numeric p95/error_rate + zero breaches; FAIL ⇒ within_budget false; ERROR ⇒ within_budget false + errors[]; breach observed/budget non-null non-negative. Corpus PASS satisfies. |
| F5 | major | **ACCEPT** | sample_adequate required + optional limitations[] (required non-empty when inadequate); PASS ⇒ adequate; FAIL ⇒ breach ∨ inadequacy evidence; YAML+boundary; sim adds sample_adequate true (the sim's own scenario declaration — same class as execution provenance, mirrors canary). |
| F6 | major | **ACCEPT** | budget.throughput_min_rps optional in the context; threshold semantics documented (p95/p99/error_rate = upper bounds, observed ≥ threshold breaches; throughput = lower bound, observed < threshold breaches). |
| F7 | minor | **ACCEPT** | House audit_id formula documented (perf-load-test:{idempotency_key}). |
| F8 | minor | **ACCEPT** | metrics.p95 + metrics.error_rate required numeric on PASS/FAIL; p99/throughput optional runner-supplied — corpus p99/throughput NOT fabricated (no-fabrication doctrine). |
| F9 | minor | **ACCEPT** | Dead observability-design refs removed; SLI/SLO design → designing-tech-lead-handoff; executable budget = the approved workflow-supplied context. |
| F10 | minor | **ACCEPT** | ADVISORY marker + one validating fenced example per contract section. |
