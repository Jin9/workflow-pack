---
name: implementing-go-template-requirements
description: >-
  Apply a single requirement (spec line, ticket, bug report, user story) to a
  Go service that follows the go-template scaffold by editing ONLY business
  logic under `app/[domain]/` plus narrow `register*` wiring in `router/`.
  Also accepts requirement-driven Fowler refactors (God Handler, Long
  Parameter List, Too Many Returns, Feature Envy) scoped to handlers,
  consumers, and access-layer signatures. Locks `main.go`, `config/`,
  `router/deps.go`, `Makefile`, `Dockerfile`, CI, and tooling from
  modification. Use when the user says "implement this requirement in the
  go-template service", "add this endpoint per spec without touching infra",
  "fix this bug, business logic only", "wire up this Kafka event from the
  requirement", "implement spec.md item N", or "refactor this handler to
  address [named smell]". Do NOT use to create a new service from scratch,
  change middleware, modify `main.go`/`config/`/`router/deps.go`/`Dockerfile`/
  `Makefile`/CI, do frontend or non-Go work, or perform refactors with no
  named smell.
argument-hint: Describe the requirement (spec section, ticket title, bug summary). The skill picks the right files, keeps scaffold untouched, and runs the verification gate.
---

# Implementing Go-Template Requirements

Use this skill to translate **one requirement** into code inside a Go service that follows the `go-template` scaffold. The job is **business logic, not scaffolding**. The scaffold (bootstrap, config, middleware, CI, infrastructure wiring) is **locked**: do not edit it unless the requirement explicitly forces a scaffold delta, and only after STOP-and-ask confirmation.

---

## 1. When to use this skill

Trigger on:

- "implement this requirement in the go-template service"
- "add this endpoint per spec without touching infra"
- "fix this bug, business logic only"
- "wire up this Kafka event from the requirement"
- "implement spec.md item N"
- "extend `<domain>` to satisfy `<requirement>`"
- "refactor `<handler|consumer|service>` to address a named smell from `references/fowler-patterns.md` §4 (God Handler, Long Parameter List, Too Many Returns, Feature Envy, etc.)"
- A user message that pastes a requirement/spec/ticket and asks for an implementation in this repo

Do NOT use for:

- Creating a new service from scratch (use a scaffolding skill or copy `go-template` manually).
- Changing middleware, security headers, CORS, timeouts, or the Gin engine setup.
- Modifying `main.go`, `config/`, `router/deps.go`, `Makefile`, `Dockerfile`, CI pipelines, `.scripts/`, `.golangci.yaml`, `.mockery.yaml`, `.env.template`.
- Frontend, Terraform, Kubernetes, non-Go work.
- "Clean this up while we're here" requests with no named smell from `references/fowler-patterns.md` §4. Ask the user which smell applies; if none, decline.

---

## 2. The scaffold-lock policy (the defining rule)

Three zones. Every edit must be classified before it is made.

| Zone | Files | What you may do |
|---|---|---|
| ✅ ALLOWED | `app/<domain>/**` (every business-logic file, including `access/` and generated `mocks/mocks.go`) | Edit freely within the conventions in §4 and `references/naming-conventions.md`. |
| ⚠️ NARROW | `router/router.go` (only the `register<Domain>Routes(r, d)` block for your domain), `router/subscriber.go` (only the entry inside `registerEventRoutes`), `spec.md` (only to document new endpoint/event) | Add or change ONLY the named block. Do not touch middleware chain, `New()` skeleton, Kafka consumer-group lifecycle, security headers, CORS, timeout, or logger. |
| 🛑 FORBIDDEN | `main.go`, `config/`, `router/deps.go`, `Makefile`, `Dockerfile`, `docker-compose.yml`, `gitlabci.yml`, `.github/`, `.scripts/`, `.golangci.yaml`, `.mockery.yaml`, `.env.template`, `VERSION`, `CHANGELOG.md`, `go.mod`, `go.sum` | STOP. Do not edit. Ask the user. |

> The ALLOWED file prefixes realise Fowler's Repository (`storage_*`), Cache (`cache_*`), Gateway (`client_*`), Service Layer (`service_*`), and Domain Model patterns. `router/deps.go` is the Composition Root (FORBIDDEN). See `references/fowler-patterns.md` for the cross-walk and the small-safe-steps refactoring discipline that applies when extending handler/consumer code.

**STOP triggers** — these signal the requirement crosses the scaffold boundary and you must ask before proceeding:

