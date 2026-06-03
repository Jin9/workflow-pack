# Review Rubric (Frontend)

The canonical scan list applied at step 4 of `SKILL.md`. Each item is the
same banking-grade rule the Generate stage applies — re-cast as an
*adversarial question* the reviewer asks of the code. Mapping is 1:1:
every rule a Generate stage must follow, the Review stage must verify.

Framing matters:
- Generate's `self-review-checklist.md`: "Did I do X?" (first-person)
- This file: "Show me where X is. Cite the line." (third-person, adversarial)

When a question's answer is "no" or "not visible in the code," emit a
finding. Severity is assigned at step 7 using `severity-guide.md`.

## Non-negotiable questions (F1–F12)

Source: `implement-frontend-feature/references/implementation-rules.md`
§ Banking-grade frontend non-negotiables.

| # | Rule | Adversarial scan question |
|---|------|---------------------------|
| F1 | TypeScript strict — no `any` outside parsers | Does any file outside a `parser*` / `codegen/` / `mocks/` path contain the `any` keyword as a type position (not as part of `as const`, `unknown` narrow, identifier name)? Cite the file:line. |
| F2 | Generated API types only | Does any file define a type whose shape mirrors an API request/response (matches `codegen/` types) instead of importing from `codegen/`? Cite the duplicate. |
| F3 | Pillar separation | Does any file with `component_pillar: Primitive` import from a fetching layer (TanStack Query, axios, fetch hook, repo equivalent) or from a `Feature` / `Page` file? Cite the import. |
| F4 | Server state never mirrored | Is there a `useEffect` that reads from a query cache and writes the result into a `useState`, Zustand store, or context? Cite the offending effect. |
| F5 | WCAG 2.1 AA minimum | For each Page / Feature / Primitive file: are there any forbidden patterns from `a11y-checklist.md` (`<div onClick>`, placeholder-as-label, `tabindex > 0`, removed focus outline, color-only state)? Cite the violation. |
| F6 | No `localStorage` auth tokens | Does any file call `localStorage.setItem(...)` or `sessionStorage.setItem(...)` with a key matching `/token|jwt|access|refresh|session|auth|bearer/i`? Cite the call. |
| F7 | `dangerouslySetInnerHTML` requires DOMPurify + `// SAFE:` | For every `dangerouslySetInnerHTML` use: is there a `DOMPurify.sanitize(...)` on the same value AND a `// SAFE:` comment naming the threat model? Cite the unsafe usage. |
| F8 | URL props scheme-allowlist + `rel=noopener` | For every `href` / `src` / `formAction` prop sourced from a variable: is the value validated against an allowlist (`http`, `https`, `mailto`, `tel`)? For every `target="_blank"`: is `rel="noopener noreferrer"` present? Cite the gap. |
| F9 | Per-field PII treatment helper | For every entry in input's `pii_field_classification`: is the field rendered through its declared helper (`MaskedField`, `RedactedField`, `AuditOnViewField`, or repo equivalent)? Cite a raw render of PII. |
| F10 | Design-token-only styling | Does any file contain a hex literal (`#[0-9a-fA-F]{3,8}`), `rgb(...)`, `hsl(...)`, an arbitrary Tailwind value (`\\[N(px|em|rem)\\]`), or an inline `style={{color: ...}}` / `style={{padding: ...}}` for a tokenized value? Cite the literal. |
| F11 | Tests by role / label, `userEvent`, MSW | Do any test files use `getByTestId` / `queryByTestId` without a `// reason:` justification comment? Do any tests use `fireEvent` instead of `userEvent` for typing / clicking? Do any tests call `global.fetch = jest.fn(...)` instead of using MSW? Cite the offender. |
| F12 | Analytics event on user-significant actions | For every form submit / mutation / navigation handler / persisted-state toggle: is an analytics event emitted whose type appears in `audit_events_emitted`? Cite the missing emit OR the mismatch. |

## v2 augmentation questions (A1–A9)

Source: `implement-frontend-feature/references/implementation-rules.md` § v2 augmentations.

