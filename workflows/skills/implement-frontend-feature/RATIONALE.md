# RATIONALE — implement-frontend-feature

> **Audience**: humans reviewing the skill before merge / promotion.
> **Not loaded into LLM context.**
>
> **Phase**: Phase 6+ per `COGNITIVE_OS.md` Section 10. Do NOT invoke in a
> running workflow until the frontend Dev workflow is approved per roadmap.
> Frontmatter `status: ready-for-phase-6` signals this.
>
> **Source skill**: `treasury/crafting-frontend-code/` (mono-skill, 6 modes).

## 1. Why this skill exists

The frontend Dev workflow needs a `generate` stage exactly parallel to the
backend's `implement-backend-feature`. The source skill `crafting-frontend-code`
covers `design`, `optimize`, `fix`, `analyze`, `review`, `plan` — none of
which emit a new feature's worth of production code from an approved design.

This skill fills the gap with the same atomic-skill discipline used for
backend, then layers on frontend-specific banking-grade non-negotiables that
the backend skill cannot enforce: a11y (regulatory), PII field-level
treatment, design-token discipline, bundle budget, analytics events instead
of audit events, optimistic-UI rollback as compensation.

## 2. What was extracted from the source

| Source file | Target | Notes |
|-------------|--------|-------|
| `SKILL.md` Safety workflow steps 3–6 | `references/self-review-checklist.md` sections A, K, L | Re-cast as YES/NO with NO routing per section |
| `SKILL.md` Validation gate (all 7 checks) | `references/self-review-checklist.md` (folded across sections B, D, E, F, G) | Each gate became a checklist item with routing |
| `SKILL.md` Operating posture (identity, risk, change policy) | `SKILL.md` Purpose + Anti-Patterns | Compressed — atomic body stays lean |
| `SKILL.md` Thinking model L4 | `SKILL.md` Procedure step 6 (Generate) | L1–L3 deliberately out of scope (design stage owns them) |
| `references/architecture.md` (pillars, state ownership map, data flow, composition, rendering model, risky patterns) | `references/react-typescript-conventions.md` (pillars + data flow + rendering) and `references/state-management-rules.md` (ownership + risky patterns) | Split across two files because pillars belong with TS conventions and ownership belongs with state |
| `references/typescript.md` (strict patterns, discriminated unions, branded types, generics) | `references/react-typescript-conventions.md` § TypeScript | Banking-grade upgrade: `any` outside parsers and `as` outside parsers moved from "risky pattern" to "blocking" |
| `references/state-data.md` (TanStack Query, Zustand, RHF+Zod, URL state, optimistic updates) | `references/state-management-rules.md` | Re-organized as a top-down decision tree |
| `references/accessibility.md` (semantic HTML, keyboard, forms, focus, contrast, motion, screen reader, testing, risky patterns) | `references/a11y-checklist.md` (sections A–H + forbidden patterns) | Re-cast as YES/NO blocking checklist for banking-grade regulatory posture |
| `references/security.md` (XSS, CSRF, token storage, CSP, dependencies, sensitive data, high-risk patterns) | `references/security-checklist.md` (sections A–I + routing) | Upgrades soft `localStorage` warning to blocking; adds PII field-level section (G) and generated-types section (I) |
| `references/testing.md` (pyramid, Vitest + RTL, MSW, Playwright, visual, a11y tests) | `references/react-typescript-conventions.md` § Testing + `self-review-checklist.md` § I | Risky patterns table preserved verbatim |
| `references/styling-design-system.md` (tokens, theming, variants, layering, risky patterns) | `references/implementation-rules.md` F10 + `self-review-checklist.md` § F | Banking-grade addition: token gap → `uncertainty_flag`, never inline literal |

## 3. v2 augmentations added (NEW beyond source)

Parallel to backend's A1–A7, plus two frontend-specific (A8 bundle, A9 token).

