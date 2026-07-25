# Security Checklist (Frontend Banking-Grade)

Applied at step 6 (during generation) AND step 8 (before emit) of `SKILL.md`.
Every item is YES/NO. A NO on any security item routes `human-queue` — security
NOs are never `loop_back` (the workflow does not retry security mistakes;
a human looks).

Source: extracted from
`treasury/crafting-frontend-code/references/security.md`. Source described
some patterns as "preferred default"; this file makes them blocking.

## A. XSS

- [ ] No `dangerouslySetInnerHTML` on user input or server HTML without `DOMPurify` sanitization AND a `// SAFE:` comment naming the threat model.
- [ ] No string concatenation into JSX that disables React's escaping.
- [ ] URL props (`href`, `src`, `formAction`) validated against scheme allowlist (`http`, `https`, `mailto`, `tel`). `javascript:` rejected.
- [ ] No `eval`, `new Function()`, or dynamic `import()` of user-controlled paths.
- [ ] No copy-pasted snippets from blog posts / Stack Overflow without code review.
- [ ] Third-party SVGs sanitized before rendering inline.

## B. CSRF

- [ ] For cookie-based auth: session cookie has `SameSite=Lax` (or `Strict`).
- [ ] Mutating fetches use one of: CSRF token in header, `credentials: 'include'` + same-site + `X-Requested-With`, OR token-in-header auth (Bearer). Verified per mutation.
- [ ] No state-changing `GET` requests — mutations use `POST` / `PUT` / `PATCH` / `DELETE`.

## C. Auth-token storage

- [ ] No auth token written to `localStorage`. NO.
- [ ] No auth token written to `sessionStorage`. NO.
- [ ] Session tokens stored in `HttpOnly` + `Secure` + `SameSite` cookie.
- [ ] Short-lived access tokens in memory (React state / module var). Lost on reload — that is correct.
- [ ] Persisted client state (Zustand `persist` middleware) does NOT include auth tokens.

## D. Content Security Policy (CSP)

- [ ] CSP starts from `default-src 'self'`; loosened only for required origins.
- [ ] `script-src` uses nonces or hashes; NO `'unsafe-inline'`, NO `'unsafe-eval'`.
- [ ] `frame-ancestors 'none'` (or specific origins) — prevents clickjacking.
- [ ] CSP violations reported via `report-uri` / `report-to`.
- [ ] CSP configured at the framework / proxy level — not in `<meta>` tags (which can be tampered).

## E. Dependency / supply chain

- [ ] No new npm dependency introduced beyond what the design names.
- [ ] If repo uses subresource integrity (`integrity=`) for CDN scripts, new scripts include it.
- [ ] No third-party script added without explicit design approval.
- [ ] No `postinstall` script in any added dependency without audit.

## F. Sensitive data in the client

- [ ] No secrets, API keys, internal IDs the user shouldn't see rendered into the DOM (even hidden / `display:none` / `aria-hidden`).
- [ ] Next.js env vars: only `NEXT_PUBLIC_*` reach the client; server-only env vars never leak.
- [ ] PII NEVER placed in URL (PII would land in browser history, referrer headers, analytics).
- [ ] Logs sent from the client scrub PII and tokens before transmission.

## G. PII handling

- [ ] Every field in input's `pii_field_classification` is rendered through its declared treatment helper (`mask` / `redact` / `audit-on-view`).
- [ ] PII fields NEVER logged to `console.*`, `window.onerror`, analytics events, or third-party error reporters.
- [ ] Audit-on-view fields emit an analytics event of type `pii.viewed.<field>` when displayed.
- [ ] Test fixtures use synthetic PII only (no real names, account numbers, government IDs).

## H. Cross-origin / framing

- [ ] `target="_blank"` ALWAYS paired with `rel="noopener noreferrer"`.
- [ ] `<iframe>` from third-party origins has `sandbox` attribute with minimal capabilities.
- [ ] `postMessage` listeners verify `event.origin` against an allowlist.

## I. Generated types (API contract)

- [ ] All API request / response types imported from `codegen/` (OpenAPI / GraphQL output).
- [ ] No hand-rolled `Response` type beyond a parser-local adapter (and that adapter is the only place an `as` cast appears).

## Routing of any NO

| Section with NO | Action |
|-----------------|--------|
| A (XSS), C (token storage), F (sensitive data), G (PII) | `human-queue` immediately. Do not emit. No retry. |
| B (CSRF), D (CSP), E (dependencies), H (cross-origin), I (generated types) | First NO: `loop_back` to design (security requirement was under-specified). Repeated NO after re-design: `human-queue`. |

## Populating `security_review` in output

| Output field | Maps to sections |
|--------------|------------------|
| `xss_surfaces` | A — empty array if no `dangerouslySetInnerHTML`; otherwise each entry MUST have a `mitigation` describing the `DOMPurify` call and the `// SAFE:` comment location |
| `csrf_protected` | B — `true` only when every mutation passes |
| `csp_compliant` | D — `true` only when the feature emits no inline scripts and references no `'unsafe-*'` |
| `token_storage_strategy` | C — `httpOnly-cookie` / `in-memory` / `n/a` (read-only display) |
| `pii_fields_handled` | G — every entry in input's `pii_field_classification` mirrored with the treatment helper actually used |
