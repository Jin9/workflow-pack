# Implementation recipes

One recipe per common requirement shape. Each recipe lists the exact file set, the order to write them, and the wiring step.

## Recipe A — Add a new HTTP endpoint to an existing domain

Use when: requirement says "add `POST /api/v1/<domain>/<aggregate>/<action>` that does X" (e.g. `/api/v1/platform/product/create`).

Files (in order):

1. **(Optional)** `app/<domain>/access/storage_<dep>.go` — if the endpoint needs a new query, add the method to the interface and impl.
2. **(Optional)** `app/<domain>/handler.go` — if a new dependency must be injected, add a field to `HandlerConfig` and `handler`, and wire it in `NewHandler`.
3. `app/<domain>/handler_<action>.go` — request struct, response struct, `func (h *handler) <Action>(c *gin.Context)` using `wrapper.BindJSON` + `wrapper.Respond`.
4. **(If the handler runs multi-step orchestration)** `app/<domain>/service_<action>.go` — move the orchestration into an unexported `*handler` method (`h.<action>`); the handler keeps only bind → call → error→HTTP → respond.
5. `app/<domain>/handler_<action>_test.go` — boundary cases in external `package <domain>_test` (success + every error branch the handler still owns). Use `templates/handler_test.go.tmpl`.
6. **(If step 4 applies)** `app/<domain>/service_<action>_test.go` — internal `package <domain>` cases for `h.<action>` (success, each sentinel error via `errors.Is`, each `if err != nil`). Use `templates/service_test.go.tmpl`.
7. **Narrow edit** `router/router.go` — add `<domain>Group.POST("/<action>", <domain>Handler.<Action>)` inside the existing `register<Domain>Routes` block. If the function does not exist yet, add it and call it from `New()`.
8. **Narrow edit** `spec.md` — document the endpoint with request/response schemas.

Wiring example (router.go, inside `register<Domain>Routes`):

```go
productGroup := r.Group("/api/v1/platform/product")
{
    productGroup.POST("/create", productHandler.CreateProduct)
    productGroup.POST("/detail", productHandler.GetProduct)
    productGroup.POST("/list",   productHandler.ListProducts)
    productGroup.POST("/update", productHandler.UpdateProduct)  // ← new
}
```

Path shape `/api/v1/<domain>/<aggregate>/<action>`: namespace `platform`, aggregate (the `app/` package) `product`, action `update`.

Tests required (handler + service only — not the constructor or `access/`):

