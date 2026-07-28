"""Content for the regenerated ShopPilot BA leg (breakdown + elaboration).

Every value here is derived from the run's own source bytes:
`tmp/runs/shoppilot/S0-intake/ecommerce_mvp_business_only.gap-closed.md` (the
gap-closed requirement, sections cited per row) and the recorded corpus epics
under `tmp/runs/shoppilot/S1b-ba-brief/`. Nothing is invented: no synthetic
latency, no guessed threshold, no retroactive statistic. A value the source does
not state is carried as an open rule or an open question, never a number.

Scope note: this sample regenerates the SAME ground the recorded corpus covered
(its 8 stories), regrouped under the business-dependency epic rule, so the
before/after comparison is like-for-like. Catalogue, coupon-administration and
review moderation exist in the source requirement but had no corpus story, so
they are out of this sample's scope and deliberately carry no rules.
"""

IDEMPOTENCY_KEY = "3f6c0b2e-7a41-4d9b-9c2a-8e5b1f0a4d22"
SOURCE_DOC = "ecommerce_mvp_business_only.gap-closed.md"

# --------------------------------------------------------------------------
# Business rules — stated once, cited by id everywhere else.
# --------------------------------------------------------------------------
RULES = [
    ("RULE-AUTH-01", "An access token is valid for 15 minutes and a refresh token for 14 days; using a refresh token rotates it.",
     "threshold", "gap-closed 19 (numeric policy parameters)", "T2", ["ENTITY-SESSION"], None),
    ("RULE-AUTH-02", "Failed authentication returns one identical message whether the email is unknown or the password is wrong.",
     "constraint", "gap-closed 8.1 (security) and the recorded epic metric account-enumeration leakage = 0", "T2", ["ENTITY-CUSTOMER"], None),
    ("RULE-AUTH-03", "A password is stored only as a one-way hash and never appears in a log or an API response.",
     "constraint", "gap-closed 6.7 (data privacy)", "T2", ["ENTITY-CUSTOMER"], "PDPA B.E. 2562 s24"),
    ("RULE-AUTH-04", "A rotated refresh token is single-use: replaying a already-rotated refresh token is refused and the session family is invalidated.",
     "state-transition", "gap-closed 4.2 (signing up and logging in) plus 19 refresh-token lifetime", "T2", ["ENTITY-SESSION"], None),
    ("RULE-CHECKOUT-01", "The payable total is computed server-side at confirm; a client-supplied total is never trusted.",
     "constraint", "gap-closed 4.6 (checkout)", "T2", ["ENTITY-ORDER"], "Consumer Protection Act; Electronic Transactions Act"),
    ("RULE-CHECKOUT-02", "Shipping is free when the pre-discount subtotal is 1,500 THB or more, and a flat 60 THB below that.",
     "threshold", "gap-closed 6.3 (shipping fee) and 19 (approved by Merchant Owner)", "T2", ["ENTITY-ORDER"], None),
    ("RULE-CHECKOUT-03", "Confirm is refused unless the cart holds at least one item, every item is on sale and in stock, any coupon still validates, and the chosen address belongs to the confirming customer.",
     "eligibility", "gap-closed 4.6 (final checks before confirm)", "T2", ["ENTITY-ORDER", "ENTITY-CART"], None),
    ("RULE-CHECKOUT-04", "Order confirm is idempotent on the client idempotency key: a repeat returns the original order and creates no second order, reservation or charge.",
     "constraint", "gap-closed 4.7 (avoiding double-charges) and 17 (idempotency)", "T2", ["ENTITY-ORDER"], None),
    ("RULE-COUPON-01", "At most one coupon applies to an order; coupons do not stack.",
     "constraint", "gap-closed 4.5 and 6.4 (coupon stacking)", "T2", ["ENTITY-ORDER"], None),
    ("RULE-COUPON-02", "A coupon discount floors the payable total at 0 THB; a discount larger than the goods total never returns money to the customer.",
     "calculation", "gap-closed 4.5 and 6.4 (coupon stacking)", "T2", ["ENTITY-ORDER"], None),
    ("RULE-COUPON-03", "A coupon is re-validated at confirm against its active window and its total and per-customer quotas; the value shown on screen is never trusted.",
     "eligibility", "gap-closed 4.5 (applying coupons) and 6.4", "T2", ["ENTITY-ORDER"], None),
    ("RULE-STOCK-01", "Adding an item to a cart reserves nothing; stock is reserved for the ordered quantity at order confirm.",
     "state-transition", "gap-closed 5.5 (stock reservation lifecycle)", "T2", ["ENTITY-STOCK"], None),
    ("RULE-STOCK-02", "A stock reservation expires 30 minutes after creation and its units return to available.",
     "threshold", "gap-closed 5.5 and 19 (TTL approved by Operations Lead)", "T2", ["ENTITY-STOCK"], None),
    ("RULE-STOCK-03", "A successful payment converts reserved units to sold; a failed, timed-out or cancelled-before-payment order releases them back to available.",
     "state-transition", "gap-closed 5.5 (stock reservation lifecycle)", "T2", ["ENTITY-STOCK"], None),
    ("RULE-STOCK-04", "Available stock for a product never becomes negative, whether from concurrent confirms or from an admin adjustment.",
     "constraint", "gap-closed 5.4 (managing inventory)", "T2", ["ENTITY-STOCK"], None),
    ("RULE-STOCK-05", "When two confirms race for the last unit exactly one succeeds; the loser is refused at confirm with an out-of-stock error.",
     "constraint", "gap-closed 5.5 (last-item race) and 20 (reliability)", "T2", ["ENTITY-STOCK"], None),
    ("RULE-STOCK-06", "An admin may not reduce a product's stock below the quantity currently reserved.",
     "constraint", "gap-closed 5.5 (admin adjustment while reserved)", "T2", ["ENTITY-STOCK"], None),
    ("RULE-STOCK-07", "Every admin stock adjustment records the actor, the time, the signed delta and a mandatory reason.",
     "constraint", "gap-closed 5.4 (managing inventory) and 6.6 (audit trail intent)", "T2", ["ENTITY-STOCK"], None),
    ("RULE-ORDER-01", "An order advances awaiting-payment to paid to packing to shipped to delivered, and the sequence never runs backwards.",
     "state-transition", "gap-closed 4.9 (tracking the order) and 5.7 (fulfilling orders)", "T2", ["ENTITY-ORDER"], None),
    ("RULE-ORDER-02", "A delivered order can never be cancelled or moved to any other state.",
     "state-transition", "gap-closed 4.9 and 5.7", "T2", ["ENTITY-ORDER"], None),
    ("RULE-ORDER-03", "Marking an order shipped requires a non-empty tracking number.",
     "constraint", "gap-closed 5.7 (fulfilling orders, step 2)", "T2", ["ENTITY-ORDER"], None),
    ("RULE-ORDER-04", "A customer may cancel only their own order and only while it is awaiting-payment.",
     "authorization", "gap-closed 4.10 (cancelling an order)", "T2", ["ENTITY-ORDER"], None),
    ("RULE-ORDER-05", "An admin may cancel a paid order only before packing has started, and must record a reason.",
     "authorization", "gap-closed 4.10 and 5.7; approver named in 17 (Operations Lead)", "T2", ["ENTITY-ORDER"], None),
    ("RULE-ORDER-06", "Price, product name and shipping address are snapshotted onto the order at creation; later catalogue edits never change an existing order.",
     "constraint", "gap-closed 4.9 (price snapshot) and 6.8 (pricing snapshot principle)", "T2", ["ENTITY-ORDER"], None),
    ("RULE-ORDER-07", "An order number is unique system-wide, human-readable, and not trivially predictable from the previous one.",
     "constraint", "gap-closed 4.9 (order number)", "T2", ["ENTITY-ORDER"], None),
    ("RULE-ORDER-08", "A customer can read only their own orders.",
     "authorization", "gap-closed 6.7 (data privacy) and 20 (own-data-only isolation)", "T2", ["ENTITY-ORDER"], "PDPA B.E. 2562 s24"),
    ("RULE-PAYMENT-01", "Payment callbacks are idempotent on the provider event id; a replayed callback never applies twice.",
     "constraint", "gap-closed 4.7 and 17 (provider replay)", "T2", ["ENTITY-PAYMENT"], None),
    ("RULE-PAYMENT-02", "A failed or timed-out payment can never later be confirmed as successful using the same payment transaction.",
     "state-transition", "gap-closed 4.9 (rules to watch)", "T2", ["ENTITY-PAYMENT"], None),
    ("RULE-PAYMENT-03", "A refund above 3,000 THB requires dual approval by Finance and the Merchant Owner; refunds are manual and recorded with an idempotency key.",
     "authorization", "gap-closed 17 (manual-refund SOP) and 19 (dual-approval threshold)", "T2", ["ENTITY-PAYMENT"], None),
    ("RULE-COPY-01", "Payment-failure and out-of-stock messages use neutral wording and never imply fraud, risk or wrongdoing.",
     "constraint", "gap-closed 18 (customer-facing copy, UX and Legal reviewed)", "T2", ["ENTITY-ORDER"], "Consumer Protection Act"),
    ("RULE-AUDIT-01", "Every order status change and every stock adjustment records who acted, when, and what changed.",
     "constraint", "gap-closed 6.6 (audit trail intent)", "T2", ["ENTITY-ORDER", "ENTITY-STOCK"], None),
    ("RULE-PRIVACY-01", "Personal data never appears in a log that does not need it, and no customer-facing screen shows another customer's personal data.",
     "constraint", "gap-closed 6.7 (data privacy)", "T2", ["ENTITY-CUSTOMER", "ENTITY-ORDER"], "PDPA B.E. 2562 s24"),
    # Retention and residency (gap-closed 16) are deliberately NOT rules. They are
    # declarative data policy attached to each entity, so they live on
    # ENTITY.retention / ENTITY.residency where the data is defined. Modelling them
    # as rules would have produced a rule no story implements - which the
    # every-rule-is-referenced cross-check would then flag as a missing story.
]

