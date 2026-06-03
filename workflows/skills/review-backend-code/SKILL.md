---
name: review-backend-code
version: 1.0.0
description: >
  Adversarially verify Go backend code emitted by a Generate stage against the
  approved design and the 11 banking-grade decision rules + v2 augmentations,
  then issue a machine-readable verdict (approve, loop_back, or human-queue).
  Use when reviewing the output of implement-backend-feature before the build
  stage. Use when verifying that a Generate stage's claims (idempotency,
  audit, compensation) are actually implemented in the emitted code. Use when
  scoring a Go feature for banking-grade readiness before a Validate stage.
  Do NOT use for full defensive security review across infra, gateways, K8s
  (use reviewing-software-security). Do NOT use for chaos test planning
  (use a separate chaos-plan skill). Do NOT use for frontend, infra, or
  greenfield architecture review.
stage_type: review
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: detailed}
expected_duration_p95_seconds: 90
max_retries_recommended: 2
compatibility: claude-code, codex, opencode
---

# Review Backend Code

## Purpose

Verify that Generate-stage output for one Go backend feature actually satisfies
the approved design and the banking-grade rule set. Trust-but-verify the
Generate stage's claims (idempotency strategy, audit events, compensating
actions), scan the emitted code against the 11 base decision rules and 7 v2
augmentations, and issue a machine-readable verdict that the workflow engine
routes per Section 8 Review Pattern. Read-only — emits no code.

## When to use this skill

- Use when: the workflow's next stage is `validate-build` and the Generate
  stage's output needs verification first.
- Use when: a `review`-type stage selects this skill for a Go target package.
- Use when: a Generate stage emits `uncertainty_flags` that need triage before
  the workflow proceeds.
- Do NOT use when: the task is a full security audit across infra / gateways
  — defer to `reviewing-software-security`.
- Do NOT use when: the task is chaos test planning — separate skill.
- Do NOT use when: the target is frontend, infra, or greenfield architecture.
- Do NOT use when: the task is writing remediation code — this skill suggests
  fix shape only; emission belongs to a Generate stage.

## Input

Input MUST validate against `schemas/input.json`. Required fields:

| Field | Type | Notes |
|-------|------|-------|
| `design_document` | string (markdown) | Same document the Generate stage consumed. |
| `target_package` | string | Same package path the Generate stage targeted. |
| `implement_stage_output` | object | Verbatim output of `implement-backend-feature` (per its `schemas/output.json`). |
| `code_under_review` | array of `{path, content}` | Production files emitted by Generate. |
| `tests_under_review` | array of `{path, content}` | Companion tests emitted by Generate. |
| `idempotency_key` | string (UUID v4) | Same key. Same input → same verdict bytes. |

Optional: `convention_overrides`, `severity_floor` (default `P3`).

## Procedure

Run all 7 steps in order. Never skip step 6 (claims-vs-reality check) — it is
the unique reason this skill exists.

1. **Pre-flight — input completeness.** Verify every required field is
   present and that `code_under_review` is non-empty. If absent, emit a
   single `P1` finding of category `input_incomplete` and verdict
   `human-queue`.
2. **Read the design.** Extract: L1 invariant, declared idempotency strategy,
   declared audit event types, declared compensating actions, declared error
   classes, public contract. These are the *truth* against which claims are
   checked.
3. **Read the Generate claims.** From `implement_stage_output` capture:
   `idempotency_strategy`, `audit_events_emitted`, `compensating_actions`,
   `decision_metadata.pattern_choices`, `uncertainty_flags`. These are
   *what Generate said it did*.
4. **Scan the code — rule sweep.** Walk every file in `code_under_review`
   against `references/review-rubric.md` (the 11 base rules + 7 v2
   augmentations re-cast as adversarial scan questions). Every violation
   becomes one finding.
5. **Scan the tests — discipline sweep.** Walk every file in
   `tests_under_review` against the test items in
   `references/review-checklist.md` (table-driven, no network, no secrets,
   no shared state, coverage claim plausible).
