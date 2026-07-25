# Review Checklist

Applied at steps 4 + 5 of `SKILL.md` — a deterministic YES/NO scan over
every file in `code_under_review` and `tests_under_review`. Every NO becomes
one finding. The check itself does NOT assign severity — `severity-guide.md`
does that at step 7.

Source: extracted from
`treasury/crafting-backend-code/SKILL.md` "Validation gate" +
`treasury/validating-banking-implementation/SKILL.md` review-mode checks, re-organized to
match `implement-backend-feature/references/self-review-checklist.md` so the
generate-side and review-side cover the same ground from opposite ends.

## A. Data correctness (code)

- [ ] Every command handler enforces an invariant from the design's L1 (cite the line that holds the invariant).
- [ ] Every query handler is side-effect-free (no inserts / updates / deletes / event publishes).
- [ ] Every persistence call sits inside an explicit transaction scope OR a single-statement write whose atomicity the comment / commit message justifies.
- [ ] No cross-aggregate write inside a single transaction without outbox / saga / compensation.
- [ ] Concurrency-sensitive paths use `SELECT ... FOR UPDATE`, an advisory lock, or a documented compare-and-swap (cite the lock acquisition).
- [ ] No edit to a committed migration file. New migrations are additive.

## B. Idempotency (code)

- [ ] Every external side-effect handler reads `idempotency_key` at the boundary (cite the parameter).
- [ ] A persistence call to the dedup store is visible (cite the function / table).
- [ ] A replay branch returns the stored response without re-running the side-effect (cite the branch).
- [ ] A same-key + different-`request_hash` branch returns a 409 / domain-equivalent error (cite the branch).
- [ ] Kafka consumers dedup on `(topic, partition, offset)` AND on business idempotency key.
- [ ] If `idempotency_strategy` declares "naturally idempotent," the code path is in fact read-only (no inserts / updates / deletes / publishes / external calls).

## C. Errors (code)

- [ ] Every returned error wrapped with `fmt.Errorf("...: %w", err)` (cite an un-wrapped return).
- [ ] Every error has a class (`client | server | dependency`) at the type level, not inferred at the edge.
- [ ] No panic in a request or worker path (except a transport-edge `recover` that increments a metric and emits an audit event).
- [ ] No `_ = err`. No silently dropped errors.
- [ ] No SQL fragment / internal ID / stack trace / env value / PII in any error response shape (cite the leak).

## D. Context propagation (code)

- [ ] Every exported function takes `ctx context.Context` as first parameter.
- [ ] No `context.Background()` / `context.TODO()` inside a request path.
- [ ] ctx flows into every repo call, HTTP / gRPC client, Kafka producer, and downstream goroutine.
- [ ] ctx not stored in a struct field.

## E. Observability (code)

- [ ] Every declared failure mode in the design has a counter increment in the code.
- [ ] Every handler emits a span; span name = `package.Method`.
- [ ] Every log line includes `trace_id`.
- [ ] Metric labels are bounded — no user IDs, free-form strings, or PII as labels.

## F. Security (code)

- [ ] AuthN check is present at the transport boundary (cite the middleware / call).
- [ ] AuthZ check is against the use case's required permission, not the transport route.
- [ ] Every input validated using the repo's validator before reaching the use case.
- [ ] All SQL parameterized — no string concatenation into SQL.
- [ ] No hardcoded secrets / tokens / connection strings / private keys.
- [ ] No `curl` / `wget` / `net/http` to external hosts inside tests.
- [ ] No hand-rolled crypto where a repo-approved helper exists.
- [ ] PII fields named in the design are masked in logs / error responses.

## G. Audit (code)

- [ ] Every state-changing path emits exactly one audit event (cite the emit).
- [ ] Every emitted `event_type` appears in `implement_stage_output.audit_events_emitted`.
- [ ] Audit payload includes actor, action, target, timestamp, trace_id, decision_metadata.

## H. Compensation (code)

- [ ] Every irreversible external side-effect call has a corresponding entry in `implement_stage_output.compensating_actions`.
- [ ] Each `compensating_actions[].action_skill_ref` is plausible (named in a way the workflow can resolve).
- [ ] If compensation is impossible, the workflow stage is declared `human-queue` (read this from the design / workflow definition, not the code).

## I. Tests (tests_under_review)

- [ ] A test file exists for every production file in `code_under_review`.
- [ ] Per-file coverage claim `>= test_coverage_target` from input is plausible (the test exercises the branches required to reach the number).
- [ ] Tests are table-driven for handlers, services, and repo unit tests.
- [ ] No test depends on wall-clock time, network, or random ordering.
- [ ] No `t.Skip(...)` without a named unblock condition.
- [ ] No real PII in fixtures. Synthetic data only.
- [ ] No `curl` / `wget` / `net/http` to external hosts.
- [ ] No secret read from environment in the test.

## J. Scope discipline

- [ ] No Go module imported that is not in `go.mod` (cross-reference the file headers).
- [ ] No edit to a generated artifact (`*.pb.go`, OpenAPI client).
- [ ] No reformatting / cleanup outside the changed files.
- [ ] Public contract has not widened beyond what the design declares.

## K. Claims-vs-reality (used at step 6)

- [ ] Every `audit_events_emitted` entry has a matching emit call in the code.
- [ ] Every `compensating_actions[].trigger` has a matching call site in the code.
- [ ] `idempotency_strategy` text matches the code's actual behavior (not aspirational text).
- [ ] Every `decision_metadata.pattern_choices` entry is consistent with the code.
- [ ] Every `uncertainty_flag` raised by Generate is triaged: resolved-by-code / still-open / needs-escalation.

## Routing of NO answers

A NO becomes a finding. Severity is assigned at step 7 using
`severity-guide.md`. As a quick mental map (the matrix is authoritative):

| Section | Default severity |
|---------|------------------|
| A (data), B (idempotency), F (security), G (audit), H (compensation) | `P1` |
| C (errors), D (context), E (observability), I (tests), K (claims-vs-reality) | `P2` |
| J (scope discipline) | `P2` unless the only NO is a cosmetic re-format, then `P3` |
