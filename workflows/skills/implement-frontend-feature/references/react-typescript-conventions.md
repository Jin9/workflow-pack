# React + TypeScript Conventions (Banking-Grade Generate Stage)

Conventions for code emitted by step 6 of `SKILL.md`. Source: extracted from
`treasury/crafting-frontend-code/references/architecture.md` and
`typescript.md`. Banking-flavored: stricter on types, pillars, and tests.

**Discovery overrides defaults.** If the repo already follows a different
convention (e.g., Redux Toolkit instead of Zustand, a custom error envelope,
a project-specific logger), mirror it and emit a `convention_conflict`
uncertainty flag so reflection can update the template.

## Component pillars

Every emitted file MUST declare its pillar in `files_generated[].component_pillar`.

| Pillar | Owns | Forbidden |
|--------|------|-----------|
| `Page` | Route-level data fetching, error + loading + empty boundaries, layout shell, SEO meta | Direct presentation of primitives — compose Features |
| `Feature` | Interaction state, form orchestration, business UI logic, mutations | Cross-feature imports of internal state |
| `Primitive` | Pure presentation + a11y (Button, Input, Dialog) | Fetching, business rules, app-specific copy |
| `Hook` | Side effects (network, storage, subscriptions, timers) | JSX |
| `Type` | Pure type declarations, branded types, schemas | Runtime values beyond `satisfies` literals |
| `Util` | Pure functions (parsers, formatters, validators) | I/O, React imports |

Rules:
- Primitives never import from Features or Pages.
- Features import freely from Primitives, Hooks, Types, Utils.
- Pages compose Features and own only the route's concerns (fetch / boundaries / layout).
- Leaves never fetch.

## Data flow

- Top-down props for pure presentation.
- Hooks for side-effects and data dependencies.
- Events bubble up via callbacks. Avoid prop-drilling > 2 levels — use
  context, composition, or a store.
- Context for transient cross-cutting (theme, auth identity). NEVER for
  high-frequency mutable state (cursor, scroll, form draft).

## Composition

- Composition (children, slots) over configuration props.
- Compound components (`<Tabs><Tabs.List/><Tabs.Panel/></Tabs>`) for related parts.
- Headless primitives (Radix, React Aria) + repo's styling — do NOT
  re-invent menu / dialog / popover a11y.
- Render props or hooks over HOCs.

## Rendering model

| Need | Pick |
|------|------|
| SEO matters, content per-request | SSR |
| SEO matters, stable content | SSG / ISR |
| Auth-gated app, no SEO | CSR (or RSC with client islands) |
| Server-only data, no interactivity | RSC |
| Highly interactive island in SSR/SSG | Client Component |

Rule: cheapest model that meets SEO / freshness / interactivity. Do NOT
introduce SSR/RSC to an existing CSR surface without a migration reason.

## TypeScript

### Compiler defaults (greenfield only — repo's `tsconfig.json` wins)

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "verbatimModuleSyntax": true,
    "moduleResolution": "bundler"
  }
}
```

### Type-first patterns

- `type` for data shapes, unions, mapped / conditional types.
- `interface` for extensible contracts (component props, plugin shapes).
- Explicit return types on exported functions and React components.
- `unknown` not `any` when narrowing is needed.
- `satisfies` not `as` for literal config:
  ```ts
  const routes = { home: '/', settings: '/settings' } satisfies Record<string, string>
  ```

### Discriminated unions for state machines

```ts
type FetchState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error }

function assertNever(x: never): never { throw new Error('unreachable') }

switch (state.status) {
  case 'idle':    return null
  case 'loading': return <Spinner/>
  case 'success': return <View data={state.data}/>
  case 'error':   return <ErrorView error={state.error}/>
  default: assertNever(state)
}
```

### Branded types at boundaries

```ts
type Brand<T, B> = T & { readonly __brand: B }
type UserId = Brand<string, 'UserId'>
const asUserId = (s: string) => s as UserId
```

Brand at parsers / API layer; body of code stays clean.

### Generics

- Add only when the consumer benefits.
- Constrain: `<T extends { id: string }>`, not bare `<T>`.
- Default type params for ergonomic call sites: `<T = unknown>`.

### Forbidden (banking-grade upgrade)

- `any` outside parser / boundary code.
- `as` casts outside parsers / boundaries.
- `// @ts-ignore` without a comment naming the gap and a follow-up TODO.
- Re-declaring types that already exist in codegen output.
- `Function` or `object` as types — use specific signatures.
- Optional chaining masking a real type bug (`obj?.field` when `obj` is non-nullable).

## Testing conventions

- Test behavior, not implementation. Query by role / label.
- `data-testid` only when no semantic alternative exists, with a comment.
- `userEvent` (not `fireEvent`) — simulates real user flow.
- One assertion per behavior. Multiple `expect`s per `it` are fine if they
  test one behavior together.
- MSW for network. Same handlers in dev and tests.
- Don't snapshot whole components — snapshot small derived structures.
- `findBy*` / `waitFor` — never sleep / timing-based assertions.
- No `useState` / React-internals mocking.

| Layer | Tool | Tests |
|-------|------|-------|
| Unit | Vitest | Pure functions, hooks, reducers |
| Component | Vitest + RTL | One component, mocked deps |
| Integration | Vitest + RTL + MSW | Feature, real network mocks |
| E2E | Playwright | Real browser, real / seeded backend |
| Visual | Playwright + Percy / Chromatic / Argos | Pixel diffs (stable states only) |
| A11y | `@axe-core/react` (dev) + `@axe-core/playwright` (CI) | Key routes |

## Risky patterns to avoid

- Business logic in `Primitive`.
- Fetching in leaf components.
- Mirroring server state into a client store.
- Context for high-frequency updates.
- "God hook" doing fetch + form + transform + side-effects.
- Page components with large repeated JSX blocks hiding feature boundaries.
- `useState` for state that should round-trip via URL.
