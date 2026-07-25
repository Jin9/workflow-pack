# S3 BE contract — auth context (OpenAPI 3.1 source of truth)

_Generated from S2 `api_contracts` (offline, contract-faithful summary; the runnable `auth.openapi.yaml` is generated from these operations by `befe-contract-design`)._

| operation | semantics | request keys | failure modes |
|---|---|---|---|
| `auth.login` | sync | email, password | invalid_credentials_generic, rate_limited |
| `auth.refresh` | sync | refresh_token | expired_token, replayed_token_family_revoked, invalid_token |