| # | Augmentation | Adversarial scan question |
|---|--------------|---------------------------|
| A1 | Analytics event shape | For every analytics emit: does the payload include `{event_type, actor, action, target, page, timestamp}` with no PII in `decision_metadata`? Cite a malformed or PII-leaking event. |
| A2 | Double-submit prevention + idempotency key | For every form / mutation: is the submit control disabled while `isSubmitting` / `isPending` is true? Is an `Idempotency-Key` (or repo equivalent) header set on the mutation? Cite the missing disable or missing key. |
| A3 | Optimistic UI compensation | For every `onMutate` with `setQueryData`: is there an `onError` that rolls back to the snapshot? Cite the missing rollback. |
| A4 | Client error classification | For every error path in a handler / hook: does the error carry a class (`client_input | client_state | network | server`) at the type level, not inferred at the UI edge? Cite the unclassified error. |
| A5 | Test fixtures discipline | Do any test files call real networks (no MSW), read secrets from `process.env`, share state between cases, snapshot whole components, or `test.skip` without a named unblock condition? Cite the offender. |
| A6 | Convention discovery overrides defaults | If the code uses a greenfield default (e.g., Zustand) but the repo uses something else (e.g., Redux Toolkit elsewhere): did Generate emit a `convention_conflict` uncertainty flag? Cite the divergence the flag should have named. |
| A7 | No silent dependency additions | Does any emitted file import a package not in `package.json`? Did Generate emit a `dependency_addition` uncertainty flag for it? Cite the import. |
| A8 | Bundle budget guard | If input has `bundle_budget_kb` and `bundle_impact_estimate_kb > bundle_budget_kb`: is a `bundle_overrun` uncertainty flag present? Cite the missing flag. |
| A9 | Token-gap discipline | If the code inlines a literal that should be a token (caught by F10): is a `token_gap` uncertainty flag present naming the missing token? If both — inline literal AND no flag — emit a finding for both F10 and A9. |

## Workflow-contract questions (C1–C5)

In addition to the rules, the Review stage verifies the Generate stage's
contract-level claims. These exist because the workflow exists.

| # | Contract item | Adversarial scan question |
|---|---------------|---------------------------|
| C1 | Companion tests exist | Is there a test file for every production file (matched by name suffix or sibling-directory convention)? Cite the unaccompanied production file. |
| C2 | Per-file coverage claim plausibility | For each `tests_generated[].coverage_pct`: does the test file appear to exercise the branches required (test count vs branch count rough check)? Cite an obviously thin test. |
| C3 | `a11y_compliance` substantiation | For each boolean claimed `true`: find code evidence — `focus_management_implemented` → a `useEffect` calling `.focus()` on route change / modal open; `axe_clean` → axe import in dev or test; `keyboard_navigable` → no `tabindex > 0` and no `<div onClick>` (already covered by F5 — this is the cross-check). False claim = `P1`. |
| C4 | `security_review` substantiation | Each `xss_surfaces[]` entry → matching `DOMPurify.sanitize` + `// SAFE:` comment in the cited file. `token_storage_strategy: httpOnly-cookie` → no `localStorage.setItem("auth*"...)` anywhere. `pii_fields_handled` mirrored in code. False claim = `P1`. |
| C5 | `state_ownership` coverage | Every state piece named in the design appears in the map; map values match the code (e.g., `pagination: URL` means `useSearchParams` is in the code, not `useState`). Mismatch = `P2`. |

## Out-of-scope by design

This skill does NOT cover:

- Full OWASP Top 10 walk — `reviewing-software-security` scope.
- Visual / pixel regression — separate visual-diff stage.
- Web Vitals / Lighthouse performance optimization — `analyze-frontend-performance`.
- Architectural / boundary critique — the design stage's job; this stage
  takes the design as given.
- Backend code — `review-backend-code`.

If a reviewer spots an issue outside scope, surface it as an
`uncertainty_flag` of kind `out_of_scope_observation`, not a finding.
