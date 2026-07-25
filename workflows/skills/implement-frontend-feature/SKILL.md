---
name: implement-frontend-feature
version: 2.0.0
description: "Generate production-grade React/TypeScript code for one frontend feature from an approved UI design, with banking-grade discipline: WCAG 2.1 AA a11y, no any outside parsers, no localStorage auth tokens, no unsanitized dangerouslySetInnerHTML, design-token-only styling, generated API types, and PII field-level handling. Use when implementing a React component from an approved UI design. Use when generating a Next.js page with server state and forms from a spec. Use when implementing a feature module with TypeScript strict mode and a11y guarantees. Do NOT use for backend code (use implement-backend-feature). Do NOT use for pure CSS or styling tweaks without component logic. Do NOT use for greenfield architecture decisions (defer to designing-tech-lead-handoff). Do NOT use for infrastructure or build tooling. Do NOT use for fixing existing UI bugs (use generate-frontend-fix)."
stage_type: generate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: detailed, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_generation, file_write]
expected_duration_p95_seconds: 180
max_retries_recommended: 2
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Implement Frontend Feature

## Purpose

Take a single approved frontend design and emit production-grade React /
TypeScript code plus companion tests for one frontend code-generation pass.
Owns code synthesis only — analysis, design, review, and validation live in
sibling atomic skills.
Banking-grade non-negotiables apply on every output: WCAG 2.1 AA a11y,
TypeScript strict, no auth token in `localStorage`, no unsanitized HTML
injection, design-token-only styling, generated API types, PII field-level
treatment, analytics events at user-significant actions.

## When to use this skill

- Use when: implementing a React component, page, or feature module from an
  approved UI design.
- Use when: a code-generation step selects this skill for a TypeScript /
  React target package.
- Use when: a design specifies a11y, PII, and token-storage requirements and
  the next stage is code emission.
- Do NOT use when: the target is backend, infra, or pure CSS.
- Do NOT use when: greenfield architecture decisions are still open — defer
  to `designing-tech-lead-handoff`.
- Do NOT use when: fixing an existing UI bug — defer to `generate-frontend-fix`.
- Do NOT use when: optimizing performance of existing code — defer to
  `analyze-frontend-performance`.
- Do NOT use when: reviewing already-emitted code — defer to
  `review-frontend-code`.

## Input contract

ADVISORY — documents the assembled stage input; the engine validates workflow input
and stage OUTPUTS only (engine/validation.py). Validate against `schemas/input.json`.
Required: `api_contracts` + `component_map` (tl-design's architecture blueprint,
elaborated through the SPA scaffold conventions), the ux-intake pack fields —
`maturity_level` (3 = implementation-ready; **2 = BA-derived draft: proceed WITH a
P2 advisory uncertainty flag**), `status`, `p1_findings` (MUST be empty — any P1
UX finding blocks implementation), and the eight pack-relative spec paths
(tokens, route map, component inventory, microcopy, screen states, form
validation, responsive, accessibility — resolve via
`dirname(upstream_artifacts["ux-intake"])`, reject traversal) — plus
`idempotency_key` (engine-injected generation-attempt identity; never embedded
in emitted source). Optional engine-injected: `upstream_artifacts`,
`loop_back_feedback` (frontend-review findings the regeneration MUST apply).
Quality floors (WCAG AA, coverage 0.80) are reference defaults; a regulated PII
treatment that cannot be determined from the specs is `needs-input` — NEVER
inferred from field names or prose.

**Example (validates against schemas/input.json):**
```json
{
  "api_contracts": { "template_version": "1.0", "contracts": [] },
  "component_map": { "template_version": "1.0", "components": [] },
  "maturity_level": 2,
  "status": "ready-for-audit",
  "p1_findings": [],
  "tokens_path": "ux-design-c3f8a1d2/tokens.json",
  "route_map_path": "ux-design-c3f8a1d2/route-map.md",
  "component_inventory_path": "ux-design-c3f8a1d2/component-inventory.md",
  "microcopy_path": "ux-design-c3f8a1d2/microcopy.json",
  "screen_states_path": "ux-design-c3f8a1d2/screen-states.md",
  "form_validation_path": "ux-design-c3f8a1d2/form-validation.md",
  "responsive_spec_path": "ux-design-c3f8a1d2/responsive-spec.md",
  "accessibility_spec_path": "ux-design-c3f8a1d2/accessibility-spec.md",
  "idempotency_key": "c3f8a1d2-4b6e-4f09-9a7c-1e2d3b4a5c6d"
}
```