# --------------------------------------------------------------------------
# Domain model — entities, fields (PII declared once, here), state machines.
# --------------------------------------------------------------------------
ENTITIES = [
    {
        "id": "ENTITY-CUSTOMER", "name": "Customer",
        "description": "A person with an account who can place and track their own orders.",
        "owner": "Data Protection Officer (Khun Apinya)",
        "retention": "5 years after last order activity, then deleted or anonymised (gap-closed 16, Revenue Code envelope)",
        "residency": "Thailand / Singapore (ap-southeast) only (gap-closed 16)",
        "key_fields": [
            {"name": "customer_email", "type": "string", "pii_class": "direct",
             "lawful_basis": "PDPA s24 contract; s19 consent for marketing", "masking": "domain only in admin lists; redacted in logs"},
            {"name": "customer_phone", "type": "string", "pii_class": "direct",
             "lawful_basis": "PDPA s24 contract", "masking": "last 4 digits in admin lists; redacted in logs"},
            {"name": "customer_name", "type": "string", "pii_class": "direct",
             "lawful_basis": "PDPA s24 contract", "masking": "none in order context; redacted in non-order logs"},
            {"name": "password", "type": "string", "pii_class": "regulatory-confidential",
             "lawful_basis": "PDPA s24 account security", "masking": "one-way hash only; never displayed, logged or returned"},
        ],
    },
    {
        "id": "ENTITY-SESSION", "name": "Session",
        "description": "An authenticated session represented by a short-lived access token and a rotating refresh token.",
        "owner": "Tech Lead (Khun Anan)",
        "retention": "session tokens purged after 90 days (gap-closed 16)",
        "residency": "Thailand / Singapore (ap-southeast) only",
        "key_fields": [
            {"name": "session_tokens", "type": "opaque", "pii_class": "regulatory-confidential",
             "lawful_basis": "PDPA s24 account security", "masking": "hashed or opaque; never logged or displayed"},
        ],
        "states": ["active", "expired", "rotated", "revoked"],
        "transitions": [
            {"from": "active", "to": "expired", "trigger": "the access token passes its 15-minute lifetime", "guard": "RULE-AUTH-01", "reversible": True},
            {"from": "expired", "to": "active", "trigger": "the customer presents a valid refresh token", "guard": "RULE-AUTH-01", "reversible": True},
            {"from": "active", "to": "rotated", "trigger": "a refresh token is exchanged", "guard": "RULE-AUTH-04", "reversible": False,
             "compensating_action": "invalidate the whole session family and require a fresh login"},
            {"from": "active", "to": "revoked", "trigger": "the customer logs out or a replayed refresh token is detected", "guard": "RULE-AUTH-04", "reversible": False,
             "compensating_action": "none required - revocation is the safe terminal state"},
        ],
    },
    {
        "id": "ENTITY-CART", "name": "Cart",
        "description": "A customer's working basket before checkout. Holds no stock.",
        "owner": "Product Manager (Khun Pim)",
        "retention": "purged after 30 days of inactivity (gap-closed 16)",
        "residency": "Thailand / Singapore (ap-southeast) only",
        "key_fields": [
            {"name": "cart_id", "type": "string", "pii_class": "none"},
            {"name": "line_items", "type": "array", "pii_class": "none"},
        ],
    },
    {
        "id": "ENTITY-STOCK", "name": "Stock",
        "description": "Per-product inventory tracked as three quantities: available, reserved and sold.",
        "owner": "Operations Lead (Khun Mali)",
        "retention": "stock adjustment history retained 5 years with the audit record (gap-closed 16)",
        "residency": "Thailand / Singapore (ap-southeast) only",
        "key_fields": [
            {"name": "available", "type": "integer", "pii_class": "none"},
            {"name": "reserved", "type": "integer", "pii_class": "none"},
            {"name": "sold", "type": "integer", "pii_class": "none"},
        ],
        "states": ["available", "reserved", "sold"],
        "transitions": [
            {"from": "available", "to": "reserved", "trigger": "a customer confirms an order for the quantity", "guard": "RULE-STOCK-01", "reversible": True},
            {"from": "reserved", "to": "available", "trigger": "the 30-minute reservation expires, or payment fails, or the order is cancelled before payment", "guard": "RULE-STOCK-03", "reversible": True},
            {"from": "reserved", "to": "sold", "trigger": "payment is captured successfully", "guard": "RULE-STOCK-03", "reversible": False,
             "compensating_action": "an admin cancellation before packing returns the units to available and opens a manual refund under RULE-PAYMENT-03"},
        ],
    },
    {
        "id": "ENTITY-ORDER", "name": "Order",
        "description": "A confirmed purchase with a frozen price snapshot, a status timeline and a human-readable order number.",
        "owner": "Merchant Owner (Khun Wirat)",
        "retention": "5 years (financial and dispute evidence, gap-closed 16, Revenue Code)",
        "residency": "Thailand / Singapore (ap-southeast) only",
        "key_fields": [
            {"name": "order_number", "type": "string", "pii_class": "none"},
            {"name": "shipping_address", "type": "object", "pii_class": "direct",
             "lawful_basis": "PDPA s24 contract and delivery", "masking": "snapshotted into the order; redacted in non-order logs"},
            {"name": "price_snapshot", "type": "object", "pii_class": "none"},
            {"name": "tracking_number", "type": "string", "pii_class": "none"},
        ],
        "states": ["awaiting-payment", "paid", "packing", "shipped", "delivered", "cancelled", "payment-failed", "payment-timeout"],
        "transitions": [
            {"from": "awaiting-payment", "to": "paid", "trigger": "payment capture succeeds", "guard": "RULE-PAYMENT-01", "reversible": False,
             "compensating_action": "an admin cancellation before packing releases the stock and opens a manual refund under RULE-PAYMENT-03"},
            {"from": "awaiting-payment", "to": "payment-failed", "trigger": "the provider reports a declined payment", "guard": "RULE-PAYMENT-02", "reversible": False,
             "compensating_action": "release the reserved stock under RULE-STOCK-03"},
            {"from": "awaiting-payment", "to": "payment-timeout", "trigger": "no payment result arrives before the reservation expires", "guard": "RULE-STOCK-02", "reversible": False,
             "compensating_action": "release the reserved stock under RULE-STOCK-03"},
            {"from": "awaiting-payment", "to": "cancelled", "trigger": "the owning customer cancels", "guard": "RULE-ORDER-04", "reversible": False,
             "compensating_action": "release the reserved stock under RULE-STOCK-03"},
            {"from": "paid", "to": "packing", "trigger": "an admin starts picking the goods", "guard": "RULE-ORDER-01", "reversible": False,
             "compensating_action": "none - the transition is internal and carries no external effect"},
            {"from": "paid", "to": "cancelled", "trigger": "an admin cancels before packing, with a reason", "guard": "RULE-ORDER-05", "reversible": False,
             "compensating_action": "release the sold stock to available and record a manual refund under RULE-PAYMENT-03"},
            {"from": "packing", "to": "shipped", "trigger": "an admin dispatches with a tracking number", "guard": "RULE-ORDER-03", "reversible": False,
             "compensating_action": "no in-MVP compensation - returns are out of scope (gap-closed 6.5)"},
            {"from": "shipped", "to": "delivered", "trigger": "the goods reach the customer", "guard": "RULE-ORDER-01", "reversible": False,
             "compensating_action": "no in-MVP compensation - returns are out of scope (gap-closed 6.5)"},
        ],
    },
    {
        "id": "ENTITY-PAYMENT", "name": "Payment",
        "description": "A mock-provider payment attempt against one order, identified by a provider event id.",
        "owner": "Finance Lead (Khun Decha)",
        "retention": "5 years with the order record (gap-closed 16)",
        "residency": "Thailand / Singapore (ap-southeast) only",
        "key_fields": [
            {"name": "provider_event_id", "type": "string", "pii_class": "none"},
            {"name": "amount_thb", "type": "integer", "pii_class": "financial",
             "lawful_basis": "PDPA s24 contract", "masking": "shown to the owning customer and to the back office only"},
        ],
        "states": ["initiated", "captured", "declined", "timed-out"],
        "transitions": [
            {"from": "initiated", "to": "captured", "trigger": "the provider reports success", "guard": "RULE-PAYMENT-01", "reversible": False,
             "compensating_action": "manual refund recorded with an idempotency key under RULE-PAYMENT-03"},
            {"from": "initiated", "to": "declined", "trigger": "the provider reports failure", "guard": "RULE-PAYMENT-02", "reversible": False,
             "compensating_action": "none - no money moved"},
            {"from": "initiated", "to": "timed-out", "trigger": "no provider result arrives in time", "guard": "RULE-PAYMENT-02", "reversible": False,
             "compensating_action": "none - no money moved"},
        ],
    },
]

