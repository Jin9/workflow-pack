---
name: red-teaming-implementation-plan
version: 0.2.0
description: Adversarially red-team an implementation plan or Tech-Lead design BEFORE any code is written, then issue a machine-readable PROCEED, REVISE, or BLOCK verdict with severity-ranked findings. Use when asked to red-team an implementation plan, adversarially review a plan before building, check whether a plan is safe to fan out to per-component work, or critique a Tech-Lead design before code. Runs as a critic separate from the plan's author (a generator is never its own critic), states a steelman of the plan first, applies reviewer-bias mitigation, and BLOCKs deterministically on unresolved P1 governance gaps. Do NOT use to review a code diff or pull request (use review-backend-code or review-frontend-code). Do NOT use for deep security threat-modeling (a dedicated threat-modeling workflow owns that). Do NOT use to author or revise the plan itself.
stage_type: review
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: enhanced, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 120
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Red-Teaming the Implementation Plan

## Purpose

Stress-test a Tech-Lead design / implementation plan against the requirements it
must satisfy and against the ways plans fail, **before** the expensive fan-out to
per-component implementation. Emit a single, severity-ranked, machine-readable
verdict that a workflow engine gates on. Read-only: this skill critiques a plan;
it never writes the plan, the code, or the fix.

## When to use this skill

- Use when: a plan / TL-design artifact has been produced and the next step would
  be to fan out into implementation, and you want an adversarial gate first.
- Use when: asked to "red-team", "adversarially review", or "stress-test" a plan,
  or to decide whether a plan is "safe to fan out".
- Do NOT use: to review emitted code, a diff, or a PR (that is
  `review-backend-code` / `review-frontend-code`).
- Do NOT use: for full security threat-modeling (a dedicated threat-modeling
  workflow owns that; this gate only checks the plan's security *handoffs*).
- Do NOT use: to write or revise the plan (the planning/design skill owns that).

## Input contract

`schemas/input.json` is **ENFORCED** — the engine validates the ASSEMBLED payload
against it before this stage runs (fail-closed, exactly like output validation);
it documents the POST-adapter payload assembled at stage `plan-review`. Required: hydrated `epics` and `stories` (plus the original
`story_files` refs) and `governance_gaps` from ba-research, `component_map` and
`api_contracts` from tl-design, and the engine-injected `idempotency_key`.
Optional engine-injected: `upstream_artifacts` (producer stage id → artifact path
relative to this stage's dir), `loop_back_feedback` (this skill's own prior
findings, when tl-design re-ran after a REVISE/BLOCK). The BA fields follow the
manifest dialect (`eliciting-banking-brief` `schemas/manifest.json` +
`epic-sidecar.json`/`story-sidecar.json`) — the canonical BA `output.json` is NOT
the stage handoff and must not be copied into this consumer schema.

Missing or unparseable required input is a **stage-input failure with no
artifact** — fail closed; there is no partial/no-verdict output shape.

**Full-plan review:** the five picked fields are a projection. Resolve
`upstream_artifacts["tl-design"]` (relative to the stage dir) and review the
COMPLETE TL artifact — ADRs, data model, infrastructure, connectivity,
observability, design smells, coverage gaps. If it is unavailable, limit
findings to the five delivered fields, record that limitation in `bias_checks`,
and lower `confidence` — never claim a lens was assessed when it was not.

**Provenance honesty:** the assembled payload carries no author identity. The
critic must still not be the plan's author (a generator is never its own
critic); record "author model unknown" in `bias_checks` and cap `confidence` at
0.75 until a future contract supplies trustworthy provenance.

**Example (validates against schemas/input.json):**

```json
{
  "epics": [{"id": "EPIC-AUTH", "title": "Customer authentication", "story_refs": [{"id": "STORY-AUTH-01", "slug": "otp-login", "file": "STORY-AUTH-01-otp-login.json"}]}],
  "story_files": [{"id": "STORY-AUTH-01", "epic_id": "EPIC-AUTH", "file": "STORY-AUTH-01-otp-login.json"}],
  "stories": [{"id": "STORY-AUTH-01", "epic_id": "EPIC-AUTH", "title": "OTP login", "acceptance_criteria": ["OTP expires in 5 minutes"]}],
  "governance_gaps": [],
  "component_map": {"components": [{"name": "auth-service", "responsibility": "OTP issuance and verification", "dependencies": ["otp-contract"]}]},
  "api_contracts": {"contracts": [{"contract_name": "otp-contract", "provider_component": "auth-service", "consumer_components": ["web-spa"]}]},
  "idempotency_key": "req-2026-07-12-shoppilot-001"
}
```

## Output contract