- Success path.
- Each missing-required-field case (one per `binding:"required"` tag on the request struct).
- Each downstream error from access/service calls.
- Model-getter parse failures if the response includes a UUID from a string-typed field (drives the handler's error branch).
- If logic was extracted in step 4, the branch coverage on `h.<action>` lives in the service test; the handler test only covers the thin boundary.

## Recipe B — Add a new Kafka consumer to an existing domain

Use when: requirement says "consume `<EVENT_NAME>` and do X".

Files (in order):

1. **(Optional)** `app/<domain>/access/storage_<dep>.go` — if the consumer needs a new query/mutation, add the method.
2. **(Optional)** `app/<domain>/handler.go` — extend `HandlerConfig` if a new dependency is needed.
3. `app/<domain>/consumer_<action>.go` — payload struct, `func (h *handler) On<Action>(ctx context.Context, msg kafka.Message[json.RawMessage]) error` using `kafka.BindMessage`.
4. `app/<domain>/consumer_<action>_test.go` — table-driven cases.
5. **Narrow edit** `router/subscriber.go` — add `routes["<EVENT_NAME>"] = <domain>Handler.On<Action>` inside `registerEventRoutes`. `<EVENT_NAME>` follows `<DOMAIN>_<AGGREGATE>_<ACTION>` (UPPER_SNAKE).
6. **Narrow edit** `spec.md` — document the event name and payload schema.

Wiring example (subscriber.go, inside `registerEventRoutes`):

```go
routes["PLATFORM_PRODUCT_CREATED"] = productHandler.OnProductCreated
routes["PLATFORM_INVOICE_PAID"]    = invoiceHandler.OnInvoicePaid  // ← new
```

Tests required:

- Success.
- Invalid JSON payload (malformed).
- Validation failure (one case per `binding:"required"` field in the payload struct).
- UUID parse failure for any string-typed UUID field.
- Each downstream error from access/service calls.

## Recipe C — Extend the access layer with a new storage method

Use when: requirement says "the new feature needs to query/write something we don't store yet".

Files (in order):

1. `app/<domain>/access/storage_<dep>.go` — add the method to the interface AND the impl. Co-locate the method body, any new sentinel errors, and any new constants in the same file.
2. **Regenerate mocks** — run `mockery`. Never hand-edit `access/mocks/mocks.go`.
3. The caller(s) — the handler or consumer that uses the new method (Recipes A or B).

Anti-patterns to avoid:

- Adding the method only to the impl without updating the interface (handler will not see it via DI).
- Adding the method to the interface without updating mocks (tests will fail to compile).
- Creating a new `access/storage_<otherdep>.go` when the existing one is the right place (only split when the access object wraps a genuinely different external resource).

## Recipe D — Fix a bug in business logic without scaffold changes

Use when: requirement is a bug report ("when X happens, Y is wrong").

Steps:

1. **Localise** the bug to a specific handler/consumer/service or access method using the requirement's reproduction steps.
2. **Read** the implicated file plus its existing test file.
3. **Add a failing test** that reproduces the bug as a new case in the existing table-driven test file. The case name should match the bug report's symptom.
4. **Fix the code** in the smallest possible scope:
   - Single-file fix preferred. Multi-file fixes need a justification per file (still inside ALLOWED zone).
   - Do NOT add new abstractions. Do NOT rename existing identifiers unless renaming is the fix.
5. **Run the test** — confirm it now passes.
6. **Verify** no regressions in adjacent tests via `go test -race ./app/<domain>/...`.
7. **Update spec.md** only if the bug fix changes the public contract.

Anti-patterns to avoid:

- "While I'm here, let me also..." — out of scope. Surface the additional issue to the user; do not bundle.
- Adding a feature flag for the fix.
- Renaming the function/file to clarify intent — that is refactoring, not bug-fixing.

## Recipe E — Add a new domain (aggregate)

Use when: requirement introduces a new bounded context that does not yet exist (`app/<newdomain>/` is absent).

Permitted because `app/` as a whole is in the ALLOWED zone. Still requires care because routing wiring is NARROW.

Files (in order):

1. `app/<newdomain>/access/storage_<dep>.go` — interface + impl + model + sentinel errors.
2. `app/<newdomain>/handler.go` — HandlerConfig + handler + NewHandler.
3. `app/<newdomain>/handler_<action>.go` (for each endpoint) and/or `consumer_<action>.go` (for each event).
4. Matching `*_test.go` for each.
5. **Narrow edit** `router/router.go` — add `register<Newdomain>Routes(r, d)` function and call it from `New()`.
6. **Narrow edit** `router/subscriber.go` — add entries to `registerEventRoutes` if the domain consumes events.
7. `spec.md` — document the new endpoints/events.

STOP triggers for this recipe (Recipe E specifically):

- The new domain needs a new infrastructure client → STOP, requires editing `router/deps.go` (FORBIDDEN).
- The new domain needs a new env var → STOP, requires editing `config/config.go` (FORBIDDEN).

In both cases, surface the STOP to the user before proceeding.

## Recipe F — Refactor a handler/consumer to address a named smell

Use when: the requirement IS a refactor request and names a specific smell from `fowler-patterns.md` §4 — e.g. "this handler is a God Handler", "`service_create.go` has Long Parameter List", "`access.GetMemberWithProfile` has Too Many Returns, collapse to a result object", "`OnInvoicePaid` has Feature Envy on `Invoice`". All work stays inside the ALLOWED zone — `app/<domain>/**` only.

Steps:

1. **Confirm the smell.** It must match a row in `fowler-patterns.md` §4. If the user has not named one, STOP and ask which smell applies. "Clean it up" / "make it nicer" is not a smell.
2. **Snapshot the test suite.** Run `go test -race -cover ./app/<domain>/...`. It must be green *before* any refactor step. Capture the coverage number.
3. **Pick exactly one refactoring** from `fowler-patterns.md` §5 that matches the smell. Common pairings:
   - God Handler → Extract Function (into `service_<action>.go`).
   - Long Parameter List → Introduce Parameter Object (`<Action>Params`) or Preserve Whole Object.
   - Too Many Returns → Introduce Result Object (`<Action>Result`).
   - Feature Envy → Move Function (push behaviour onto the Model in `storage_<dep>.go`).
   - Conditional Explosion → Replace Conditional with Strategy.
   Do not chain. One refactoring per step.
4. **Apply the minimal change.** Stay in `app/<domain>/**` plus any narrow `router/router.go` or `router/subscriber.go` edit that a renamed identifier forces (still NARROW zone — only the existing `register<Domain>*` block). When the refactoring is Extract Function (God Handler → `service_<action>.go`), add or extend `service_<action>_test.go` in the **internal** `package <domain>` to cover the moved logic, and thin the handler test down to the boundary it still owns.
5. **Regenerate mocks** via `mockery` if any `access/` interface signature changed. Never hand-edit `access/mocks/mocks.go`.
6. **Re-run tests.** `go test -race -cover ./app/<domain>/...` must be green; **in-scope** coverage (handlers/consumers/services, excluding constructors and `access/`) must equal or exceed the snapshot from step 2.
7. **Commit the refactor on its own.** Run `make precommit`. Commit message names the smell and the refactoring (e.g. `refactor(auth): introduce parameter object on resolveExistingMember`).
8. **Loop or stop.** If the smell from step 1 is gone, stop. If another §4 smell is present, go back to step 3 for a fresh single-action pass.
9. **No feature work in this commit.** If the requirement also has a feature delta, that is a separate task — close out the refactor commit first, then run Recipe A / B / C / D for the feature on top of the cleaned code.

STOP triggers for Recipe F:

- The refactor would touch `router/deps.go`, `main.go`, `config/`, `Dockerfile`, or any other FORBIDDEN file → STOP, surface the scaffold-lock conflict, ask the user before continuing.
- A test fails after a refactor step → revert the step (`git checkout -- <files>`). Pick a smaller refactor or a different §4 smell. Do **not** "fix" the test to match the new behaviour — the test pinned the behaviour for a reason.
- The signature change requires a cross-domain import (e.g. `app/product` importing `app/member`) → STOP. Redesign via Kafka event. Cross-domain imports remain forbidden.
- Coverage drops after a step → revert. The refactor must be behaviour-preserving by definition.

Anti-patterns to avoid:

- Renaming for taste (no §4 row names "ugly name" or "unclear identifier"). Renames belong inside a refactoring step, not as the refactoring itself.
- Introducing speculative abstractions ("we might need this later"). Apply a refactoring only when a §4 smell is present *now*.
- Bundling "while I'm here" feature work into the refactor commit.
- Hand-editing generated mocks instead of running `mockery`.