GLOSSARY = [
    {"term": "reservation", "canonical_form": "stock reservation",
     "surface_form": ["กันสต๊อก", "hold"],
     "definition": "Units moved from available to reserved at order confirm, released after 30 minutes if payment does not complete."},
    {"term": "price snapshot", "canonical_form": "price snapshot",
     "surface_form": ["ราคา ณ เวลาที่สั่งซื้อ"],
     "definition": "The price, product name and address frozen onto an order at creation so later catalogue edits cannot change it."},
    {"term": "provider replay", "canonical_form": "provider callback replay",
     "surface_form": ["callback ซ้ำ"],
     "definition": "The mock payment provider re-sending a callback with an event id already processed; must not apply twice."},
    {"term": "own-data-only", "canonical_form": "own-data-only isolation",
     "surface_form": ["ดูได้เฉพาะของตัวเอง"],
     "definition": "A customer may read only records they own; enforced on every customer-facing read.",
     "regulatory_tie": "PDPA B.E. 2562 s24"},
]

# --------------------------------------------------------------------------
# Business flows.
# --------------------------------------------------------------------------
FLOWS = [
    {
        "id": "FLOW-CUSTOMER-PURCHASE", "name": "Customer purchase journey",
        "actor": "Registered customer",
        "trigger": "A logged-in customer has items in the cart and opens checkout.",
        "steps": [
            {"seq": 1, "actor": "customer", "action": "signs in and receives an access and a refresh token",
             "entity_refs": ["ENTITY-SESSION"], "rule_refs": ["RULE-AUTH-01", "RULE-AUTH-02"], "story_refs": ["STORY-PURCHASE-01"]},
            {"seq": 2, "actor": "customer", "action": "opens checkout, chooses a stored address and optionally enters one coupon",
             "entity_refs": ["ENTITY-CART"], "rule_refs": ["RULE-COUPON-01", "RULE-COUPON-03"], "story_refs": ["STORY-PURCHASE-03"]},
            {"seq": 3, "actor": "system", "action": "computes subtotal, discount, shipping and net total server-side",
             "entity_refs": ["ENTITY-ORDER"], "rule_refs": ["RULE-CHECKOUT-01", "RULE-CHECKOUT-02", "RULE-COUPON-02"], "story_refs": ["STORY-PURCHASE-03"]},
            {"seq": 4, "actor": "customer", "action": "confirms the order",
             "entity_refs": ["ENTITY-ORDER"], "rule_refs": ["RULE-CHECKOUT-03", "RULE-CHECKOUT-04"], "story_refs": ["STORY-PURCHASE-03"]},
            {"seq": 5, "actor": "system", "action": "reserves stock for every line and creates the order in awaiting-payment",
             "entity_refs": ["ENTITY-STOCK", "ENTITY-ORDER"], "rule_refs": ["RULE-STOCK-01", "RULE-STOCK-05"], "story_refs": ["STORY-PURCHASE-05"]},
            {"seq": 6, "actor": "customer", "action": "pays through the mock provider",
             "entity_refs": ["ENTITY-PAYMENT"], "rule_refs": ["RULE-PAYMENT-01"], "story_refs": ["STORY-PURCHASE-04"]},
            {"seq": 7, "actor": "system", "action": "converts the reservation to sold and moves the order to paid",
             "entity_refs": ["ENTITY-STOCK", "ENTITY-ORDER"], "rule_refs": ["RULE-STOCK-03", "RULE-ORDER-01"], "story_refs": ["STORY-PURCHASE-04"]},
            {"seq": 8, "actor": "customer", "action": "tracks the order against its frozen price snapshot",
             "entity_refs": ["ENTITY-ORDER"], "rule_refs": ["RULE-ORDER-06", "RULE-ORDER-08"], "story_refs": ["STORY-PURCHASE-06"]},
        ],
        "decision_points": [
            {"at_step": 4, "question": "Does the coupon still validate at confirm time?",
             "rule_refs": ["RULE-COUPON-03"],
             "branches": [{"condition": "the coupon is active and within both quotas", "goes_to": "5"},
                          {"condition": "the coupon expired or hit a quota while the customer browsed", "goes_to": "outcome: confirm refused"}]},
            {"at_step": 5, "question": "Is every ordered line still in stock at confirm?",
             "rule_refs": ["RULE-STOCK-05", "RULE-CHECKOUT-03"],
             "branches": [{"condition": "every line has enough available units", "goes_to": "6"},
                          {"condition": "another confirm won the last unit first", "goes_to": "outcome: out of stock at confirm"}]},
            {"at_step": 7, "question": "Did the mock provider capture the payment?",
             "rule_refs": ["RULE-PAYMENT-01", "RULE-PAYMENT-02"],
             "branches": [{"condition": "captured", "goes_to": "8"},
                          {"condition": "declined", "goes_to": "outcome: payment not completed"},
                          {"condition": "no result before the reservation expires", "goes_to": "outcome: reservation expired"}]},
        ],
        "outcomes": [
            {"name": "order placed and paid", "kind": "success", "entity_state": "paid", "story_refs": ["STORY-PURCHASE-04"]},
            {"name": "confirm refused", "kind": "failure", "entity_state": "awaiting-payment", "story_refs": ["STORY-PURCHASE-03"]},
            {"name": "out of stock at confirm", "kind": "failure", "entity_state": "awaiting-payment", "story_refs": ["STORY-PURCHASE-05"]},
            {"name": "payment not completed", "kind": "failure", "entity_state": "payment-failed", "story_refs": ["STORY-PURCHASE-04"]},
            {"name": "reservation expired", "kind": "abandon", "entity_state": "payment-timeout", "story_refs": ["STORY-PURCHASE-05"]},
        ],
        "story_refs": ["STORY-PURCHASE-01", "STORY-PURCHASE-02", "STORY-PURCHASE-03", "STORY-PURCHASE-04", "STORY-PURCHASE-05", "STORY-PURCHASE-06"],
    },
    {
        "id": "FLOW-ADMIN-FULFILMENT", "name": "Back-office fulfilment journey",
        "actor": "Merchant admin",
        "trigger": "A paid order appears in the back-office queue.",
        "steps": [
            {"seq": 1, "actor": "admin", "action": "reviews the paid order and confirms the goods are on hand",
             "entity_refs": ["ENTITY-ORDER", "ENTITY-STOCK"], "rule_refs": ["RULE-ORDER-01"], "story_refs": ["STORY-BACKOFFICE-02"]},
            {"seq": 2, "actor": "admin", "action": "adjusts stock to match a physical count, recording a reason",
             "entity_refs": ["ENTITY-STOCK"], "rule_refs": ["RULE-STOCK-06", "RULE-STOCK-07"], "story_refs": ["STORY-BACKOFFICE-01"]},
            {"seq": 3, "actor": "admin", "action": "moves the order to packing",
             "entity_refs": ["ENTITY-ORDER"], "rule_refs": ["RULE-ORDER-01"], "story_refs": ["STORY-BACKOFFICE-02"]},
            {"seq": 4, "actor": "admin", "action": "dispatches with a tracking number and moves the order to shipped",
             "entity_refs": ["ENTITY-ORDER"], "rule_refs": ["RULE-ORDER-03"], "story_refs": ["STORY-BACKOFFICE-02"]},
            {"seq": 5, "actor": "admin", "action": "records delivery",
             "entity_refs": ["ENTITY-ORDER"], "rule_refs": ["RULE-ORDER-01", "RULE-ORDER-02"], "story_refs": ["STORY-BACKOFFICE-02"]},
        ],
        "decision_points": [
            {"at_step": 3, "question": "Has the customer asked to cancel before packing starts?",
             "rule_refs": ["RULE-ORDER-05", "RULE-PAYMENT-03"],
             "branches": [{"condition": "no cancellation requested", "goes_to": "4"},
                          {"condition": "cancellation requested and packing has not started", "goes_to": "outcome: cancelled before packing"},
                          {"condition": "cancellation requested after packing started", "goes_to": "4"}]},
        ],
        "outcomes": [
            {"name": "order delivered", "kind": "success", "entity_state": "delivered", "story_refs": ["STORY-BACKOFFICE-02"]},
            {"name": "cancelled before packing", "kind": "escalation", "entity_state": "cancelled", "story_refs": ["STORY-BACKOFFICE-02"]},
        ],
        "story_refs": ["STORY-BACKOFFICE-01", "STORY-BACKOFFICE-02"],
    },
]

