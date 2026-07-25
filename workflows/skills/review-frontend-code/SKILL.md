---
name: review-frontend-code
version: 2.0.0
description: Adversarially verify React/TypeScript code emitted by a Generate stage against the approved UI design, the UX evidence pack, and the 26 banking-grade frontend rules, resolve and hash-verify the reviewed bytes from the producer manifest, check every producer claim (a11y compliance, security review, PII handling, state ownership) against the real code, then issue a machine-readable verdict (approve, loop_back, or human-queue) with a provenance audit_id. Use when reviewing the output of implement-frontend-feature before the test gates. Use when verifying that a Generate stage's claims are actually implemented in the emitted code. Use when scoring a React/TS feature for banking-grade readiness. Do NOT use for backend code (use review-backend-code). Do NOT use for adversarial validation of a running system (use validating-banking-implementation). Do NOT use for automated scan gates (the SAST and AppSec pipeline skills own those). Do NOT use for visual regression or Web Vitals optimization.
stage_type: review
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: detailed, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 90
max_retries_recommended: 2
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Review Frontend Code

## Purpose

Verify that Generate-stage output for one React/TypeScript feature actually
satisfies the approved UI design, the UX evidence pack, and the banking-grade
frontend rule set. Trust-but-verify: the producer's claims (a11y compliance,
security review, PII handling, state ownership) are checked against the
resolved code bytes, never taken on faith. Read-only — emits no code, no
remediation patches.

## When to use this skill

- Use when: `implement-frontend-feature` has produced its manifest and the next
  step is the S4 review gate.
- Use when: asked to verify a Generate stage's claims against the emitted
  React/TS code.
- Use when: the implementation emits `uncertainty_flags` of kind `token_gap` /
  `bundle_overrun` / `convention_conflict` that need triage.
- Do NOT use: for backend code (`review-backend-code`), adversarial validation
  of a running system (`validating-banking-implementation`), automated scan
  gates (the SAST / AppSec pipeline skills), visual regression (a separate
  visual-diff stage), Web Vitals optimization, or writing remediation code
  (fix shape only).

## Input contract

`schemas/input.json` is **ENFORCED** — the engine validates the ASSEMBLED payload
against it before this stage runs (fail-closed, exactly like output validation);
it documents the POST-adapter payload assembled at stage `frontend-review`. Required: `files_generated` and `tests_generated` (the
producer manifest, picked from frontend-implement), `api_contracts` (design
truth, picked from tl-design), the UX evidence picks from ux-intake
(`pack_dir`, `tokens_path`, `component_inventory_path`,
`screen_states_path`, `form_validation_path`, `responsive_spec_path`,
`accessibility_spec_path` — the specs the implementation is reviewed against),
and the engine-injected `idempotency_key`. Optional engine-injected:
`upstream_artifacts`, `loop_back_feedback`.

**Resolving the reviewed bytes (mandatory):** resolve
`upstream_artifacts["frontend-implement"]` relative to the stage dir and load
the full validated producer artifact — that artifact is the claim truth. Read
each manifest file at
`dirname(artifact)/frontend_worktree_root/<manifest path>` and verify its
`content_hash`. A missing file, missing claim, unreadable UX evidence, or hash
mismatch is `human-queue` / `input_incomplete` — never an inferred approval.

**Example (validates against schemas/input.json):**

```json
{
  "files_generated": [{"path": "src/features/checkout/CheckoutForm.tsx", "content_hash": "9b12f1e6c56c1e00c4f4f4a1a5c9b8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1", "size_bytes": 6212, "lines_added": 188}],
  "tests_generated": [{"path": "src/features/checkout/CheckoutForm.test.tsx", "content_hash": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b", "test_type": "component"}],
  "api_contracts": {"contracts": [{"contract_name": "checkout-confirm", "provider_component": "checkout-service", "consumer_components": ["web-spa"]}]},
  "pack_dir": "ux-design-1a2b3c4d",
  "tokens_path": "ux-design-1a2b3c4d/tokens/design-tokens.json",
  "component_inventory_path": "ux-design-1a2b3c4d/specs/component-inventory.md",
  "screen_states_path": "ux-design-1a2b3c4d/specs/screen-states.md",
  "form_validation_path": "ux-design-1a2b3c4d/specs/form-validation.md",
  "responsive_spec_path": "ux-design-1a2b3c4d/specs/responsive.md",
  "accessibility_spec_path": "ux-design-1a2b3c4d/specs/accessibility.md",
  "idempotency_key": "req-2026-07-12-shoppilot-001"
}
```

