# Review Checklist (Frontend)

Applied at steps 4 + 5 of `SKILL.md` — a deterministic YES/NO scan over
every file in `code_under_review` and `tests_under_review`. Every NO becomes
one finding. Severity is assigned at step 7 by `severity-guide.md`.

Source: extracted from
`implement-frontend-feature/references/self-review-checklist.md` (sections
A–L, mirrored 1:1 from opposite end) + claims-vs-reality section K from
`review-backend-code/references/review-checklist.md` adapted for frontend
contract items.

## A. Pillar discipline (code)

- [ ] Every file's declared `component_pillar` matches its actual content (no fetching in `Primitive`, no JSX in `Hook`).
- [ ] No `Primitive` imports from `Feature` / `Page` / fetching layer.
- [ ] No `Feature` imports another feature's internal state.
- [ ] No leaf component performs network calls.

## B. Type safety (code)

- [ ] No `any` outside parser / `codegen/` / `mocks/` paths (cite file:line).
- [ ] No `as` cast outside parser / boundary.
- [ ] No `// @ts-ignore` without comment + follow-up TODO.
- [ ] API request / response types imported from `codegen/` (no hand-rolled `Response` types beyond parser-local adapters).
- [ ] State machines modeled as discriminated unions with `assertNever`.

## C. State ownership (code + claims)

- [ ] Every state piece named in the design appears in `state_ownership` output.
- [ ] No `useEffect` that mirrors server cache data into `useState` / Zustand / context.
- [ ] No URL-shaped state stored in `useState` / store.
- [ ] No form state in both RHF and `useState`.
- [ ] No high-frequency state (cursor / scroll / form draft) in context.
- [ ] `persist` middleware does NOT contain auth tokens or PII.

## D. A11y (code + claims)

- [ ] No `<div onClick>` for clickable things.
- [ ] No placeholder-as-only-label.
- [ ] No `tabindex > 0`.
- [ ] No removed focus outline without replacement.
- [ ] No color-only state conveyance.
- [ ] No `<img>` without `alt` attribute (decorative `alt=""` is fine).
- [ ] Every form input has an associated `<label>`.
- [ ] Validation errors associated via `aria-describedby` + `role="alert"`.
- [ ] Tab order matches visual order (no jump via `tabindex > 0`).
- [ ] Modal / overlay closes on `Esc`, traps focus, returns focus to trigger.
- [ ] At least one component test asserts via `getByRole` / `getByLabel`.
- [ ] `axe` plan present (dev `@axe-core/react` install OR CI `@axe-core/playwright` assertion).
- [ ] `a11y_compliance.wcag_level >= AA`.
- [ ] Every `a11y_compliance` boolean claim is substantiated by visible code.

## E. Security (code + claims)

- [ ] No `dangerouslySetInnerHTML` without `DOMPurify.sanitize(...)` AND `// SAFE:` comment.
- [ ] No string concatenation into JSX that disables React escaping.
- [ ] URL props (`href`, `src`, `formAction`) validated against scheme allowlist.
- [ ] No `eval`, `new Function()`, dynamic `import()` of user-controlled paths.
- [ ] Mutating fetches have CSRF protection (token, `credentials: 'include'`, `X-Requested-With`, or Bearer).
- [ ] No state-changing `GET` requests.
- [ ] No `localStorage.setItem` / `sessionStorage.setItem` with key matching `/token|jwt|access|refresh|session|auth|bearer/i`.
- [ ] Session tokens in HttpOnly cookie (or in-memory short-lived) — code consistent with `token_storage_strategy` claim.
- [ ] No secrets / API keys / internal IDs rendered into DOM (even hidden).
- [ ] No PII in URL.
- [ ] Client logs scrub PII / tokens before transmission.
- [ ] `target="_blank"` always with `rel="noopener noreferrer"`.

## F. PII (code + claims)

- [ ] Every field in input's `pii_field_classification` rendered through its declared treatment helper (`MaskedField` / `RedactedField` / `AuditOnViewField` or repo equivalent).
- [ ] No PII in `console.*`, `window.onerror`, analytics events, error reporters.
- [ ] `audit-on-view` fields emit `pii.<field>.viewed` analytics event.
- [ ] Test fixtures use synthetic PII only (no real names / account numbers / government IDs).
- [ ] `security_review.pii_fields_handled` mirrors input classification exactly.

