# Three-amigos review — ShopPilot MVP breakdown

| Epics | Stories | Rules | Entities | Flows | Tier | State |
|---|---|---|---|---|---|---|
| 2 | 8 | 32 | 6 | 2 | T2 | `ready-for-amigos` |

## Blockers

None. `legal_status: present` — Legal, DPO and Compliance are named and engaged (gap-closed 14), so no P1 governance gap blocks elaboration.

## Epics and why they are epics

### EPIC-STOREFRONT-PURCHASE — A customer can buy something end to end

**Value alone.** Customers complete purchases unassisted on the web, which is the merchant's first direct online sales channel and the thing the adoption and funnel KPIs in gap-closed 3.1 and 3.2 measure.

**Why this is one epic.** A customer buying something is one indivisible business outcome. An account with nothing to buy, a cart that cannot hold stock, and a checkout with no payment step each deliver zero business value alone, so the four service-shaped candidates are one epic. It ships without the back office because gap-closed 7.8 provides seed catalogue and demo accounts.

**Folded in:**

- candidate EPIC-AUTH - enabler; a login screen delivers no business value on its own (test 1)
- candidate EPIC-CHECKOUT - cannot promise an item without the reservation candidate (test 3)
- candidate EPIC-INVENTORY reservation half - exists only to make checkout honest (test 3)
- candidate EPIC-ORDER customer-tracking half - the same purchase outcome seen after the fact (test 3)

### EPIC-BACKOFFICE-OPERATIONS — Staff run stock and fulfilment from one console

**Value alone.** Staff keep inventory accurate and move paid orders through packing and dispatch from one console, which is the operational handling time and same-day fulfilment KPI in gap-closed 3.3.

**Why this is one epic.** Keeping stock accurate and auditable is value staff receive whether or not a single order exists, and it carries its own operational KPI. The fulfilment half does consume orders the purchase epic produces, but that is a sequencing dependency inside a delivery plan, not the business dependency test 3 asks about: this epic's value proposition does not require the other to have shipped.

**Folded in:**

- candidate EPIC-INVENTORY admin half - the same console, the same operational value (test 3)
- candidate EPIC-ORDER admin-fulfilment half - the same console, the same operational value (test 3)

## Business flows

```
FLOW-CUSTOMER-PURCHASE  (actor: Registered customer)
  trigger: A logged-in customer has items in the cart and opens checkout.
  1 customer signs in and receives an access and a refresh token  [RULE-AUTH-01, RULE-AUTH-02]
  2 customer opens checkout, chooses a stored address and optionally enters one coupon  [RULE-COUPON-01, RULE-COUPON-03]
  3 system   computes subtotal, discount, shipping and net total server-side  [RULE-CHECKOUT-01, RULE-CHECKOUT-02, RULE-COUPON-02]
  4 customer confirms the order  [RULE-CHECKOUT-03, RULE-CHECKOUT-04]
  ? Does the coupon still validate at confirm time?  [RULE-COUPON-03]
      the coupon is active and within both quotas -> 5
      the coupon expired or hit a quota while the customer browsed -> outcome: confirm refused
  5 system   reserves stock for every line and creates the order in awaiting-payment  [RULE-STOCK-01, RULE-STOCK-05]
  ? Is every ordered line still in stock at confirm?  [RULE-STOCK-05, RULE-CHECKOUT-03]
      every line has enough available units -> 6
      another confirm won the last unit first -> outcome: out of stock at confirm
  6 customer pays through the mock provider  [RULE-PAYMENT-01]
  7 system   converts the reservation to sold and moves the order to paid  [RULE-STOCK-03, RULE-ORDER-01]
  ? Did the mock provider capture the payment?  [RULE-PAYMENT-01, RULE-PAYMENT-02]
      captured -> 8
      declined -> outcome: payment not completed
      no result before the reservation expires -> outcome: reservation expired
  8 customer tracks the order against its frozen price snapshot  [RULE-ORDER-06, RULE-ORDER-08]
  outcomes: order placed and paid (paid) | confirm refused (awaiting-payment) | out of stock at confirm (awaiting-payment) | payment not completed (payment-failed) | reservation expired (payment-timeout)
```

