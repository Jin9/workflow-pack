# RATIONALE — review-frontend-code

> **Audience**: humans reviewing the skill before merge / promotion.
> **Not loaded into LLM context.**
> **Phase**: Phase 6+ — `status: ready-for-phase-6`. Do NOT invoke in a
> running workflow until the frontend Dev workflow is approved per
> `COGNITIVE_OS.md` roadmap.
>
> **Source skills consulted**:
> - `treasury/crafting-frontend-code/` (mode `review` and source non-negotiables)
> - `treasury/validating-banking-implementation/` (auto-reject criteria pattern)
> - `treasury/reviewing-software-security/` (severity + confidence + anti-fabrication discipline)
> - `treasury/implement-frontend-feature/` (the Generate upstream this skill verifies)
> - `treasury/review-backend-code/` (shape and verdict matrix — keep them parallel)

## 1. Why this skill exists

The frontend Dev workflow (Phase 6+) needs a Review stage between
`implement-frontend-feature` (Generate) and `validate-frontend-build`
(Validate). Without it, claims like `a11y_compliance.axe_clean: true` or
`security_review.token_storage_strategy: 'httpOnly-cookie'` go
unverified — the build runner catches type errors and failed tests, not
banking-grade discipline gaps.

This skill is the trust-but-verify layer for the frontend Generate
stage, exact parallel to `review-backend-code`. Same 8-step procedure,
same verdict matrix, same anti-fabrication discipline. Frontend-flavored
P1 categories: a11y blockers (regulatory), XSS / token-storage / PII
leaks (catastrophic), CSRF gaps, missing optimistic-update compensation,
business logic in Primitive (boundary violation).

## 2. What was extracted from the sources

| Source | Where it landed |
|--------|-----------------|
| `crafting-frontend-code/SKILL.md` review-mode checklist (P1/P2/P3, evidence-backed) | `SKILL.md` Procedure + `output.json` finding shape |
| `crafting-frontend-code/SKILL.md` Validation gate items (typecheck, a11y, security) | `review-checklist.md` sections B/D/E folded |
| `crafting-frontend-code/references/accessibility.md` forbidden patterns | `review-rubric.md` F5 + `review-checklist.md` § D + `severity-guide.md` P1 a11y categories |
| `crafting-frontend-code/references/security.md` high-risk patterns | `review-rubric.md` F6–F8 + `severity-guide.md` P1 XSS / token-storage / CSRF |
| `implement-frontend-feature/references/implementation-rules.md` F1–F12 + A1–A9 | `review-rubric.md` (1:1 mapping, re-cast as adversarial questions) |
| `implement-frontend-feature/references/self-review-checklist.md` sections A–L | `review-checklist.md` sections A–L (mirrored 1:1 from opposite end) |
| `validating-banking-implementation/SKILL.md` auto-reject criteria | `severity-guide.md` P1 category list |
| `reviewing-software-security/SKILL.md` severity + confidence + standards discipline | `severity-guide.md` Confidence + standards-identifier list + "withhold rather than fabricate" rule (verbatim) |
| `review-backend-code/SKILL.md` 8-step procedure + verdict matrix | `SKILL.md` Procedure + `severity-guide.md` Verdict matrix (shape preserved, categories re-flavored) |

## 3. v2 augmentations added (NEW beyond sources)

| # | Augmentation | Where |
|---|--------------|-------|
| 1 | Machine-readable `verdict` enum + `loop_back_target_stage` enum | `output.json` |
| 2 | Claims-vs-reality verification (step 6) | `SKILL.md` Procedure, `review-rubric.md` § C1–C5, `review-checklist.md` § L |
| 3 | `claims_verified` / `claims_unverified` arrays | `output.json` |
| 4 | `audit_metadata.rules_evaluated >= 26` floor (12 F + 9 A + 5 C) | `output.json`, harness `RulesEvaluatedFloorAssertion` |
| 5 | `design_ambiguity` / `bundle_overrun` / `token_gap` route to `design` (not `implement`) | `severity-guide.md` verdict matrix |
| 6 | `severity_floor` input knob | `input.json` |

## 4. Frontend-specific additions (NEW beyond `review-backend-code`)