## Output contract

Validate against `schemas/output.json`: `verdict` (approve|loop_back|human-queue),
`loop_back_target_stage` (`frontend-implement` or null — a consistency record;
the YAML failure_policy is authoritative), `findings[]` (each with required
`confidence`; Low confidence marks its evidence `[needs verification]`),
`claim_checks[]` (`{claim_ref, status, evidence}`; unverified ⇒ `finding_ref`),
`a11y_verdict` and `security_verdict` (separately routable blocker surfaces;
`focus_management_evident` / `csrf_protections_verified` may be **null = not
applicable** — never report `true` for an unperformed check), `audit_metadata`
(`rules_evaluated` exactly 26 = 12 non-negotiables + 9 augmentations + 5
contract items; `production_files_scanned` + `test_files_scanned` ≥ 1; positive
`lines_scanned`; `claims_checked` == `len(claim_checks)` — derived, never
independent), `uncertainty_flags`, and `audit_id`.

The schema enforces the verdict matrix: a P1 finding anywhere forces
`human-queue`; `approve` requires no P1/P2, a null target, every claim check
verified/not-applicable; `loop_back` requires the executable target
(`frontend-implement` — the ONLY executable loop edge), no P1, and a P2 or
unverified claim. `design_ambiguity`, `bundle_overrun`, and `token_gap` route
to `human-queue` with a null target — this stage cannot loop to tl-design or
the UX stage. No severity floor exists; every finding is emitted.

`audit_id` (live): `UUIDv5(HOUSE_NS, "frontend-review:{idempotency_key}")`,
`HOUSE_NS = uuid5(NAMESPACE_URL, "https://squad-delivery/audit")` — distinct
from the engine's per-attempt audit id in `events.jsonl`.

**Example (validates against schemas/output.json):**

```json
{
  "verdict": "approve",
  "loop_back_target_stage": null,
  "findings": [],
  "claim_checks": [
    {"claim_ref": "security_verdict.token_storage_verified", "claim_type": "security", "status": "verified", "evidence": "auth token in httpOnly cookie; no localStorage/sessionStorage writes found"}
  ],
  "a11y_verdict": {"wcag_level_verified": "AA", "axe_run_evidence_present": true, "role_label_queries_present": true, "focus_management_evident": true},
  "security_verdict": {"xss_mitigations_verified": true, "token_storage_verified": true, "pii_helpers_verified": true, "csrf_protections_verified": null, "dependency_additions_detected": []},
  "audit_metadata": {"rules_evaluated": 26, "production_files_scanned": 37, "test_files_scanned": 3, "lines_scanned": 2316, "claims_checked": 1},
  "uncertainty_flags": [],
  "audit_id": "0d0b3a54-93a4-5d38-8f6b-52c86e1f3d9a"
}
```

## Procedure

1. **Resolve and verify the input** (Input contract): producer artifact via
   `upstream_artifacts`, manifest bytes under `frontend_worktree_root`, content
   hashes, UX evidence files under `pack_dir`. Any failure ⇒ `human-queue` /
   `input_incomplete`.
2. **Read the design truth.** From tl-design `api_contracts` and the UX pack:
   component inventory, screen states, form validation, responsive and
   accessibility specs, design tokens, declared PII fields with treatments.
3. **Rule sweep — production code.** Walk every manifest production file
   against `references/review-rubric.md` (F1–F12 + A1–A9 + C1–C5). Every
   violation = one finding.