6. **Claims-vs-reality.** For each Generate claim, prove the corresponding
   code exists:
   - `idempotency_strategy` claims a key → find the key parameter at the
     boundary, find the dedup store call, find the replay branch. Missing
     any of these = `P1` finding.
   - Each `audit_events_emitted` entry → find the emit call in the code.
     Missing = `P1` finding.
   - Each `compensating_actions[].trigger` → find the call site of the
     irreversible action. Missing = `P1` finding.
   - `pattern_choices` → verify the chosen pattern is actually in the
     code. Mismatch = `P2` finding.
7. **Severity, verdict, emit.** Apply `references/severity-guide.md` to
   classify every finding (P1 / P2 / P3). Compute the verdict per the
   verdict matrix in that file. Emit a payload conforming to
   `schemas/output.json`.

## Output Contract

Output MUST validate against `schemas/output.json`. Structured fields:

| Field | Type | Purpose |
|-------|------|---------|
| `verdict` | enum `approve | loop_back | human-queue` | Routed by the workflow engine. |
| `loop_back_target_stage` | enum `design | implement | null` | Required when verdict is `loop_back`; null otherwise. |
| `findings` | array of `{severity, category, rule_violated, file, line, evidence, fix_shape, standards_ref}` | One entry per gap. Empty = clean. |
| `claims_verified` | array of strings | Plain-text list of Generate claims that the code substantiates. |
| `claims_unverified` | array of strings | Plain-text list of Generate claims that the code does NOT substantiate. Non-empty forces `loop_back` or `human-queue`. |
| `audit_metadata` | object `{review_duration_inferred, rules_evaluated, files_scanned, lines_scanned}` | For the workflow audit event. |
| `uncertainty_flags` | array of `{kind, location, note}` | Ambiguities surfaced during the review (e.g., design says "use repo's logger" but two loggers are in scope). |

## Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Input fields missing or `code_under_review` empty | Step 1 | Single finding `P1 / input_incomplete`, verdict `human-queue` |
| Design or claims unreadable / malformed | Step 2 or 3 | Single finding `P1 / input_malformed`, verdict `human-queue` |
| Any `P1` finding | Step 7 | Verdict `human-queue` (security, idempotency, audit, compensation, data correctness) |
| Any `P2` finding, no `P1` | Step 7 | Verdict `loop_back` to `implement` |
| `claims_unverified` non-empty, no `P1`/`P2` | Step 7 | Verdict `loop_back` to `implement` |
| Design ambiguity discovered (the design itself is wrong) | Step 2 | `uncertainty_flag` of kind `design_ambiguity`, verdict `loop_back` to `design` |
| Only `P3` findings, no unverified claims | Step 7 | Verdict `approve` (notes carried forward, not blocking) |
| Reviewer suspects a finding but cannot cite file:line | Self-review | DO NOT publish at full confidence — emit at `severity_floor` with `[needs verification]` in `evidence` |

## Anti-Patterns

- DO NOT emit code or remediation patches — suggest fix shape only (function signature + invariants).
- DO NOT approve when any Generate claim is unsubstantiated by the code, even if no other finding exists.
- DO NOT fabricate file:line references, standards identifiers, or CWE numbers. Withhold instead.
- DO NOT publish P1 / P2 findings at low confidence without a `[needs verification]` tag in `evidence`.
- DO NOT widen scope beyond the files in `code_under_review` / `tests_under_review` — adjacent issues are an addendum, not blocking findings.
- DO NOT loop indefinitely on the same finding across re-reviews; after 2 loops, escalate to `human-queue` per workflow `max_loops`.
- DO NOT silently downgrade a finding to make the verdict `approve` — the verdict is a function of findings, not the other way around.
- DO NOT process real PII in evidence snippets — ask for redaction if a payload contains it.

## References

| Need | File |
|------|------|
| The 11 base decision rules + 7 v2 augmentations re-cast as adversarial scan questions | `references/review-rubric.md` |
| P1 / P2 / P3 classification with banking-grade auto-routing matrix | `references/severity-guide.md` |
| Deterministic YES/NO scan list grouped by category (applied at steps 4 + 5) | `references/review-checklist.md` |
| Extraction lineage, augmentations, drops, deviations | `RATIONALE.md` (human audit only — do not load into LLM context) |
