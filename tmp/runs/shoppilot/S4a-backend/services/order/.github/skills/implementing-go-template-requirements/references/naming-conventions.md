# Naming conventions

These rules are **load-bearing**: the codebase wires routes, mocks, and tests by file/identifier convention. Breaking them breaks tooling silently.

## File name prefix table

The type prefix comes **first**. Never `<action>_handler.go` or `<dep>_storage.go`.

| Prefix | Purpose | Example |
|---|---|---|
| `handler_<action>.go` | HTTP endpoint method on `*handler` | `handler_create.go`, `handler_issue_token.go` |
| `handler_<action>_test.go` | Table-driven test for the matching handler | `handler_create_test.go` |
| `consumer_<action>.go` | Kafka event handler method on `*handler` | `consumer_create.go`, `consumer_paid.go` |
| `consumer_<action>_test.go` | Table-driven test for the matching consumer | `consumer_create_test.go` |
| `service_<action>.go` | Private service helper(s) split out of a handler/consumer, grouped by action (unexported `*handler` method) | `service_authenticate_google.go`, `service_apply.go` |
| `service_<action>_test.go` | Internal-package (`package <domain>`) test for the matching service helper | `service_apply_test.go` |
| `storage_<dep>.go` | Persistence repository (Firestore, MySQL, S3/GCS) | `storage_member.go`, `storage_product.go` |
| `cache_<dep>.go` | Cache repository (Redis, Memcached) | `cache_product.go` |
| `client_<dep>.go` | External API gateway | `client_google.go` |

`<action>` is a short verb or verb-phrase: `create`, `get`, `list`, `paid`, `issue_token`, `resolve_identity`.
`<dep>` is the name of the resource the access layer wraps: `member`, `product`, `google`, `s3`.

## Package and import rules

- **One package per aggregate** under `app/`. Folder name == package name.
- **Boundary** tests (handler/consumer) use the external `_test` package: `package product_test`, `package auth_test`. **Service** tests use the **internal** package: `package product` — service helpers are unexported `*handler` methods, reachable only from inside the package. Both coexist in the same directory. (The `access/` layer is out of unit-test scope under this skill.)
- The `access/` sub-package is named `access` (no domain prefix). Import it with an alias if needed: `import productaccess ".../app/product/access"`.
- **No cross-domain imports**. `app/product` MUST NOT import `app/member`. Communicate via Kafka events.
- The generated mocks package: `package access_mocks` (mockery default for the configured dir).

## `access/` co-location rule

Each `access/<prefix>_<dep>.go` file is a self-contained unit. In ONE file, in this order:

1. Sentinel errors (`var ErrXxxNotFound = errors.New("...")`).
2. Interface definition (the public API).
3. Unexported impl struct.
4. Compile-time interface check: `var _ <Interface> = (*<impl>)(nil)`.
5. Internal constants (collection names, table names) as unexported `const`.
6. Exported constructor returning the interface.
7. Method implementations.
8. Value-object types (`type XxxStatusType string` and the typed enum values).
9. Domain model struct.
10. Domain-model methods (e.g. `GetID() (uuid.UUID, error)`).

**Forbidden inside `access/`**: separate `model.go`, `errors.go`, `constants.go` files. Co-locate everything in the access file that uses it.

## Identifier conventions

- Constructor returns the **interface**, struct is **unexported**:
  ```go
  type MemberStorage interface { ... }
  type memberStorage struct { ... }
  var _ MemberStorage = (*memberStorage)(nil)
  func NewMemberStorage(fs *gcpfirestore.Client) MemberStorage { return &memberStorage{fs: fs} }
  ```