- New infrastructure: new database, cache, queue, external HTTP service that needs a new SDK client.
- New env var that does not fit an existing config struct branch.
- Change to logging behavior, signal handling, or graceful shutdown.
- Anything that would change `go.mod`, `Dockerfile` base image, or CI steps.

When a STOP fires: surface the conflict, name the forbidden files involved, and ask the user to confirm the scaffold delta before continuing. Do not silently edit forbidden files.

Full rationale per file: `references/scaffold-lock-policy.md`.

---

## 3. Workflow

Run these in order. Every step has an entry and exit condition.

**Step 1 — Parse the requirement.**
- Entry: user message containing a requirement, spec excerpt, ticket, or bug description.
- Extract: kind (new endpoint / new consumer / new storage method / bugfix), target domain, name of action or event, inputs, outputs, side effects (DB writes, Kafka publish), dependencies (storage, cache, external client).
- Exit: a one-paragraph summary of *what* the change is and *which files* it implies. Restate to the user before editing if any extraction is ambiguous.

**Step 2 — Locate the domain.**
- Entry: target domain name from Step 1.
- List `app/<domain>/` to confirm it exists. Read `app/<domain>/handler.go` to see existing `HandlerConfig` dependencies.
- If `app/<domain>/` does not exist: this is a new-domain creation, still allowed (the whole `app/` tree is in the allowlist). Announce the new-domain decision and continue.
- Exit: confirmed target domain path.

**Step 3 — Audit existing access interfaces.**
- Entry: target domain confirmed.
- Read every `access/storage_*.go`, `access/cache_*.go`, `access/client_*.go` in the domain. Match the requirement's I/O needs against existing methods.
- Reuse existing methods where possible. Extend an interface only when the requirement genuinely needs a new query.
- Exit: a list of access-layer additions (new methods, new interfaces) or "no access changes needed".

**Step 4 — Apply the scaffold-lock test.**
- Entry: a draft list of files to create or modify.
- For each file, classify into ALLOWED / NARROW / FORBIDDEN per §2.
- If any file is FORBIDDEN: stop, surface the conflict, ask the user.
- If any file is NARROW: confirm you will edit only the named block.
- Exit: a clean edit plan, all files classified.

**Step 5 — Implement file deltas in dependency order.**
- Entry: clean edit plan from Step 4.
- Order:
  1. `app/<domain>/access/storage_<dep>.go` — interface + unexported impl + domain model + sentinel errors, co-located. Use `templates/storage.go.tmpl`.
  2. `app/<domain>/access/cache_<dep>.go` or `client_<dep>.go` if requirement calls for them.
  3. `app/<domain>/handler.go` — extend `HandlerConfig` and `handler` ONLY if a new dependency must be injected.
  4. `app/<domain>/handler_<action>.go` — use `templates/handler.go.tmpl`.
  5. `app/<domain>/consumer_<action>.go` — use `templates/consumer.go.tmpl`.
  6. `app/<domain>/service_<action>.go` — split orchestration/business logic OUT of the handler/consumer and **group it here** so the boundary stays thin (bind → call `h.<action>(ctx, …)` → map error→HTTP → respond). Extract whenever the handler runs multi-step orchestration — not only when the logic is reused. The helper is an unexported `*handler` method. See `references/fowler-patterns.md` §2.
  7. Narrow edit `router/router.go` — add `register<Domain>Routes(r, d)` call and function. Do not touch anything else.
  8. Narrow edit `router/subscriber.go` — add the event handler entry inside `registerEventRoutes`. Do not touch consumer-group lifecycle.
  9. `spec.md` — document the new endpoint/event in the existing format. Do not reformat unrelated sections.
- Exit: every file in the plan is written and follows naming + style conventions.