```
FLOW-ADMIN-FULFILMENT  (actor: Merchant admin)
  trigger: A paid order appears in the back-office queue.
  1 admin    reviews the paid order and confirms the goods are on hand  [RULE-ORDER-01]
  2 admin    adjusts stock to match a physical count, recording a reason  [RULE-STOCK-06, RULE-STOCK-07]
  3 admin    moves the order to packing  [RULE-ORDER-01]
  ? Has the customer asked to cancel before packing starts?  [RULE-ORDER-05, RULE-PAYMENT-03]
      no cancellation requested -> 4
      cancellation requested and packing has not started -> outcome: cancelled before packing
      cancellation requested after packing started -> 4
  4 admin    dispatches with a tracking number and moves the order to shipped  [RULE-ORDER-03]
  5 admin    records delivery  [RULE-ORDER-01, RULE-ORDER-02]
  outcomes: order delivered (delivered) | cancelled before packing (cancelled)
```

## Business rules

| Id | Rule | Type |
|---|---|---|
| `RULE-AUTH-01` | An access token is valid for 15 minutes and a refresh token for 14 days; using a refresh token rotates it. | threshold |
| `RULE-AUTH-02` | Failed authentication returns one identical message whether the email is unknown or the password is wrong. | constraint |
| `RULE-AUTH-03` | A password is stored only as a one-way hash and never appears in a log or an API response. | constraint |
| `RULE-AUTH-04` | A rotated refresh token is single-use: replaying a already-rotated refresh token is refused and the session family is invalidated. | state-transition |
| `RULE-CHECKOUT-01` | The payable total is computed server-side at confirm; a client-supplied total is never trusted. | constraint |
| `RULE-CHECKOUT-02` | Shipping is free when the pre-discount subtotal is 1,500 THB or more, and a flat 60 THB below that. | threshold |
| `RULE-CHECKOUT-03` | Confirm is refused unless the cart holds at least one item, every item is on sale and in stock, any coupon still validates, and the chosen address belongs to the confirming customer. | eligibility |
| `RULE-CHECKOUT-04` | Order confirm is idempotent on the client idempotency key: a repeat returns the original order and creates no second order, reservation or charge. | constraint |
| `RULE-COUPON-01` | At most one coupon applies to an order; coupons do not stack. | constraint |
| `RULE-COUPON-02` | A coupon discount floors the payable total at 0 THB; a discount larger than the goods total never returns money to the customer. | calculation |
| `RULE-COUPON-03` | A coupon is re-validated at confirm against its active window and its total and per-customer quotas; the value shown on screen is never trusted. | eligibility |
| `RULE-STOCK-01` | Adding an item to a cart reserves nothing; stock is reserved for the ordered quantity at order confirm. | state-transition |
| `RULE-STOCK-02` | A stock reservation expires 30 minutes after creation and its units return to available. | threshold |
| `RULE-STOCK-03` | A successful payment converts reserved units to sold; a failed, timed-out or cancelled-before-payment order releases them back to available. | state-transition |
| `RULE-STOCK-04` | Available stock for a product never becomes negative, whether from concurrent confirms or from an admin adjustment. | constraint |
| `RULE-STOCK-05` | When two confirms race for the last unit exactly one succeeds; the loser is refused at confirm with an out-of-stock error. | constraint |
| `RULE-STOCK-06` | An admin may not reduce a product's stock below the quantity currently reserved. | constraint |
| `RULE-STOCK-07` | Every admin stock adjustment records the actor, the time, the signed delta and a mandatory reason. | constraint |
| `RULE-ORDER-01` | An order advances awaiting-payment to paid to packing to shipped to delivered, and the sequence never runs backwards. | state-transition |
| `RULE-ORDER-02` | A delivered order can never be cancelled or moved to any other state. | state-transition |
| `RULE-ORDER-03` | Marking an order shipped requires a non-empty tracking number. | constraint |
| `RULE-ORDER-04` | A customer may cancel only their own order and only while it is awaiting-payment. | authorization |
| `RULE-ORDER-05` | An admin may cancel a paid order only before packing has started, and must record a reason. | authorization |
| `RULE-ORDER-06` | Price, product name and shipping address are snapshotted onto the order at creation; later catalogue edits never change an existing order. | constraint |
| `RULE-ORDER-07` | An order number is unique system-wide, human-readable, and not trivially predictable from the previous one. | constraint |
| `RULE-ORDER-08` | A customer can read only their own orders. | authorization |
| `RULE-PAYMENT-01` | Payment callbacks are idempotent on the provider event id; a replayed callback never applies twice. | constraint |
| `RULE-PAYMENT-02` | A failed or timed-out payment can never later be confirmed as successful using the same payment transaction. | state-transition |
| `RULE-PAYMENT-03` | A refund above 3,000 THB requires dual approval by Finance and the Merchant Owner; refunds are manual and recorded with an idempotency key. | authorization |
| `RULE-COPY-01` | Payment-failure and out-of-stock messages use neutral wording and never imply fraud, risk or wrongdoing. | constraint |
| `RULE-AUDIT-01` | Every order status change and every stock adjustment records who acted, when, and what changed. | constraint |
| `RULE-PRIVACY-01` | Personal data never appears in a log that does not need it, and no customer-facing screen shows another customer's personal data. | constraint |

