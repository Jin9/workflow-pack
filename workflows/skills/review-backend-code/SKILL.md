---
name: review-backend-code
version: 2.0.0
description: Adversarially verify Go backend code emitted by a Generate stage against the approved design and the 22 banking-grade review rules, resolve and hash-verify the reviewed bytes from the producer manifest, check every producer claim (idempotency, audit, compensation, patterns) against the real code, then issue a machine-readable verdict (approve, loop_back, or human-queue) with a provenance audit_id. Use when reviewing the output of implement-backend-feature before the test gates. Use when verifying that a Generate stage's claims are actually implemented in the emitted code. Use when scoring a Go feature for banking-grade readiness. Do NOT use for frontend code (use review-frontend-code). Do NOT use for adversarial or chaos validation of a running system (use validating-banking-implementation). Do NOT use for automated scanning gates (the SAST and AppSec pipeline gates own those). Do NOT use for greenfield architecture review.
stage_type: review
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: detailed, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 90
max_retries_recommended: 2
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Review Backend Code

## Purpose

Verify that Generate-stage output for one Go backend feature actually satisfies
the approved design and the banking-grade rule set. Trust-but-verify: the
producer's claims are checked against the resolved code bytes, never taken on
faith. The reviewer is a critic separate from the generator; it emits a verdict
the engine gates on and never edits the code.

## When to use this skill

- Use when: `implement-backend-feature` has produced its manifest and the next
  step is the S4 review gate (the reviewed feature then feeds `qa-plan`).
- Use when: asked to verify a Generate stage's claims (idempotency, audit
  events, compensation, outbox patterns) against the emitted Go code.
- Use when: a Generate stage emits `uncertainty_flags` that need triage before
  the workflow proceeds.
- Do NOT use: for frontend code (`review-frontend-code`), adversarial/chaos
  validation of a running system (`validating-banking-implementation`),
  automated scan gates (the SAST / AppSec pipeline skills), architecture
  review, or writing remediation code (this skill suggests fix shape only).

## Input contract

`schemas/input.json` is **ENFORCED** — the engine validates the ASSEMBLED payload
against it before this stage runs (fail-closed, exactly like output validation);
it documents the POST-adapter payload assembled at stage `backend-review`. Required: `files_generated` and `tests_generated` (the
producer manifest, picked from backend-implement), `api_contracts` (design
truth, picked from tl-design), and the engine-injected `idempotency_key`.
Optional engine-injected: `upstream_artifacts`, `loop_back_feedback`.

**Resolving the reviewed bytes (mandatory):** resolve
`upstream_artifacts["backend-implement"]` relative to the stage dir and load the
full validated producer artifact — that artifact is the claim truth
(`idempotency_strategy`, `audit_events_emitted`, compensation, pattern
choices). Its directory is the producer root: resolve every manifest `path`
strictly beneath that root, verify each `content_hash` against the real bytes,
and only then read the source. A missing path, traversal attempt, unreadable
file, or hash mismatch is `human-queue` / `input_incomplete` — never an
inferred verdict.

The engine `idempotency_key` identifies this review attempt (and derives
`audit_id`); it is NOT an application idempotency key and must never be expected
in the generated code. Application idempotency is reviewed from
`api_contracts.contracts[].idempotency_rules` and the producer's
`runtime_idempotency` / `idempotency_strategy`.

**Example (validates against schemas/input.json):**

```json
{
  "files_generated": [{"path": "services/checkout/app/checkout/service.go", "content_hash": "9b12f1e6c56c1e00c4f4f4a1a5c9b8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1", "lines_added": 214}],
  "tests_generated": [{"path": "services/checkout/app/checkout/service_test.go", "content_hash": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b", "coverage_pct": 0.97}],
  "api_contracts": {"contracts": [{"contract_name": "checkout-confirm", "provider_component": "checkout-service", "idempotency_rules": "confirm dedupes on the client idempotency key"}]},
  "idempotency_key": "req-2026-07-12-shoppilot-001"
}
```

## Output contract

Validate against `schemas/output.json`: `verdict` (approve|loop_back|human-queue),
`loop_back_target_stage` (`backend-implement` or null — a consistency record;
the YAML failure_policy is authoritative), `findings[]` (each with required
`confidence`; emitted severity is post-confidence-adjustment; Low confidence
marks its evidence `[needs verification]`), `claim_checks[]` (one typed entry
per producer claim: `{claim_ref, status, evidence}`; unverified ⇒ `finding_ref`
required), `audit_metadata` (`rules_evaluated` exactly 22,
`production_files_scanned` + `test_files_scanned` ≥ 1, positive
`lines_scanned`), `uncertainty_flags`, and `audit_id`.

The schema enforces the verdict matrix: a P1 finding anywhere forces
`human-queue`; `approve` requires no P1/P2, a null target, and every claim check
verified or not-applicable; `loop_back` requires the executable target, no P1,
and at least one P2 or unverified claim. Design ambiguity routes to
`human-queue` (this stage cannot loop to tl-design). Every P1/P2/P3 finding is
always emitted — there is no severity floor; filtering is presentation-only.

