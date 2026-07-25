# auth-service — API spec (v1.0)

Changelog: v1.0 — initial.

| Method | Path | Contract | Auth | Notes |
|---|---|---|---|---|
| POST | `/auth/register` | (register) | public | unique email; password rules server-side |
| POST | `/auth/login` | `auth.login` | public | issues 15-min access + 14-day refresh; generic error (no enumeration) |
| POST | `/auth/refresh` | `auth.refresh` | refresh token | single-use rotation; replay → family revoke |
| POST | `/auth/logout` | (logout) | access token | revokes session |

Emits: `auth.session.issued`, `auth.session.rotated`, `auth.family.revoked`. No PII/token in logs.
