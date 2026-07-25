# How to use this skill

## What the skill expects as input

A **single requirement** in any of these shapes:

- A line item from `spec.md` ("implement section 3.2").
- A ticket title + acceptance criteria ("PROD-142: add update-product endpoint that validates...").
- A bug report ("when memberRole is empty, issue-token returns 500 instead of 400").
- A user story ("as an org admin, I want to delete a product so it no longer appears in list").
- A Kafka event contract ("consume `PLATFORM_INVOICE_PAID`, set invoice status to PAID").

The skill works best when the input includes:

1. **Kind** — new endpoint? new event consumer? bug fix? new domain?
2. **Target domain** — which `app/<domain>/` is involved.
3. **Inputs / outputs** — request fields, response fields, payload fields.
4. **Side effects** — DB writes, Kafka publishes, external calls.

If any of these are missing, the skill restates the parsed requirement back and asks for the missing piece **before** editing files.

## Trigger phrases that map to this skill

- "implement this requirement in the go-template service"
- "add this endpoint per spec without touching infra"
- "fix this bug, business logic only"
- "wire up this Kafka event from the requirement"
- "implement spec.md item N"
- "extend `<domain>` to satisfy `<requirement>`"

---

## Example 1 — New HTTP endpoint on an existing domain

**Input (what the user types):**

> Implement `POST /api/v1/platform/product/update` per spec.md §Product. Request: `{ "productId": "uuid", "name": "string", "price": "number" }`. Response: `{ "productId": "uuid" }`. Updates the product name and price in storage. Returns 404 if not found.

**Agent flow under the skill:**

1. **Parse** → kind=new endpoint, domain=`product`, action=`update`, inputs= `productId+name+price`, outputs=`productId`, side effects=storage update, dependencies=`productStorage`.
2. **Locate domain** → `app/product/` exists, read `handler.go` to see existing `HandlerConfig`.
3. **Audit access** → `app/product/access/storage_product.go` exists with `UpdateProduct`. Reuse, do NOT extend.
4. **Scaffold-lock test** → planned files:
   - ✅ `app/product/handler_update.go`
   - ✅ `app/product/handler_update_test.go`
   - ⚠️ `router/router.go` (add one line inside `registerProductRoutes`)
   - ⚠️ `spec.md` (add the endpoint doc)
   - No FORBIDDEN files. Proceed.
5. **Implement** in order:
   - `handler_update.go` (uses `templates/handler.go.tmpl`)
   - `handler_update_test.go` (uses `templates/handler_test.go.tmpl`)
   - `router/router.go`: add `productGroup.POST("/update", productHandler.UpdateProduct)` inside the existing block.
   - `spec.md`: add the new endpoint section.
6. **Regenerate mocks** → no interface changes, skip.
7. **Tests** → success + missing-productId + missing-name + missing-price + storage error + GetID parse failure + not-found case. Boundary test in external `package product_test`; no test for `NewHandler` or the `access/` layer (out of scope). If the handler had grown into a multi-step orchestration, the logic would move to `service_update.go` with an internal-package `service_update_test.go`.
8. **Verify** → `make precommit` passes; the in-scope coverage gate prints nothing — handler/consumer/service at 100%, with constructors and the `access/` sub-package filtered out (command in `references/testing-pattern.md`).
9. **Diff allowlist** → only `app/product/...`, `router/router.go`, `spec.md`. Clean.

**Files touched: 4. Files untouched (kept locked): everything else.**

---

## Example 2 — New Kafka consumer

**Input:**

> Add a consumer for the `PLATFORM_MEMBER_SUSPENDED` event. Payload: `{ "memberId": "uuid", "reason": "string" }`. When received, set member status to SUSPENDED in storage.

**Agent flow:**

1. **Parse** → kind=new consumer, domain=`member`, event=`PLATFORM_MEMBER_SUSPENDED`, action=`suspended`.
2. **Locate** → `app/member/access/storage_member.go` exists. Read it.
3. **Audit access** → existing methods: `GetMemberByEmail`. Missing: `GetMemberByID` and `UpdateMember`. Need to extend interface.
4. **Scaffold-lock test** → planned files:
   - ✅ `app/member/access/storage_member.go` (extend interface)
   - ✅ `app/member/access/mocks/mocks.go` (regenerate)
   - ✅ `app/member/consumer_suspended.go`
   - ✅ `app/member/consumer_suspended_test.go`
   - ⚠️ `router/subscriber.go` (add one entry in `registerEventRoutes`)
   - ⚠️ `spec.md` (document the event)
   - No FORBIDDEN files. Proceed.
