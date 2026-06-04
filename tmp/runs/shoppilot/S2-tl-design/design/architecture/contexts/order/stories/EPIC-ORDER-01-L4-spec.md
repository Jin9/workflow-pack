---
story_id: EPIC-ORDER-01
context_id: order
command: GetOwnOrder (sync_http, idempotency_required: false)
events_emitted: []  # read-only
no_event_rationale: "Read-only query with own-data-only authz; no state mutation, so no domain event."
api_spec_endpoint_ref: "order-service GET /orders/:orderNo"
spec_status: ready-for-implementation
---

# L4 — EPIC-ORDER-01 · Track own order (frozen snapshot)

- **Command:** `GetOwnOrder` → order aggregate (query); returns immutable snapshot + status timeline + tracking when shipped.
- **Idempotency:** n/a (read).
- **Events:** none — read-only (see `no_event_rationale`).
- **Invariants:** own-data-only (non-owner denied, no data disclosed); snapshot never drifts with catalog edits (ADR-003).
- **AC ref:** STORY-ORDER-01.
