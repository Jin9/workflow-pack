---
story_id: EPIC-AUTH-01
context_id: auth
command: AuthenticateCustomer (sync_http, idempotency_required: false)
events_emitted: [auth.session.issued (domain)]
api_spec_endpoint_ref: "auth-service POST /auth/login"
spec_status: ready-for-implementation
---

# L4 — EPIC-AUTH-01 · Authenticate customer

- **Command:** `AuthenticateCustomer` → session aggregate; verifies credentials; issues 15-min access + 14-day refresh.
- **Idempotency:** none (login is not replayed; rate-limited).
- **Events:** `auth.session.issued` (domain) when a session pair is issued.
- **Invariants:** generic failure message (no account enumeration); no credential/token value in logs.
- **AC ref:** STORY-AUTH-01 (happy/error/audit).
