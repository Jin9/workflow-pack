# Adjudication — red-teaming-implementation-plan (S2.5 plan-review)

Source: codex/red-teaming-implementation-plan.md · exit=0. Verified: input.json requires a phantom
`plan` envelope (+ ba_brief/author_model/tier) vs the real assembled payload (epics/story_files/stories/
governance_gaps/component_map/api_contracts + injected); corpus plan-review.json has bias_checks (4) and
evidence on all 4 findings → F6 tightening corpus-safe; corpus INDEX governance_gaps == [] → F4 preflight
corpus-consistent AND codifies the live-proven run-77777777 BLOCK; policies.py routes PROCEED→OK,
REVISE→REWORK, BLOCK→REWORK (loop_back, cap 1, then abort), reroute→REWORK, hard-fail→FAIL — the
SKILL.md "BLOCK to a human" and boundary "BLOCK aborts"+"Strict envelope (AP:false)" (actual AP:true)
claims are all false; RTP-01 "needs-input → human-queue" contradicts the loop_back failure_policy;
pr-design-review + reviewing-software-security do not exist in this pack.

GATE-SAFETY NOTE: F4 STRENGTHENS the adversarial gate (deterministic P1/blocks_tl_handoff → BLOCK);
nothing here widens verdict routes, bumps max_loops, or relaxes the by-design BLOCK — the never-do
list is untouched.

| F# | Sev | Verdict | Rationale / modified form |
|----|-----|---------|---------------------------|
| F1 | blocker | **ACCEPT** | input.json ← stub (post-adapter truth: hydrated plural + governance_gaps + tl fields + injected; ADVISORY marker; AP:false). Phantom plan/ba_brief/author_model/tier retired. brk → 0.2.0 + pin. |
| F2 | major | **ACCEPT** | Stub already types story_files/epics/stories against the eliciting manifest/sidecar schemas (authored in the eliciting chunk); note added that canonical output.json is NOT the stage handoff. |
| F3 | major | **ACCEPT** | Procedure: resolve upstream_artifacts["tl-design"] relative to the stage dir and review the FULL TL artifact (ADRs/data model/infra/observability); if unavailable, limit claims to the five delivered fields, record the limitation in bias_checks, lower confidence — never claim lenses that were not assessed. |
| F4 | major | **ACCEPT** | Deterministic governance preflight: any P1 or blocks_tl_handoff:true gap ⇒ high finding + BLOCK; P2 ⇒ ≥medium + REVISE unless explicitly resolved; `governance` added to category enum (additive); upstream gap type/evidence preserved in the finding. Strengthens the gate; corpus (no gaps, PROCEED) consistent. |
| F5 | major | **ACCEPT** | House audit_id formula documented in Output contract + audit_id.description: UUIDv5(HOUSE_NS, "plan-review:{idempotency_key}"), producer-stamped, independent of optional inputs, distinct from the events.jsonl attempt id. Corpus aid grandfathered. |
| F6 | major | **ACCEPT** | Skill-schema tightening only (boundary/YAML untouched — no consumer picks these): root required += bias_checks (minItems 1); finding required += evidence; minLength 1 on steelman/claim/evidence/recommendation. Corpus already satisfies. findings:[] stays legal for a clean PROCEED. |
| F7 | major | **ACCEPT** | RTP-01 "needs-input → human-queue / no verdict" removed: missing/unparseable required input = stage-input failure with NO artifact (fail-closed); only defensible reviews emit the envelope. No human-queue claim the policy does not provide. |
| F8 | major | **ACCEPT** | Docs rewritten to the policies.py truth: PROCEED releases; REVISE and BLOCK BOTH loop_back to tl-design (max_loops 1, findings threaded); non-proceed after cap → abort (HardFail); reroute → loop_back; hard-fail → fail. Boundary desc drops "Strict envelope" (AP is true) and "BLOCK aborts". Named-human adjudication is supervisory, not an artifact route. |
| F9 | major | **ACCEPT** | Phantom author_model gone (F1); provenance honesty: assembled payload carries no author identity → bias_checks MUST record "author model unknown" and confidence is capped at 0.75 until a future contract supplies trustworthy provenance (corpus value 0.75 — consistent). |
| F10 | minor | **ACCEPT** | Dead refs: pr-design-review → review-backend-code / review-frontend-code (bare names); reviewing-software-security → generic "a dedicated threat-modeling workflow". |

Version: 0.1.0 → 0.2.0 (breaking input rewrite + strict-schema tightening on 0.x) + YAML pin lockstep.
Boundary: description resync only (required stays [verdict, findings, audit_id] == YAML — R3 clean).
