# A11y Checklist (WCAG 2.1 AA Banking-Grade)

Applied at step 6 (during generation) AND step 8 (before emit) of `SKILL.md`.
Every item is YES/NO. A NO on any item blocks emission and routes
`loop_back` to design (a11y is a banking-grade BLOCKER, not a warning).

Source: extracted from
`treasury/crafting-frontend-code/references/accessibility.md`. Source
described a11y as "target"; this file makes every item blocking for
banking-grade regulatory compliance.

## A. Semantic HTML before ARIA

- [ ] Every clickable thing is a `<button>` (action) or `<a href>` (navigation). NO `<div onClick>`.
- [ ] Every input has a `<label htmlFor>` or wrapping `<label>`. Placeholder is NEVER the only label.
- [ ] Page uses `<nav>` / `<main>` / `<header>` / `<footer>` / `<section>` landmarks where applicable.
- [ ] Headings are in order (`<h1>` → `<h2>` → `<h3>`). Exactly one `<h1>` per page.
- [ ] List-shaped content uses `<ul>` / `<ol>` / `<li>`, not divs.
- [ ] ARIA used only as fallback when semantics don't exist. Wrong ARIA is worse than no ARIA.

## B. Keyboard

- [ ] Tab order matches visual order. NO `tabindex > 0`.
- [ ] Custom widgets follow WAI-ARIA Authoring Practices keyboard contract (menu / listbox / dialog / tabs).
- [ ] `Esc` closes overlays. `Enter` / `Space` activates buttons.
- [ ] No keyboard traps — modals trap correctly while open, release on close.
- [ ] Skip-to-content link present on Page-pillar components.

## C. Forms

- [ ] Every input has an associated label (`<label htmlFor>` or wrapping).
- [ ] Required fields marked in label text — NOT by color or `*` alone.
- [ ] Validation errors programmatically associated via `aria-describedby` AND announced via `role="alert"` (or live region).
- [ ] Related fields grouped with `<fieldset>` + `<legend>` where applicable.
- [ ] Field-level error survives keyboard navigation — not just visible on blur.

## D. Focus management

- [ ] After route change, focus moves to the page heading or main content.
- [ ] Modal opens → focus first interactive element. Modal closes → focus returns to trigger.
- [ ] Background `inert` (or `aria-hidden`) while modal is open.
- [ ] Visible focus ring on every interactive element. Custom focus styles MUST replace, never remove.
- [ ] No auto-focus on a deep field on page load (steals focus from screen readers).

## E. Color & contrast

- [ ] Text contrast `>= 4.5:1` (normal text); `>= 3:1` (large text or UI components).
- [ ] State NEVER conveyed by color alone — paired with icon, text, or pattern (error red + icon + message).
- [ ] Tested under simulated color-blindness (Chrome DevTools or equivalent).
- [ ] Focus ring contrast `>= 3:1` against adjacent background.

## F. Motion & preferences

- [ ] Respects `prefers-reduced-motion`: disable / shorten transforms, parallax, autoplay.
- [ ] Respects `prefers-color-scheme` for theming (if the repo supports themes).
- [ ] No autoplay video / audio without user gesture.
- [ ] No flashing content >= 3 times per second (seizure risk).

## G. Screen reader

- [ ] All images have `alt` text — decorative images use `alt=""`, informative ones describe content.
- [ ] Icon-only buttons have `aria-label` describing the action.
- [ ] Toast / transient notifications paired with `role="alert"` or `role="status"` (screen readers may miss visual-only toasts).
- [ ] Dynamic content updates announced via live regions (`aria-live="polite"` for status, `assertive` only for errors).
- [ ] Manual smoke test plan included: NVDA / VoiceOver walkthrough for critical flows.

## H. Test gates

- [ ] `@axe-core/react` runs in dev (logs violations to console).
- [ ] `@axe-core/playwright` runs in CI on key routes for Page-pillar components.
- [ ] Component test asserts at least one `getByRole` / `getByLabel` — never only `getByTestId`.

## Routing of any NO

| Section with NO | Action |
|-----------------|--------|
| A (semantic), B (keyboard), C (forms), D (focus), E (contrast), F (motion), G (screen reader) | `loop_back` to design — a11y is a blocker, not a warning. Document the gap in the `uncertainty_flag.note`. |
| H (test gates) | If the only NO is "axe not run yet," document in `decision_metadata.pattern_choices` and proceed; if the test infrastructure is missing entirely, `uncertainty_flag` of kind `convention_conflict`. |

## Forbidden patterns (auto-NO)

- `<div onClick>` for clickable things.
- Removing focus outline without replacing it.
- Placeholder as the only label.
- `aria-label` on a `<div>` that pretends to be a button.
- Auto-focusing a deep field on page load.
- `tabindex > 0` (hijacks tab order).
- Toast-only error messaging without inline `role="alert"`.
- Color-only state conveyance.
- Carousels / accordions without keyboard contract.
- `<img>` without `alt` (use `alt=""` for decorative).

## Populating `a11y_compliance` in output

Every NO not blocking sets the corresponding boolean to `false` in the
output's nested `a11y_compliance` object — the Review stage will catch the
false-claim mismatch.

| Output field | Maps to sections |
|--------------|------------------|
| `keyboard_navigable` | B |
| `screen_reader_tested` | G |
| `color_contrast_verified` | E |
| `focus_management_implemented` | D |
| `axe_clean` | H |
| `wcag_level` | Aggregate (A-G all pass → `AA`; design declares `AAA` and all-stricter checks pass → `AAA`) |