## Procedure

Run all 9 steps in order. Do not skip steps for "small" features.

1. **Pre-flight — design completeness.** Verify the design declares L1 / L2 /
   L3 / L4 AND has no `TBD` on a11y, security, PII, or token storage. Any
   `TBD` on those four that the specs cannot resolve = execution failure (retry → human queue). No loop_back route exists FROM this stage.
2. **Pre-flight — target path exists.** Read `target_feature_path`. If
   missing, execution failure. If present, discover conventions: component layer
   structure, hook patterns, TypeScript settings, state libraries, test
   stack, token/theme system. Discovery outranks the greenfield defaults in
   `references/react-typescript-conventions.md`.
3. **Inspect — repo-first.** Read at least 2 sibling components / hooks /
   types in the same area. Mirror their boundary, naming, and import
   layout. Conflicts with design → `uncertainty_flag`, prefer repo.
4. **Plan — pillars.** Classify every emitted file into one pillar:
   `Page` / `Feature` / `Primitive` / `Hook` / `Type` / `Util` per
   `references/react-typescript-conventions.md`. A Primitive may not own
   business logic. A Page owns fetching / boundaries / layout shell.
5. **Plan — state ownership.** Map every state piece to one owner:
   `server` (TanStack Query or repo equivalent), `client` (Zustand /
   repo equivalent), `URL` (search params / router), `form` (RHF / repo
   equivalent), `local` (`useState`), or `derived` (compute on render).
   Never mirror `server` into `client`.
6. **Generate — code.** Emit files. Every emitted file MUST satisfy ALL of:
   type-safety, state, a11y, security, PII, design-token, API-type, and
   analytics rules — every rule is blocking, none is "preferred."
   Detailed rules (authoritative): `references/implementation-rules.md`
   (F1–F12 + v2 augmentations A1–A9), `references/react-typescript-conventions.md`
   (pillars, TS strict), `references/a11y-checklist.md` (YES/NO a11y scan),
   `references/security-checklist.md` (YES/NO security scan), and
   `references/state-management-rules.md` (ownership decision tree).
7. **Generate — tests.** Companion tests per `react-typescript-conventions.md`
   § Tests: Vitest + RTL for components/hooks, MSW for network mocks. Tests
   query by role / label, not by class / test-id. Coverage `>= test_coverage_target`
   (default 0.80) per file. Failing coverage = execution failure (over-scoped) → retry → human queue.
8. **Self-review.** Apply every YES/NO in `references/self-review-checklist.md`.
   Any NO halts emission and routes per the Failure Modes table.
9. **Emit.** Produce a payload conforming to `schemas/output.json`. Populate
   nested `a11y_compliance` and `security_review` objects in full — they are
   required, not best-effort.

## Output contract

Output MUST validate against `schemas/output.json`. Structured fields:

| Field | Type | Purpose |
|-------|------|---------|
| `files_generated` | array of `{path, content_hash, lines_added, component_pillar}` | Files written. `component_pillar` ∈ `Page | Feature | Primitive | Hook | Type | Util`. |
| `tests_generated` | array of `{path, content_hash, test_type, coverage_pct}` | `test_type` ∈ `unit | component | integration | e2e | visual | a11y`. |
| `a11y_compliance` | nested object — REQUIRED `{wcag_level, keyboard_navigable, screen_reader_tested, color_contrast_verified, focus_management_implemented, axe_clean}` | Every sub-field present, no defaults. |
| `security_review` | nested object — REQUIRED `{xss_surfaces, csrf_protected, csp_compliant, token_storage_strategy, pii_fields_handled}` | `xss_surfaces` MUST be empty or each entry has a `mitigation`. `token_storage_strategy` ∈ `httpOnly-cookie | in-memory | n/a`. |
| `state_ownership` | map `state_piece → server | client | URL | form | local | derived` | Every state piece named in the design must appear. |
| `bundle_impact_estimate_kb` | number | Best-effort estimate. Over `bundle_budget_kb` triggers `uncertainty_flag`. |
| `compensating_actions` | array | Required for any mutation path (optimistic UI rollback, undo affordance, idempotent retry). Empty for read-only. |
| `audit_events_emitted` | array of event-type strings | Every user-significant action contributes one entry. Empty only for display-only components. |
| `uncertainty_flags` | array of `{kind, location, note}` | Advisory only (e.g. the maturity-2 P2 advisory). Blocking ambiguity terminates execution; `loop_back_feedback` arrives only FROM frontend review. |
| `decision_metadata` | object `{pillar_choices, state_library_choices, repo_conventions_followed}` | For audit. |
| `audit_id` | string (uuid) | Producer-stamped, deterministic: UUIDv5(HOUSE_NS, "frontend-implement:{idempotency_key}") for live derivations (corpus ids sim-convention, grandfathered). |

