# S4a · Backend implementation + S4a-r review

**Skills:** `implement-backend-feature 1.0.0` (impl, auto/sandbox) · `review-backend-code 1.0.0` (review,
async-peer) · **status:** ✅ real Go emitted under [`services/`](services/) — 4 microservices that **compile and
pass `go test` offline** against mocked access interfaces. (Not live-runnable without real
Firestore/MySQL/Redis/Kafka; `golangci-lint`/`govulncheck` are not run offline.)

Generates production Go per bounded context from the approved design + S3 contracts, with idempotency, audit
events, and compensating actions; the paired review verifies it against the banking-grade rules.

## Real services ([`services/`](services/))

Stamped from the canonical `reference/repo-generator/` go-template scaffold (module
`gitlab.com/example-org/platform/backend/<svc>`, `git init -b develop` stripped) and implemented
under each service's locked-scaffold `app/<domain>/` zone — so the on-disk tree is the **real go-template
layout** (`main.go` at root, `app/<domain>/handler_*.go · service_*.go · consumer_*.go · access/storage_*.go`),
**not** the `internal/...` layout the YAML/early manifest speculated.

| Service | Domain | In-scope coverage |
|---|---|---|
| `services/auth` | login (no-enumeration), single-use refresh rotation + token-family revoke | 96.6% |
| `services/inventory` | atomic conditional decrement (ADR-002), 30m TTL release (ADR-004), status consumer | 100% |
| `services/checkout` | idempotency keys, server-computed total, sync reserve+create (ADR-007), transactional outbox (ADR-008), mock PSP | 96.6% |
| `services/order` | idempotent create, immutable snapshot (ADR-003), forward-only state machine, payment consumer | 100% |

Per service, `go build ./... && go vet ./... && go test -race ./app/...` all pass offline; in-scope =
handlers/services/consumers (the `access/` infra seam compiles against the real clients but is excluded from
coverage and mocked in tests). Scaffold-locked files (`main.go`, `config/`, `router/deps.go`, `go.mod`, CI) are
unmodified; only `app/<domain>/**` + the NARROW `register<Domain>Routes`/`register<Domain>Events` hooks + `spec.md`.

## Artifacts
- **`backend-artifacts.json`** — the impl contract (`workflows/schemas/backend-artifacts.json`), **computed from
  the real files** by `_sim/simulate.py`: `files_generated[]` (real path · `sha256` of file bytes · real line
  count), `tests_generated[]` (real `coverage_pct`), `idempotency_strategy`, `compensating_actions[]` (incl. the
  SAGA revoke + TTL release), `audit_events_emitted[]`, `decision_metadata`.
- **`review/backend-review.json`** — the review contract (`workflows/schemas/backend-review.json`):
  **verdict `approve`**, empty `findings`, `claims_verified` (idempotency keys, audit on every state change,
  compensating release, outbox), `claims_unverified: []`, `audit_metadata` (`files_scanned`/`lines_scanned`
  derived from the real manifest).

> Both skill schemas are `additionalProperties:false` and emit **no top-level `audit_id`** (audit lives in the
> emitted code's `audit_events` / `audit_metadata`); the YAML's speculative `go_files/test_files/audit_id` are
> not the built contract.
