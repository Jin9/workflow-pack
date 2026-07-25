# S3 BE contract — checkout context (OpenAPI 3.1 source of truth)

_Generated from S2 `api_contracts` (offline, contract-faithful summary; the runnable `checkout.openapi.yaml` is generated from these operations by `befe-contract-design`)._

| operation | semantics | request keys | failure modes |
|---|---|---|---|
| `checkout.confirm` | sync | cart_id, address, coupon, idempotency_key | coupon_expired, out_of_stock, validation_error, auth_required |
| `checkout.capture` | sync | order_id, provider_event_id | payment_declined, payment_timeout, amount_mismatch_rejected |
