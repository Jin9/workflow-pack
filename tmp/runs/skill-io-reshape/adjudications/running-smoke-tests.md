# Adjudication — running-smoke-tests (T11 smoke-tests, replay-bound, receipt-based)

Source: codex/running-smoke-tests.md · exit=0. Verified: input.json models phantom probes/target_env/
tier vs the real pick (release-handoff.receipt_id + injected — the canary receipt pattern, donor input
requires exactly [receipt_id, idempotency_key]); corpus gate probes lack executed (latency_ms already
nullable in the schema); no top-level receipt_id/execution; S6 receipt = RCPT-shoppilot-20260607-0001;
YAML policy = retry ×1 exponential → smoke-test-failures (F6's wording matches exactly).

| F# | Sev | Verdict | Rationale / modified form |
|----|-----|---------|---------------------------|
| F1 | blocker | **ACCEPT** | input.json ← stub (receipt_id + idempotency_key + injected; ADVISORY marker + example); probes/target_env/tier retired; receipt resolves through the read-only deployment registry into its target + approved smoke manifest; endpoints outside the receipt's approved target are rejected. doc → brk; 0.1.0 → 0.2.0 + pin. |
| F2 | major | **ACCEPT** | Top-level receipt_id (echoed unchanged) + execution{mode, target_source} REQUIRED (runner ⇒ +runner/evidence_ref/report_sha256; replay ⇒ reference-corpus) in skill+boundary+YAML; sim gains the S6 receipt id (derived from the run's own receipt) + replay provenance. |
| F3 | major | **ACCEPT-MODIFIED** | probes minItems 1 = every resolved manifest probe; items require name/executed/green; non-green ⇒ redacted reason; conditionals: PASS ⇒ all executed ∧ all green ∧ all_green true; FAIL ⇒ ≥1 executed ∧ (≥1 non-green ∨ unexecuted) ∧ all_green false; ERROR ⇒ none executed ∧ all_green false. MODIFIED: latency_ms stays OPTIONAL-nullable — stamping fixed synthetic latencies into the corpus would fabricate measurement data (no-fabrication doctrine); executed:true is the sim's own declared scenario and is added. |
| F4 | major | **ACCEPT** | House audit_id formula documented (smoke-tests:{idempotency_key}); corpus id grandfathered; included in the validating example. |
| F5 | major | **ACCEPT** | pii_handling none → redact; probe rows carry only normalized redacted end-state summaries / offline evidence refs — never response bodies, credentials, or captured identifiers. |
| F6 | minor | **ACCEPT** | SM-02..04 rewritten to the configured route: FAIL/ERROR retry once (exponential) then smoke-test-failures; hold/rollback is the named human's / release controller's decision; preflight needs-input (unknown receipt / missing approved manifest) distinguished from runner-time ERROR. |