# --------------------------------------------------------------------------
# Stakeholders (gap-closed 14, named owners) — enumeration includes nobody
# absent, because the gap-closure workshop engaged Legal, DPO and Compliance.
# --------------------------------------------------------------------------
STAKEHOLDERS = [
    {"role": "Product Manager", "name_or_team": "Khun Pim", "raci": "A", "status": "present", "authority_mode": "rule", "attribution_confidence": "named"},
    {"role": "Merchant Owner", "name_or_team": "Khun Wirat", "raci": "A", "status": "present", "authority_mode": "rule", "attribution_confidence": "named"},
    {"role": "Operations Lead", "name_or_team": "Khun Mali", "raci": "R", "status": "present", "authority_mode": "rule", "attribution_confidence": "named"},
    {"role": "Marketing Lead", "name_or_team": "Khun Fah", "raci": "R", "status": "present", "authority_mode": "proposal", "attribution_confidence": "named"},
    {"role": "Legal Counsel", "name_or_team": "Khun Somchai", "raci": "A", "status": "present", "authority_mode": "rule", "attribution_confidence": "named"},
    {"role": "Data Protection Officer", "name_or_team": "Khun Apinya", "raci": "A", "status": "present", "authority_mode": "rule", "attribution_confidence": "named"},
    {"role": "Compliance Officer", "name_or_team": "Khun Niran", "raci": "C", "status": "present", "authority_mode": "rule", "attribution_confidence": "named"},
    {"role": "Finance Lead", "name_or_team": "Khun Decha", "raci": "R", "status": "present", "authority_mode": "rule", "attribution_confidence": "named"},
    {"role": "UX Lead", "name_or_team": "Khun Ploy", "raci": "C", "status": "present", "authority_mode": "preference", "attribution_confidence": "named"},
    {"role": "Tech Lead", "name_or_team": "Khun Anan", "raci": "C", "status": "present", "authority_mode": "estimate", "attribution_confidence": "named"},
]

