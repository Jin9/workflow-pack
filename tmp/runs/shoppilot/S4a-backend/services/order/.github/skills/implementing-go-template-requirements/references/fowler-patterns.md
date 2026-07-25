# Fowler patterns — cross-walk and discipline

The scaffold's file-prefix conventions are Fowler's patterns in disguise. This page names them, shows the canonical examples from `go-template/app/auth/`, and gives the refactoring discipline to apply when writing or extending **handler** and **consumer** code.

**Scope**: this reference applies to `handler_<action>.go`, `consumer_<action>.go`, `service_<action>.go`, and the **method signatures** exported from `access/storage_*.go` / `cache_*.go` / `client_*.go` (the public interface — Long Parameter List and Too Many Returns smells apply here). It does **NOT** apply to the adapter **internals** of those access files — the SDK-marshalling code stays terse on purpose.

---

## 1. Pattern → file mapping

| Fowler pattern (PoEAA / Refactoring) | File in this scaffold | Canonical example |
|---|---|---|
| **Repository** | `app/<domain>/access/storage_<dep>.go` | `app/auth/access/storage_member.go` |
| **Cache** | `app/<domain>/access/cache_<dep>.go` | `app/<domain>/access/cache_<dep>.go` |
| **Gateway** | `app/<domain>/access/client_<dep>.go` | `app/auth/access/client_google.go` |
| **Service Layer** (private method on `*handler`) | `app/<domain>/service_<action>.go` | `app/auth/service_authenticate_google.go` |
| **Domain Model** | The `<Model>` struct co-located in `storage_<dep>.go` | `Member`, `Product` |
| **Value Object** | Typed string + constants in `storage_<dep>.go` | `MemberStatusType` |
| **Data Transfer Object** | `<Action>Request` / `<Action>Response` in `handler_<action>.go` | `IssueTokenRequest`, `ResolveIdentityResponse` |
| **Special Case / Sentinel** | `var ErrXxxNotFound = errors.New(...)` | `ErrMemberNotFound` (in `storage_member.go`) |
| **Composition Root** | `router/deps.go` | 🛑 FORBIDDEN under this skill |

When you see one of these file prefixes, you are looking at the named pattern. Treat the pattern name as a reading lens, not a license to add new abstractions.

---

## 2. Service Layer in practice

The most consequential Fowler pattern for this skill is the **Service Layer** — the seam between the HTTP boundary (the `gin.Context` handler) and the access layer.

`app/auth/handler_resolve_identity.go` is the canonical example. The handler delegates two multi-step orchestrations to private methods:

```go
// handler_resolve_identity.go:42
googleData, err := h.authenticateGoogle(ctx, req.GoogleAccessToken)
// ...
// handler_resolve_identity.go:90
resp, err := h.resolveExistingMember(ctx, memberInfo, googleData.profileImage)
```

The two service files (`service_authenticate_google.go`, `service_resolve_existing_member.go`) own the orchestration. The handler itself owns:

1. Binding the request (`wrapper.BindJSON`).
2. Branching on error type (`errors.Is(err, errUnauthorized)`).
3. Mapping each outcome to an HTTP status + `wrapper.Respond`.

That separation is Fowler's Service Layer.

### Rules for `service_<action>.go` (load-bearing)