No open rules — every value in the catalogue is stated by the source with a named approving owner (gap-closed 19).

## Domain entities and state machines

**ENTITY-CUSTOMER** — A person with an account who can place and track their own orders.
  - owner: Data Protection Officer (Khun Apinya); retention: 5 years after last order activity, then deleted or anonymised (gap-closed 16, Revenue Code envelope)
  - personal data: customer_email, customer_phone, customer_name, password

**ENTITY-SESSION** — An authenticated session represented by a short-lived access token and a rotating refresh token.
  - owner: Tech Lead (Khun Anan); retention: session tokens purged after 90 days (gap-closed 16)
  - personal data: session_tokens
  - active -> expired on the access token passes its 15-minute lifetime [RULE-AUTH-01]
  - expired -> active on the customer presents a valid refresh token [RULE-AUTH-01]
  - active -> rotated on a refresh token is exchanged [RULE-AUTH-04]
  - active -> revoked on the customer logs out or a replayed refresh token is detected [RULE-AUTH-04]

**ENTITY-CART** — A customer's working basket before checkout. Holds no stock.
  - owner: Product Manager (Khun Pim); retention: purged after 30 days of inactivity (gap-closed 16)

**ENTITY-STOCK** — Per-product inventory tracked as three quantities: available, reserved and sold.
  - owner: Operations Lead (Khun Mali); retention: stock adjustment history retained 5 years with the audit record (gap-closed 16)
  - available -> reserved on a customer confirms an order for the quantity [RULE-STOCK-01]
  - reserved -> available on the 30-minute reservation expires, or payment fails, or the order is cancelled before payment [RULE-STOCK-03]
  - reserved -> sold on payment is captured successfully [RULE-STOCK-03]

**ENTITY-ORDER** — A confirmed purchase with a frozen price snapshot, a status timeline and a human-readable order number.
  - owner: Merchant Owner (Khun Wirat); retention: 5 years (financial and dispute evidence, gap-closed 16, Revenue Code)
  - personal data: shipping_address
  - awaiting-payment -> paid on payment capture succeeds [RULE-PAYMENT-01]
  - awaiting-payment -> payment-failed on the provider reports a declined payment [RULE-PAYMENT-02]
  - awaiting-payment -> payment-timeout on no payment result arrives before the reservation expires [RULE-STOCK-02]
  - awaiting-payment -> cancelled on the owning customer cancels [RULE-ORDER-04]
  - paid -> packing on an admin starts picking the goods [RULE-ORDER-01]
  - paid -> cancelled on an admin cancels before packing, with a reason [RULE-ORDER-05]
  - packing -> shipped on an admin dispatches with a tracking number [RULE-ORDER-03]
  - shipped -> delivered on the goods reach the customer [RULE-ORDER-01]

**ENTITY-PAYMENT** — A mock-provider payment attempt against one order, identified by a provider event id.
  - owner: Finance Lead (Khun Decha); retention: 5 years with the order record (gap-closed 16)
  - personal data: amount_thb
  - initiated -> captured on the provider reports success [RULE-PAYMENT-01]
  - initiated -> declined on the provider reports failure [RULE-PAYMENT-02]
  - initiated -> timed-out on no provider result arrives in time [RULE-PAYMENT-02]

