# Adjudication — running-sast-security-gate (T3 sast-gate, replay-bound)

Source: codex/running-sast-security-gate.md · exit=0. Verified: input.json models phantom
source_ref/baseline/severity_floor/tier vs the real pick (backend-implement.files_generated + injected);
corpus gate = {PASS, findings [], secrets 0, new_vs_baseline {new 0, fixed 2}, audit_id} — no
execution/scan_scope/policy; skill required [verdict, secrets, audit_id] vs YAML/boundary [verdict,
findings, secrets, audit_id] (disagreement); gates.yaml: automatic gate, retry once → sast-gate-failures
named-human queue (the "named-human sign-off on every verdict" claim is false); SAST is a static scan —
the network-fetch capability is unneeded.

| F# | Sev | Verdict | Rationale / modified form |
|----|-----|---------|---------------------------|
| F1 | blocker | **ACCEPT** | input.json ← stub (files_generated w/ producer item shape + injected); source_ref/baseline/severity_floor/tier retired (policy arrives via output `policy` record; baseline via ref); manifest paths resolve relative to dirname(upstream_artifacts["backend-implement"]); unusable manifest ⇒ NO artifact, retry → human-queue (no undefined needs-input route); sandbox_network_access capability dropped. doc → brk, 0.2.0. |
| F2 | blocker | **ACCEPT** | execution{mode, target_source} + scan_scope{targets_scanned} REQUIRED (skill+YAML+boundary; replay-bound → T6 pattern); runner mode requires scanner name/version + evidence_ref + report sha256; replay forces reference-corpus; sim gains replay provenance; "replay ran no scanner" documented. |
| F3 | major | **ACCEPT** | findings + new_vs_baseline added to skill required; new_vs_baseline to YAML+boundary; complete required/optional sets stated in the Output contract. Corpus already carries both. |
| F4 | major | **ACCEPT** | policy{severity_floor, baseline_mode, baseline_ref} + blocking_reasons[] required; findings gain fingerprint/baseline_status(new\|existing)/blocking; new_vs_baseline → {new, existing, fixed} (corpus gains existing: 0 — derived from its own empty findings; fixed: 2 kept, the sim's declared scenario); errors[]; conditionals: PASS ⇒ secrets 0 ∧ no blocking finding ∧ no blocking reasons; FAIL ⇒ ≥1 blocking reason; secrets>0 ⇒ FAIL; ERROR ⇒ errors[]. Procedure semantics corrected (fixed = baseline findings absent from the current scan). |
| F5 | major | **ACCEPT** | House audit_id formula in schema + Output contract (sast-gate:{idempotency_key}); corpus id grandfathered — never rewritten. |
| F6 | major | **ACCEPT** | Auto-gate truth: PASS completes the leaf; execution/schema failure retries once then sast-gate-failures for named-human RESOLUTION (not sign-off of every verdict); PASS = evidence, not release authorization. |
| F7 | major | **ACCEPT** | pii_handling none → redact (substantive correction — finding summaries can quote source); [PII:REDACTED:CLASS=...] required in finding-summary descriptions. |
| F8 | minor | **ACCEPT** | Unresolvable [[literature/...]] vault links in references/sast-gate.md replaced with bare-text source mentions (cross-model portability; no matching tracked assets). |
