---
name: review-frontend-code
description: >
  Adversarially verify React/TypeScript code emitted by a Generate stage
  against the approved UI design and the 12 banking-grade frontend
  non-negotiables + 9 v2 augmentations, then issue a machine-readable
  verdict (approve, loop_back, or human-queue). Use when reviewing the
  output of implement-frontend-feature before the build stage. Use when
  verifying that a Generate stage's claims (a11y_compliance,
  security_review, pii_fields_handled) are actually implemented in the
  emitted code. Use when scoring a React/TS feature for banking-grade
  readiness before a Validate stage. Do NOT use for full defensive
  security review across infra (use reviewing-software-security).
  Do NOT use for visual regression review (use a visual-diff stage skill).
  Do NOT use for backend code (use review-backend-code). Do NOT use for
  Lighthouse / Web Vitals optimization (use analyze-frontend-performance).
  Do NOT use for greenfield architecture review.
compatibility: [claude-code, codex, opencode]
metadata:
  version: 1.0.0
  stage_type: review
  status: ready-for-phase-6
  input_schema: schemas/input.json
  output_schema: schemas/output.json
  banking_grade: {idempotent: true, reversible: n/a, audit_level: detailed}
  expected_duration_p95_seconds: 90
  max_retries_recommended: 2
---

# Review Frontend Code

## Purpose

Verify that previously-generated code for one React/TypeScript feature actually
satisfies the approved UI design and the banking-grade frontend rule set.
Trust-but-verify the implementation's claims (a11y compliance, security
review, PII handling, state ownership, bundle impact, analytics events),
scan the emitted code against the 12 non-negotiables and 9 v2 augmentations,
and issue a machine-readable verdict. A caller MAY map the verdict to its own
routing. Read-only — emits no code, no remediation patches.

## When to use this skill

- Use when: generated React/TypeScript code needs verification before a
  build/validation step.
- Use when: a review step selects this skill for a React / TypeScript target.
- Use when: the implementation emits `uncertainty_flags` of kind `token_gap` /
  `bundle_overrun` / `convention_conflict` that need triage.
- Do NOT use when: the task is a full security audit across infra / gateways
  / K8s — defer to `reviewing-software-security`.
- Do NOT use when: the task is visual regression — a separate visual-diff
  stage owns pixel comparison.
- Do NOT use when: the target is backend (use `review-backend-code`).
- Do NOT use when: the task is Web Vitals / Lighthouse optimization —
  defer to `analyze-frontend-performance`.
- Do NOT use when: the task is writing remediation code — this skill
  suggests fix shape only; emission belongs to a code-generation step.

## Input

Input MUST validate against `schemas/input.json`. Required fields:

| Field | Type | Notes |
|-------|------|-------|
| `design_document` | string or object | Same design the implementation consumed. |
| `target_feature_path` | string | Same path the implementation targeted. |
| `implement_stage_output` | object | Verbatim output of `implement-frontend-feature` (per its `schemas/output.json`). |
| `code_under_review` | array of `{path, content, component_pillar}` | Production files emitted by Generate, with the declared pillar. |
| `tests_under_review` | array of `{path, content, test_type}` | Companion tests emitted by Generate. |
| `idempotency_key` | string (UUID v4) | Same key. Same input → same verdict bytes. |

Optional: `convention_overrides`, `severity_floor` (default `P3`).

## Procedure

Run all 8 steps in order. Step 6 (claims-vs-reality) is non-skippable —
it is the unique reason this skill exists.

1. **Pre-flight — input completeness.** Verify every required field;
   `code_under_review` non-empty. Missing → single finding `P1 /
   input_incomplete`, verdict `human-queue`.
2. **Read the design.** Extract: L1 intent, L2 component tree + state
   ownership + rendering model, L3 a11y contract + token-storage + error
   states, L4 file sketch, declared PII fields with treatments. These are
   the *truth* against which claims are checked.
3. **Read the Generate claims.** From `implement_stage_output` capture:
   `a11y_compliance`, `security_review`, `state_ownership`,
   `bundle_impact_estimate_kb`, `compensating_actions`,
   `audit_events_emitted`, `pillar_choices`, `uncertainty_flags`. These
   are *what Generate said it did*.
4. **Scan the code — rule sweep.** Walk every file in `code_under_review`
   against `references/review-rubric.md` (the 12 non-negotiables F1–F12 +
   9 augmentations A1–A9 re-cast as adversarial scan questions). Every
   violation = one finding.
5. **Scan the tests — discipline sweep.** Walk every file in
   `tests_under_review` against the test items in
   `references/review-checklist.md` (query by role/label, MSW for network,
   `userEvent` not `fireEvent`, no real network/secrets, no sleep).
6. **Claims-vs-reality.** For each Generate claim, prove or refute:
   - Every `a11y_compliance` boolean = `true` → find the supporting code
     (focus management hook, axe-clean test, role-based queries). False
     claim = `P1` finding.
   - Every `security_review.xss_surfaces[]` entry → find the matching
     `DOMPurify` call AND the `// SAFE:` comment. Missing = `P1`.
   - `security_review.token_storage_strategy` matches the code (e.g.,
     `httpOnly-cookie` claim → no `localStorage.setItem("auth*"...)`).
     Mismatch = `P1`.
   - Every `security_review.pii_fields_handled[].field` rendered through
     its declared treatment helper. Missing helper = `P1`.
   - Every `audit_events_emitted` entry → find the emit call (analytics
     SDK or repo equivalent). Missing = `P1`.
   - Every `compensating_actions[].trigger` → find the optimistic-update
     rollback or undo affordance. Missing = `P1`.
   - `state_ownership` map → every state piece named in the design
     appears in the map. Missing entry = `P2`.
   - `pillar_choices` consistency → a `Primitive` file does not import
     from a fetching layer; a leaf does not fetch. Mismatch = `P2`.
   - `bundle_impact_estimate_kb` plausibility → estimate vs sum of
     emitted file sizes (rough). Implausible = `P3` note.
