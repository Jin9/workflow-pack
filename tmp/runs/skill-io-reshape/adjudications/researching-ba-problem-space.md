# Adjudication — researching-ba-problem-space (S1a s1-discovery)

Source: codex/researching-ba-problem-space.md · exit=0 (succeeded on quota-window retry). Verified:
input.json models phantom initiative/context/tier vs the real assembled payload (raw_request + requester
from workflow input, normalized_request picked from intake, injected idempotency_key); ba-research picks
s1-discovery.regulatory_regimes + handoff_to_intake but required_fields guarantees neither (2 baseline
findings); corpus discovery.json: recommendation proceed, NO handoff, regulatory_regimes = list[str],
risk_types exactly {value, usability, feasibility, viability}, de_risk on all 4 → F3/F8 tightenings
corpus-safe; boundary handoff_to_intake is an untyped bare object; corpus discovery-input.json still
carries the phantom shape; no corpus file records a requester.

| F# | Sev | Verdict | Rationale / modified form |
|----|-----|---------|---------------------------|
| F1 | blocker | **ACCEPT** | input.json ← stub (raw_request/requester/normalized_request/idempotency_key + injected optionals; ADVISORY marker). Corpus discovery-input.json rewritten to the post-adapter truth using ONLY run-recorded values: raw_request ← the fixture's own initiative text, normalized_request ← the run's S0 run-plan, idempotency_key kept; requester ← "shoppilot-demo" (self-evidently synthetic slug — the sim never recorded one; no invented human). 1.0.0 → 2.0.0 + pin. |
| F2 | blocker | **ACCEPT-MODIFIED** | Failure shapes get the HOUSE failure_state {failure_code (RB-01\|RB-02\|RB-03), message, remediation} (+ optional blockers[], open_questions[]) — NOT Codex's {code, summary} dialect, for fleet consistency with eliciting/planning. Four required top-level fields always emitted; no handoff on blocked outcomes. |
| F3 | blocker | **ACCEPT** | regulatory_regimes promoted to skill+boundary+YAML required ([] = "none identified"); handoff_to_intake stays optional (proceed replay omits it) + OPTIONAL_PICK_WHITELIST ("s1-discovery","handoff_to_intake") with the consumer default documented (absent ⇒ no seeding — eliciting's discovery-absent byte-identity untouched). Clears 2 baseline findings. |
| F4 | major | **ACCEPT** (local scope) | Boundary handoff_to_intake fully typed (mirrors skill schema); recommendation enum already exact; problem_framing/regimes already string-typed in both. The scoping-ba-intake output.json half lands in the scoping chunk (schemas authored there) — noted as forward-dependency. |
| F5 | major | **ACCEPT** | Positioning corrected everywhere: discovery runs AFTER S0 normalization, BEFORE brief elaboration; always-present normalized_request never triggers RB-01; backward-routing-to-intake instructions removed. |
| F6 | major | **ACCEPT** | Handoff guard gains top-level `recommendation: {const: proceed}` in the existing if-branch — a needs-work/do-not-build artifact can no longer carry a proceed handoff. Handoff NOT required when proceed (replay behavior preserved). |
| F7 | major | **ACCEPT** | Invented "field-for-field compatible" flattening/merge-recipe text replaced with the real transform: picked fields nest under `discovery` (NESTED_HANDOFF), handoff stays at discovery.handoff_to_intake.*; opportunities/assumptions dropped from the claimed transfer (YAML never picks them). |
| F8 | major | **ACCEPT** | proceed branch: assumptions minItems 4 + four draft-07 `contains` (one per risk_type) + de_risk required per item; needs-work/do-not-build allow partial coverage. Corpus (4/4 + de_risk) validates. |
| F9 | major | **REJECT (corpus rewrite) / ACCEPT (doc)** | Stamping the house-formula audit_id into corpus discovery.json + INDEX + regenerating viewers is a PROVENANCE REWRITE — the standing doctrine grandfathers corpus aid() ids and forbids falsifying recorded history (same ruling as ux F8, qa-plan F4). ACCEPTED half: document UUIDv5(HOUSE_NS, "s1-discovery:{idempotency_key}") as the LIVE derivation, independent of optional inputs, distinct from the engine attempt id. |
| F10 | major | **ACCEPT** | Vocabulary literals fixed everywhere: proceed-to-intake → proceed; needs-discovery-work → needs-work; do-not-build retained. |

Version: 1.0.0 → 2.0.0 (breaking: required promotion + input contract rewrite) + YAML pin.
Boundary required += regulatory_regimes == YAML required_fields (R3 lockstep).
