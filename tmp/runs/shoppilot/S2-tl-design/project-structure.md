# ShopPilot — project structure (polyrepo · Go + React/TS)

> Derived from the S1 BA pack (4 epics: AUTH · CHECKOUT · ORDER · INVENTORY) and the pipeline's implementation
> conventions. Backend services reuse the **canonical Go skeleton** in
> [`repo-generator/project-skeleton/`](../../../../repo-generator/project-skeleton/) (stamped by
> [`generate-repos.sh`](../../../../repo-generator/generate-repos.sh)); the frontend is a single React/TS app.
> This is the intended layout S4a/S4b will generate into — **not** committed code.

## Topology

**Polyrepo.** One Go module per bounded context + one frontend app. Bounded contexts split by **epic workstream**,
never by tech layer. Services share nothing in-process; they talk over **sync HTTP** (request/response) and **async
Kafka events**. No cross-domain Go imports — within a service, aggregates communicate via events too.

| Repo | Bounded context (epic) | Module path | Default branch |
|---|---|---|---|
| `auth-service` | Customer auth & sessions (EPIC-AUTH) | `gitlab.com/b2c-e-commerce-platform/platform/backend/auth-service` | `develop` |
| `inventory-service` | Stock reservation & audit (EPIC-INVENTORY) | `…/backend/inventory-service` | `develop` |
| `checkout-service` | Server-side checkout & mock payment (EPIC-CHECKOUT) | `…/backend/checkout-service` | `develop` |
| `order-service` | Orders, fulfillment & price snapshot (EPIC-ORDER) | `…/backend/order-service` | `develop` |
| `web` | Storefront + back office | (npm workspace) | `develop` |

Audit is **cross-cutting** (every state-change writes `{event, actor, ts, before, after, outcome, audit_id}`):
each service owns its append-only audit table and publishes to a shared `audit` topic — see `architecture-overview.md`.

### Generate the four backend repos

```bash
# from the workspace root — stamps each repo from the skeleton, rewrites the module path,
# syncs the implementing-go-template-requirements skill, and runs `git init -b develop`:
./repo-generator/generate-repos.sh auth-service inventory-service checkout-service order-service
# → /generated/<name>/ per repo
```

## Canonical Go service skeleton (every backend repo)

Faithful to `repo-generator/project-skeleton/` (the 4-layer DDD + CQRS house style):

```
<service>/
├── main.go                     # bootstrap + graceful shutdown; log/slog + config init
├── go.mod  go.sum              # module: …/backend/<service>
├── config/
│   ├── config.go               # env-backed configuration
│   └── config_test.go
├── router/
│   ├── deps.go                 # composition root — infra clients (MySQL, Kafka, Redis)
│   ├── router.go               # Gin engine + HTTP route registration
│   └── subscriber.go           # Kafka event → handler routing
├── app/                        # DDD: one package per aggregate (no cross-domain imports)
│   └── <aggregate>/            # ← per-service breakdown below
├── migrations/                 # SQL schema migrations — ADD per service (not in base skeleton)
├── Makefile  Dockerfile  gitlabci.yml
├── .golangci.yaml  .mockery.yaml  .env.template  .gitignore
├── .scripts/                   # dev tooling (setup, version bump, release-cloudrun)
├── .local/githook/             # pre-commit config
├── .github/skills/implementing-go-template-requirements/   # canonical impl skill (synced at generation)
└── VERSION  CHANGELOG.md  README.md  spec.md
```

### Aggregate package shape (`app/<aggregate>/`)

Type prefix comes **first** (`handler_`, `consumer_`, `service_`, `storage_`/`cache_`/`client_`); one `_test.go`
per in-scope file; `access/` is the repo/cache/gateway layer (model + errors co-located in each file):

```
app/<aggregate>/
├── handler.go                  # HandlerConfig → handler → NewHandler(cfg) *handler
├── handler_<action>.go         # one HTTP action per file (+ Request/Response types)
├── handler_<action>_test.go
├── consumer_<action>.go        # one Kafka event per file (+ Message types)
├── consumer_<action>_test.go
├── service_<action>.go         # private helpers split from a handler/consumer
├── service_<action>_test.go
└── access/
    ├── storage_<dep>.go        # MySQL repository (sentinel errs + iface + impl + model, co-located)
    ├── cache_<dep>.go          # Redis cache (optional)
    └── client_<dep>.go         # external API gateway (e.g. mock PSP)
```

## Per-service `app/` breakdown

### `auth-service` — EPIC-AUTH

```
app/
├── auth/                       # registration + login + logout; generic invalid-credentials; login rate-limit
│   ├── handler_register.go     handler_login.go     handler_logout.go
│   ├── service_authenticate.go # password hash verify; no account enumeration
│   └── access/
│       ├── storage_customer.go # Customer (email unique, password one-way hash)
│       └── cache_ratelimit.go  # Redis login-attempt counters
└── session/                    # token lifecycle
    ├── handler_refresh.go      # 15-min access + 14-day refresh; atomic rotation; replay → revoke family
    ├── service_rotate.go       # single-use rotation, idempotent under concurrent refresh
    └── access/
        ├── storage_session.go  # Session + refresh-token family (revoked_at, family_id)
        └── cache_token.go      # Redis access-token / opaque lookups
# emits (audit): auth.login · auth.refresh · auth.logout    (no token values ever logged)
```

