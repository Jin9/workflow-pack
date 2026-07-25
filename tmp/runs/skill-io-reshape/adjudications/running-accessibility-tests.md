# Adjudication — running-accessibility-tests (T4 accessibility-tests, replay-bound)

Source: codex/running-accessibility-tests.md · exit=0. Verified: input.json models phantom
target/wcag_level/tier vs the real pick (frontend-implement.files_generated + injected); corpus gate =
{verdict PASS, wcag_violations [], needs_review [], manual_checks[2], audit_id} — NO execution, NO
standard; skill required [verdict, manual_checks, audit_id] vs boundary/YAML [verdict, wcag_violations,
audit_id] (three-way disagreement); stage is replay-bound (runtime-binding) with no script runner →
the T6 pattern applies (execution REQUIRED is live-safe).

| F# | Sev | Verdict | Rationale / modified form |
|----|-----|---------|---------------------------|
| F1 | blocker | **ACCEPT** | input.json ← stub (files_generated from frontend-implement + injected; ADVISORY marker); phantom target/wcag_level/tier retired. |
| F2 | major | **ACCEPT** | execution{mode, target_source, runner?, engine?, evidence_ref?, report_sha256?} + scan_scope{targets_scanned} REQUIRED (replay-only stage — T6 pattern, no live executor to break); runner mode conditionally requires runner evidence; sim gains {"mode":"replay","target_source":"reference-corpus"} + targets_scanned derived from the corpus manifest count. YAML + boundary lockstep. |
| F3 | major | **ACCEPT** | Skill required → [verdict, wcag_violations, needs_review, manual_checks, audit_id] (omission can no longer mean "none"); corpus already conforms. |
| F4 | major | **ACCEPT** | if/then: PASS ⇒ empty violations + empty needs_review; FAIL ⇒ ≥1 violation or needs-review item; ERROR ⇒ non-empty errors[]. Corpus PASS valid. |
| F5 | major | **ACCEPT** | Configurable wcag_level input removed; required output standard{name WCAG, version 2.1, level AA} (const stamp — the gate IS the AA gate per its own prose); corpus gains the stamp via simulate.py (derived constant, not invented data). |
| F6 | major | **ACCEPT** | House audit_id formula documented (accessibility-tests:{idempotency_key}); corpus aid grandfathered. |
| F7 | major | **ACCEPT** | pii_handling → redact; redaction rules for needs_review.note / manual_checks / errors / DOM excerpts documented. |
| F8 | minor | **ACCEPT** | Violations require non-empty wcag_ref + targets[]; needs_review requires targets[]; minLength on text; manual_checks non-empty + uniqueItems. Corpus empty arrays validate. |
| F9 | minor | **ACCEPT** | Reclassified doc → brk; 0.1.0 → 0.2.0 + pin, boundary, corpus atomically. |
