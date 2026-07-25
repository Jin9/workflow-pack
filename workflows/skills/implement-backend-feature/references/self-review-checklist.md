# Self-Review Checklist

Applied at step 6 of `SKILL.md`, before emitting any output. Every item is
YES/NO. Any NO halts emission and routes per the table at the bottom.

Source: extracted from the pre-consolidation source pack (provenance: workflows/skills/README.md) safety
workflow steps 4–7 and the validation gate. Reformatted as a deterministic
checklist for the Generate stage.

## A. Data correctness

- [ ] Every command handler enforces an invariant from the design's L1.
- [ ] Every query handler is side-effect free.
- [ ] Every persistence call runs inside an explicit transaction scope (or
      explicitly documents why a single-statement write is sufficient).
- [ ] Cross-aggregate writes use outbox or saga — never two repos in one
      transaction without justification in `decision_metadata`.
- [ ] Concurrency-sensitive paths use `SELECT ... FOR UPDATE`, an advisory
      lock, or a documented compare-and-swap.
- [ ] Migrations are additive. No edit to committed migration files.

## B. Idempotency

- [ ] Every external side-effect path takes `idempotency_key` at the boundary.
- [ ] Replay with the same key returns the stored response without re-running
      the side-effect.
- [ ] Replay with the same key + different `request_hash` returns a 409 /
      domain-equivalent error.
- [ ] Naturally idempotent paths (GET, pure analyze) state so in
      `idempotency_strategy` and skip persistence.
- [ ] Kafka consumers dedupe on `(topic, partition, offset)` AND on business
      idempotency key.

## C. Errors

- [ ] Every returned error is wrapped with `fmt.Errorf("...: %w", err)`.
- [ ] Every error has a class (`client | server | dependency`) attached at the
      type level, not inferred at the edge.
- [ ] No panic in a request or worker path (except a transport-edge recover
      that increments a metric and emits an audit event).
- [ ] No `_ = err`. No silently dropped errors.
- [ ] Public error responses contain no SQL fragments, no internal IDs the
      caller doesn't own, no stack traces, no env values, no PII.

## D. Context propagation

- [ ] Every exported function takes `ctx context.Context` as first parameter.
- [ ] No `context.Background()` / `context.TODO()` inside a request path.
- [ ] ctx flows into every repository call, HTTP/gRPC client, Kafka producer,
      and downstream goroutine.
- [ ] No ctx stored in a struct.

## E. Observability

- [ ] Every declared failure mode increments a metric (counter).
- [ ] Every handler emits a span; span name = `package.Method`.
- [ ] Every log line includes `trace_id`. Where actor / target are known, they
      are present.
- [ ] Metric labels have bounded cardinality. No user IDs or free-form strings
      as labels.

## F. Security

- [ ] AuthN is checked at the transport boundary. No code reaches the use case
      without an authenticated principal (or an explicitly public endpoint
      named in the design).
- [ ] AuthZ is checked against the use case's required permission, not the
      transport route.
- [ ] Every input is validated using the repo's validator before reaching the
      use case.
- [ ] No SQL string concatenation. All queries parameterized.
- [ ] No secrets in code, fixtures, or test data. No connection strings.
      No tokens. No private keys.
- [ ] No `curl`, `wget`, or `net/http` to external hosts inside tests.
- [ ] No hand-rolled crypto. Repo-approved crypto/auth helpers only.
- [ ] PII fields named in the design are masked in logs.

## G. Audit

- [ ] Every state-changing path emits exactly one audit event.
- [ ] Every emitted event type appears in `audit_events_emitted` output.
- [ ] Audit event payload includes actor, action, target, timestamp,
      trace_id, decision_metadata.
- [ ] Read-only paths emit no audit event (not a NO — just a sanity check).

## H. Compensation

- [ ] Every irreversible external side-effect declares a compensating action
      in `compensating_actions` output.
- [ ] If compensation is impossible, `decision_metadata.pattern_choices`
      explains why and the workflow stage is set to `human-queue`.

## I. Tests

- [ ] Companion tests exist for every emitted production file.
- [ ] Per-file coverage `>= test_coverage_target` (default 0.80).
- [ ] Tests are table-driven for handlers, services, and repo unit tests.
- [ ] No tests depend on wall-clock time, network, or random ordering.
- [ ] No `t.Skip(...)` without a named unblock condition.

## J. Scope discipline

- [ ] No new Go modules added that are not in `go.mod`.
- [ ] No edits to generated artifacts (protobuf, OpenAPI clients).
- [ ] No reformatting / cleanup outside the changed files.
- [ ] No widening of a public contract beyond what the design declares.

## Routing of any NO

| Section with NO | Action |
|-----------------|--------|
| A (data correctness), B (idempotency), F (security) | `human-queue` immediately. Do not emit. |
| C (errors), D (context), G (audit), H (compensation) | `loop_back` to design (the design did not specify enough discipline) |
| E (observability), I (tests), J (scope) | Fix in place inside step 4 / 5, then re-run self-review. If still NO after one re-try, `human-queue`. |