The a11y/security objects are producer SELF-REVIEW claims — T4 (accessibility)
and T7 (AppSec) provide the test evidence; the success branch schema-enforces
the blocking booleans.

**Example (validates against schemas/output.json — blocked variant):**
```json
{
  "output_type": "blocked_implementation",
  "blockers": [
    { "code": "BLOCK-A11Y-CONTRAST", "description": "Design requires gradient text below 4.5:1 — WCAG AA cannot be met." }
  ],
  "audit_id": "b8e4f0a2-6c35-4d91-8f27-1a9b3c5e7d04"
}
```

## Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Design has unresolved a11y / security / PII / token-storage question | Step 1 | execution failure → retry ×2 → frontend-implement-failures queue |
| Scaffold target unresolvable | Step 2 | execution failure → retry ×2 → frontend-implement-failures queue |
| Repo convention conflicts with design pattern | Step 3 | Prefer repo, emit `uncertainty_flag` of kind `convention_conflict` |
| Cannot meet WCAG `AA` (e.g., design requires gradient text under 4.5:1) | Step 6 a11y | `blocked_implementation` artifact — a11y is a BLOCKER, not a warning |
| Cannot generate component test for an interaction | Step 7 | `loop_back` to design (component is over-scoped or untestable as drawn) |
| Generated code introduces an XSS / CSRF / token-storage / PII-leak surface without mitigation | Step 8 self-review | `human-queue` — security NO is never `loop_back` |
| Bundle impact exceeds `bundle_budget_kb` | Step 9 | `uncertainty_flag` of kind `bundle_overrun`, verdict deferred to the review step |
| Self-review finds NO on type-safety / state / a11y / security | Step 8 | First NO on security / PII: `human-queue`; everything else: `loop_back` |

## Constraints

The blocking anti-patterns (no `any` outside parsers, no server→client state
mirroring, no token in `localStorage`/`sessionStorage`, no unsanitized
`dangerouslySetInnerHTML`, no skipped a11y / focus / labels, no silent
dependency additions, no component without a companion test, no PII logged,
no off-token styling, no hand-rolled API types, no business logic in a
`Primitive` / fetch in a leaf, no skipped self-review) are enumerated
authoritatively as YES/NO checks in the reference set — do NOT restate them
here. Detailed rules: `references/implementation-rules.md` (F1–F12),
`references/a11y-checklist.md` (§ Forbidden patterns / auto-NO),
`references/security-checklist.md` (§ A–I), and
`references/state-management-rules.md`.

## References

| Need | File |
|------|------|
| Banking-grade frontend non-negotiables + 9 v2 augmentations (analytics events, optimistic rollback, error classes, token discipline, bundle guard, etc.) | `references/implementation-rules.md` |
| Component pillars (Page / Feature / Primitive / Hook / Type / Util), TypeScript strict patterns, test conventions | `references/react-typescript-conventions.md` |
| YES/NO a11y scan applied at step 6 + step 8 | `references/a11y-checklist.md` |
| YES/NO security scan applied at step 6 + step 8 | `references/security-checklist.md` |
| State ownership decision tree (server / client / URL / form / local / derived) | `references/state-management-rules.md` |
| YES/NO self-review applied at step 8 before emit | `references/self-review-checklist.md` |
| Extraction lineage, augmentations, drops, deviations | `RATIONALE.md` (human audit only — do not load into LLM context) |