### `inventory-service` — EPIC-INVENTORY

```
app/
├── stock/                      # available / reserved / sold per SKU; never negative
│   ├── handler_reserve.go      # SYNC + atomic + idempotent (confirm key) — resolves last-item race at confirm
│   ├── handler_adjust.go       # admin set with mandatory reason; reject if would drop below reserved
│   ├── consumer_released.go    # release on order payment-failed/timeout/cancelled
│   ├── consumer_sold.go        # convert reserved → sold on payment success
│   └── access/storage_stock.go
└── reservation/                # 30-minute TTL holds
    ├── service_sweep.go        # TTL auto-release sweep (background)
    └── access/storage_reservation.go
# emits: stock.reserved · stock.released · stock.adjusted (audit on every change)
```

### `checkout-service` — EPIC-CHECKOUT (checkout + mock payment)

```
app/
├── cart/                       # line items; 30-day expiry
│   ├── handler_get.go  handler_add_item.go  handler_remove_item.go
│   └── access/storage_cart.go
├── checkout/                   # server-side total + idempotent confirm (orchestrates reserve + order create)
│   ├── handler_confirm.go      # idempotency key; total = subtotal − coupon + shipping (free ≥1500 THB else 60)
│   ├── service_compute_total.go  service_apply_coupon.go   # coupon re-validated AT confirm, floored at 0
│   └── access/
│       ├── client_inventory.go # SYNC reserve call to inventory-service
│       └── client_order.go     # create order (awaiting-payment) in order-service
├── coupon/                     # one coupon per order; expiry checked at confirm
│   └── access/storage_coupon.go
└── payment/                    # mock PSP capture; provider-replay dedup
    ├── handler_capture.go      # mock success / failure / timeout
    ├── consumer_provider_callback.go   # dedup on provider event id → applies once (no double-charge)
    └── access/
        ├── client_psp.go       # mock provider gateway (no PAN/CVV — PSP tokenizes; PCI-DSS boundary)
        └── storage_payment.go
# emits: order.created (awaiting-payment) · order.payment_captured {success|failure|timeout}
```

### `order-service` — EPIC-ORDER

```
app/
├── order/                      # Order aggregate: frozen snapshots + forward-only state machine
│   ├── handler_create.go       # snapshot price/items/address at creation; order no. ORD-YYYYMMDD-XXXXXX
│   ├── handler_get.go          # own-order isolation (customer sees only their orders)
│   ├── handler_transition.go   # admin: paid→packing→shipped(tracking req'd)→delivered; reject backward; idempotent
│   ├── consumer_paid.go        # on order.payment_captured success → paid
│   ├── consumer_payment_failed.go  # → payment-failed / payment-timeout
│   └── access/storage_order.go # Order + immutable OrderSnapshot
└── shipment/                   # shipment + tracking number (required for shipped → delivered)
    └── access/storage_shipment.go
# emits: order.status_changed {before, after, actor}   (audit on every transition)
```

## Frontend — `web/` (React/TS, Next.js)

Provisional; finalized against the **S1.5 UX pack** (design tokens + route map + maturity).

```
web/
├── package.json  tsconfig.json  next.config.js
├── src/
│   ├── app/                        # Next.js app router
│   │   ├── (storefront)/           # public + customer
│   │   │   ├── page.tsx            # browse / search
│   │   │   ├── products/  cart/  checkout/
│   │   │   ├── orders/  orders/[id]/   # own-order list + tracking (frozen snapshot)
│   │   │   └── (auth)/ login/ register/
│   │   └── admin/                  # back office
│   │       ├── orders/             # fulfillment state-machine UI
│   │       ├── inventory/          # stock adjust (reason required)
│   │       └── coupons/
│   ├── components/                 # design-system components (from ux.pack tokens)
│   ├── lib/
│   │   ├── api/                    # typed clients per S3 contract (auth · checkout · order · inventory)
│   │   └── auth/                   # access/refresh token handling
│   └── styles/                     # tokens from ux.pack
├── public/
└── __tests__/                      # (or co-located *.test.tsx)
```

## Notes

- **`migrations/`** and the concrete `app/<aggregate>` files above are the **target** of S4a; the base skeleton
  ships only `app/.gitkeep`. Counts/filenames here follow the `naming-conventions` (load-bearing: routes, mocks, and
  tests are wired by convention).
- HTTP routes: `/api/v1/<namespace>/<aggregate>/<action>`; event topic keys: `<DOMAIN>_<AGGREGATE>_<ACTION>` (UPPER_SNAKE).
- Cross-**service** calls are HTTP or Kafka; cross-**aggregate** (same service) is Kafka only — never a direct import.
