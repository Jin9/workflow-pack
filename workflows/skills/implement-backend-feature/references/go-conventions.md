# Go Conventions (Banking-Grade Generate Stage)

These conventions apply to code emitted by step 4 of `SKILL.md`. They are
banking-flavored: stricter than vanilla Go idiom on errors, context, audit,
and test discipline. Source: extracted from
the pre-consolidation source pack (provenance: workflows/skills/README.md) and augmented
with conventions enforced by the workflow engine.

**Discovery overrides defaults.** If the target package already follows a
different convention (e.g., uses a custom logger, a project-specific error
wrapper, a generated mock library), mirror the existing pattern and emit an
`uncertainty_flag` of kind `convention_conflict` so the template can be
updated by reflection.

## Service Structure

- One deployable per bounded capability.
- Explicit bootstrap: `cmd/<service>/main.go` wires config, logger, tracer,
  metrics, transport, dependencies, then calls a top-level `Run(ctx)`.
- Health (`/healthz`) and readiness (`/readyz`) endpoints required.
- Typed config struct, validated on load. No `os.Getenv` scattered in business code.
- Graceful shutdown: `signal.NotifyContext` → cancel root ctx → drain in-flight
  work with bounded timeout → close transport last.
- Standard observability: structured logger, RED metrics, OpenTelemetry tracer.

## Package Boundaries

- `internal/<capability>/`: domain owner.
  - `domain.go`: aggregates, value objects, invariants.
  - `service.go`: use-case orchestration.
  - `repository.go`: persistence interface + Postgres impl in `repository_pg.go`.
  - `handler.go`: HTTP/gRPC transport, thin.
  - `consumer.go`: Kafka consumer, idempotent.
  - `events.go`: outbound event schemas.
- Interfaces live at the consumer boundary, not the implementor.
- No cross-capability imports except via `pkg/` or events.

## `context.Context`

- Every exported function takes `ctx context.Context` as the first parameter.
  No exceptions for "small" helpers — small helpers grow.
- Never store ctx in a struct.
- Never use `context.Background()` or `context.TODO()` inside a request path.
  Acceptable only in `main.go` (root) and `_test.go`.
- Always propagate ctx into repo calls, HTTP clients, gRPC clients, Kafka
  producers, and downstream goroutines.

## Errors

- Always wrap with `fmt.Errorf("operation: %w", err)`. Operation = the verb
  describing what failed in this layer.
- Define typed errors at the boundary:

```go
type Error struct {
    Class   ErrorClass // client | server | dependency
    Code    string     // stable string for clients
    Message string     // human-safe message, no PII, no internals
    Cause   error      // wrapped for logs only
}
```

- `errors.Is` / `errors.As` for checks. No string matching on error messages.
- Never panic in a request or worker path. Recover only at the transport edge
  with explicit metric increment + audit event for the panic.
- Public error responses MUST NOT leak SQL fragments, internal IDs the caller
  doesn't own, stack traces, or env values.

## Logging, Metrics, Traces

- Use the repo's logger interface. If discovery shows `zap.SugaredLogger`,
  mirror it. If `slog`, mirror it.
- Log levels: `debug` (off in prod), `info` (lifecycle), `warn` (degraded but
  serving), `error` (failed request). No `panic` level.
- Every log line includes: `trace_id`, `actor_id` (where known), `target_id`.
- Metrics: one counter per declared failure mode, one histogram for latency,
  one gauge for in-flight. Label cardinality bounded — no user IDs as labels.
- Traces: span per use-case method. Span name `package.Method`. Record
  attributes for inputs that are not PII.

## CQRS

- Command handlers: task-based, name starts with verb (`DisburseLoan`,
  `ApproveApplication`). Hold the invariant. Take a typed command, return
  a typed result + error.
- Query handlers: side-effect free. Return read models, not aggregates.
- Read models live in a separate package from the write model.

## Event-Driven (Kafka / Outbox)

- Producers: write to outbox table inside the same transaction as the state
  change. A separate dispatcher publishes from outbox to Kafka.
- Consumers: idempotent against `(topic, partition, offset)` and against the
  business idempotency key. Dead-letter on poison after N retries (N from
  config, default 5).
- Event versioning: additive only within a major version. Breaking change =
  new topic + dual-write window.
- Every event carries `event_id` (UUID v4), `occurred_at` (RFC3339),
  `producer` (service name), `trace_id`.

## PostgreSQL

- All queries parameterized. No string concatenation into SQL.
- Migrations are additive (expand → backfill → contract). Never edit a
  committed migration; add a new one.
- Explicit transaction scopes: `BEGIN` and `COMMIT` are visible in the code,
  not implicit through ORM magic.
- Indexes added in the same migration as the query that needs them.
- Concurrency-sensitive paths (decrement balance, allocate slot, etc.) use
  `SELECT ... FOR UPDATE` or an advisory lock — pick one per aggregate and
  document.

## HTTP APIs

- Stable request/response contracts. Versioned in the URL (`/v1/...`) or
  Accept header — follow repo discovery.
- Typed request validation at the handler boundary using the repo's validator.
- Consistent error envelope:

```json
{"code": "INVALID_AMOUNT", "message": "amount must be > 0", "trace_id": "..."}
```

- OpenAPI / proto updated in the same PR as the handler change when the repo
  already maintains them.
- Backwards-compatible additions only (new optional field, new endpoint).
  Breaking change requires a new version + deprecation window.

## Tests

- Table-driven for handlers, services, and repository unit tests.
- One assertion library per repo — use what discovery shows (`testify`,
  `gotest.tools`, stdlib).
- Coverage `>= test_coverage_target` (default 0.80) on the emitted files.
  Coverage measured per-file, not aggregate, to prevent dilution.
- Mock at the interface boundary the package owns. No mocking of stdlib.
- Integration tests against real Postgres / Kafka via `testcontainers`
  if discovery shows the repo uses it; otherwise note absence in
  `decision_metadata.pattern_choices` and stick to unit tests.
- No flaky tests. A test that depends on wall-clock time, network, or random
  ordering is rejected at self-review.

## Linting

- `golangci-lint run` must exit clean. If the repo has a config, use it. No
  `//nolint:...` without a comment explaining why.
- `go vet ./...` must exit clean.
- `gofmt -s -d` returns empty diff. `goimports -l` returns empty list.
