# Adjudication — validating-banking-implementation (T10 adversarial-pentest, human L3 gate)

Source: codex/validating-banking-implementation.md · exit=0. Verified: input.json models phantom
implementation_ref/threat_personas vs the real picks (qa-validate totals + verdict + injected); corpus
gate = {verdict pass, persona_findings [], audit_id} — no execution; skill output required [verdict,
audit_id] while YAML+boundary require persona_findings (skill schema is the laggard); YAML policy
human-queue max_retries 0 vs frontmatter max_retries_recommended 1; timeout 900 < declared p95 1800.

| F# | Sev | Verdict | Rationale / modified form |
|----|-----|---------|---------------------------|
| F1 | blocker | **ACCEPT** | input.json ← stub (strict totals mirror + uppercase QA verdict — documented as the UPSTREAM QA verdict, distinct from this stage's lowercase pass/conditional/fail; injected optionals; ADVISORY marker). implementation_ref/threat_personas/tier retired from the raw shape. doc → brk; 0.1.0 → 0.2.0 + pin. |
| F2 | blocker | **ACCEPT** | Optional workflow input adversarial_pentest_context {target_ref, target_kind ci-sandbox\|uat-sandbox, authorization_ref REQUIRED (explicit pentest authorization — strengthens the sanctioned-use posture), threat_personas?, runner_profile_ref?, tier?} + from_workflow_input pick; live mode absent-context ⇒ needs-input; replay unaffected; procedure attaches to an already-staged authorized sandbox target, never deploys. |
| F3 | major | **ACCEPT** | persona_findings added to skill required (YAML+boundary already require it; corpus [] valid). |
| F4 | major | **ACCEPT** | execution{mode, target_source} REQUIRED (fleet shape; runner ⇒ +evidence_ref/report_sha256) in skill+YAML+boundary; sim gains replay provenance. |
| F5 | major | **ACCEPT** | House audit_id formula (adversarial-pentest:{idempotency_key}); the "human decision is logged under this id" conflation removed — the L3 gate verdict record is engine-side (events.jsonl/HITL), external to the artifact. |
| F6 | major | **ACCEPT** | conditional/fail ⇒ persona_findings minItems 1; persona/scenario/evidence minLength 1 + non-whitespace. Corpus pass valid. |
| F7 | major | **ACCEPT** | Default persona roster defined in the reference with stable persona_id + authorization context + objective + allowed scenario classes; inline threat_personas (context) items require {persona_id, objective, auth_context}; output persona carries the stable persona_id. |
| F8 | minor | **ACCEPT** | pii_handling none → redact (evidence strings can quote captured data); [PII:REDACTED:CLASS=...] standardized. |
| F9 | minor | **ACCEPT** | timeout_seconds 900 → 2100 (the documented 1800s p95 is authoritative for a real pentest; a 900s timeout would kill every live run) + max_retries_recommended 1 → 0 (matches the human-queue policy's zero retries). |
