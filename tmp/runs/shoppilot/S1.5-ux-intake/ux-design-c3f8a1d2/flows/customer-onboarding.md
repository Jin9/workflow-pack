---
flow_id: customer-onboarding
related_epics: [EPIC-AUTH]
related_stories: [STORY-AUTH-01, STORY-AUTH-02]
---

# Flow — Customer Onboarding

Registration → login → first authenticated session (with silent refresh).

```mermaid
sequenceDiagram
    actor C as Customer
    participant R as /register
    participant L as /login
    participant API as Auth API
    C->>R: enter name, email, phone, password
    R->>API: create account (email unique; password rules server-side)
    API-->>R: created
    C->>L: enter email + password
    L->>API: login
    API-->>L: access token (15m) + refresh token (14d)
    Note over L,API: no password/token value in any log (STORY-AUTH-01)
    L-->>C: redirect to / (catalog)
    Note over C,API: later — access token expires
    C->>API: silent refresh (rotating refresh token)
    API-->>C: new access+refresh pair; old refresh revoked (STORY-AUTH-02)
```

## Screen-by-screen
1. **`/register`** — TextField(name/email/phone) + PasswordField. Email format `field.email.error-format`; phone `field.phone.error-format`. Success → `/login`.
2. **`/login`** — credentials; generic error `screen.login.error-state` (no account enumeration). Success → `/`.
3. **Session (no screen)** — silent refresh rotates the token family; a replayed refresh revokes the family.

## Edge cases
- Wrong password / unknown email → identical generic message (`screen.login.error-state`).
- Refresh token replayed → family revoked → `error.session-expired` → back to `/login`.
- Network failure during register/login → `error.network`, no partial account.

## Cross-references
- Screens: `../screens/EPIC-AUTH/stories/STORY-1-customer-logs-email-password.md`, `STORY-2-customer-refreshes-expired-session-securely.md`
- States: `../screen-states.md` (`/register`, `/login`)
