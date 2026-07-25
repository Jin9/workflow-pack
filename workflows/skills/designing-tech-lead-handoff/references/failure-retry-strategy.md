# L3 failure handling & retry strategy (scaffold-v1.1 §4 — L3 §6.5)

Goes into L3-TECHNICAL-STRATEGY.md as §6.5 and informs connectivity +
observability + every Orchestrator's compensation section.

## 6.5.1 Failure principle

`Failure ≠ rollback` is the default. When an async operation fails the system
does NOT roll back upstream state. Instead it: saves current state durably;
records retry metadata (count, last attempt ts, last error); records the last
emitted event (idempotency anchor); retries per the policy below. Applies to
all async event-driven flows in the context.

## 6.5.2 Retry pattern

State which pattern each async integration uses + parameters (max retries,
backoff curve, total timeout):

| Pattern | When applicable | Pros | Cons |
|---|---|---|---|
| Time-based delay | Bounded retry count, transient failures | Simple, predictable | Aggressive on persistent failures |
| Batch inquiry | Long-running async with status-pollable endpoints | Bounded resource cost | Higher latency to terminal state |
| Selective replay | Event-sourced contexts | Precise recovery | Requires event-log infra |

## 6.5.3 Compensating actions (carve-outs)

Compensation is NOT the default — required only where a state change has
external visibility or financial impact and cannot be reversed via retry.
Declare each explicitly: triggering failure | compensating command | target
Aggregate | why compensation not retry | retry-until-success required? If a
context has none, state "No compensating actions; all failures handled via
retry per §6.5.2." Absence is documented, not silent.

## 6.5.4 Idempotency anchors

For each retrying operation declare the idempotency-key derivation rule — this
is what makes "failure ≠ rollback" safe. If undecidable from the brief, make
it a TL decision (ADR) or a P1/P2 open question; never fabricate.

## 6.5.5 Failure detection

How the system knows a failure occurred: active health check, consumer-side
timeout, downstream alert, DLQ depth. Reference the observability spec.

## 6.5.6 Manual-intervention triggers

When automatic retry escalates to human action (threshold-based, e.g. "after
10 retries spanning 24h, page on-call"). Critical for banking-grade; lighter
for lower tiers.
