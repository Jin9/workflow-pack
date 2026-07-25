# Tech-Lead Integration Contracts Template

**Parent:** [`../templates.md`](../templates.md)
**Owner role:** [Tech-Lead](../roles.md) · **`template_version`:** 0.1.0

Component-agnostic contracts emitted by Tech-Lead before fan-out. Tech-Designers conform to these; they do not negotiate boundaries. Promoted from the inline v0.1 stub used in dry-run #1.

**File location:** `<workflow_root>/design/architecture/contracts.json`

---

## Fields (per top-level object)

- `template_version` — string (semver), required
- `contracts` — array of contract objects, required (≥1)

## Fields (per contract entry)

- `contract_name` — string, required, format `<service>.<action>` for HTTP, `events.<topic>` for async
- `payload_shape` — object, required, JSON-Schema-ish description of request + response (or event body for async)
- `semantics` — enum, required: `sync` | `async` | `system_internal`
- `idempotency_rules` — string, required (one paragraph): key shape, scope, TTL, behavior on collision
- `failure_modes` — array of strings, required (≥1): enumerate distinct error codes + the resulting system state
- `ordering_guarantees` — string, required: per-partition ordering for async; "n/a (sync)" for sync
- `contract_version` — string (semver), required

---

## Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "tech-lead-contracts/v0.1.0",
  "type": "object",
  "additionalProperties": false,
  "required": ["template_version", "contracts"],
  "properties": {
    "template_version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
    "contracts": {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object", "additionalProperties": false,
        "required": [
          "contract_name", "payload_shape", "semantics",
          "idempotency_rules", "failure_modes", "ordering_guarantees", "contract_version"
        ],
        "properties": {
          "contract_name":      { "type": "string", "minLength": 1 },
          "payload_shape":      { "type": "object" },
          "semantics":          { "enum": ["sync", "async", "system_internal"] },
          "idempotency_rules":  { "type": "string", "minLength": 1 },
          "failure_modes":      { "type": "array", "minItems": 1, "items": { "type": "string", "minLength": 1 } },
          "ordering_guarantees":{ "type": "string", "minLength": 1 },
          "contract_version":   { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" }
        }
      }
    }
  }
}
```

---

## Example (known-good — single contract from dry-run #1)

```json
{
  "contract_name": "events.payment.completed",
  "payload_shape": {
    "topic": "ecom.order-state.events",
    "key": "orderId (UUID)",
    "value": {
      "eventId": "UUID v7",
      "eventType": "payment.completed",
      "occurredAt": "ISO 8601 UTC",
      "aggregateId": "orderId",
      "fromStatus": "PENDING_PAYMENT (audit-only; consumers MUST read current state)",
      "amountMinor": "int64 (THB minor units)",
      "paymentIntentId": "UUID"
    }
  },
  "semantics": "async",
  "idempotency_rules": "Consumer dedup via consumed_events PK on eventId (ON CONFLICT DO NOTHING) AND state-driven SELECT FOR UPDATE on the aggregate. event.fromStatus is audit-only; the consumer reads current reservation/order state and acts on the actual transition.",
  "failure_modes": [
    "Consumer crash mid-processing → next delivery picks up via Kafka rebalance; consumed_events PK guards against double-apply",
    "Stale fromStatus (cancel + payment.completed race) → state-driven consumer skips no-op; documented PR-003 race"
  ],
  "ordering_guarantees": "Per-orderId ordering preserved (single partition by orderId). No global ordering guaranteed — consumer must be tolerant of cross-orderId interleaving.",
  "contract_version": "0.1.0"
}
```

---

## Negative examples

### Negative #1 — Vague idempotency, missing failure modes

```json
{
  "contract_name": "checkout.commit",
  "payload_shape": {"request": "...", "response": "..."},
  "semantics": "sync",
  "idempotency_rules": "Idempotent",
  "failure_modes": ["Various"],
  "ordering_guarantees": "n/a",
  "contract_version": "0.1.0"
}
```

What Plan-Reviewer should catch:

1. `idempotency_rules: "Idempotent"` is content-free. Idempotency is the most subtle property of a write endpoint; the contract MUST specify the key shape, scope, TTL, and collision behavior. Tag: `contract_ambiguity` (high) → TL.
2. `failure_modes: ["Various"]` is unenumerable. Tag: `contract_ambiguity` (high).
3. `payload_shape` placeholders. Tag: `contract_ambiguity` (high).

### Negative #2 — Async contract missing partition key

```json
{
  "contract_name": "events.order.cancelled",
  "payload_shape": {
    "topic": "ecom.order.events",
    "value": {"orderId": "UUID", "fromStatus": "string"}
  },
  "semantics": "async",
  "idempotency_rules": "Consumers should be idempotent.",
  "failure_modes": ["Consumer error"],
  "ordering_guarantees": "Best effort",
  "contract_version": "0.1.0"
}
```

What Plan-Reviewer should catch:

1. `payload_shape` is missing the `key` field — without a partition key, ordering is global (impossible in Kafka) or unspecified (= bug). Tag: `contract_ambiguity` (high).
2. `ordering_guarantees: "Best effort"` is the same as no guarantee — caused dry-run #1's PR-003 race. Tag: `contract_ambiguity` (high) → TL.
3. `idempotency_rules` defers to consumers without specifying the dedup key shape. Tag: `contract_ambiguity` (medium).
