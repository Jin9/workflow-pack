# S3 BE contract — inventory context (OpenAPI 3.1 source of truth)

_Generated from S2 `api_contracts` (offline, contract-faithful summary; the runnable `inventory.openapi.yaml` is generated from these operations by `befe-contract-design`)._

| operation | semantics | request keys | failure modes |
|---|---|---|---|
| `inventory.reserve` | system_internal | confirm_id, items | insufficient_stock, sku_not_found |
| `inventory.release` | system_internal | reservation_id, reason | reservation_not_found |
| `inventory.adjust` | sync | sku, new_available, reason | below_reserved_rejected, sku_not_found, missing_reason |
