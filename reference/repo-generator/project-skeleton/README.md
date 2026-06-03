# Go Service Skeleton

Blueprint repository for scaffolding A-Team platform microservices in Go. Clone this repo, drop your own domains under `app/`, register them in `router/router.go` and `router/subscriber.go`, and you have a production-ready service with HTTP routing, Kafka event handling, structured logging, and graceful shutdown — all wired up.

## Architectural Foundation

This skeleton codifies four architectural pillars. Every file and convention traces back to one of them.

| Pillar | How It's Applied |
|--------|-----------------|
| **Domain-Driven Design** | One package per aggregate under `app/<domain>/`. The `access/` sub-package wraps infrastructure behind domain-specific interfaces: `storage_` for persistence, `cache_` for caching, `client_` for external APIs. Domain models co-locate with their access file. No cross-domain imports. |
| **CQRS** | Write paths (create, update, delete) and read paths (get, list) are separate handler files. Kafka events propagate state changes across bounded contexts. |
| **Fowler-Style Patterns** | Behavior-preserving refactoring via small safe steps. Logic moves to Domain Models (Tell, Don't Ask). Strict layer targets: Handlers for transport, Services for flow control, Domain for business rules, and Adapters (`storage_`, `cache_`, `client_`) for external protocols. |
| **Go Idioms** | Accept interfaces/return structs, compile-time interface checks, `sync.Once` singletons, `context.Context` propagation, `%w` error wrapping, table-driven tests, `log/slog` structured logging. |

## What Lives Where

**Core Application**

```text
main.go                    Bootstrap, graceful shutdown, runtime tuning
config/config.go           Environment-backed configuration (nested structs + sync.Once)
router/deps.go             Composition root — infrastructure client creation & cleanup
router/router.go           Gin engine, middleware chain, HTTP route registration hook
router/subscriber.go       Kafka event→handler routing hook, consumer lifecycle
app/                       One sub-package per business aggregate (empty in the skeleton)
app/<domain>/access/       Repository / Cache / Gateway layer (storage_, cache_, client_)
```

**Shared Infrastructure (external module)**

Infrastructure and utility packages are imported from the shared **common** module at `gitlab.com/b2c-e-commerce-platform/platform/backend/common`:

| Package | Purpose |
|---------|---------|
| `logger` | Structured `slog`-based logging with key replacers and field censoring |
| `middleware` | SecurityHeaders, CORS, RefID, TraceContext, AccessLog, Timeout |
| `wrapper` | Generic HTTP response envelope (`ResponseOption[T]`, `BindJSON[T]`) |
| `serror` | Source-location error wrapping with investigation context |
| `kafka` | Producer/Consumer, EventRouter, BindMessage, logging interceptor |
| `firestore` | Firestore client wrapper |
| `database` | MySQL connection helper |
| `redis` | Redis client factory |
| `httpclient` | HTTP client with middleware options |
| `crypt` | AES-GCM encryption |
| `hash` | bcrypt hashing with pepper |
| `token` | JWT signing (ES256) |
| `codec` | Base64 encoding/decoding |
| `config` | Env parsing, `ParseEnv[T]`, environment helpers |
| `health` | Liveness, readiness, Prometheus metrics |
| `app` | Shared constants (`CodeSuccess`, `SetTimestamps`) |

These packages do **not** live in this repository — services import them, never vendor or copy them.

---

## Quick Start

### Prerequisites

- Go 1.26+
- Access to the private module host `gitlab.com/b2c-e-commerce-platform/platform/backend`
- A valid `.env` file based on `.env.template`

Set `GOPRIVATE` for private modules:

```bash
go env -w GOPRIVATE=gitlab.com/b2c-e-commerce-platform/platform/backend
```

### Local Setup

1. Copy `.env.template` to `.env` and fill in the values.
2. Run `make setup` to install project tools and hooks.
3. Run `make test` to confirm the workspace is healthy.
4. Run `make run` to start the service in Docker.

---

## Generating a New Microservice

This repository is a **skeleton** — it provides the scaffolding for new services with no example domains.

1. **Clone** this repo (or use it as a GitLab template)
2. **Rename** the module in `go.mod`
3. **Create** your domains under `app/<domain>/` following the conventions in "How to Extend"
4. **Update** `config/config.go` to match your service's configuration
5. **Wire** HTTP routes in `router/router.go` (inside `registerRoutes`) and Kafka events in `router/subscriber.go` (inside `registerEventRoutes`)
6. **Update** `.env.template`, `VERSION`, `CHANGELOG.md` and CI variables

Keep everything else intact: `main.go`, `router/deps.go` structure, `Makefile`, `Dockerfile`, `.golangci.yaml`, `.mockery.yaml`.

---

## Using This Skeleton with an AI Coding Assistant

This repository ships a self-contained skill at `.github/skills/implementing-go-template-requirements/`. It teaches an LLM-based coding assistant (Claude Code, Cursor, GitHub Copilot Chat, Codex CLI, etc.) to translate **one requirement** (spec line, ticket, bug report, user story) into code under `app/<domain>/` while keeping the scaffold (`main.go`, `config/`, `router/deps.go`, `Makefile`, `Dockerfile`, CI) locked.

### What's in the skill

```text
.github/skills/implementing-go-template-requirements/
├── SKILL.md                            # Entry point: scaffold-lock policy + workflow
├── references/
│   ├── scaffold-lock-policy.md         # ALLOWED / NARROW / FORBIDDEN zones
│   ├── naming-conventions.md           # File prefixes, signature shape, package rules
│   ├── implementation-recipe.md        # Per-task recipes: endpoint / consumer / storage / bugfix / refactor
│   ├── testing-pattern.md              # mockArgs / args / want / prepare table-driven pattern
│   ├── common-module-quickref.md       # wrapper, serror, kafka, app helpers
│   ├── verification-checklist.md       # Pre-commit checklist + diff allowlist gate
│   └── fowler-patterns.md              # Named smells + small-safe-steps refactoring
├── templates/
│   ├── handler.go.tmpl
│   ├── handler_test.go.tmpl
│   ├── consumer.go.tmpl
│   ├── consumer_test.go.tmpl
│   ├── service_test.go.tmpl
│   └── storage.go.tmpl
└── examples/
    └── usage.md
```

### Apply it to your assistant

| Tool | One-time setup | Activation |
|---|---|---|
| **Claude Code** (`claude`) | Symlink into your skills dir: `ln -s "$(pwd)/.github/skills/implementing-go-template-requirements" ~/.claude/skills/` (user-scope) **or** `mkdir -p .claude/skills && ln -s ../../.github/skills/implementing-go-template-requirements .claude/skills/` (project-scope) | Auto-discovered; description triggers on the phrases below. Or force it: `Use the implementing-go-template-requirements skill to ...` |
| **Cursor** | Add a rule in `.cursor/rules/implementing-go-template-requirements.mdc` referencing the SKILL.md content (or `@`-mention it in chat) | Mention the rule, or `@.github/skills/implementing-go-template-requirements/SKILL.md` |
| **GitHub Copilot Chat** | Reference the file in context: `#file:.github/skills/implementing-go-template-requirements/SKILL.md` | Add the `#file:` reference at the top of your prompt |
| **Codex CLI / ChatGPT** | Paste `SKILL.md` into the system prompt or attach the folder as project context | Mention "follow the implementing-go-template-requirements skill" |
| **Generic / other LLMs** | Provide `SKILL.md` (and any referenced files it asks for) as system context | Prompt with one of the trigger phrases below |

### Trigger phrases

- "implement this requirement in the go-template service"
- "add this endpoint per spec without touching infra"
- "fix this bug, business logic only"
- "wire up this Kafka event from the requirement"
- "implement spec.md item N"
- "extend `<domain>` to satisfy `<requirement>`"
- "refactor `<handler|consumer|service>` to address [named smell]" (God Handler, Long Parameter List, Too Many Returns, Feature Envy)

### Example prompts

```text
Implement spec.md §"Create Invoice": add a POST /api/v1/platform/invoice/create
endpoint. Persist in Firestore. Follow the implementing-go-template-requirements
skill.
```

```text
Wire up the INVOICE_PAID Kafka event in the invoice domain. Business logic only.
Use the implementing-go-template-requirements skill.
```

```text
Refactor app/product/handler_create.go — it's a God Handler. Apply the small-safe-steps
workflow from the skill's fowler-patterns reference.
```

### Scaffold-lock guarantee

The skill enforces three zones:

| Zone | What the assistant may do |
|---|---|
| ✅ ALLOWED — `app/<domain>/**` | Edit freely within the conventions |
| ⚠️ NARROW — `router/router.go` / `router/subscriber.go` / `spec.md` | Add or change ONLY the named block (e.g. one `register<Domain>Routes` function) |
| 🛑 FORBIDDEN — `main.go`, `config/`, `router/deps.go`, `Makefile`, `Dockerfile`, CI, tooling | STOP and ask the user before touching |

If a requirement genuinely needs a scaffold delta (new database, new env var, new middleware), the skill stops and surfaces the conflict instead of silently editing locked files. Full rationale in `.github/skills/implementing-go-template-requirements/references/scaffold-lock-policy.md`.

---

## Project Structure

```text
.
├── app/                                  # (empty) — add app/<domain>/ aggregates here
├── config/
│   ├── config.go
│   └── config_test.go
├── router/
│   ├── deps.go                           # Composition root — infrastructure clients
│   ├── router.go                         # Gin engine + registerRoutes hook
│   └── subscriber.go                     # Kafka lifecycle + registerEventRoutes hook
├── .github/
│   └── skills/
│       └── implementing-go-template-requirements/   # AI coding assistant skill
├── .scripts/                             # Dev setup, CI, deployment scripts
├── main.go
├── go.mod / go.sum
├── Makefile
├── Dockerfile
├── gitlabci.yml
├── spec.md                               # API request/response spec
├── VERSION / CHANGELOG.md
├── .env.template
├── .golangci.yaml
└── .mockery.yaml
```

Each `app/<domain>/access/` directory should contain domain-specific infrastructure wrappers, categorized by prefix:

| Prefix | Fowler Pattern | Example |
|--------|---------------|----------|
| `storage_<dep>.go` | Repository | Firestore, MySQL, PostgreSQL, S3/GCS |
| `cache_<dep>.go` | Cache | Redis, Memcached |
| `client_<dep>.go` | Gateway | HTTP APIs, gRPC services |

Each file holds the interface, implementation, and domain model together — no separate `model.go` or `errors.go`. A `mocks/` subdirectory contains generated test doubles.

---

## Package Usage Examples

### `logger` — Structured Logging

Initialize once in `main.go`. Replacers are composable — each maps slog keys to platform-specific names.

```go
import "gitlab.com/b2c-e-commerce-platform/platform/backend/common/logger"

// Initialize with cloud-specific key replacers and sensitive-field masking.
_ = logger.New(
    logger.AWSKeyReplacer,        // msg→message, time→timestamp
    logger.OpenSearchKeyReplacer, // msg→message, time→@timestamp, level→log.level
    logger.CensorReplacer,        // masks password, access_token, api_key, secret
)
```

Register additional sensitive fields at startup:

```go
logger.AddCensor("card_number", "****-****-****-****")
logger.AddCensor("cvv", "***")

// Or bulk-load from config:
logger.LoadCensorsFromMap(map[string]string{
    "email": "***EMAIL***",
    "ssn":   "***SSN***",
})
```

---

### `serror` — Structured Error Wrapping

Wraps errors with source-location tracking and investigation context. The observability middleware automatically extracts and logs these fields.

```go
import "gitlab.com/b2c-e-commerce-platform/platform/backend/common/serror"

// Wrap an existing error (captures file:line:func)
if err := db.Insert(ctx, record); err != nil {
    return serror.Wrap(err)
}

// Create a new error
return serror.New("validation failed")

// Attach investigation context (flows to access log automatically)
return serror.Wrap(err).With(
    slog.String("organization_id", orgID),
    slog.String("product_name", req.Name),
)
```

---

### `wrapper` — Standard HTTP Response

Generic response envelope with metadata for the access log middleware.

```go
import "gitlab.com/b2c-e-commerce-platform/platform/backend/common/wrapper"
import "gitlab.com/b2c-e-commerce-platform/platform/backend/common/app"

// Request binding (returns (T, bool); auto-responds 400 on failure)
req, ok := wrapper.BindJSON[CreateProductRequest](c, slog.String("handler", "CreateProduct"))
if !ok {
    return
}

// Success response
wrapper.Respond(c, wrapper.ResponseOption[CreateProductResponse]{
    HTTPStatus: http.StatusCreated,
    Code:       app.CodeSuccess,
    Message:    app.MessageSuccess,
    Data:       &CreateProductResponse{ProductID: productID},
})

// Error response (Err flows to AccessLog middleware for structured logging)
wrapper.Respond(c, wrapper.ResponseOption[CreateProductResponse]{
    HTTPStatus: http.StatusInternalServerError,
    Code:       app.CodeInternalError,
    Message:    app.MessageInternalError,
    Err: serror.Wrap(err).With(
        slog.String("product_name", req.Name),
    ),
})
```

---

### `config` — Environment-Based Configuration

Loads configuration from environment variables using struct tags.

```go
import "gitlab.com/b2c-e-commerce-platform/platform/backend/common/config"
import myconfig "gitlab.com/b2c-e-commerce-platform/platform/backend/project-skeleton/config"

// Load the full application config (prefix-based)
cfg := myconfig.C(config.Env)

// Environment checks
if config.IsLocalEnv() {
    // local-only setup
}
if config.IsProdEnv() {
    // production-only setup
}
```

---

### `kafka` — Producer Logging Interceptor

Wraps a producer with structured logging. Three modes: Debug, Meta, Silent.

```go
import "gitlab.com/b2c-e-commerce-platform/platform/backend/common/kafka"

producer := kafka.MustNewProducer(cfg)

// Auto-select mode from ENV (LOCAL/DEV→Debug, UAT/PROD→Meta)
logged := kafka.WithLoggingFromEnv(producer, os.Getenv("ENV"))

// Or explicit mode
debug  := kafka.WithLogging(producer, kafka.LogInterceptorOption{Mode: kafka.LogModeDebug})  // full payload
meta   := kafka.WithLogging(producer, kafka.LogInterceptorOption{Mode: kafka.LogModeMeta})   // metadata only
silent := kafka.WithLogging(producer, kafka.LogInterceptorOption{Mode: kafka.LogModeSilent}) // no logging

// In PROD (Meta mode), attach investigation attrs — no payload is logged
logged.SendMessageWithOption("topic", msg, kafka.SendMessageOption{
    LogAttrs: []slog.Attr{
        slog.String("organization_id", orgID),
    },
})
```

---

### `kafka` — Consumer & Event Router

Event-driven consumer with routing by event name.

```go
import "gitlab.com/b2c-e-commerce-platform/platform/backend/common/kafka"

// Create a consumer group
group := kafka.MustNewConsumerGroup(kafka.ConsumerConfig{
    KafkaConf: kafka.NewConsumerConfigAtLeastOnce(),
    Brokers:   []string{"broker-1:9092"},
    GroupID:   "project-skeleton",
})

// Register event handlers per aggregate
handlers := map[string]kafka.KafkaHandler{
    "PRODUCT_CREATED": productHandler.OnProductCreated,
    "PRODUCT_UPDATED": productHandler.OnProductUpdated,
    "MEMBER_CREATED":  memberHandler.OnMemberCreated,
}

// Create event router (acts as access-log for the async path)
processor := kafka.NewEventRouter(handlers)
handler := kafka.NewConsumerGroupHandler(ctx, processor)

// Consume
group.Consume(ctx, []string{"events"}, handler)
```

---

## Runtime Flow

1. `main.go` loads configuration and initializes structured logging (`logger.New`).
2. `router.StartSubscriber(...)` starts the Kafka consumer group (if broker settings are present). This starts **before** HTTP to ensure event processing begins immediately.
3. `router.New(...)` builds the Gin engine, creates infrastructure clients via `NewDeps`, registers middleware and all API routes.
4. The HTTP server starts with graceful shutdown wired via `signal.NotifyContext`.
5. On SIGINT/SIGTERM: HTTP server drains → Kafka consumer stops → infrastructure clients close → process exits.

---

## Configuration

Configuration is loaded from environment variables in `config/`.

| Area | Variables |
|---|---|
| Server | `ENV`, `HOSTNAME`, `PORT` |
| CORS | `ACCESS_CONTROL_ALLOW_ORIGIN` |
| Headers | `REF_ID_HEADER_KEY` |
| JWT | `JWT_ISSUER`, `JWT_AUDIENCE`, `JWT_EXP_DURATION`, `SECRET_JWT_PRIVATE_KEY` |
| Firestore | `GCP_PROJECT_ID`, `GCP_CREDENTIALS_JSON`, `GCP_FIRESTORE_DATABASE_ID`, `GCP_FIRESTORE_CONNECT_TIMEOUT` |
| Google OAuth | `GOOGLE_OAUTH2_VERIFY_TOKEN`, `GOOGLE_OAUTH2_GET_USER_PROFILE`, `GOOGLE_OAUTH2_REVOKE_TOKEN` |
| Secrets | `SECRET_AESGCM_KEY`, `SECRET_HASH_PEPPER` |
| Kafka consumer | `KAFKA_BROKERS`, `KAFKA_GROUP_ID`, `KAFKA_TOPICS`, `KAFKA_OFFSETS_INITIAL`, `KAFKA_REBALANCE_STRATEGY` |
| Kafka producer | `KAFKA_PRODUCER_BROKERS` |
| MySQL | `MYSQL_HOST`, `MYSQL_PORT`, `SECRET_DB_USERNAME`, `SECRET_DB_PASSWORD`, `MYSQL_DATABASE` |
| Redis | `REDIS_ADDR`, `SECRET_REDIS_PASSWORD` |
| HTTP Client | `HTTP_CLIENT_ENABLE_LOG_DEBUG` |

Notes:

- `GCP_CREDENTIALS_JSON` and `SECRET_JWT_PRIVATE_KEY` are base64-decoded at startup.
- Kafka subscriber startup is skipped when `KAFKA_BROKERS`, `KAFKA_GROUP_ID`, or `KAFKA_TOPICS` are empty.
- Kafka producer is skipped if `KAFKA_PRODUCER_BROKERS` is empty.

---

## Commands

The `Makefile` is the main entry point for development tasks.

| Command | Description |
|---|---|
| `make setup` | Install tools and project hooks |
| `make upgrade` | Upgrade dev tools (golangci-lint, govulncheck, swagger, pkgsite) |
| `make mod` | Run `go fmt` and `go mod tidy` |
| `make lint` | Run `golangci-lint` with auto-fix |
| `make test` | Run full test suite with race detection |
| `make test-integration` | Run integration tests (requires external services) |
| `make coverage` | Generate and open HTML coverage report |
| `make vuln` | Run `govulncheck` |
| `make precommit` | Run mod + lint + test + vuln + vet before committing |
| `make ci` | Full CI pipeline (precommit + diff check) |
| `make docker` | Build the Docker image |
| `make run` | Start the container with `.env` |
| `make swagger` | Regenerate OpenAPI spec |
| `make openapi` | Serve Swagger UI locally on port 8910 |
| `make doc` | Serve Go package docs locally on port 6060 |
| `make bump-version` | Bump version (usage: `make bump-version version=v0.0.1`) |
| `make clean` | Remove build artifacts and caches |
| `make release-cloudrun` | Build, push, and deploy to Cloud Run |

---

## HTTP APIs

HTTP routes are registered in `router/router.go` via the `registerRoutes(r, d)` hook.

| Area | Routes |
|---|---|
| Health | `GET /liveness`, `GET /readiness`, `GET /metrics` |
| Domain | (none — register your `register<Domain>Routes(r, d)` functions inside `registerRoutes`) |

Detailed request and response shapes live in `spec.md`.

---

## Kafka Events

Kafka event routing is registered in `router/subscriber.go` via the `registerEventRoutes(d)` hook.

The skeleton ships with no event registrations. For each new aggregate, add a `register<Domain>Events(d)` function in its package that returns a `map[string]kafka.KafkaHandler`, then `mergeRoutes(routes, register<Domain>Events(d))` from inside `registerEventRoutes`.

---

## How to Extend the Codebase

### Add a New Domain Aggregate

1. Create `app/<domain>/`.
2. Create `app/<domain>/access/storage_<dep>.go` with interface + impl + domain model.
3. (Optional) Create `access/cache_<dep>.go` for caching, `access/client_<dep>.go` for external APIs.
4. Add a `handler.go` defining `HandlerConfig` + `handler` struct + `NewHandler`.
5. Add `handler_<action>.go` files for HTTP endpoints (route shape `/api/v1/<domain>/<aggregate>/<action>`, e.g. `/api/v1/platform/product/create`).
6. Add `consumer_<action>.go` files for Kafka events (event names `<DOMAIN>_<AGGREGATE>_<ACTION>` in UPPER_SNAKE, e.g. `PLATFORM_PRODUCT_CREATED`).
7. Keep the boundary thin: split multi-step orchestration out of handlers/consumers into `service_<action>.go` (unexported `*handler` methods).
8. Wire HTTP routes by adding a `register<Domain>Routes(r, d)` function in `router/router.go` and calling it from `registerRoutes`.
9. Wire Kafka events by adding a `register<Domain>Events(d)` function in `router/subscriber.go` and `mergeRoutes`-ing it from `registerEventRoutes`.
10. Write tests for handlers, consumers, and services (the constructor and `access/` layer are out of scope): boundary tests in external `package <domain>_test`, service tests in internal `package <domain>` (`service_<action>_test.go`). Aim for 100% coverage of those in-scope files.

### Add a New HTTP Endpoint

1. Add or update a handler in `app/<domain>/handler_<action>.go` (route `/api/v1/<domain>/<aggregate>/<action>`); extract multi-step logic into `service_<action>.go`.
2. Wire the route in `router/router.go` inside the matching `register<Domain>Routes` function.
3. Add boundary tests beside the handler (`handler_<action>_test.go`, external `package <domain>_test`) and, for any extracted service, an internal-package `service_<action>_test.go`.

### Add a New Kafka Event

1. Add a `consumer_<action>.go` file in the domain package (e.g. `app/product/consumer_create.go`); extract orchestration into `service_<action>.go`.
2. Register the event name (`<DOMAIN>_<AGGREGATE>_<ACTION>`, UPPER_SNAKE, e.g. `PLATFORM_PRODUCT_CREATED`) in `router/subscriber.go` inside the matching `register<Domain>Events` function.
3. Add tests in `consumer_<action>_test.go`.

### Add a New Infrastructure Client

Dependencies fall into two categories that determine how they flow into domain code:

**Raw infrastructure SDKs** (Firestore, MySQL, Redis, S3/GCS, `*http.Client`) — must be wrapped:
1. Add the SDK client field to `Deps` struct in `router/deps.go`.
2. Initialize it in `NewDeps()` and add its `Close()` to the cleanup function.
3. Create `access/storage_<dep>.go`, `access/cache_<dep>.go`, or `access/client_<dep>.go` in the domain package.
4. In `register<Domain>Routes` / `register<Domain>Events`, construct the access-layer impl and pass it via `HandlerConfig`.

**Common module abstractions** (`hash.HashManager`, `crypt.Cipher`, `token.JWTSigner`, `kafka.Producer`) — pass directly:
1. Add the interface field to `Deps` struct (if not already there).
2. Initialize it in `NewDeps()` with the corresponding `MustNew*` constructor.
3. Pass it directly to `HandlerConfig` — no `access/` wrapper needed (they are already interfaces).

### Dependency Injection Pattern (`router/deps.go`)

All infrastructure clients are initialized once in `router/deps.go` and passed to handlers via the `Deps` struct. This is the **composition root** — it keeps `main.go` thin and co-locates cleanup with initialization.

#### Step 1 — Register the client in `Deps`

```go
// router/deps.go
type Deps struct {
    cfg             config.Config

    // Raw SDK handles — wrapped in access/ before reaching domain code
    httpClient      *http.Client
    firestoreClient *commonfirestore.Client
    mysqlClient     *sql.DB
    redisClient     redis.UniversalClient

    // Common module abstractions — already interfaces, passed directly to HandlerConfig
    hash            hash.HashManager
    cipher          crypt.Cipher
    token           token.JWTSigner
    producer        kafka.Producer
}
```

#### Step 2 — Initialize and clean up in `NewDeps`

```go
func NewDeps(ctx context.Context, cfg config.Config) (Deps, func()) {
    httpClient := httpclient.NewHTTPClient(...)
    fs := commonfirestore.MustNewClient(ctx, newFirestoreConfig(cfg))
    db := database.MustNewMySQLWithConfig(newMySQLConfig(cfg))
    rdb := commonredis.MustNew(cfg.Redis.Addr, cfg.Redis.Password)
    producer := newProducer(cfg)

    d := Deps{
        cfg:             cfg,
        httpClient:      httpClient,
        firestoreClient: fs,
        mysqlClient:     db,
        redisClient:     rdb,
        hash:            newHashManager(cfg),
        cipher:          newCipher(cfg),
        token:           newTokenManager(cfg),
        producer:        producer,
    }

    cleanup := func() {
        _ = fs.Close()
        _ = db.Close()
        _ = rdb.Close()
        if producer != nil {
            _ = producer.Close()
        }
    }

    return d, cleanup
}
```

#### Step 3 — Pass to domain handlers via `router.go`

```go
// router/router.go
func registerProductRoutes(r *gin.Engine, d Deps) {
    // Raw SDK → wrap in access/ layer (domain never sees the SDK directly)
    productStorage := productaccess.NewProductStorage(d.firestoreClient.Inner())

    h := product.NewHandler(product.HandlerConfig{
        // access/ interfaces — domain-specific wrappers
        ProductStorage: productStorage,
        // common module interfaces can be passed directly:
        // Hash: d.hash,
        // Cipher: d.cipher,
    })

    productGroup := r.Group("/api/v1/platform/product")
    {
        productGroup.POST("/create", h.CreateProduct)
    }
}
```

---

## Maintenance Notes

- Keep `main.go` thin: initialization and shutdown only.
- Keep domain logic in `app/` rather than in `router/` or helper packages.
- Prefer small files with responsibility-based names over large catch-all files.
- Use `spec.md` when changing request or response payloads.
- Update tests next to the code they validate.
- No cross-domain imports (`app/product` never imports `app/member`).
- Use compile-time interface checks: `var _ Interface = (*impl)(nil)`.
- File naming uses prefix convention: `handler_`, `consumer_`, `service_`, `storage_`, `cache_`, `client_`.
- Routes follow `/api/v1/<domain>/<aggregate>/<action>`; Kafka event names follow `<DOMAIN>_<AGGREGATE>_<ACTION>` (UPPER_SNAKE), mirroring the route segments.
- Comments are lean: a terse doc line on exported identifiers only — no inline narration, decorative dividers, or `// Arrange/Act/Assert` markers.
- Unit tests cover handlers, consumers, and services; the constructor (`New*`) and the `access/` layer are out of scope. Boundary tests live in external `package <domain>_test`; service tests in internal `package <domain>`.
- Co-locate domain models and errors with the access file that uses them — no separate `model.go` or `errors.go` in `access/`.
- Raw SDK handles must be wrapped in `access/`; common module interfaces pass directly to `HandlerConfig`.

### Refactoring Guidelines
When addressing tech debt or making structural improvements, follow **Martin Fowler's refactoring principles**:
- **Layer Mapping**: Handlers strictly perform transport concerns. Service logic coordinates flow without business rules. Domain models contain all domain/business logic. Adapters manage pure I/O.
- **Workflow**: Identify smells (e.g., God handlers, primitive obsession, conditional explosions), make small isolated changes, verify with tests, and repeat. Do not rewrite wholesale.
- **Tell, Don't Ask**: Move data manipulation into the domain models representing the data; don't pull data out to manipulate it externally.

---

## Troubleshooting

- If startup fails early, check base64-encoded secrets (`SECRET_JWT_PRIVATE_KEY`, `GCP_CREDENTIALS_JSON`) first.
- If HTTP starts but Kafka does not, verify `KAFKA_BROKERS`, `KAFKA_GROUP_ID`, and `KAFKA_TOPICS` are present and non-empty.
- If Firestore access fails, check `GCP_PROJECT_ID`, `GCP_CREDENTIALS_JSON`, and `GCP_FIRESTORE_DATABASE_ID`.
- If MySQL connection fails, verify `MYSQL_HOST`, `MYSQL_PORT`, `SECRET_DB_USERNAME`, `SECRET_DB_PASSWORD`, and `MYSQL_DATABASE`.
- If Redis connection fails, verify `REDIS_ADDR` and `SECRET_REDIS_PASSWORD`.

---

## Repository Purpose

This repository serves as a **foundational skeleton** for new A-Team microservices. It ships with no example domains — only the scaffolding (bootstrap, config, deps, router/subscriber hooks, build pipeline) needed to start coding.

When creating a new service:

- **Keep**: `main.go` structure, `router/` wiring pattern, `config/` pattern, `Makefile`, `Dockerfile`, `.golangci.yaml`, `.mockery.yaml`, middleware chain, all tooling scripts.
- **Add**: `app/` domains for your business logic, `config/config.go` fields for your service, route and event registrations inside the existing hooks.
- **Import**: All infrastructure from the `common` module — never copy.