- Handler config: `HandlerConfig` (exported) → `handler` (unexported) → `NewHandler(cfg HandlerConfig) *handler`.
- HTTP request/response types live in the same file as the handler that uses them: `CreateProductRequest`, `CreateProductResponse`.
- Kafka payload types live in the same file as the consumer that consumes them: `CreateProductMessage`, `PaidInvoiceMessage`.
- HTTP routes: `/api/v1/<domain>/<aggregate>/<action>` — `<domain>` = API namespace (e.g. `platform`), `<aggregate>` = the `app/` package directory, `<action>` = verb. e.g. `/api/v1/platform/product/create`.
- Event names (the topic-keys used in `registerEventRoutes`): `<DOMAIN>_<AGGREGATE>_<ACTION>` in UPPER_SNAKE, mirroring the route's three segments (event `<action>` is the event verb, usually past tense). e.g. `PLATFORM_PRODUCT_CREATED`, `PLATFORM_INVOICE_PAID`. The `<aggregate>` token is the `app/` package; `<domain>` is the API namespace — not the `app/<domain>/` path placeholder used elsewhere in this skill.

## Function signature conventions

The shape of every method on `*handler`, every service helper, and every access method:

```go
func (recv *T) Name(ctx context.Context, p1, p2, p3 T) (Result, error)
```

- `ctx context.Context` is always the **first** parameter on any I/O method.
- **Max 3 parameters after `ctx`.** 4+ is a Long Parameter List smell — apply **Introduce Parameter Object** (define a `<Action>Params` struct in the same file) or **Preserve Whole Object** (pass an existing Model instead of decomposing its fields). See `fowler-patterns.md` §5.
- **Return arity defaults to `(T, error)`.** Allowed exceptions:
  - `(T, bool)` for lookup-style "found / not-found" checks where a sentinel error would be noisy at the call site.
  - Naked `error` for I/O methods that produce no value (e.g. `Update`, `Delete`).
- **3+ return values is forbidden.** Apply **Introduce Result Object** — define a typed `<Action>Result` struct in the same file and return `(<Action>Result, error)`.
- DTOs used only inside one service helper (one domain) stay **unexported** (see `googleAuthData` in `app/auth/service_authenticate_google.go`). DTOs that cross a public seam (handler ↔ access, request body, response body) are **exported**.

## Error conventions

- **Access layer**: `fmt.Errorf("failed to <verb> <noun>: %w", err)`. Wraps cause with `%w`. No `serror` here.
- **Handler / consumer / service layer**: `serror.Wrap(err).With(slog.String("key", value), ...)`. Attach investigation context.
- Sentinel errors live at the top of the access file that returns them: `var ErrMemberNotFound = errors.New("member not found")`.

## Context conventions

- Every I/O method takes `ctx context.Context` as its first argument.
- Handlers obtain context via `c.Request.Context()`.
- Consumers receive context as the first param of their kafka.KafkaHandler signature.

## Logger convention

- `log/slog` ONLY. No third-party loggers.
- Initialised once in `main.go` via the common-module `logger.New`. Do not re-initialise in business logic.
- Attach structured attrs when logging from a handler: `slog.String("member_id", id.String())`.

## Comment style

- Lean. One terse doc line on exported identifiers; no inline narration, no decorative section dividers (`// --- … ---`), no `// Arrange`/`// Act`/`// Assert` markers. Comment a non-obvious *why* or a real gotcha only — never restate what the code plainly does.

## Test conventions (overview — full pattern in `testing-pattern.md`)

- Unit-test scope: handlers, consumers, services. The constructor (`New*`) and the `access/` layer are **out of scope**.
- One `_test.go` per in-scope code file: `handler_<action>_test.go`, `consumer_<action>_test.go`, `service_<action>_test.go`.
- Test file package: external `<domain>_test` for handler/consumer tests; internal `<domain>` for service tests.
- Local types: `mockArgs`, `args`, `want`.
- Closure name: `prepare(m mockArgs, args args)`.
- Mock constructor: `<package>_mocks.New<Interface>Mock(t)` (e.g. `access_mocks.NewMemberStorageMock(t)`).
- Mock API: `.EXPECT().<Method>(...).Return(...)`.

## Forbidden naming

- `handler_<action>.go` is correct. `<action>_handler.go` is **wrong**.
- `storage_<dep>.go` is correct. `<dep>_storage.go` or `<dep>_repository.go` is **wrong**.
- Files named `model.go`, `errors.go`, `constants.go`, `types.go`, or `util.go` inside `access/` are **wrong** — co-locate.
- A test file without a matching code file is **wrong** — match 1:1.
