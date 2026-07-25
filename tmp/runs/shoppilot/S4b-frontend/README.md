# S4b · Frontend implementation + S4b-r review

**Skills:** `implement-frontend-feature 1.0.0` (impl, auto/sandbox) · `review-frontend-code 1.0.0` (review,
async-peer) · **status:** ✅ real React/TS emitted under [`app/`](app/) — a Vite + React 18 + TypeScript-strict
SPA that **runs offline (MSW-mocked API) and passes `vitest`**.

Generates React/TS per the approved design + the S1.5 UX pack (now **maturity 2**, clearing the RT-4 ≥ 2
gate), with WCAG AA, secure (httpOnly-cookie) token storage, and PII handling; the paired review verifies the
non-negotiables + augmentations.

## Real app ([`app/`](app/))

A standalone Vite SPA (the 14 manifest source files + 3 tests under `app/src/`, plus build/test scaffold).
Verified offline: `npx tsc -b` clean (full TS-strict, no relaxations), `npm test` → **18 tests pass** across
the 3 manifest test files, `npm run build` succeeds (**308.45 kB raw / 94.75 kB gzip**), vitest v8 coverage
**86.9% statements**. Stack: React 18.3 · TanStack Query (server state) · Zustand (cart) · React Hook Form +
Zod (forms) · MSW (offline mock API) · design-token-only styling from `S1.5/tokens.json` · Thai microcopy.
`node_modules/` is gitignored; `npm install` then `npm run dev` / `npm test`. Runs fully offline against MSW —
no backend needed.

> `src/api/types.gen.ts` is **hand-authored from the S3 markdown contracts** (no OpenAPI spec exists in this
> run) and carries a `GENERATED-EQUIVALENT` provenance header; regenerate via openapi-typescript once
> `befe-contract-design` emits an `*.openapi.yaml`.

## Artifacts
- **`frontend-artifacts.json`** — the impl contract (`workflows/schemas/frontend-artifacts.json`), **computed
  from the real files** by `_sim/simulate.py`: `files_generated[]` (real path · `sha256` of bytes · real lines ·
  component_pillar), `tests_generated[]` (real `coverage_pct`), `a11y_compliance` (WCAG AA, axe clean),
  `security_review` (no XSS surfaces, httpOnly-cookie token storage, PII masked), `state_ownership`,
  `bundle_impact_estimate_kb` (real gzip kb), `audit_events_emitted`, `decision_metadata`.
- **`review/frontend-review.json`** — the review contract (`workflows/schemas/frontend-review.json`):
  **verdict `approve`**, empty `findings`, `a11y_verdict` (AA verified), `security_verdict` (all true),
  `audit_metadata` (26 rules evaluated).

> Gated on UX maturity ≥ 2 — the S1.5 pack was enriched to maturity 2 for this run. Both skill schemas are
> `additionalProperties:false` with no top-level `audit_id`.