| # | Addition | Why it's frontend-specific |
|---|----------|----------------------------|
| 1 | Nested `a11y_verdict` object in output (`wcag_level_verified`, `axe_run_evidence_present`, `role_label_queries_present`, `focus_management_evident`) | A11y is a banking-grade blocker AND a regulatory requirement. Surfacing it as a separate nested object lets the workflow engine route on it without parsing the findings array. Backend has no parallel — there is no a11y in API code. |
| 2 | Nested `security_verdict` object in output (`xss_mitigations_verified`, `token_storage_verified`, `pii_helpers_verified`, `csrf_protections_verified`, `dependency_additions_detected`) | Frontend security surface is fundamentally different from backend (XSS, token storage in browser, CSRF for cookie-auth flows). Same routability rationale as a11y_verdict. |
| 3 | `confidence` exception for a11y / token storage — these stay at declared severity even at `Low` confidence | A11y is regulatory; token storage is catastrophic on leak. Dropping a tier for these would hide the kind of error you most want surfaced. |
| 4 | `audit_metadata.claims_checked` floor | Frontend Generate emits more nested claims (a11y_compliance with 6 booleans, security_review with 5 fields, state_ownership map) than backend. Floor forces the reviewer to actually walk them. |
| 5 | `PillarViolation` as a `P1` when business logic appears in `Primitive` | Frontend pillar separation is a boundary violation; backend has analogous concept but enforced via package boundaries that the compiler / lint catches. Frontend needs the reviewer to enforce. |
| 6 | `dependency_additions_detected` array in `security_verdict` | npm supply chain is the frontend's largest attack surface; surfacing detected additions as a first-class field makes downstream review easy. |
| 7 | Rubric items C3 (a11y_compliance substantiation) and C4 (security_review substantiation) | Backend Review has C3 (`decision_metadata` consistency) only; frontend's nested compliance objects need their own substantiation rules. |
| 8 | Standards identifier list adds `WCAG #.#.#` shape | Backend's list doesn't include WCAG. Frontend findings should cite specific WCAG criteria (e.g., `WCAG 1.4.3` for contrast). |

## 5. What was intentionally dropped

| Dropped | Reason |
|---------|--------|
| 5 of 6 modes from `crafting-frontend-code` (`design`, `optimize`, `fix`, `analyze`, `plan`) | Each is a separate atomic skill in v2. |
| `validating-banking-implementation` chaos planning + full OWASP walk | Out of scope. Chaos is its own stage; full OWASP belongs in `reviewing-software-security`. |
| `reviewing-software-security` 11-area taxonomy + 12 worked examples | Same — that skill remains the comprehensive security review. This stage spot-checks via F5–F8 + categories in severity-guide. |
| Visual regression review | Separate visual-diff stage. |
| Web Vitals / Lighthouse analysis | `analyze-frontend-performance` scope. |

## 6. Deviations from convention (flagged)

| Convention | We did | Why |
|------------|--------|-----|
| `tests/README.md` | `tests/harness-guide.md` | `BANNED_DOCS` constraint (same trade-off as the three prior skills). |
| Nested `banking_grade:` YAML (per `COGNITIVE_OS.md` Section 7) | Inline `{idempotent: true, reversible: n/a, audit_level: detailed}` | Flat-YAML validator can't parse indented frontmatter. |
| `status: ready` | `status: ready-for-phase-6` | Skill is correct but the upstream / downstream skills aren't built; do not auto-promote until Phase 6 sequencing completes. |

## 7. What still needs human review

- **`rules_evaluated >= 26` is a hard count.** If the rule set grows
  (e.g., a 13th non-negotiable, a 10th augmentation), the floor must
  grow with it. Consider moving to a fraction (`>= 1.0`) if the rule
  set churns.
- **Frontend rubric reuses identifiers F* / A* / C* from
  `implement-frontend-feature`.** Renaming on the Generate side would
  break this Review side. Recommend a contract test in CI once a
  workflow engine exists.
- **`PillarConsistencyAssertion`** (in harness-guide.md) requires the
  reviewer LLM to actually inspect file contents for pillar violations.
  The harness assertion checks the verdict, not the depth — the depth
  check requires real LLM behavior. Same v1 limitation as backend.
- **`StateOwnershipCompletenessAssertion`** heuristic still applies —
  parsing "state ownership" from the design document is fragile.
  Structured design schema would fix this.
- **`dependency_additions_detected`** depends on the reviewer being able
  to read `package.json`. Harness needs to pass it in as part of input
  context or the assertion is best-effort. Documented as a v1 limitation.
- **A11y / token-storage confidence exception** (no severity drop at
  `Low` confidence) is documented in `severity-guide.md` but not
  enforced by schema. Worth adding a harness assertion.

## 8. Phase 6 readiness checklist

Before promoting `status: ready-for-phase-6` → `status: ready`:

1. Frontend Dev workflow YAML drafted + approved per `COGNITIVE_OS.md` Section 6.
2. `design-frontend-feature` skill built (Generate upstream's upstream).
3. `implement-frontend-feature` rule set frozen (so this skill's rubric IDs stay valid).
4. `validate-frontend-build` skill built — consumes this skill's approve verdict.
5. Workflow engine supports the bundle / token-gap routing per severity-guide.md.

## 9. Recommended next skills to build

1. **`validate-frontend-build`** (`stage_type: validate`) — runs `tsc`,
   `eslint`, `vitest`, `@axe-core/playwright` on emitted code, returns
   structured pass/fail. Mechanical, smallest remaining gap. Build first.
2. **`design-frontend-feature`** (`stage_type: design`) — produces the
   approved UI design that `implement-frontend-feature` consumes. Larger
   skill; can be sketched and tightened iteratively. Build second.

With these two, the frontend Dev workflow chain `design → implement →
review → validate` becomes end-to-end functional except for the final
`commit` stage (which inherits the backend's commit-skill design once
authored).