## G. Tokens / styling (code)

- [ ] No hex literals / `rgb()` / `hsl()` in source files (allowed only in token definition).
- [ ] No arbitrary Tailwind values (`[437px]`, `[#hex]`) for values reachable by a token.
- [ ] No inline `style={{color: ...}}` / `style={{padding: ...}}` for tokenized values.
- [ ] Component variants via `cva` / `tailwind-variants` (or repo equivalent), not string concat.
- [ ] If a token is missing, a `token_gap` uncertainty flag is present.

## H. Analytics / audit (code + claims)

- [ ] Every form submit / mutation / navigation / persisted-state toggle emits one event.
- [ ] Every emitted event type appears in `audit_events_emitted`.
- [ ] Event payload includes `{event_type, actor, action, target, page, timestamp}` with no PII in `decision_metadata`.
- [ ] Display-only Primitives emit nothing.

## I. Mutations / compensation (code + claims)

- [ ] Every mutation declares a `compensating_actions` entry (rollback to snapshot OR undo affordance OR idempotent retry).
- [ ] Submit button disabled while in-flight.
- [ ] `Idempotency-Key` header (or repo equivalent) sent on every mutation.
- [ ] Optimistic update `onMutate` paired with `onError` rollback.

## J. Tests (tests_under_review)

- [ ] Test file exists for every production file.
- [ ] Per-file coverage `>= test_coverage_target` claim is plausible vs visible test count / branch count.
- [ ] Tests query by `getByRole` / `getByLabel` (NOT `getByTestId` without `// reason:` comment).
- [ ] `userEvent` used for interactions (NOT `fireEvent`).
- [ ] MSW handlers used for network (NOT `global.fetch = jest.fn(...)`).
- [ ] No `findBy*` skipped via sleep / `setTimeout`.
- [ ] No `test.skip(...)` without named unblock condition.
- [ ] No real network calls (no `nock`, no `msw.bypass()`).
- [ ] No `process.env` secret reads in fixtures.
- [ ] No real PII in fixtures.

## K. Scope discipline (code)

- [ ] No npm module imported that is not in `package.json`.
- [ ] No edit to `codegen/` or `prisma/migrations` files.
- [ ] No reformatting / cleanup outside the changed files.
- [ ] Public component API not widened beyond design.

## L. Claims-vs-reality (used at step 6)

- [ ] Every `a11y_compliance` boolean claimed `true` has supporting code evidence.
- [ ] Every `security_review.xss_surfaces[]` entry has a matching `DOMPurify` call AND `// SAFE:` comment.
- [ ] `security_review.token_storage_strategy` matches the code (no contradicting `localStorage` writes).
- [ ] Every `security_review.pii_fields_handled[].field` rendered through declared helper.
- [ ] `security_review.csrf_protected: true` substantiated for every mutation.
- [ ] Every `audit_events_emitted` entry has a matching emit call.
- [ ] Every `compensating_actions[].trigger` has a matching rollback / undo.
- [ ] `state_ownership` map matches the code (e.g., `pagination: URL` → `useSearchParams` in code).
- [ ] `bundle_impact_estimate_kb` roughly matches sum of file sizes / import graph.
- [ ] Every `decision_metadata.pillar_choices` entry consistent with file content.
- [ ] Every Generate `uncertainty_flag` triaged: resolved-by-code / still-open / needs-escalation.

## Routing of NO answers (default severity, severity-guide.md is authoritative)

| Section with NO | Default severity |
|-----------------|------------------|
| D (a11y), E (XSS, token storage), F (PII), I (compensation), L (false claim on a11y/security/PII) | `P1` |
| B (type), C (state), G (tokens), H (analytics), J (tests), K (scope) | `P2` |
| A (pillar) | `P2` unless business logic in `Primitive` is heavy → `P1` |
| F (test fixtures cosmetic) | `P3` |
