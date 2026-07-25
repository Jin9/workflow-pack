# API Spec (Request/Response)

This document lists all HTTP paths from router/router.go with request/response payloads derived from handler structs.

## Response envelope (all JSON responses)

Responses are wrapped by the common response envelope. Successful responses include:

```json
{
  "code": "SUCCESS",
  "message": "SUCCESS",
  "data": {},
  "traceId": "string (optional)"
}
```

Error responses use the same envelope with `code`/`message` indicating the error and `data` omitted or null. HTTP status codes are set per handler.

## Naming conventions

- **Routes**: `/api/v1/<domain>/<aggregate>/<action>` — `<domain>` = API namespace (e.g. `platform`), `<aggregate>` = the `app/` package, `<action>` = verb. e.g. `POST /api/v1/platform/product/create`.
- **Kafka events**: `<DOMAIN>_<AGGREGATE>_<ACTION>` in UPPER_SNAKE, mirroring the route segments (event `<action>` is usually past tense). e.g. `PLATFORM_PRODUCT_CREATED`.

Full conventions live in `.github/skills/implementing-go-template-requirements/`.
