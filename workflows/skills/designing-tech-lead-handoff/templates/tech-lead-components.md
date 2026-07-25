# Tech-Lead Component List Template

**Parent:** [`../templates.md`](../templates.md)
**Owner role:** [Tech-Lead](../roles.md) · **`template_version`:** 0.1.0

The component decomposition emitted by Tech-Lead alongside the integration contracts. Each entry drives one fan-out pipeline (TD → Dev → QA-L1 ‖ Reviewer-L1).

**File location:** `<workflow_root>/design/architecture/components.json`

---

## Fields (per top-level object)

- `template_version` — string (semver), required
- `components` — array, required (≥1)

## Fields (per component entry)

- `component_name` — string, required, lowercase-kebab (`identity`, `frontend-web`)
- `required` — boolean, required (`true` = unresolved `high` ⇒ run terminates `Failed`)
- `complexity` — enum: `simple` | `standard` | `complex`, required (drives Tech-Designer model tier — see [`../model-routing.md`](../model-routing.md))
- `complexity_rationale` — string, required when `complexity != standard` — one sentence justifying the tag
- `dependencies` — array of `contract_name` refs, required (must resolve to entries in `contracts.json`; orphan dep is a structural failure)
- `parallel_safe` — boolean, required (whether the component's pipeline can run alongside others)
- `microservice_split_threshold` — string, optional — if the component is one microservice today but might split later, name the metric (latency p95, qps, blast-radius) at which it splits

---

## Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "tech-lead-components/v0.1.0",
  "type": "object",
  "additionalProperties": false,
  "required": ["template_version", "components"],
  "properties": {
    "template_version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
    "components": {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object", "additionalProperties": false,
        "required": ["component_name", "required", "complexity", "dependencies", "parallel_safe"],
        "properties": {
          "component_name":   { "type": "string", "pattern": "^[a-z][a-z0-9-]*$" },
          "required":         { "type": "boolean" },
          "complexity":       { "enum": ["simple", "standard", "complex"] },
          "complexity_rationale": { "type": "string", "minLength": 1 },
          "dependencies":     { "type": "array", "items": { "type": "string", "minLength": 1 } },
          "parallel_safe":    { "type": "boolean" },
          "microservice_split_threshold": { "type": "string" }
        }
      }
    }
  }
}
```

---

## Example (known-good)

```json
{
  "template_version": "0.1.0",
  "components": [
    {
      "component_name": "inventory",
      "required": true,
      "complexity": "complex",
      "complexity_rationale": "Concurrent reservation + commit + sweeper; lock-order pin + state-driven event consumer.",
      "dependencies": [
        "cross-cutting.response-envelope",
        "cross-cutting.auth",
        "cross-cutting.error-codes",
        "cross-cutting.idempotency",
        "cross-cutting.persistence",
        "cross-cutting.route-convention",
        "inventory.stock.read",
        "inventory.reservation.create",
        "inventory.reservation.sweep-expired",
        "events.payment.completed",
        "events.reservation.expired"
      ],
      "parallel_safe": true,
      "microservice_split_threshold": "If reservation throughput exceeds 1k qps OR sweeper backlog > 10k expired rows / tick, split reservation aggregate into its own service."
    }
  ]
}
```

---

## Negative examples

### Negative #1 — Complexity undertagged on a concurrent component

```json
{
  "component_name": "inventory",
  "required": true,
  "complexity": "standard",
  "dependencies": ["inventory.stock.read", "inventory.reservation.create"],
  "parallel_safe": true
}
```

What Plan-Reviewer should catch:

1. Inventory has concurrent state mutation (FOR UPDATE on stock_levels), per-SKU lock ordering, and a sweeper goroutine. `standard` undertags the work and routes Tech-Designer to a lower model tier where ambiguity will compound. Tag: `complexity_misjudged` (medium) → TL.
2. `dependencies` list is incomplete — missing cross-cutting refs that every component needs (response envelope, auth, error codes). Tag: `architecture_risk` (medium).
3. Missing `complexity_rationale` (required when not `standard` — but here it IS `standard`, so the field isn't required by schema; the issue is conceptual under-tagging, not a schema break).

### Negative #2 — Orphan dependency (cite to a non-existent contract)

```json
{
  "component_name": "checkout",
  "required": true,
  "complexity": "complex",
  "complexity_rationale": "Multi-service orchestration with idempotency and compensation.",
  "dependencies": [
    "checkout.commit",
    "checkout.preview",
    "inventory.reservation.create",
    "order.create-internal",
    "payment.intent.create"
  ],
  "parallel_safe": true
}
```

What Plan-Reviewer should catch:

1. `order.create-internal` does not exist in `contracts.json` (Tech-Lead never authored it). The orchestrator's structural-validity check fails before fan-out. Tag: `architecture_risk` (high) → TL.
2. This was the precise gap that surfaced in dry-run #1 as Checkout TD's CHK-AMBIG-001 — the orchestrator should have caught it at TL emission time.

Expected routing: orphan-dep failures route to TL with `architecture_risk` (high), plan-stage cap 1.