- The helper is an **unexported method on `*handler`** — `func (h *handler) authenticateGoogle(...)`. Not a free function. Not a separate struct.
- First argument is `ctx context.Context`.
- Returns a typed value or pointer plus `error`.
- Errors use `fmt.Errorf("...: %w", err)` for wrapping. **Not** `serror.Wrap` — that belongs at the response layer (the handler's `wrapper.Respond` call).
- Internal DTOs (data carried across helpers in the same domain) are **unexported** structs — see `googleAuthData` in `service_authenticate_google.go:13`.
- Internal sentinels (errors the handler branches on with `errors.Is`) are **unexported** package-level vars — see `errUnauthorized` in `service_authenticate_google.go:10`.
- Service helpers do **NOT** touch `*gin.Context`. They return data; the handler formats the response.

### When to extract a service helper

Use Extract Function and create `service_<action>.go` when **any** of:

- The handler exceeds ~100 lines.
- The handler does two or more multi-step orchestrations (auth, then lookup, then mapping).
- The same orchestration is needed in a second handler or consumer.
- Logic is being inlined that interrogates a returned Model's fields heavily before producing the response (Feature Envy smell).

Do **not** extract a helper just to shorten one linear five-line block — that's noise, not Service Layer.

### Splitting and testing extracted helpers

When you split functions out of a handler/consumer, **group them into `service_<action>.go`** — one file per action/orchestration. The handler then keeps only: bind the request → call `h.<action>(ctx, …)` → branch on the returned error → `wrapper.Respond`. Everything between binding and response formatting moves to the service file.

Each `service_<action>.go` ships a matching `service_<action>_test.go`. Because the helper is an **unexported** `*handler` method, that test file must declare the **internal** `package <domain>` (not `<domain>_test`) — that is the only way to reach the method. Boundary tests stay external; both packages coexist in the directory. Test the service helper directly (success, each sentinel error via `errors.Is`, each `if err != nil` from an access call); the handler test then only needs to cover the thin boundary it still owns. See `references/testing-pattern.md` → "Service-layer variant".

`promo-service` is the canonical reference: `handler_apply.go` stays thin and delegates to `service_apply.go` (`applyPromo`, `publishExhausted` — unexported `*handler` methods), which is unit-tested from inside `package promo`.

---

## 3. Tell-Don't-Ask, scoped to handlers and consumers

The principle: **the handler tells a helper or model to do the work; it does not pull primitives out and decide externally.**

In this codebase, Tell-Don't-Ask shows up in two places:

**(a) Handler → Service Layer.** The handler tells `h.authenticateGoogle(ctx, token)` to do the whole Google dance. It does not call `h.googleClient.ValidateAccessToken`, then check the response code, then call `GetUserProfile`, then call `RevokeToken` inline. Compare:

```go
// PRACTICED (handler_resolve_identity.go:42) — Tell-Don't-Ask
googleData, err := h.authenticateGoogle(ctx, req.GoogleAccessToken)

// ANTI-PATTERN — God Handler with inline ask-decide
validateResp, _ := h.googleClient.ValidateAccessToken(ctx, req.GoogleAccessToken)
if validateResp.Code >= 400 { /* ... */ }
userResp, _ := h.googleClient.GetUserProfile(ctx, req.GoogleAccessToken)
if userResp.Code >= 400 { /* ... */ }
// ...two more steps inlined...
```

**(b) Handler / consumer → Domain Model (when justified).** When state-mutation logic for a Model would cluster in one handler, push the behaviour onto the Model:

```go
// Possible refactor
invoice.MarkAsPaid()             // tell — Move Function applied
// instead of:
invoice.Status = access.InvoiceStatusPaid  // ask-and-set — handler owns the rule
```

This codebase currently keeps Models thin (mostly `GetID()` and field tags). That is acceptable. Push behaviour to the Model only when:

- The same mutation appears in 2+ handlers or consumers, **and**
- The mutation has an invariant the Model can defend (e.g., "you cannot mark as paid an invoice in DRAFT without a payment record").

For one-off field assignments, leaving them in the handler is fine. **Don't introduce premature abstractions.**

### What Tell-Don't-Ask does NOT mean in Go

- It does **not** mean "add getters and setters". Go avoids those.
- It does **not** mean "make every field private". The access models intentionally export fields for storage tags.
- It does **not** apply to `storage_*.go` / `cache_*.go` / `client_*.go` — those are adapters; they expose data, not behaviour.

---

## 4. Code smells to scan for (handlers and consumers)

Scan a handler or consumer for these before declaring the requirement done. Hit on any → consider one of the refactorings in §5.

| Smell | What it looks like in a handler/consumer |
|---|---|
| **God Handler / Service** | One handler mixes HTTP binding, validation, auth, multiple infra calls, deep business logic, AND response formatting. |
| **Primitive Obsession** | A `string` or `int` is passed where a typed Value Object exists (e.g. raw `"ACTIVE"` instead of `access.MemberStatusActive`). |
| **Feature Envy** | The handler intensely interrogates a Model's fields (`if member.Status == X && member.CreatedAt.After(...) && ...`) instead of asking the Model or a service helper. |
| **Conditional Explosion** | Deeply nested `if/else` or a large `switch`/branch on an enum-like value, especially when each branch produces a different orchestration. |
| **Mixed Abstraction Levels** | High-level orchestration sits next to byte-manipulation or low-level marshalling in the same function. |
| **Leakage** | Repository internals (Firestore query objects, raw SQL, `*sql.Row`) appear in the handler body. |
| **Long Parameter List** | A method on `*handler`, a service helper, or an access method has **4+ parameters after `ctx`**. Often a sign that a DTO or Model is being decomposed at the call site (caller pulls fields off a struct and re-passes them one by one). |
| **Too Many Returns** | A function returns **3+ values** (`(T1, T2, error)`, `(T, int, error)`, `(T, bool, error)`). Callers must remember the position of each return; the signature is refactor-resistant and noisy at every call site. |

---

## 5. Refactoring catalog actions used here

The subset of Fowler's catalog that lands in this codebase. Apply one at a time.

| Refactoring | Apply when | How it looks here |
|---|---|---|
| **Extract Function** | Handler exceeds ~100 lines OR has a reusable multi-step orchestration. | Create `service_<action>.go`. Move the block. Replace the inlined block with `h.<action>(ctx, ...)`. |
| **Move Function** | A state mutation for a Model is duplicated across handlers AND has an invariant. | Add a method to the Model in `storage_<dep>.go`. Call it from the handler/consumer. |
| **Introduce Value Object** | A `string` or `int` carries domain meaning. | Define `type FooType string` and constants in the Model's access file. Replace the raw type at all call sites. |
| **Replace Conditional with Strategy** | A large `switch` on an enum-like Value Object dispatches to different orchestrations. | Build a `map[FooType]func(ctx, ...) (..., error)` populated in `NewHandler`. Replace the switch with a map lookup. |
| **Encapsulate State** | (Already standard) | Unexported impl + exported interface + `var _ Interface = (*impl)(nil)`. Don't violate this. |
| **Separate Formatting** | Handler builds response fields mid-orchestration. | Service helper returns typed data; handler is the only place that touches `wrapper.Respond` and `*gin.Context`. |
| **Introduce Parameter Object** | A method has 4+ params after `ctx`, OR the same group of params appears together in 2+ signatures. | Define `<Action>Params` struct in the same file as the function (handler / service / access). Pass the struct; callers build it once. Internal to one domain → unexported; crosses a public seam → exported. |
| **Introduce Result Object** | A function returns 3+ values, OR the same return tuple appears across 2+ functions. | Define `<Action>Result` struct alongside the function. Return `(<Action>Result, error)`. Allowed two-value exceptions: `(T, bool)` for lookup-style "found" checks, naked `error` for I/O with no value. |

---

## 6. Small safe steps — the refactoring workflow

When a requirement forces touching an existing handler/consumer, follow this loop:

1. **Identify** one smell from §4.
2. **Choose** one refactoring from §5.
3. **Apply** the minimal change.
4. **Verify** with the existing tests (`go test ./app/<domain>/...`). The test suite must stay green after each step.
5. **Repeat** until the handler/consumer is clean for the requirement at hand.

**Guardrails**:

- DO NOT mix refactoring with the requirement's feature work in the same commit. Refactor first, commit, then add the feature, commit. (`make precommit` between commits.)
- DO NOT introduce abstractions speculatively. Apply a refactoring only when a smell from §4 is present.
- STOP when the smell is gone. "Good enough" is the target, not "ideal".

---

## 7. Go adaptations

Fowler's catalog assumes class-based inheritance. Go does not have it. Adaptations used in this scaffold:

- **No classical inheritance → composition + interfaces.** Service Layer is a method on `*handler`, not a subclass.
- **"Accept interfaces, return structs"** (Go proverb) is Fowler-compatible. Constructors return interfaces (`NewMemberStorage` returns `MemberStorage`). Composition Root passes concrete deps in.
- **Compile-time interface check** `var _ Interface = (*impl)(nil)` is a Go-specific safety net, not a Fowler pattern. Keep it on every impl.
- **No getters/setters.** Tell-Don't-Ask is realised through behaviour methods (`invoice.MarkAsPaid()`, `member.Suspend(reason)`), not `SetStatus(...)`.
- **Error wrapping** is `%w` in `fmt.Errorf` at the service/access layers; `serror.Wrap(err).With(slog attrs...)` at the handler-response layer. The chain is preserved.

---

## 8. Quick decision tree

When implementing a handler or consumer under this skill:

1. Is the handler/consumer doing **one** linear thing? → Inline is fine. Stop.
2. Is it doing **two or more multi-step orchestrations**? → Extract a `service_<action>.go` per orchestration.
3. Is the same orchestration needed in **another handler/consumer**? → Promote to `service_<action>.go` now (not later).
4. Is a state mutation on the Model **duplicated** AND **has an invariant**? → Move Function to the Model.
5. Anything else (one-off field tweak, simple branch) → Stay inline. Don't over-engineer.
6. Does this function have **4+ params after `ctx`**? → **Introduce Parameter Object** (`<Action>Params` struct).
7. Does this function return **3+ values**? → **Introduce Result Object** (`<Action>Result` struct). The only allowed two-value exceptions are `(T, error)` (default), `(T, bool)` for lookup checks, and naked `error` for I/O with no value.

---

## 9. Source acknowledgement

The smell catalog, refactoring actions, and small-safe-steps workflow originate from Martin Fowler's *Refactoring: Improving the Design of Existing Code* (2e) and *Patterns of Enterprise Application Architecture*. They are summarised more fully in the neighbouring skill at `go-template/.github/skills/platform-go-service/references/refactoring-fowler.md` (broader scope: covers all layers). This page is the **handler/consumer-scoped condensation** used by this skill.
