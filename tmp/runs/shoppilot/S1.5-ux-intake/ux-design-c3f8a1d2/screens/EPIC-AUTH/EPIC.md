# Screens — EPIC-AUTH (Customer authentication and session management)

- **BA epic:** EPIC-AUTH (`../../../../S1b-ba-brief/EPIC-AUTH/EPIC-AUTH.json`)
- **Related routes:** `/register`, `/login` (+ silent session refresh, no route)
- **Stakeholder note:** PM (Khun Pim, A), Tech Lead (Khun Anan, C), DPO (Khun Apinya, C). Credentials are PII under PDPA.
- **Customer-journey position:** entry point — gates checkout, orders, tracking.

## Stories
- `stories/STORY-1-customer-logs-email-password.md` ← BA STORY-AUTH-01
- `stories/STORY-2-customer-refreshes-expired-session-securely.md` ← BA STORY-AUTH-02