**Step 6 — Regenerate mocks.**
- Entry: access-layer interfaces changed (added/removed/renamed methods).
- Run `mockery` (using the repo's existing `.mockery.yaml` — do not edit it).
- Never hand-edit `app/<domain>/access/mocks/mocks.go`.
- Exit: mocks are current.

**Step 7 — Write tests (handlers, consumers, and services only).**
- Entry: handler/consumer/service code complete.
- **Unit-test scope**: `handler_<action>.go`, `consumer_<action>.go`, and `service_<action>.go`. **Out of scope**: the constructor (`NewHandler`/`New*`), the access layer (`storage_*`/`cache_*`/`client_*`), generated `mocks/`, and domain-model getters. Do not write unit tests for those under this skill — access adapters are exercised indirectly at the boundary.
- One test file per in-scope code file: `handler_<action>_test.go`, `consumer_<action>_test.go`, `service_<action>_test.go`.
- **Test package by layer**:
  - Boundary tests (handler/consumer) → external `package <domain>_test`; they call **exported** methods (`h.<Action>`, `h.On<Action>`). Use `templates/handler_test.go.tmpl` / `templates/consumer_test.go.tmpl`.
  - Service tests → internal `package <domain>`; service helpers are **unexported** `*handler` methods reachable only from inside the package. Use `templates/service_test.go.tmpl`. `package <domain>` and `package <domain>_test` test files coexist in the same directory.
- Pattern (all layers): `mockArgs` / `args` / `want` local types + `prepare(m, args)` closure + table-driven cases. Full pattern in `references/testing-pattern.md`.
- Cover every branch:
  - HTTP handler: success, each missing-required-field case, every `if err != nil` from access/service calls, model-getter parse failures (a bad UUID that makes `GetID()` fail) — these cover the **handler's** error branch, not the getter itself.
  - Kafka consumer: success, invalid JSON payload, validation failure (missing required fields), uuid parse failure, each `if err != nil` from access calls.
  - Service helper: success, each sentinel error it returns (assert with `errors.Is`), every `if err != nil` from access calls.
- Target: **100% statement coverage of in-scope functions** in the `app/<domain>/` package — constructors and the `access/` sub-package are excluded from the gate.
- Exit: the coverage command in `references/testing-pattern.md` (which filters out `/access/` and `New*`) prints nothing.

**Step 8 — Run the verification gate.**
- Entry: code + tests complete.
- Run `make precommit` (or equivalent: `go fmt ./...`, `go vet ./...`, `golangci-lint run --fix`, `go test -race -cover ./...`).
- All must pass. Coverage must remain at the existing threshold.
- Exit: green build.

**Step 9 — Diff allowlist check.**
- Entry: green build.
- Run `git diff --name-only` against the merge base of your working branch.
- Confirm every file is in ALLOWED (or is a NARROW edit limited to its named block).
- If any FORBIDDEN file appears: revert it. Surface to the user that the gate caught a scaffold leak.
- Exit: a clean diff that touches only business logic + narrow wiring + spec doc.

---

## 4. Naming and style — load-bearing conventions

The type prefix comes **first** in the filename. Never `<action>_handler.go` or `<dep>_storage.go`.

| Prefix | Purpose | Fowler pattern | Example |
|---|---|---|---|
| `handler_<action>.go` | HTTP endpoint method on `*handler` | (boundary; DTOs live here) | `handler_create.go` |
| `consumer_<action>.go` | Kafka event handler method on `*handler` | (boundary) | `consumer_paid.go` |
| `service_<action>.go` | Private service helper extracted from a handler/consumer | Service Layer | `service_authenticate_google.go` |
| `storage_<dep>.go` | Persistence repository (Firestore, MySQL, S3) | Repository | `storage_member.go` |
| `cache_<dep>.go` | Cache repository (Redis, Memcached) | Cache | `cache_product.go` |
| `client_<dep>.go` | External API gateway | Gateway | `client_google.go` |

`access/` files **co-locate** interface + unexported impl + domain model + sentinel errors + constants in a **single file**. NO separate `model.go`, `errors.go`, or `constants.go` inside `access/`.

Other rules (full list in `references/naming-conventions.md`):

- **Service files group extracted logic.** When you split functions out of a handler/consumer, move them into `service_<action>.go` as unexported `*handler` methods and keep the boundary thin. Each `service_<action>.go` ships a matching `service_<action>_test.go` in the internal `package <domain>`. See `references/fowler-patterns.md` §2.
- One package per aggregate under `app/`. **No cross-domain imports** — domains communicate via Kafka events.
- Constructor returns the **interface**; impl struct is **unexported**. Compile-time check: `var _ Interface = (*impl)(nil)`.
- Context first: `func(ctx context.Context, ...)` on every I/O method.
- Errors at access layer: `fmt.Errorf("...: %w", err)`. Errors at handler/consumer layer: `serror.Wrap(err).With(slog.String(...))`.
- **Function signature shape**: `func (recv *T) Name(ctx context.Context, p1, p2, p3 T) (Result, error)`. Max **3 parameters after `ctx`** — 4+ is a Long Parameter List smell and triggers **Introduce Parameter Object** (`<Action>Params` struct) or **Preserve Whole Object**. Return arity defaults to **`(T, error)`**; the only allowed exceptions are `(T, bool)` for lookup-style "found / not-found" checks where a sentinel error would be noisy, and naked `error` for I/O methods that produce no value (`Update`, `Delete`). **3+ return values is forbidden** — apply **Introduce Result Object** (`<Action>Result` struct). Full convention in `references/naming-conventions.md`; refactor mechanics in `references/fowler-patterns.md` §4–§5.
- HTTP responses: `wrapper.BindJSON[T]` + `wrapper.Respond` + `wrapper.ResponseOption[T]` + `app.Code*` / `app.Message*` constants.
- Kafka consumers: `kafka.BindMessage(msg.Payload, &target)`. **NEVER** `json.Unmarshal` in a consumer.
- **Routes**: `/api/v1/<domain>/<aggregate>/<action>` — `<domain>` = API namespace (e.g. `platform`), `<aggregate>` = the `app/` package directory, `<action>` = verb. e.g. `POST /api/v1/platform/promo/apply`.
- **Event names**: `<DOMAIN>_<AGGREGATE>_<ACTION>` — UPPER_SNAKE, the same three tokens as the route (the event `<action>` is the event verb, usually past tense). e.g. `PLATFORM_PROMO_EXHAUSTED`, `PLATFORM_ORDER_CANCELLED`. The `<aggregate>` token is the `app/` package; the `<domain>` token is the API namespace — distinct from the `app/<domain>/` path placeholder used elsewhere in this skill.
- **Comments are lean**: one terse doc line on exported identifiers; no inline narration, decorative dividers, or `// Arrange/Act/Assert` markers. Comment only a non-obvious *why* or a real gotcha.
- Logger: `log/slog` only. No third-party loggers. Logger is initialised once in `main.go` — do not re-initialise.

---

## 5. Pre-commit checklist

Before claiming the requirement done, every box must be ticked.

- [ ] Step 9 diff check passed: no FORBIDDEN files touched.
- [ ] File names match the prefix table in §4.
- [ ] One package per aggregate; no cross-domain imports.
- [ ] `access/` files co-locate interface + impl + model + sentinel errors.
- [ ] `var _ Interface = (*impl)(nil)` on every new impl.
- [ ] Constructor returns interface; impl struct unexported.
- [ ] `context.Context` first arg on every I/O method.
- [ ] Access layer wraps errors with `fmt.Errorf("...: %w", err)`.
- [ ] Handler/consumer layer wraps errors with `serror.Wrap(err).With(slog attrs...)`.
- [ ] HTTP handlers use `wrapper.BindJSON` + `wrapper.Respond` with `app.Code*` / `app.Message*`.
- [ ] Kafka consumers use `kafka.BindMessage`; signature `func(ctx context.Context, msg kafka.Message[json.RawMessage]) error`.
- [ ] Routes follow `/api/v1/<domain>/<aggregate>/<action>`; event names follow `<DOMAIN>_<AGGREGATE>_<ACTION>` (UPPER_SNAKE).
- [ ] Comments are lean — terse godoc on exported identifiers only; no narration, dividers, or `// Arrange/Act/Assert` markers.
- [ ] Tests follow `mockArgs` / `args` / `want` / `prepare` pattern.
- [ ] Each `service_<action>.go` has a matching internal-package `service_<action>_test.go`; boundary (handler/consumer) tests stay in external `package <domain>_test`.
- [ ] No dedicated test for the constructor (`New*`) and no unit tests for the `access/` layer — both are out of scope.
- [ ] Mocks regenerated via `mockery` (not hand-edited).
- [ ] 100% statement coverage of in-scope files (handler/consumer/service); constructors (`New*`) and the `access/` sub-package are excluded from the gate.
- [ ] `make precommit` (or equivalent) passes.
- [ ] `spec.md` updated for new endpoint/event (if applicable).
- [ ] Tell-Don't-Ask in handlers and consumers: orchestration goes through service helpers (`service_<action>.go`); no God Handler smell. See `references/fowler-patterns.md`.

Full checklist with rationale and failure modes: `references/verification-checklist.md`.

---

## 6. Constraints (hard rules)

- **DO NOT** edit any file in the FORBIDDEN zone (§2) without explicit user confirmation. The scaffold lock is the core safety property of this skill.
- **DO NOT** add cross-domain imports. `app/product` cannot import `app/member`. Communicate via Kafka events.
- **DO NOT** create `model.go`, `errors.go`, or `constants.go` inside `access/`. Co-locate them in the file that uses them.
- **DO NOT** pass raw SDK handles directly to handler/consumer code — always wrap in `access/`.
- **DO NOT** mix refactor commits with feature commits. Refactor first, commit, run `make precommit`, then add the feature, commit. One refactoring action per commit (Fowler small-safe-steps).
- **DO NOT** accept refactor requests without a named smell from `references/fowler-patterns.md` §4. "Clean this up" is not a requirement — ask which smell applies; if none, decline.
- **DO NOT** use `json.Unmarshal` in Kafka consumers — `kafka.BindMessage` enforces validation tags.
- **DO NOT** introduce preemptive abstractions. Keep the change concrete and minimal.
- **DO NOT** edit generated mocks by hand. Regenerate via `mockery`.
- **DO NOT** skip the diff allowlist check (Step 9) — it is the final gate that catches scaffold leakage.

---

## 7. References

| Need | File |
|---|---|
| Full scaffold-lock allowlist + per-file rationale | `references/scaffold-lock-policy.md` |
| File naming conventions and package rules | `references/naming-conventions.md` |
| Per-task recipes: add-endpoint, add-consumer, add-storage-method, fix-bug | `references/implementation-recipe.md` |
| Table-driven test pattern with `mockArgs`/`args`/`want`/`prepare` | `references/testing-pattern.md` |
| Quick reference for common-module helpers (`wrapper`, `serror`, `kafka`, `app`) | `references/common-module-quickref.md` |
| Pre-commit checklist and diff allowlist check | `references/verification-checklist.md` |
| Fowler pattern cross-walk + code smells + small-safe-steps refactoring discipline (handlers/consumers scope) | `references/fowler-patterns.md` |

## 8. Templates

| Need | File |
|---|---|
| `handler_<action>.go` skeleton | `templates/handler.go.tmpl` |
| `handler_<action>_test.go` skeleton | `templates/handler_test.go.tmpl` |
| `consumer_<action>.go` skeleton | `templates/consumer.go.tmpl` |
| `consumer_<action>_test.go` skeleton | `templates/consumer_test.go.tmpl` |
| `service_<action>_test.go` skeleton (internal-package test for an unexported `*handler` service method) | `templates/service_test.go.tmpl` |
| `access/storage_<dep>.go` skeleton with interface + impl + model | `templates/storage.go.tmpl` |

---

## 9. Troubleshooting

| Signal | Action |
|---|---|
| Requirement seems to need a new database or external service | STOP. The requirement crosses scaffold boundary. Surface the conflict, name `router/deps.go` and `config/`, ask the user to approve a scaffold delta. |
| `git diff` shows `main.go` or `config/` edits | Revert. The scaffold lock failed. Re-read §2 and Step 9. |
| Coverage stuck below 100% | Add a case per `if err != nil` in the handler/consumer/service. Include model-getter parse failures and `kafka.BindMessage` validation failures. Coverage is measured on in-scope files only — exclude `/access/` and `New*` from the gate (command in `references/testing-pattern.md`). |
| Coverage gate flags a constructor or `access/` method as uncovered | Expected — they are out of scope. Use the filtered coverage command; do not write tests just to satisfy them. |
| Need to test an unexported service helper (`h.applyPromo`) | Put the test in internal `package <domain>` (not `<domain>_test`), build the handler via `NewHandler`, and call the method directly. Use `templates/service_test.go.tmpl`. |
| Kafka consumer accepts invalid payload | Replace `json.Unmarshal` with `kafka.BindMessage` — it deserialises **and** runs binding tags. |
| `mockery` regenerates an unexpected mock file | Check `.mockery.yaml` (do not edit it — ask the user if the config is wrong). |
| Test stalls on `mock.MatchedBy` | Confirm `args.ctx` is assigned **before** calling `prepare(m, args)` inside the loop. |
| User names a smell from `references/fowler-patterns.md` §4 (God Handler, Long Parameter List, Too Many Returns, Feature Envy, …) and asks to refactor | Run **Recipe F** in `references/implementation-recipe.md`. Stay inside ALLOWED zone, one refactoring at a time from §5, tests green between each step. Refactor commit is separate from any feature commit. |
| User asks to "just refactor while we're here" with no smell named | Ask which smell from `references/fowler-patterns.md` §4 applies. If the user cannot name one, decline — "clean it up" is not a requirement. |
| New or modified function has 4+ params after `ctx` | Long Parameter List smell. Apply **Introduce Parameter Object** (`<Action>Params` struct) per `references/fowler-patterns.md` §5 before merging. |
| New or modified function returns 3+ values | Too Many Returns smell. Apply **Introduce Result Object** (`<Action>Result` struct) per `references/fowler-patterns.md` §5. `(T, bool)` lookups and naked `error` are the only allowed exceptions to `(T, error)`. |
| Handler over ~100 lines, or mixes auth + validation + business + formatting | God Handler smell. Extract a `service_<action>.go` per `references/fowler-patterns.md` §2; apply the small-safe-steps workflow. |