## Story skeletons

**EPIC-STOREFRONT-PURCHASE**

- `STORY-PURCHASE-01` Customer signs in to their own account — Must, 5 pts — RULE-AUTH-01, RULE-AUTH-02, RULE-AUTH-03
- `STORY-PURCHASE-02` Customer continues a session without signing in again — Must, 5 pts — RULE-AUTH-01, RULE-AUTH-04
- `STORY-PURCHASE-03` Customer checks out at a server-computed total — Must, 8 pts — RULE-CHECKOUT-01, RULE-CHECKOUT-02, RULE-CHECKOUT-03, RULE-CHECKOUT-04, RULE-COUPON-01, RULE-COUPON-02, RULE-COUPON-03
- `STORY-PURCHASE-04` Customer pays through the mock provider without being charged twice — Must, 8 pts — RULE-PAYMENT-01, RULE-PAYMENT-02, RULE-STOCK-03, RULE-ORDER-01, RULE-COPY-01
- `STORY-PURCHASE-05` Stock is held at confirm and released when payment does not complete — Must, 13 pts — RULE-STOCK-01, RULE-STOCK-02, RULE-STOCK-03, RULE-STOCK-04, RULE-STOCK-05
- `STORY-PURCHASE-06` Customer tracks their own order at the price they agreed — Must, 5 pts — RULE-ORDER-04, RULE-ORDER-06, RULE-ORDER-07, RULE-ORDER-08, RULE-PRIVACY-01

**EPIC-BACKOFFICE-OPERATIONS**

- `STORY-BACKOFFICE-01` Admin corrects stock with a reason that survives audit — Must, 5 pts — RULE-STOCK-04, RULE-STOCK-06, RULE-STOCK-07, RULE-AUDIT-01
- `STORY-BACKOFFICE-02` Admin advances an order through fulfilment without going backwards — Must, 8 pts — RULE-ORDER-01, RULE-ORDER-02, RULE-ORDER-03, RULE-ORDER-05, RULE-PAYMENT-03, RULE-AUDIT-01

## Questions for this session

**For dev**

- `OQ-1` (P2) When a coupon fails re-validation at confirm, does the order reprice without the coupon or is the confirm refused outright?
  - why it matters: The two behaviours differ in observable outcome and in how many round trips the customer sees; RULE-COUPON-03 states the re-check but not the branch.
  - affects: STORY-PURCHASE-03, RULE-COUPON-03
- `OQ-2` (P2) For the last-item race, is the winner the first confirm to reach the stock decrement, or the first to have opened checkout?
  - why it matters: RULE-STOCK-05 fixes that exactly one wins but not the tie-break; the answer decides whether an ordering guarantee has to be built.
  - affects: STORY-PURCHASE-05, RULE-STOCK-05

**For tester**

- `OQ-3` (P2) How is a 30-minute reservation expiry observed in test - is there a way to advance the clock, or must a test wait?
  - why it matters: RULE-STOCK-02 is untestable in a pipeline gate without an injectable clock; deciding late forces either a 30-minute test or an untested rule.
  - affects: STORY-PURCHASE-05, RULE-STOCK-02
- `OQ-4` (P2) Which admin actions must be provably rejected for a non-admin account, and how is that asserted in the fulfilment tests?
  - why it matters: RULE-ORDER-05 names the authority but the negative-path coverage is a test-design decision that changes the story's acceptance criteria.
  - affects: STORY-BACKOFFICE-02, RULE-ORDER-05

**For PM**

- `OQ-5` (P3) Does the order number have a stated format beyond being readable and not trivially predictable?
  - why it matters: RULE-ORDER-07 constrains the properties, not the shape; customers quote this number to support.
  - affects: STORY-PURCHASE-06, RULE-ORDER-07

## What happens next

Verdicts: `agreed` | `split-stories` | `descope` | `needs-rework`.
Only `agreed` releases story elaboration.
Anything else returns this breakdown with the findings attached.

`audit_id` 8659756a-2c96-5816-967b-395f99790c77