`audit_id` (live): `UUIDv5(HOUSE_NS, "backend-review:{idempotency_key}")`,
`HOUSE_NS = uuid5(NAMESPACE_URL, "https://squad-delivery/audit")` — distinct
from the engine's per-attempt audit id in `events.jsonl`.

**Example (validates against schemas/output.json):**

```json
{
  "verdict": "approve",
  "loop_back_target_stage": null,
  "findings": [],
  "claim_checks": [
    {"claim_ref": "backend-artifacts.json#/idempotency_strategy", "claim_type": "idempotency", "status": "verified", "evidence": "confirm/capture/reserve dedupe on the client idempotency key as declared"}
  ],
  "audit_metadata": {"rules_evaluated": 22, "production_files_scanned": 45, "test_files_scanned": 24, "lines_scanned": 3463},
  "uncertainty_flags": [],
  "audit_id": "f6b6f262-ae03-59dd-9166-d9b3a1b81e94"
}
```

## Procedure

1. **Resolve and verify the input** (Input contract): producer artifact via
   `upstream_artifacts`, manifest paths beneath the producer root, content
   hashes. Any failure ⇒ `human-queue` / `input_incomplete` — never proceed on
   partial bytes.
2. **Read the design truth.** From `api_contracts`: contracts, idempotency
   rules, error vocabularies. From the resolved producer artifact: what
   Generate *said* it did.
3. **Rule sweep — production code.** Walk every manifest production file
   against `references/review-rubric.md`; every violation is one finding
   `{severity, confidence, category, rule_violated, file, line, evidence,
   fix_shape}`.
4. **Discipline sweep — tests.** Walk every manifest test file against the test
   items in `references/review-checklist.md` (table-driven, no network, no
   secrets, no shared state, plausible coverage claims).
5. **Claims-vs-reality.** One `claim_checks[]` entry per claim, `claim_ref`
   pointing at where the claim was made. Prove the code exists:
   - `idempotency_strategy` claims a key → find the key parameter at the
     boundary, the dedup store call, the replay branch. Missing any = `P1`.
   - Each `audit_events_emitted` entry → find the emit call. Missing = `P1`.
   - Each compensation trigger → find the call site of the irreversible
     action. Missing = `P1`.
   - Pattern choices → verify the pattern is actually in the code.
     Mismatch = `P2`.
   An unverified claim gets a `claims_vs_reality` finding and carries its
   `finding_ref` — loop-back feedback must be actionable. Never skip this
   step; it is the unique reason this skill exists.
6. **Adjust for confidence** (`references/severity-guide.md`), then **decide
   the verdict** per the matrix and emit. Routing is the engine's job: approve
   releases; loop_back re-runs backend-implement with findings threaded (max 2
   loops, then human-queue).

## Failure modes

| Condition | Output | Escalation |
|---|---|---|
| Producer artifact/manifest unresolvable, path traversal, unreadable file, hash mismatch | NO clean verdict — `human-queue` / `input_incomplete` | named human |
| P1 finding (security, idempotency, audit, compensation, data correctness) | verdict `human-queue`, null target | named human |
| P2 findings or unverified claims, no P1 | verdict `loop_back` → backend-implement | cap 2, then human-queue |
| Design ambiguity (the design itself is wrong or unclear) | `uncertainty_flag` kind `design_ambiguity`, verdict `human-queue`, null target | this stage cannot loop to tl-design |
| Suspected finding without a citable file:line | emit at Low confidence with `[needs verification]` in evidence | never publish at full confidence |

## Constraints

- Read-only on the code: DO NOT emit code or remediation patches — suggest fix
  shape only (function signature + invariants).
- No severity floor, ever: every P1/P2/P3 is emitted; the engine forwards the
  findings to regeneration, so suppression would create a blind remediation
  loop. Presentation layers may hide P3 advisories without changing the
  artifact.
- DO NOT approve when any claim check is unverified, even with no other
  finding. DO NOT silently downgrade a finding to reach approve — the verdict
  is a function of findings, never the reverse.
- DO NOT fabricate file:line references, standards identifiers, or CWE
  numbers — withhold instead.
- DO NOT widen scope beyond the manifest files — adjacent issues are an
  addendum, not blocking findings.
- DO NOT process real PII in evidence snippets — ask for redaction first.
- Deterministic envelope: same inputs + same `idempotency_key` ⇒ same
  `audit_id`; no clock or randomness in the artifact.

## References

| Need | File |
|------|------|
| The 22 review rules re-cast as adversarial scan questions | `references/review-rubric.md` |
| P1 / P2 / P3 classification + banking-grade auto-routing matrix | `references/severity-guide.md` |
| Deterministic YES/NO scan list (steps 3 + 4) | `references/review-checklist.md` |
| Design rationale | `RATIONALE.md` |
| Harness cases | `tests/harness-guide.md`, `tests/cases/` |
