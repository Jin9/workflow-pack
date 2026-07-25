# ADR Template

**Parent:** [`../templates.md`](../templates.md)
**Owner role:** [Tech-Lead](../roles.md) (may be promoted from a Tech-Designer or Reviewer recommendation) · **`template_version`:** 0.1.0

Architecture Decision Record. One MD per locked architectural decision. The orchestrator emits an ADR for every `LOCKED` decision in `docs/decisions.md` and every load-bearing decision Tech-Lead made during a run (sole-writer rule, outbox pattern, lock-order pin, etc.).

**File location:** `<workflow_root>/design/architecture/ADRs/ADR-<NNN>-<slug>.md`

ID format: `ADR-NNN` (zero-padded 3 digits, sequential within the workflow). Slug describes the decision in kebab-case.

---

## Required sections

1. `# ADR-NNN — <Title>`
2. `## Status` — enum: `Proposed` | `Accepted` | `Deprecated` | `Superseded by ADR-MMM`
3. `## Context` — what's the problem this decision addresses; what constraints are in play
4. `## Decision` — what we're doing (the meat of the ADR)
5. `## Consequences`
   - `### Positive` — what this enables / fixes
   - `### Negative` — what this costs / breaks / forecloses
6. `## Alternatives considered` — at least 2 other options + why rejected
7. `## Change log` — table

---

## File shape (example, drawn from dry-run #1's locked decisions)

```markdown
# ADR-003 — Order is sole writer of `orders.status`

## Status

Accepted (2026-05-07)

## Context

The Order state machine has 8 statuses (PENDING_PAYMENT, PAID, PAYMENT_FAILED, PAYMENT_EXPIRED, PACKING, SHIPPED, DELIVERED, CANCELLED) and ~10 allowed transitions. Multiple services produce events that should drive transitions: Payment (callback), Inventory (reservation expired), Checkout (commit/cancel), Admin actions.

Without a written rule, each service is tempted to UPDATE `orders.status` directly when its event handler fires. This creates:

- Cross-service writes to the same column → racy, locks-spread thin.
- Difficult-to-audit state machine: which service changed which transition?
- Higher blast radius for refactoring (touch Order's schema and 5 services break).

## Decision

**Order service is the SOLE writer of `orders.status`.** No other service writes that column.

Other services express their intent via Kafka events on `ecom.order-state.events`. Order's consumer reads each event, takes `SELECT ... FOR UPDATE` on the order row, validates the transition against the state machine, and applies it transactionally with a `status_history` row + outbox emit (if Order itself produces a downstream event like `events.order.cancelled`).

State-driven consumer: Order's consumer ignores the event's `fromStatus` field (treats it as audit-only) and acts on the actual current state of the order row. This handles the cross-topic ordering race documented in PR-003 (concurrent customer-cancel + payment-success).

## Consequences

### Positive

- Single audit point for state transitions (`status_history` table in Order's schema).
- State machine validation lives in one place (`state_machine.go` in Order) — pure function, easy to test.
- Event consumers are stateless; idempotent re-delivery is safe via `consumed_events` PK.
- Cross-topic ordering races are bounded — the consumer always reads current state.

### Negative

- Latency added: Payment success doesn't directly mutate Order; instead publishes `events.payment.completed`, Order consumes (~20-200ms). Acceptable for MVP; if real-time UX requires < 100ms, frontend polls `order.detail` after the simulate call returns.
- Coupling: every service that wants to influence Order state must produce an event Order consumes. The schema of those events is now load-bearing for cross-team work.
- More moving parts: outbox per producer, consumer dedup per consumer.

## Alternatives considered

- **Direct DB writes from Payment / Inventory.** Rejected: cross-service write contention, unclear audit, blast-radius too large.
- **API call from Payment to Order's HTTP `update-status` endpoint.** Rejected: synchronous coupling, retries on failure complicate Payment's outbox emission, callback timing harder to bound.
- **Single shared `orders` table accessed by every service.** Rejected: violates schema-per-service rule (per `cross-cutting.persistence`); deploys couple together.

## Change log

| Date | Author | Change |
|---|---|---|
| 2026-05-07 | Tech-Lead (Opus 4.7 xHigh) | Initial ADR drafted from dry-run #1 PR-003 + Reviewer-L2 sole-writer rule check |
```

---

## Negative examples

### Negative #1 — ADR with no Alternatives section

```markdown
# ADR-099 — Use bcrypt

## Status: Accepted
## Context: We need password hashing.
## Decision: Use bcrypt cost 12.
## Consequences: Passwords are hashed.
```

What's missing:

1. `Alternatives considered` — argon2id is the obvious peer; reader can't tell whether the team thought about it. Without alternatives, the ADR is a fiat declaration, not a decision record.
2. `Consequences > Negative` — bcrypt cost 12 is ~250-400ms per login; that's a real performance footprint that must be acknowledged.
3. `Context` is one sentence — the problem and the constraints (existing `common/hash` API, deployment posture, security threat model) belong here.

### Negative #2 — ADR Status: Accepted but Decision is fuzzy

```markdown
## Status: Accepted

## Decision

We'll use the right approach for caching. Probably Redis with sensible defaults. We can revisit if needed.
```

What's wrong:

1. `Decision` is content-free. ADRs document *committed* decisions; "we can revisit if needed" is the opposite of a decision.
2. If the team genuinely hasn't decided, status should be `Proposed`, with a clear question to resolve. Promote to `Accepted` only when the answer is concrete.
