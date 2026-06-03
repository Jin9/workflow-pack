# State Management Rules

Applied at step 5 (plan) and step 6 (generate) of `SKILL.md`. Decision tree
that maps every state piece in the design to exactly one owner. The output's
`state_ownership` map MUST cover every state piece named in the design.

Source: extracted from
`treasury/crafting-frontend-code/references/state-data.md`. Greenfield
defaults below are TanStack Query / Zustand / RHF + Zod — but **repo
discovery wins**. If the repo uses Redux Toolkit, Jotai, Apollo, Formik,
or anything else, mirror it and flag the divergence only if the design
contradicts the repo.

## State ownership decision tree

For each state piece in the design, walk this tree top-down. Stop at the
first match.

```
1. Does the value come from a server / API?
   YES → server state (cache layer — TanStack Query or repo equivalent)
   NO  → next question

2. Is the value part of the URL (filter, sort, page, tab, search, route param)?
   YES → URL state (search params / router hook — never window.location)
   NO  → next question

3. Is the value part of a form draft (in-progress user input)?
   YES → form state (RHF + Zod or repo equivalent)
   NO  → next question

4. Does the value need to survive across pages / components within one session?
   YES → client store (Zustand / Redux / repo equivalent) — domain-sliced
   NO  → next question

5. Is the value computable from props or other state?
   YES → derived (compute on render; useMemo only when proven needed)
   NO  → next question

6. Otherwise: local component state (useState)
```

## Per-owner rules

### Server state (TanStack Query / repo equivalent)

- Query key = stable, serializable identity. Convention: `[domain, id, params]`.
- `staleTime` per query type: read-heavy / cheap = 5–30s; expensive / static = minutes–hours.
- `gcTime` > `staleTime`; default 5 min is usually fine.
- Use `select` for derived data — keeps cache canonical, components get the slice.
- Mutations: invalidate by key prefix OR `setQueryData` for optimistic patches.
- One client per app via `QueryClientProvider`. SSR: `dehydrate` / `hydrate`.
- **Banking-grade**: mutations send `Idempotency-Key` header; UI disables submit while in-flight.

### URL state

- Filters, sort, pagination, tabs, search → URL params. Shareable, bookmarkable, back-button-friendly.
- Use the router's hook (`useSearchParams` Next/Remix, `nuqs` for typed params). NEVER `window.location` inside components.
- PII NEVER in URL — landed in history, referrers, analytics.

### Form state (RHF + Zod / repo equivalent)

```ts
const schema = z.object({ email: z.string().email(), amount: z.number().positive() })
type FormValues = z.infer<typeof schema>

const { register, handleSubmit, formState } = useForm<FormValues>({
  resolver: zodResolver(schema),
})
```

- Single source of truth = Zod schema. Derive types via `z.infer`.
- `Controller` only for fields RHF can't `register` directly.
- Async submit handler. Surface server errors via `setError`.
- Re-use the schema server-side for end-to-end validation.
- **Banking-grade**: submit button disabled while `formState.isSubmitting` is true (double-submit prevention).

### Client store (Zustand / repo equivalent)

```ts
const useStore = create<State>()((set) => ({
  filters: { status: 'all' },
  setStatus: (s) => set((st) => ({ filters: { ...st.filters, status: s } })),
}))
```

- Selectors with shallow compare: `useStore(s => s.filters.status)`.
- Slice large stores by domain.
- `persist` middleware only for truly persistent values (filters, theme).
  NEVER persist auth tokens or PII.

When to escalate to Redux Toolkit: deep undo / redo, time-travel debug,
strict pattern + middleware ecosystem requirement.

### Context

- Use for: theme, auth identity, locale, feature flags. Read often, written rarely.
- DO NOT use for high-frequency updates (cursor, scroll, form draft). Causes whole-subtree re-renders.

### Local (`useState`)

- Anything that fits in one component and doesn't need to round-trip via URL.
- If two siblings need the same `useState`, lift to nearest common ancestor OR move to a store / URL.

### Derived

- `useMemo` only when profiling shows a real cost. Premature memoization hurts readability.
- Compute on render is fine for cheap values.

## Mutations + optimistic updates

Standard pattern:

```
onMutate:
  1. Snapshot current cache value via getQueryData
  2. Write optimistic value via setQueryData
  3. Return snapshot in context

onError:
  1. Roll back to snapshot via setQueryData

onSettled:
  1. Invalidate by key prefix to reconcile with server
```

For list mutations: invalidate the list query AND the detail query.

**Banking-grade**: every optimistic mutation declares a `compensating_actions`
entry in output:

```json
{"trigger": "submit_loan_application_optimistic", "action": "rollback_to_snapshot", "timeout_seconds": 5}
```

## Forbidden patterns (auto-NO)

- Server data stored in Zustand / Redux (mirroring).
- `useEffect` syncing server data into local / client state — use the cache.
- Reading URL via `window.location` in components — use router hook.
- Form state mirrored in both RHF and `useState` — pick one.
- Mutating Zustand state directly — always via setter.
- `useState` for state that should round-trip via URL.
- `persist` middleware containing auth tokens or PII.
- Context for cursor / scroll / form draft (high-frequency).

## Populating `state_ownership` in output

For every state piece named in the design, emit one entry:

```json
{
  "filters_status": "URL",
  "current_user": "server",
  "form_draft": "form",
  "is_modal_open": "local",
  "theme": "client",
  "formatted_amount": "derived"
}
```

The Review stage cross-checks that every state piece named in the design
appears in this map — missing entries are a `claims_unverified` failure.
