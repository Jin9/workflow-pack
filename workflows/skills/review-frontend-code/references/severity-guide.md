# Severity Guide & Verdict Matrix (Frontend)

Applied at step 7 of `SKILL.md` to classify findings and compute the verdict.
Banking-grade flavored: every routing decision is deterministic, verdict is
a function of findings, not the other way around.

Source: extracted from `review-backend-code/references/severity-guide.md`
(shape) and re-categorized for frontend-specific blockers (a11y, XSS, token
storage, PII, CSRF). Confidence + standards rules preserved verbatim.

## Severity definitions

### `P1` — block

Banking-grade non-negotiables. A `P1` ALWAYS routes to `human-queue` —
never `loop_back`, never `approve`. The Generate stage cannot fix `P1`
in another iteration without a person looking.

Categories inherently `P1`:

- **A11y blocker** — `a11y_compliance.wcag_level` below `AA`, any
  `a11y_compliance` boolean falsely claimed `true`, `<div onClick>`,
  placeholder-as-label, `tabindex > 0`, removed focus outline, color-only
  state, `<img>` without `alt`. Regulatory.
- **XSS** — `dangerouslySetInnerHTML` without `DOMPurify` + `// SAFE:`
  comment, `<a href={userInput}>` without scheme allowlist, `eval` /
  `new Function`, dynamic `import()` of user-controlled path, raw third-
  party SVG inline.
- **Token storage** — auth token written to `localStorage` /
  `sessionStorage`. Any match of `setItem(key, value)` where the key
  matches `/token|jwt|access|refresh|session|auth|bearer/i`.
- **PII leak** — PII field rendered without its declared treatment
  helper; PII in `console.*`, `window.onerror`, analytics event payload,
  third-party error reporter, or URL.
- **CSRF gap** — mutating fetch missing CSRF token / `credentials: 'include'`
  / `X-Requested-With`; state-changing `GET` request.
- **Missing mutation compensation** — `onMutate` with `setQueryData` and
  no `onError` rollback.
- **Business logic in Primitive** — Primitive pillar file imports from
  fetching layer or contains business rules. Boundary violation
  audit-blocking.
- **False claim on a11y / security / PII** — Generate said `true` /
  declared; code says otherwise.

### `P2` — fix before merge

Correctness or discipline issues the next Generate iteration can address.
Routes to `loop_back` (target = `implement`).

Categories typically `P2`:

- `any` outside parser / boundary code.
- `as` cast outside parsers / boundaries.
- Hand-rolled API type duplicating `codegen/` shape.
- Server state mirrored into client store / `useState`.
- URL-shaped state in `useState` instead of search params.
- Form state mirrored in both RHF and `useState`.
- Missing test for a declared interaction.
- Per-file coverage claim implausibly high vs visible test depth.
- `state_ownership` missing an entry for a state piece in the design.
- Pillar mismatch (file declared `Primitive` but actually fetches —
  border case; if business logic is heavy, escalate to `P1`).
- Missing `convention_conflict` flag where a divergence is visible.
- Missing `Idempotency-Key` header on a mutation.
- Hand-rolled component variant string concat instead of `cva` /
  `tailwind-variants` (when repo uses them).

### `P3` — note, don't block

Style, scope, future-improvement items. Does NOT block `approve`.

Categories typically `P3`:

- Naming inconsistency that doesn't break discovery.
- `useMemo` where premature.
- Test could be table-driven but isn't (correctness unaffected).
- Plausible bundle estimate that exceeds budget by < 10% (route to design
  via flag, but no finding).
- Adjacent issue noticed in a non-reviewed file (out_of_scope_observation
  flag instead).
- Comment / docstring style.

## Confidence

Discipline borrowed from `reviewing-software-security`:

- **High** — file:line cited, behavior reproducible from the code alone.
- **Medium** — pattern is present but exploit / failure requires context
  the reviewer doesn't have.
- **Low** — suspicion only; reviewer cannot cite file:line confidently.

**Hard rule**: never publish `P1` / `P2` at `Low` confidence without an
explicit `[needs verification]` tag in `evidence`. Do not fabricate
file:line references, ARIA attributes, CWE numbers, library APIs, or
standards identifiers — withhold instead.

When confidence is `Low`, drop severity by one tier (`P1` → `P2`,
`P2` → `P3`) before applying the verdict matrix — UNLESS the area is a11y
or token storage, which stay at declared severity even at `Low`
(regulatory / catastrophic).

## Verdict matrix

Applied after every finding has a severity. Verdict is the highest
escalation any finding produces, with one extra check for unsubstantiated
claims.

| Condition | Verdict | `loop_back_target_stage` |
|-----------|---------|--------------------------|
| Any `P1` finding | `human-queue` | null |
| `claims_unverified` non-empty (and no `P1`) | `loop_back` | `implement` |
| Any `P2` finding (and no `P1` / no unverified claims) | `loop_back` | `implement` |
| `uncertainty_flag` of kind `design_ambiguity` raised in step 2 | `loop_back` | `design` (overrides `implement` routing) |
| `uncertainty_flag` of kind `bundle_overrun` from Generate, no other findings | `loop_back` | `design` (budget is a design decision) |
| `uncertainty_flag` of kind `token_gap` from Generate, no other findings | `loop_back` | `design` (token system is a design decision) |
| Only `P3` findings (no `P1` / no `P2` / no unverified claims / no design-routing flag) | `approve` | null |
| No findings at all | `approve` | null |

Notes:

- `design_ambiguity` / `bundle_overrun` / `token_gap` flags route to
  `design` — treating the symptom at `implement` won't help.
- `human-queue` from `P1` is final for this stage. Workflow policy
  decides whether the human can override.
- `approve` with `P3` findings still emits them — next stage receives
  them as a notes list, not as blockers.

## Standards identifiers

When a finding maps to a published standard, cite it in
`finding.standards_ref`. Withhold (omit the field) rather than guess.

Acceptable identifier shapes:

- `CWE-###` (CWE-79 XSS, CWE-352 CSRF, CWE-922 insecure storage are common
  for frontend)
- `OWASP A0#:2021` (A03 Injection, A07 Auth Failures)
- `OWASP API#:2023`
- `ASVS V#.#.#` (V5 input validation, V14 config)
- `WCAG #.#.#` (e.g., `WCAG 2.1.1` keyboard, `WCAG 1.4.3` contrast minimum)
- `NIST SSDF PW.#.#`

If unsure of the exact identifier, omit the field. Do NOT invent.