Validate against `schemas/output.json`: `verdict` (PROCEED|REVISE|BLOCK),
`steelman`, `findings[]`, `bias_checks[]` (all required, bias_checks non-empty),
`confidence` (0–1), and `audit_id`. Findings carry stable `RT-n` ids so a later
run can diff them; every finding carries `evidence`. An empty `findings` array
is legal only for a clean PROCEED.

`audit_id` is producer-stamped for the handoff trace:
`UUIDv5(HOUSE_NS, "plan-review:{idempotency_key}")` with
`HOUSE_NS = uuid5(NAMESPACE_URL, "https://squad-delivery/audit")` — independent
of optional inputs, and distinct from the per-attempt audit id the engine writes
to `events.jsonl`.

**Example (validates against schemas/output.json):**

```json
{
  "verdict": "REVISE",
  "steelman": "The plan cleanly separates OTP issuance from verification and reuses the existing session fabric, which minimizes new attack surface.",
  "findings": [
    {"id": "RT-1", "severity": "medium", "category": "contract", "claim": "otp-contract has no error vocabulary for lockout", "evidence": "api_contracts.contracts[0] defines success shapes only; STORY-AUTH-01 AC requires lockout after 5 failures", "recommendation": "Add lockout/throttle error responses to otp-contract before fan-out"}
  ],
  "bias_checks": ["steelman written before critique", "author model unknown — confidence capped at 0.75"],
  "confidence": 0.7,
  "audit_id": "3f7fb1f2-0f7e-5b0e-9f57-2f1e64a2b9c1"
}
```

## Procedure

1. **Governance preflight (deterministic).** Read `governance_gaps` first. Any
   gap with `severity: P1` or `blocks_tl_handoff: true` MUST produce a `high`
   finding with `category: governance` (preserving the upstream gap type,
   evidence, and required action) and the verdict MUST be **BLOCK** — a named
   human clears the gap; this skill never resolves or waives it. A `P2` gap
   produces at least a `medium` finding and **REVISE** unless the plan
   explicitly resolves it.
2. **Steelman first.** Before looking for flaws, write the strongest honest case
   FOR the plan (`steelman`). This counters reviewer self-preference and
   reject-by-default bias. Entry: a parsed plan. Exit: one paragraph.
3. **Sweep the attack lenses.** Walk every lens in
   `references/red-team-lenses.md` (requirements, architecture, contract, data,
   security-handoff, operability, cost, testability) over the FULL TL artifact
   when available (see Input contract). For each real weakness emit one finding
   `{id: RT-n, severity, category, claim, evidence, recommendation}`. Tie each
   finding to evidence in the plan or a missing requirement from the stories;
   do not flag style or speculation.
4. **Apply bias mitigation.** Re-read each finding and drop or downgrade any
   that are hallucinated, position/verbosity-driven, or unfalsifiable. Record
   which mitigations you applied in `bias_checks`.
5. **Decide the verdict** per the policy in `references/red-team-lenses.md`:
   **BLOCK** if any `high` finding sits on a required path (governance P1s land
   here by step 1); **REVISE** if there are `medium` findings but no blocking
   `high`; **PROCEED** if only `low` findings remain. Set `confidence` (0–1);
   lower it for thin evidence, and cap it at 0.75 while author provenance is
   unknown.
6. **Emit** the structured verdict (see Output contract). Stop. Routing is the
   engine's job, not this skill's.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| RTP-01 | required input missing / unparseable | NO artifact (stage-input failure) | engine failure policy — fail closed |
| RTP-02 | author provenance unknown (always, today) | verdict + `confidence` ≤ 0.75 | note in `bias_checks` |
| RTP-03 | full TL artifact unavailable via `upstream_artifacts` | verdict from the five delivered fields only | limitation recorded in `bias_checks`, lowered `confidence` |

## Constraints

- **Verdict routing (engine truth — do not re-document differently):** PROCEED
  releases the fan-out; REVISE and BLOCK both invoke the stage's single
  permitted loop_back to `tl-design` (findings threaded into the re-run); a
  non-proceed verdict after the cap aborts the run (HardFail). Named-human
  adjudication of a parked run is supervisory — it is not an artifact route
  this skill can target.
- A fully-autonomous PROCEED is impossible BY DESIGN for regulatory-scoped
  requests carrying P1 governance gaps (step 1). Never weaken this: no
  suppressing governance findings, no widening verdict routes, no bumping loop
  caps.
- Read-only on the plan: never edit, rewrite, or "fix" the artifact under
  review.
- Deterministic envelope: same `idempotency_key` + same inputs ⇒ same
  `audit_id`; findings keep stable `RT-n` ids across re-runs of the same plan.
- Severity honesty: severity ranks the risk to THIS delivery, not rhetorical
  strength; do not inflate to force a BLOCK or deflate to dodge one.

## References

- `references/red-team-lenses.md` — the eight attack lenses, the verdict
  policy, and reviewer-bias mitigations (steelman, position-bias, verbosity).
