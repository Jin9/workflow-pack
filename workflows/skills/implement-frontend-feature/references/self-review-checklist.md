# Self-Review Checklist (Frontend Generate Stage)

Applied at step 8 of `SKILL.md`, before emit. Every item is YES/NO. Any NO
halts emission and routes per the table at the bottom.

Source: extracted from `treasury/crafting-frontend-code/SKILL.md` safety
workflow steps 3–6 + validation gate (all 7 checks), augmented for the
banking-grade Generate stage.

## A. Pillar discipline

- [ ] Every emitted file is classified into exactly one pillar (`Page` / `Feature` / `Primitive` / `Hook` / `Type` / `Util`).
- [ ] No `Primitive` contains business logic, fetching, or app-specific copy.
- [ ] No leaf component fetches data. Fetching is in `Page` or in a `Hook`.
- [ ] No `Primitive` imports from `Feature` or `Page`.
- [ ] No `Feature` imports from another feature's internal state.

## B. Type safety

- [ ] TypeScript settings: `strict: true` and `noUncheckedIndexedAccess: true` are honored.
- [ ] No `any` outside parser / boundary code (cite the parser if a cast appears).
- [ ] No `as` cast outside parsers / boundaries.
- [ ] No `// @ts-ignore` without comment + follow-up TODO.
- [ ] All API request / response types imported from `codegen/` (no hand-rolled `Response` types beyond parser-local adapters).
- [ ] State machines modeled as discriminated unions with `assertNever` exhaustiveness.

## C. State ownership

- [ ] Every state piece named in the design appears in `state_ownership` output.
- [ ] No server state mirrored into client store / `useState`.
- [ ] No URL-shaped state stored in client store / `useState`.
- [ ] No form state mirrored in both RHF and `useState`.
- [ ] No high-frequency state (cursor, scroll, form draft) in context.
- [ ] No `persist` middleware storing auth tokens or PII.

## D. A11y (see `a11y-checklist.md` for full list)

- [ ] All sections A–G of `a11y-checklist.md` pass for every emitted component.
- [ ] At least one component test asserts via `getByRole` / `getByLabel`.
- [ ] `axe` plan documented (run in dev OR run in CI on this route).
- [ ] No forbidden a11y patterns present (`<div onClick>`, placeholder-as-label, `tabindex > 0`, color-only state).

## E. Security (see `security-checklist.md` for full list)

- [ ] All sections A–I of `security-checklist.md` pass for every emitted file.
- [ ] No auth token in `localStorage` / `sessionStorage`.
- [ ] No `dangerouslySetInnerHTML` without `DOMPurify` + `// SAFE:` comment.
- [ ] URL props validated against scheme allowlist.
- [ ] `target="_blank"` paired with `rel="noopener noreferrer"`.
- [ ] No PII logged to console / analytics / error reporters.
- [ ] No state-changing GET.

## F. Styling / tokens

- [ ] No hex literals, no `rgb(...)`, no arbitrary `[N px]` for values reachable by a token.
- [ ] No inline `style={{color: ...}}` for tokenized values.
- [ ] Component variants via `cva` / `tailwind-variants` (or repo equivalent) — not string concatenation of class names.
- [ ] Missing tokens raised as `uncertainty_flag` of kind `token_gap`, NOT inlined as literals.

## G. Analytics events (frontend audit)

- [ ] Every user-significant action (submit, navigate, toggle persisting state, mutation) emits one event.
- [ ] Every emitted event_type appears in `audit_events_emitted` output.
- [ ] Display-only components emit nothing (read events handled by SIEM, not application).
- [ ] No PII in event payload — only IDs, action, target, page, timestamp, trace_id.

## H. Mutations / compensation

- [ ] Every mutation path declares a compensating action (rollback to snapshot OR undo affordance OR idempotent retry).
- [ ] Submit button disabled while in-flight (double-submit prevention).
- [ ] `Idempotency-Key` header (or repo equivalent) sent on every mutation.
- [ ] Optimistic update rollback is tested.

## I. Tests

- [ ] Companion test exists for every emitted production file.
- [ ] Per-file coverage `>= test_coverage_target` (default 0.80).
- [ ] Tests query by role / label, not by class / test-id (or `data-testid` justified in comment).
- [ ] `userEvent` not `fireEvent` for interactions.
- [ ] MSW handlers used for network — no `fetch` mocking.
- [ ] No `findBy*` / `waitFor` skipped via sleep.
- [ ] No `t.skip(...)` without named unblock condition.
- [ ] No real network call, no env-secret read, no real PII in fixtures.

## J. Bundle

- [ ] `bundle_impact_estimate_kb` is computed (rough — based on imports + lines).
- [ ] If `bundle_budget_kb` is in input and the estimate exceeds it: `uncertainty_flag` of kind `bundle_overrun` emitted; verdict deferred to Review.
- [ ] No dynamic `import()` of user-controlled paths.

## K. Scope discipline

- [ ] No new npm module imported that is not in `package.json` (cross-reference `import` statements).
- [ ] No edit to generated artifacts (`codegen/`, `prisma/migrations`).
- [ ] No reformatting / cleanup outside the changed files.
- [ ] No public component API widened beyond the design.

## L. Decision metadata

- [ ] `decision_metadata.pillar_choices` non-empty (at least one entry per file).
- [ ] `decision_metadata.state_library_choices` documents the choice between repo / greenfield default if they differed.
- [ ] `decision_metadata.repo_conventions_followed` lists the conventions discovered at step 3.

## Routing of any NO

| Section with NO | Action |
|-----------------|--------|
| D (a11y) | `loop_back` to design — a11y is a blocker |
| E (security) — sections A (XSS), C (token storage), F (sensitive data), G (PII) | `human-queue` immediately, no retry |
| E (security) — other sections | First NO: `loop_back` to design; repeat NO: `human-queue` |
| B (type safety), C (state ownership), F (tokens), G (analytics), H (mutations), I (tests) | `loop_back` to design (under-specified) |
| A (pillar), J (bundle), K (scope), L (decision metadata) | Fix in place inside step 6 / 7, then re-run self-review. If still NO after one re-try: `human-queue`. |