OPEN_QUESTIONS = [
    {"id": "OQ-1", "severity": "P2",
     "question": "When a coupon fails re-validation at confirm, does the order reprice without the coupon or is the confirm refused outright?",
     "for": "dev", "why_matters": "The two behaviours differ in observable outcome and in how many round trips the customer sees; RULE-COUPON-03 states the re-check but not the branch.",
     "related_story_ids": ["STORY-PURCHASE-03"], "related_rule_ids": ["RULE-COUPON-03"]},
    {"id": "OQ-2", "severity": "P2",
     "question": "For the last-item race, is the winner the first confirm to reach the stock decrement, or the first to have opened checkout?",
     "for": "dev", "why_matters": "RULE-STOCK-05 fixes that exactly one wins but not the tie-break; the answer decides whether an ordering guarantee has to be built.",
     "related_story_ids": ["STORY-PURCHASE-05"], "related_rule_ids": ["RULE-STOCK-05"]},
    {"id": "OQ-3", "severity": "P2",
     "question": "How is a 30-minute reservation expiry observed in test - is there a way to advance the clock, or must a test wait?",
     "for": "tester", "why_matters": "RULE-STOCK-02 is untestable in a pipeline gate without an injectable clock; deciding late forces either a 30-minute test or an untested rule.",
     "related_story_ids": ["STORY-PURCHASE-05"], "related_rule_ids": ["RULE-STOCK-02"]},
    {"id": "OQ-4", "severity": "P2",
     "question": "Which admin actions must be provably rejected for a non-admin account, and how is that asserted in the fulfilment tests?",
     "for": "tester", "why_matters": "RULE-ORDER-05 names the authority but the negative-path coverage is a test-design decision that changes the story's acceptance criteria.",
     "related_story_ids": ["STORY-BACKOFFICE-02"], "related_rule_ids": ["RULE-ORDER-05"]},
    {"id": "OQ-5", "severity": "P3",
     "question": "Does the order number have a stated format beyond being readable and not trivially predictable?",
     "for": "PM", "why_matters": "RULE-ORDER-07 constrains the properties, not the shape; customers quote this number to support.",
     "related_story_ids": ["STORY-PURCHASE-06"], "related_rule_ids": ["RULE-ORDER-07"]},
]