| # | Augmentation | Lives in | Why it's new |
|---|--------------|----------|--------------|
| A1 | Analytics event shape (frontend's audit equivalent) — `{event_type, actor, action, target, page, timestamp, trace_id, decision_metadata}` | `implementation-rules.md` | Source did not specify event shape. Workflow audit needs it. |
| A2 | Idempotency = double-submit prevention + `Idempotency-Key` header + optimistic rollback | `implementation-rules.md`, `state-management-rules.md` | Frontend analog of backend A2. Source mentioned RHF `isSubmitting` but did not enforce header convention. |
| A3 | Compensating actions for optimistic UI (rollback to snapshot, undo affordance, idempotent retry) | `implementation-rules.md`, output `compensating_actions` field | Source had optimistic-update pattern but no machine-readable compensation declaration. |
| A4 | Client error classification (`client_input | client_state | network | server`) with per-class UI behavior + retry + log | `implementation-rules.md` | Source had error patterns scattered. v2 needs a stable taxonomy for retry policy + observability. |
| A5 | Test fixtures discipline (no real network, no env secret, no shared state, MSW only) | `implementation-rules.md` | Source had testing risky patterns; v2 makes them blocking. |
| A6 | Convention discovery overrides defaults | `implementation-rules.md`, `react-typescript-conventions.md` preamble | Source said "repo-first" once; v2 makes the override mechanism explicit (emit `convention_conflict` flag). |
| A7 | No silent dependency additions | `implementation-rules.md`, SKILL.md Anti-Patterns | Source warned against framework migrations; v2 escalates to `uncertainty_flag` of kind `dependency_addition`. |
| A8 | Bundle budget guard — new frontend SLA dimension | `implementation-rules.md`, output `bundle_impact_estimate_kb` field, schema `bundle_budget_kb` input | Backend has no bundle. Frontend's RUM / performance SLA needs a per-Generate budget gate. Worth proposing to `COGNITIVE_OS.md` Section 3 as a new metric. |
| A9 | Token-gap discipline — missing token → `uncertainty_flag`, never inline literal | `implementation-rules.md`, self-review § F | Source said "risky pattern"; v2 makes it a workflow-visible flag so the design system can grow. |

## 4. Frontend-specific banking-grade additions (beyond source)

Twelve non-negotiables in `implementation-rules.md` § "Banking-grade frontend
non-negotiables" — these upgrade source posture from "prefer" / "risky
pattern" to **blocking**:

| # | Rule | Source posture | Reason for upgrade |
|---|------|----------------|--------------------|
| F1 | No `any` outside parsers | "Risky pattern" | Type safety = data correctness in regulated UI |
| F2 | Generated API types only | "Prefer codegen" | Hand-rolled types drift; banking cannot ship drift |
| F3 | Component pillar separation (Primitive/Feature/Page/Hook/Type/Util) | "Reference model" | Boundary discipline is auditable |
| F4 | Server state never mirrored | "Risky pattern" | Mirroring is the canonical source of stale UI |
| F5 | WCAG 2.1 AA minimum | "Target" | Regulatory in most banking jurisdictions |
| F6 | No `localStorage` for auth tokens | "Preferred default" | XSS readability = full takeover |
| F7 | No `dangerouslySetInnerHTML` w/o DOMPurify + `// SAFE:` comment | "High-risk pattern" | XSS = direct PII / session exposure |
| F8 | URL props scheme-allowlisted, `target="_blank"` rel-noopener | "High-risk pattern" | `javascript:` URI = XSS |
| F9 | Per-field PII treatment helper | Implicit | Field-level PDPA/GDPR compliance |
| F10 | Design tokens only | "Risky pattern" | Token discipline = brand audit + re-theme without code change |
| F11 | Tests by role / label, `data-testid` justified, MSW for network | "Convention" | Test discipline catches regressions, not snapshots |
| F12 | Analytics event on every user-significant action | NOT in source | Frontend audit trail — banking-grade addition |

## 5. What was intentionally dropped (and why)

| Dropped | Reason |
|---------|--------|
| 5 of 6 modes (`design`, `optimize`, `fix`, `analyze`, `review`, `plan`) | One stage = one skill. Each is a sibling skill in v2 (`design-frontend-feature`, `analyze-frontend-performance`, `generate-frontend-fix`, `review-frontend-code`, `plan-frontend-migration`). |
| Mode dispatch logic | Workflow engine picks the skill, not the skill's body. |
| L1, L2, L3 thinking-model layers | Belong in `design-frontend-feature` — this skill receives an approved design that passed L1–L3 already. |
| Per-mode output shape table | Replaced by single Output Contract + JSON Schema. |
| `references/performance.md` deep content | Performance optimization is `analyze-frontend-performance` / `optimize-frontend-perf`. This skill only enforces bundle budget (A8) as a Generate-time guard. |
| `references/observability.md` deep content | Compressed to one rule (F12 analytics events). Full RUM / error-reporting is `observability-stage` skill (future). |
| `references/tooling-build.md` | Build / bundler / monorepo decisions are design-time. This skill consumes the existing build. |
| `references/examples.md` per-mode examples | Atomic skill emits one shape; replaced by `tests/cases/` |

## 6. Deviations from the brief (flagged)

| Brief said | We did | Why |
|------------|--------|-----|
| `tests/README.md` | `tests/harness-guide.md` | Same `BANNED_DOCS` constraint as backend skills. |
| Nested `banking_grade:` YAML | Inline YAML `{idempotent: true, reversible: soft, audit_level: detailed}` | Flat-YAML validator can't parse indented frontmatter. |
| `frontmatter validates against schemas/skill-v1.schema.json` | Validated against `quick_validate.py` only | No `skill-v1.schema.json` in repo yet — Phase 1 deliverable. |
| `status: ready` only when Phase 5 reaches frontend | Set `status: ready-for-phase-6` explicitly in frontmatter | Signals not-yet-runnable in the workflow without blocking authoring / review. |

## 7. Architectural decisions to escalate to COGNITIVE_OS.md

Proposed additions for `COGNITIVE_OS.md` Section 3 (Banking-grade non-negotiables):

- **Add "Bundle budget" to SLA targets** (Section 3 SLA table). Frontend
  workflow needs per-Generate bundle ceiling enforcement; analogous to
  P95 latency for backend. Suggested v1 target: ≤ 50 KB per feature, ≤ 250
  KB per route added.
- **Add "Field-level PII classification" to non-negotiables** (Section 3
  list). Currently only "Auditability / Idempotency / Determinism / Graceful
  degradation / Reversibility" — add a 6th item for PII classification with
  field-level treatment, applicable to any stage that emits user-facing
  surface.

## 8. What still needs human review

- **`audit_events_emitted` regex** in `output.json` is permissive
  (`^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$`). Worth narrowing once the
  event taxonomy is published.
- **`target_feature_path` regex** allows brackets for Next.js dynamic
  segments. Should be tightened if a different routing convention is
  adopted.
- **`PillarConsistencyAssertion`** in `tests/harness-guide.md` is partially
  manual — full enforcement requires the harness to read file contents to
  verify a `Primitive` does not import from a `Feature`. Documented as a
  v1 limitation; should land in harness v2.
- **`StateOwnershipCompletenessAssertion`** relies on parsing the design
  for state-piece names heuristically. A structured design schema would
  remove the heuristic — propose for `design-frontend-feature` skill input.
- **Forward-referenced sibling skills** (`design-frontend-feature`,
  `generate-frontend-fix`, `analyze-frontend-performance`,
  `review-frontend-code`) — none exist yet. Names are conventional.

## 9. Phase 6 readiness

NOT runnable in workflow yet. Required before promotion to `status: ready`:

1. Frontend Dev workflow YAML drafted and approved per
   `COGNITIVE_OS.md` Section 6.
2. `design-frontend-feature` skill built — this skill's upstream.
3. `review-frontend-code` skill built — this skill's downstream verifier.
4. `validate-frontend-build` skill built — runs `tsc`, lint, `vitest`,
   `axe`, bundle-size diff on the emitted code.
5. Workflow engine supports the `bundle_overrun` uncertainty flag routing
   (per A8).

## 10. Recommended next skill to build

`review-frontend-code` — exact parallel to `review-backend-code`. The
adversarial verifier that consumes this skill's output and proves the
claims (a11y_compliance true → axe really clean; pii_fields_handled →
fields really rendered through helpers; component_pillar → Primitive
really has no fetching imports). Build before any Validate stage.