4. **Discipline sweep — tests.** Walk every manifest test file against
   `references/review-checklist.md` (query by role/label, MSW for network,
   `userEvent` not `fireEvent`, no real network/secrets, no sleep).
5. **Claims-vs-reality.** One `claim_checks[]` entry per claim. Prove or
   refute:
   - Every `a11y_compliance` boolean `true` → find the supporting code (focus
     management hook, axe-clean test, role-based queries). False claim = `P1`.
   - Every `security_review.xss_surfaces[]` entry → the matching sanitizer
     call AND its `// SAFE:` comment. Missing = `P1`.
   - `token_storage_strategy` matches the code (httpOnly-cookie claim → no
     `localStorage.setItem("auth*")`). Mismatch = `P1`.
   - Every declared PII field rendered through its treatment helper.
     Missing = `P1`.
   - Every audit/analytics event → find the emit call. Missing = `P1`.
   - `state_ownership` map covers every design-named state piece.
     Missing = `P2`. Pillar consistency (a Primitive never fetches).
     Mismatch = `P2`.
   An unverified claim gets a `claims_vs_reality` finding and carries its
   `finding_ref`. Never skip this step.
6. **Adjust for confidence** (`references/severity-guide.md`), then **decide
   the verdict** per the matrix and emit. Routing is the engine's job: approve
   releases; loop_back re-runs frontend-implement with findings threaded
   (max 2 loops, then human-queue).

## Failure modes

| Condition | Output | Escalation |
|---|---|---|
| Producer artifact/manifest/UX evidence unresolvable or hash mismatch | NO clean verdict — `human-queue` / `input_incomplete` | named human |
| P1 finding (a11y blocker, XSS, token storage, PII leak, CSRF gap, missing mutation compensation) | verdict `human-queue`, null target | named human |
| P2 findings or unverified claims, no P1 | verdict `loop_back` → frontend-implement | cap 2, then human-queue |
| `design_ambiguity` / `bundle_overrun` / `token_gap` | `uncertainty_flag` + verdict `human-queue`, null target | this stage cannot loop to design/UX |
| Suspected finding without a citable file:line | emit at Low confidence with `[needs verification]` in evidence | never publish at full confidence |

## Constraints

- Read-only: DO NOT emit code, remediation patches, or styled fix snippets —
  fix shape only (component signature, prop type, helper name).
- No severity floor: every P1/P2/P3 is emitted; suppression creates a blind
  remediation loop.
- DO NOT approve with any unverified claim check; DO NOT silently downgrade a
  finding to reach approve.
- DO NOT fabricate file:line references, ARIA attributes, CWE numbers, or
  library APIs — withhold instead.
- DO NOT accept an "axe clean" claim without a CI axe assertion or a dev
  `@axe-core/react` install in the inspected file set.
- DO NOT downgrade a11y findings — WCAG AA is regulatory, not negotiable.
- DO NOT widen scope beyond the manifest — adjacent observations are
  `uncertainty_flags` of kind `out_of_scope_observation`, not findings.
- DO NOT process real PII in evidence snippets — redact and flag
  `needs_human_judgment`.
- Deterministic envelope: same inputs + same `idempotency_key` ⇒ same
  `audit_id`; no clock, no randomness, no inferred durations in the artifact.

## References

| Need | File |
|------|------|
| The 26 rules (F1–F12 + A1–A9 + C1–C5) as adversarial scan questions | `references/review-rubric.md` |
| P1 / P2 / P3 classification + auto-routing matrix (a11y, XSS, token, PII, CSRF) | `references/review-checklist.md` and `references/severity-guide.md` |
| Deterministic YES/NO scan list (steps 3 + 4) | `references/review-checklist.md` |
| Extraction lineage, augmentations, drops, deviations | `RATIONALE.md` (human audit only — do not load into LLM context) |
| Harness cases | `tests/harness-guide.md`, `tests/cases/` |
