# Adjudication — scanning-appsec-pipeline-gate (T7 appsec-scan, replay-bound)

Source: codex/scanning-appsec-pipeline-gate.md · exit=0. Verified: input.json models phantom
target_env/sbom/baseline; the YAML picks files_generated from BOTH implement stages and the flat merge
keeps only the frontend manifest (functionally material for live: backend files would go unscanned from
the payload — but the scan's real enumeration source is the two artifacts resolved via
upstream_artifacts, so Codex's document-the-collision approach is correct here, unlike qa-plan where the
payload fields WERE the consumed truth); corpus gate = {PASS, dast_findings [], sca_cves [], secrets 0,
audit_id} — no execution/new_vs_baseline; pact + T6 SKILL.md already document the same collision
verbatim ("the top-level field is the frontend manifest only") → all three COLLISION_WHITELIST entries
are justified; gates.yaml routes PASS auto / FAIL-ERROR retry once → named-human queue.

| F# | Sev | Verdict | Rationale / modified form |
|----|-----|---------|---------------------------|
| F1 | blocker | **ACCEPT** | input.json ← post-adapter truth: required files_generated documented as "the frontend manifest (last-writer-wins) — a hint, never the enumeration source; resolve BOTH full artifacts via upstream_artifacts"; injected optionals; scan params move to the context (F3). NO NESTED_HANDOFF change (payload pick is not the consumed truth here); nested per-producer shape reserved for a future contract. COLLISION_WHITELIST += (appsec-scan|contract-tests|integration-tests, files_generated) — all three consumers document the winner. |
| F2 | blocker | **ACCEPT-MODIFIED** | dast_findings + sca_cves required; per-finding gate_status; conditionals: PASS ⇒ secrets 0 ∧ all scanners completed ∧ no blocking finding; FAIL ⇒ secrets>0 ∨ blocking finding ∨ non-empty blocking_reasons; ERROR ⇒ non-empty errors[] (the ≥1-scanner-error link stays prose — a 3-way nested anyOf adds noise, errors[] is the machine signal). |
| F3 | major | **ACCEPT** | Optional workflow input appsec_scan_context {target_ref, target_kind ci-sandbox\|sit-sandbox, build_ref, sbom_ref, severity_floor, baseline_ref nullable, scanner profile refs} + from_workflow_input pick; live runner mode absent-context ⇒ needs-input; replay unaffected. |
| F4 | major | **ACCEPT** | execution{mode, target_source, scanners{dast,sca,secrets}.status} REQUIRED (replay-bound → T6 pattern); runner mode requires tool identity + evidence_ref + report sha256; YAML+boundary lockstep; sim gains replay provenance; doc → brk, 0.2.0. |
| F5 | major | **ACCEPT** | Nullable inline sbom retired → context sbom_ref; missing SBOM in runner mode ⇒ needs-input; failed SCA ⇒ ERROR; PASS requires scanners.sca.status == completed (the integrated gate cannot certify zero known-exploited CVEs without SCA evidence). |
| F6 | major | **ACCEPT** | new_vs_baseline required with separate dast/sca {new, accepted, fixed} counts (corpus zeros — derived from its own empty findings); DAST findings gain fingerprint/rule_id/non-secret target/baseline_status/gate_status/evidence_ref; SCA gains package/version/fix + provenance; secret_findings[] = fingerprint+detector+location ONLY, never the matched value. |
| F7 | minor | **ACCEPT** | Gate-route truth: automatic machine gate — PASS completes; FAIL/ERROR retry once then the named-human queue; "every verdict feeds named-human signoff" removed; PASS = evidence, not release authorization (kept). |
| F8 | minor | **ACCEPT** | House audit_id formula documented (appsec-scan:{idempotency_key}); corpus id grandfathered. |
