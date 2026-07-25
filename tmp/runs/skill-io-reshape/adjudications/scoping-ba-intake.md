# Adjudication — scoping-ba-intake (S0 intake) — the 2.0.0 rewrite

Source: codex/scoping-ba-intake.md · exit=0. Verified: schemas/ ABSENT (the only pipeline skill with no
schemas — engine SKILL_SCHEMA_EXEMPT = {intake, ba-research}; _sim CHECKS row is (…, None, boundary));
corpus run-plan.json = {audit_id, normalized_request (STRING), run_plan{tier_floor, stage_span,
epics_expected, pipeline, human_gates[]}, scope_sheet{envelope, contract{business_goal, in_scope,
out_of_scope, nfrs[{kind,target}], open_questions, assumptions, risk_flags}}, human_view};
envelope carries task_id + created_at (2026-06-07T00:00:00Z — a hardcoded sim constant, not a clock) and
state "ready-for-stories" (fictional — the real successor is s1-discovery); eliciting's input.json
requires normalized_request as an OBJECT while the boundary + corpus + producer all say STRING.

| F# | Sev | Verdict | Rationale / modified form |
|----|-----|---------|---------------------------|
| F1 | blocker | **ACCEPT** | AUTHOR schemas/input.json + schemas/output.json (strict draft-07, house $id, AP:false), typed from the REAL corpus shape; frontmatter points at both; legacy YAML-ish output block replaced by validating JSON examples; boundary desc drops the "substitutes for a skill schema" claim. Engine exemption removal is a P3 follow-up (validated first via the _sim CHECKS flip). |
| F2 | blocker | **ACCEPT** | normalized_request = non-empty REDACTED STRING everywhere (producer schema + BOTH consumer input schemas incl. eliciting — whose object-typed requirement contradicted the boundary, corpus and every other consumer); the structured Scope Sheet stays exclusively in scope_sheet. Cross-skill fix (eliciting input.json + example). |
| F3 | major | **ACCEPT-MODIFIED** | audit_id is the sole artifact identity (house formula intake:{idempotency_key}); nested task_id + created_at REMOVED from the envelope. MODIFIED: the corpus audit_id VALUE is preserved (grandfathered — never rewrite provenance); only the envelope STRUCTURE changes, via simulate.py. |
| F4 | major | **ACCEPT** | input.json = the POST-adapter payload: raw_request + requester (non-empty) + idempotency_key (workflow-scoped); invented scale/system_context/deadline fields dropped (the strict workflow input never supplies them — they live inside raw_request); ADVISORY marker; NO upstream_artifacts/loop_back_feedback (S0 has no producer and no loop-back path — verified in the YAML). |
| F5 | major | **ACCEPT** | scope_sheet promoted required (skill + boundary + YAML); typed envelope + contract: business_goal non-empty; in_scope/out_of_scope; nfrs[{kind,target}]; open_questions with ^OQ-[1-9][0-9]*$ ids + question + for; assumptions; unique risk_flags; AP:false throughout. Boundary stays the permissive superset. |
| F6 | major | **ACCEPT** | run_plan typed: required tier_floor (T1\|T2\|T3), stage_span (non-empty), epics_expected (int ≥0; 0 = not yet estimable); optional pipeline + unique non-empty human_gates[]; AP:false; procedure gains derivation rules (no guessing). |
| F7 | major | **ACCEPT** | Positioning truth: S0 stage `intake`, successful state `ready-for-discovery` (successor = s1-discovery); the fictional "G1 scope-confirm stop" deleted; unusably thin input = INTAKE-01 EXECUTION FAILURE routed to delivery-intake-pending — NOT a schema-valid needs-clarification artifact that the auto gate would wave through (fail-closed). Corpus state patched deterministically. |
| F8 | major | **ACCEPT** | OQ-n ids stay stable identifiers inside the Scope Sheet + its human view; the false claim that downstream stages reference them verbatim is deleted (the YAML passes only normalized_request; no consumer declares scope_sheet). No cross-stage traceability promise without a coordinated mapping. |
| F9 | minor | **ACCEPT** | Dead refs (scoping-technical-requirements, drafting-ba-stories) removed; discovery → researching-ba-problem-space; epic/story elaboration → eliciting-banking-brief; standalone-scoping referral → a plain "not outside the delivery pipeline" boundary. |

Version: 1.0.0 → 2.0.0 (breaking: schemas authored + required promotion + state vocabulary) + YAML pin.
Boundary run-plan.json required = [normalized_request, run_plan, scope_sheet, audit_id] == YAML (R3).
P3 follow-up (ledgered): flip the _sim CHECKS intake row to the new skill schema, then remove `intake`
from engine SKILL_SCHEMA_EXEMPT with pytest green.
