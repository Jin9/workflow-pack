# S6 · Deploy

| | |
|---|---|
| **Owner** | Release Manager |
| **Skill** | `handoff-to-deploy ^0.1.0 → release` |
| **Tier / Gate** | T1 · **`sync` (irreversible)** |
| **Consumes → Emits** | `qa.evidence` → `deploy.receipt` |
| **Input** | `signoff_criteria` |
| **Output contract** | `handoff-receipt.json` → `receipt_id` + **LIVE RELEASE** |
| **Human-view** | release runbook + KNOWN_ISSUES + sign-off packet (markdown) |
| **SDLC phase** | Release |
| **Status** | ⏸ **deferred** — skill + approver are a gap (OI-002) |

**IRREVERSIBLE / control-plane.** Requires **synchronous named-human approval regardless of agent confidence**.
Compensate via `handoff-revoke` (600s). Credentials must be short-lived OIDC tokens.

_Reference template: `.archive/.../templates/S6-release-runbook-packet.md`._
