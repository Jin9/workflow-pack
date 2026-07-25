# Implementation Rules (Frontend, Banking-Grade)

Applied at step 6 (Generate) and re-checked at step 8 (Self-review) of
`SKILL.md`. Synthesized from the frontend source skill's reference set
(`treasury/crafting-frontend-code/references/`) and made non-optional for
banking-grade. Where the source said "prefer" or "when relevant," this file
says "MUST" — banking-grade upgrades soft language on a11y, security, and
PII to blocking.

## Banking-grade frontend non-negotiables (12)

These are upgraded from "preferred" in the source to "blocking" here. Any
NO blocks emission and routes per `SKILL.md` Failure Modes table.

| # | Rule | Source posture | Banking-grade posture |
|---|------|----------------|------------------------|
| F1 | TypeScript `strict` — no `any` outside parsers / boundaries | "Risky pattern" (typescript.md) | Blocking. Any `any` outside a parser file = NO. |
| F2 | Generated API types only (OpenAPI / GraphQL codegen) — no hand-rolled `Response` types | "Prefer codegen" (typescript.md) | Blocking. Hand-roll allowed only in a parser-local adapter. |
| F3 | Component pillar separation (`Page` / `Feature` / `Primitive` / `Hook` / `Type` / `Util`); Primitive never owns business logic; leaf never fetches | "Reference model" (architecture.md) | Blocking. Pillar declared per file in `files_generated`. |
| F4 | Server state lives in the cache (TanStack Query or repo equivalent); never mirrored into client state | "Risky pattern" (state-data.md) | Blocking. `useEffect` that copies server state into client store = NO. |
| F5 | WCAG 2.1 AA minimum: keyboard, focus, semantic HTML, contrast, no `<div onClick>` | "Target" (accessibility.md) | Blocking. Below AA = `loop_back` to design. |
| F6 | No auth token in `localStorage` / `sessionStorage` | "Preferred default" (security.md) | Blocking. HttpOnly cookie OR in-memory only. |
| F7 | No `dangerouslySetInnerHTML` without `DOMPurify` + `// SAFE:` comment naming threat model | "High-risk pattern" (security.md) | Blocking. Missing sanitization or missing comment = NO. |
| F8 | URL props (`href`, `src`) validated against scheme allowlist; `target="_blank"` with `rel="noopener noreferrer"` | "High-risk pattern" (security.md) | Blocking. |
| F9 | PII rendered through declared treatment helper (`mask` / `redact` / `audit-on-view`); never logged | Implicit (security.md sensitive-data section) | Blocking. Every entry in `pii_field_classification` enforced. |
| F10 | Design-token-only styling — no hex literals, no arbitrary `[N px]`, no inline `style={{color: ...}}` for reachable tokens | "Risky pattern" (styling-design-system.md) | Blocking. Missing token → `uncertainty_flag` of kind `token_gap`. |
| F11 | Tests query by role / label; `data-testid` only when no other option; `userEvent` not `fireEvent`; MSW for network | "Convention" (testing.md) | Blocking. `data-testid` without justification = NO. |
| F12 | Every user-significant action emits an analytics event whose type appears in `audit_events_emitted` | Not in source | Blocking (banking-grade addition). |

## v2 augmentations (9)

Workflow-aware additions parallel to `implement-backend-feature` A1–A7, plus
two frontend-specific (A8 bundle, A9 token).

### A1. Analytics event shape (frontend's audit equivalent)

Every user-significant action (submit, navigate, toggle that persists state,
mutation) emits exactly one event:

```ts
type AnalyticsEvent = {
  event_type: string            // "loan.application.submitted"
  actor: { id: string; type: 'user' | 'system' }
  action: string                // "submit" | "click" | "navigate" | ...
  target: { kind: string; id?: string }
  page: string                  // route path
  timestamp: string             // ISO RFC3339
  trace_id?: string
  decision_metadata?: Record<string, unknown>  // never PII
}
```

`event_type` MUST appear in `audit_events_emitted` output. Display-only
components emit nothing.

### A2. Idempotency = form double-submit prevention + optimistic rollback

Every mutation path MUST:

- Disable the submit control while in-flight.
- Send a UUID-v4 request key (header `Idempotency-Key` or repo equivalent).
- For optimistic UI: snapshot → write → on error, roll back to snapshot →
  on settled, invalidate.
- Naturally idempotent paths (queries, navigation) skip but state so in
  `decision_metadata.pattern_choices`.

### A3. Compensating actions for client mutations

Every optimistic mutation declares a rollback entry in `compensating_actions`:

```json
{"trigger": "submit_loan_application_optimistic", "action": "rollback_to_snapshot", "timeout_seconds": 5}
```

User-visible undo affordances (toast with Undo, edit history) count as
additional compensation.

### A4. Client error classification

Every error path classifies at the type level:

| Class | UI behavior | Retry? | Log? |
|-------|-------------|--------|------|
| `client_input` | Inline field error via `aria-describedby` + `role=alert` | No | No (validation, not bug) |
| `client_state` | Toast + recover via undo / reset | No | Yes (warn) |
| `network` | Inline retry CTA + offline-aware copy | Yes (with backoff) | Yes (warn) |
| `server` | Inline error envelope + trace_id for support | No (idempotency unknown) | Yes (error) |

The class is part of the error type, not inferred at the boundary.

### A5. Test fixtures discipline

Tests MUST NOT: call real networks, read secrets from env, share state
across cases, snapshot whole components (snapshot small derived structures
only), `t.skip` without a named unblock condition. MSW handlers live in
`mocks/handlers/` and are reused in dev (`worker.start()`) and tests.

### A6. Convention discovery overrides defaults

Greenfield defaults (TanStack Query, Zustand, RHF+Zod, Tailwind, cva,
Vitest, Playwright) are defaults only when the repo has nothing. Repo
discovery wins. Divergence → `uncertainty_flag` of kind `convention_conflict`.

### A7. No silent dependency additions

No new npm module unless the design names it. Otherwise: halt and emit
`uncertainty_flag` of kind `dependency_addition`. Adding a dependency is a
design decision.

### A8. Bundle budget guard (new frontend SLA dimension)

Every Generate emits `bundle_impact_estimate_kb`. If input declares
`bundle_budget_kb` and the estimate exceeds it: emit `uncertainty_flag` of
kind `bundle_overrun` with the delta. Verdict deferred to the Review stage —
Generate does not unilaterally relax the budget.

### A9. Token-gap discipline

If the design references a color / spacing / radius / shadow / type / motion
value that does not exist as a token in the repo: emit `uncertainty_flag` of
kind `token_gap` naming the missing token. Do NOT inline the literal value
to ship the feature. Token gap is a design-system decision.

## Decision matrix (quick lookup)

| Situation | Action |
|-----------|--------|
| Design has `TBD` on a11y / security / PII / token storage | Step 1: `loop_back` to design |
| Target path missing | Step 2: `loop_back` to design |
| Repo convention conflicts with design pattern | Step 3: prefer repo, emit `uncertainty_flag` |
| Cannot meet WCAG AA | Step 6 a11y: `loop_back` to design (BLOCKER) |
| XSS / CSRF / token-storage / PII-leak surface introduced without mitigation | Step 8: `human-queue` (no retry) |
| Bundle estimate over budget | Step 9: `uncertainty_flag`, verdict deferred to Review |
| Test coverage below `test_coverage_target` | Step 7: `loop_back` (over-scoped) |
| Token missing for declared value | Step 6: `uncertainty_flag` of kind `token_gap` |
