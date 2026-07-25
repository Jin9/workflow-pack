# S3 BE contract — order context (OpenAPI 3.1 source of truth)

_Generated from S2 `api_contracts` (offline, contract-faithful summary; the runnable `order.openapi.yaml` is generated from these operations by `befe-contract-design`)._

| operation | semantics | request keys | failure modes |
|---|---|---|---|
| `order.create` | system_internal | confirm_id, snapshot | invalid_payload |
| `order.get` | sync | order_no, requester_id | not_owner_denied, not_found |
| `order.transition` | sync | order_no, target_state, tracking_no | illegal_backward_rejected, missing_tracking_on_shipped, not_admin |
| `order.payment.captured` | async | order_id, outcome, amount, audit_id | consumer_lag, dlq_on_poison_message |
| `order.status.changed` | async | order_id, before, after, audit_id | consumer_lag, dlq_on_poison_message |