5. **Implement**:
   - Extend `storage_member.go` with `GetMemberByID` and `UpdateMember`.
   - Run `mockery`.
   - Write `consumer_suspended.go` from `templates/consumer.go.tmpl`.
   - Write `consumer_suspended_test.go` from `templates/consumer_test.go.tmpl`.
   - Narrow edit `router/subscriber.go`: `routes["PLATFORM_MEMBER_SUSPENDED"] = memberHandler.OnSuspended`.
   - Update `spec.md`.
6. **Tests** → success + invalid JSON + missing memberId + missing reason + memberId not a UUID + GetMemberByID error + UpdateMember error.
7. **Verify** → green.

**Files touched: 6. No `main.go`/`config/`/`router/deps.go` edits.**

---

## Example 3 — Bug fix with a STOP trigger

**Input:**

> Bug: the `issue-token` endpoint returns a 500 when the user is rate-limited by the JWT signing service. We need to add Redis-backed rate limiting so we can return 429 cleanly before hitting the signer.

**Agent flow:**

1. **Parse** → kind=bug fix + new infra dependency (Redis-backed rate limiter).
2. **Locate** → `app/auth/handler_issue_token.go`.
3. **Scaffold-lock test** → planned files reveal a STOP:
   - The current service has no rate-limiter client wired in `router/deps.go`.
   - Adding Redis-backed rate limiting requires:
     - 🛑 `router/deps.go` (initialise the client) — FORBIDDEN.
     - 🛑 `config/config.go` (rate-limit env vars) — FORBIDDEN.
     - 🛑 `.env.template` (document the new env vars) — FORBIDDEN.
4. **STOP and surface**: the agent does **not** edit FORBIDDEN files. Instead it replies:

   > This requirement crosses the scaffold-lock boundary. Adding Redis-backed rate limiting requires edits to `router/deps.go` (new client init), `config/config.go` (new env branch), and `.env.template` (new env vars). These are FORBIDDEN under this skill.
   >
   > Two options:
   > - **Path A (in-scope)**: keep the 500→429 fix purely in business logic by adding a domain-level token-bucket using an existing `cache_*.go` if one is wired. (Confirm: is `app/auth/access/cache_*.go` present?)
   > - **Path B (out-of-scope)**: authorise a scaffold delta for the new Redis client. The work then runs outside this skill — please confirm explicitly.
   >
   > Which path do you want?

5. Agent waits for the user's choice. No edits made.

**This is the skill working correctly** — it caught a scaffold leak before any file was touched.

---

## Anti-examples (what the skill refuses)

| Bad input | Why the skill refuses |
|---|---|
| "Clean up the middleware chain while you're here" | Refactoring unrelated to a requirement. Out of scope. |
| "Bump the Go version to 1.26 and add this endpoint" | Scaffold edit (`Dockerfile`, `go.mod`) bundled with feature work. STOP. |
| "Build a brand-new service from scratch" | Use a scaffolding skill instead — this skill assumes a `go-template`-shaped repo already exists. |
| "Add a React page that calls this endpoint" | Non-Go work. Out of scope. |

---

## How to invoke

In Claude Code, after this skill is installed (copied to `~/.claude/skills/` or referenced via plugin):

```
/implementing-go-template-requirements <paste requirement here>
```

Or just describe the requirement in plain English with one of the trigger phrases from the list above — the skill auto-activates from the description match.

## What the skill does NOT do

- Open a PR (use a publishing skill afterwards).
- Run the service or call the endpoint live (use a `verify` skill).
- Refactor unrelated files.
- Edit `main.go`, `config/`, `router/deps.go`, `Makefile`, `Dockerfile`, CI, or any other FORBIDDEN file.
- Bump versions or write CHANGELOG entries.