7. **Severity, verdict, emit.** Apply `references/severity-guide.md` to
   classify every finding (P1 / P2 / P3). Compute verdict per the
   verdict matrix in that file.
8. **Emit.** Produce a payload conforming to `schemas/output.json`.
   Include `claims_verified` AND `claims_unverified` — both arrays are
   populated, neither is left empty unless truly so.

## Output Contract

Output MUST validate against `schemas/output.json`. Structured fields:

| Field | Type | Purpose |
|-------|------|---------|
| `verdict` | enum `approve | loop_back | human-queue` | Machine-readable outcome. `approve` = clean; `loop_back` = request revision by the code-generation step; `human-queue` = escalate to a human. A caller/orchestrator MAY map these to its own routing. |
| `loop_back_target_stage` | enum `design | implement | null` | Which upstream role to revise (`design` = the design author, `implement` = the code-generation step). Required when verdict is `loop_back`; null otherwise. |
| `findings` | array of `{severity, confidence, category, rule_violated, file, line, evidence, fix_shape, standards_ref}` | One entry per gap. Empty = clean. |
| `claims_verified` | array of strings | Generate claims the code substantiates. |
| `claims_unverified` | array of strings | Implementation claims the code does NOT substantiate. Non-empty forces `loop_back` or `human-queue`. |
| `a11y_verdict` | nested object `{wcag_level_verified, axe_run_evidence_present, role_label_queries_present, focus_management_evident}` | A11y is a banking-grade blocker — surfaced separately so a caller can route on it without parsing findings. |
| `security_verdict` | nested object `{xss_mitigations_verified, token_storage_verified, pii_helpers_verified, csrf_protections_verified, dependency_additions_detected}` | Same reason — security gets its own routable surface. |
| `audit_metadata` | object `{rules_evaluated, files_scanned, lines_scanned, claims_checked, review_duration_inferred_seconds}` | For the caller's audit trail. `rules_evaluated` floor 26 (12 non-negotiables + 9 augmentations + 5 contract items). |
| `uncertainty_flags` | array of `{kind, location, note}` | Triage of the implementation's flags + any new ambiguities the reviewer surfaces. `design_ambiguity` overrides `loop_back_target_stage` to `design`. |

## Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Input missing or `code_under_review` empty | Step 1 | Single finding `P1 / input_incomplete`, verdict `human-queue` |
| Design or claims unreadable / malformed | Step 2 or 3 | Single finding `P1 / input_malformed`, verdict `human-queue` |
| Any `P1` finding | Step 7 | Verdict `human-queue` (a11y blocker, XSS, token storage, PII leak, CSRF gap, missing mutation compensation) |
| Any `P2` finding, no `P1` | Step 7 | Verdict `loop_back` to `implement` |
| `claims_unverified` non-empty, no `P1`/`P2` | Step 7 | Verdict `loop_back` to `implement` |
| Design ambiguity discovered (design wrong, not implementation) | Step 2 | `uncertainty_flag` of kind `design_ambiguity`, verdict `loop_back` to `design` |
| Only `P3` findings, no unverified claims | Step 7 | Verdict `approve` (notes carried forward) |
| Reviewer suspects finding but cannot cite file:line | Self-review | DO NOT publish at full confidence — emit at `severity_floor` with `[needs verification]` in `evidence` |
| `bundle_overrun` flag from the implementation, no other findings | Step 7 | Verdict `loop_back` to `design` (budget is a design decision) |

## Anti-Patterns

- DO NOT emit code, remediation patches, or styled fix snippets — suggest fix shape only (component signature, prop type, helper name).
- DO NOT approve when any implementation claim is unsubstantiated, even when no other finding exists.
- DO NOT fabricate file:line references, ARIA attributes, CWE numbers, or library APIs. Withhold instead.
- DO NOT publish P1 / P2 at low confidence without `[needs verification]` tag in `evidence`.
- DO NOT widen scope beyond `code_under_review` / `tests_under_review` — adjacent observations are `uncertainty_flag` of kind `out_of_scope_observation`, not blocking findings.
- DO NOT loop indefinitely on the same finding across re-reviews; after 2 loops, escalate to `human-queue` (the caller's max-loop policy).
- DO NOT silently downgrade a finding to make the verdict `approve` — verdict is a function of findings, not the other way around.
- DO NOT process real PII in evidence snippets — if a payload contains PII, redact in `evidence` and note in `uncertainty_flag` of kind `needs_human_judgment`.
- DO NOT accept "axe clean" claim without finding either a CI axe assertion OR a dev `@axe-core/react` install in the inspected file set.
- DO NOT downgrade a11y findings — WCAG AA is regulatory, not negotiable.

## References

| Need | File |
|------|------|
| The 12 non-negotiables (F1–F12) + 9 v2 augmentations (A1–A9) + 5 contract items (C1–C5) re-cast as adversarial scan questions | `references/review-rubric.md` |
| P1 / P2 / P3 classification with banking-grade auto-routing matrix (frontend-flavored — a11y blocker, XSS, token, PII, CSRF) | `references/severity-guide.md` |
| Deterministic YES/NO scan list grouped by category (applied at steps 4 + 5) | `references/review-checklist.md` |
| Extraction lineage, augmentations, drops, deviations | `RATIONALE.md` (human audit only — do not load into LLM context) |
