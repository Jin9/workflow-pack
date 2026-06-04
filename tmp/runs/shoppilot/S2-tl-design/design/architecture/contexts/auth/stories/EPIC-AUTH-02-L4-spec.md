---
story_id: EPIC-AUTH-02
context_id: auth
command: RotateSession (sync_http, idempotency_required: true, key: refresh_token_id)
events_emitted: [auth.session.rotated (domain), auth.family.revoked (domain)]
api_spec_endpoint_ref: "auth-service POST /auth/refresh"
spec_status: ready-for-implementation
---

# L4 — EPIC-AUTH-02 · Rotate session

- **Command:** `RotateSession` → session aggregate; single-use refresh rotation.
- **Idempotency:** keyed on refresh-token id; concurrent refresh → exactly one rotation, others fail closed.
- **Events:** `auth.session.rotated` on success; `auth.family.revoked` when a replayed token is detected.
- **Invariants:** replay revokes the whole family; opaque tokens, never logged.
- **AC ref:** STORY-AUTH-02.
