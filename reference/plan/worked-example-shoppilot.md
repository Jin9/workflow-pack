# Worked Example — ShopPilot MVP through the pipeline

> Runs the five-stage flow on the real requirement `ecommerce_mvp_business_only.md` (ShopPilot MVP — a
> single-merchant B2C e-commerce shop, Thai market). The point is to show **what each stage emits**, **where the
> gate fires**, and how the **`blocked` → human resolution → re-run** loop works.
>
> The source document is itself a natural before/after: **§1–13** are the PM's business-only spec (the input);
> **§14–24** are a governance workshop that later resolves exactly the gaps Stage 3 surfaces. We use §1–13 as the
> Stage-1 input and §14–24 as the Stage-3 human resolution.
>
> `task_id = REQ-shoppilot-mvp`. All personal data is redacted as `<PII:REDACTED:CLASS=…>`; the workshop persona
> names below are the fixture's own synthetic values, shown only to illustrate "named owner".

---

## S1 · Intake & Scope → **Scope Sheet**  (`intake-agent`)

| Field | Value (excerpt) |
|-------|-----------------|
| `business_goal` | Let customers buy end-to-end on the web with no phone/chat, and let admins run catalog/stock/orders/coupons from one back office (§1.3). |
| `in_scope[]` | guest browse/search/filter; register & login; cart; coupons (1 per order); checkout with server-side totals; mock payment (success/fail/timeout); order tracking; cancel-before-pay; reviews after delivery; admin catalog/stock/coupon/order/review management; audit log; notification log (§4–§5). |
| `out_of_scope[]` | real PSP & courier; returns/refunds; loyalty; BNPL; marketplace; multi-warehouse; recommendations; live chat; mobile app; full multi-language; multi-currency; accounting integration; real email/SMS; CSV import; soft-delete recovery (§9). |
| `nfrs[]` | volume (to size at S4); latency "fast" (⚠ unquantified — §8.3); reliability (no oversell, no double-charge — §8.4); security (own-data-only, password hashing — §8.1); privacy (no PII in logs — §8.2); observability/health (§8.5). |
| `open_questions[]` | the 6 PM open questions (§10): cancelled-order review eligibility; partial refund; abandoned-cart policy; coupon-expiry-mid-session; delivered confirmation actor; stock-reservation TTL. |
| `risk_flags[]` | `unclear` (NFR "fast" not numeric); `likely-to-change` (deferred Phase-2 items). |
| `state` | `ready-for-stories` |

**Gate G1 — BA/PM confirms scope.** ✅ in/out-scope match §9; the 6 open questions are logged, not assumed.

---

## S2 · Story Drafting → **Story Set**  (`story-agent`)

Epic: **ShopPilot MVP storefront + back office.** Representative stories (full set would cover all of §4–§5):

**ST-03 — Checkout with server-side totals**
- *As a* logged-in customer *I want* to review my cart, address, coupon, shipping and net total before paying
  *so that* I pay exactly what the system computed, not a tampered client value.
- Business rules: totals computed server-side (§4.6); free shipping ≥ 1,500 THB else 60 THB (§6.3); one coupon,
  never negative, floored at 0 (§6.4); coupon re-validated at confirm (§4.5).
- Acceptance criteria (Given/When/Then):
  - *Given* a cart of 1,200 THB with `WELCOME100` *When* the customer confirms *Then* total = 1,160 THB
    (1,200 − 100 + 60 shipping) and an order is created in `awaiting-payment`.
  - *Given* a coupon that expired while the customer browsed *When* they confirm *Then* the order is rejected
    with a clear "coupon no longer valid" message (no stale client total trusted).
- Out of scope: coupon stacking (Phase 2).

**ST-05 — Stock reservation & last-item race**
- *As a* customer *I want* my checkout to reserve stock atomically *so that* two of us cannot both "succeed" on the
  last unit.
- Business rules: reserve on confirm, not on add-to-cart (§5.5); reservation TTL then release; never negative stock
  (§5.4); one winner on the race, the other sees a clear out-of-stock **at confirm, not at payment** (§12.5).
- Acceptance criteria: race path per §12.5; double-confirm yields one order (§4.7).
- `open_questions[]`: reservation TTL minutes? (carried from §10.6 — **not invented**).

**ST-09 — Admin fulfillment state machine**
- *As an* admin *I want* to move a paid order paid → packing → shipped (tracking required) → delivered *so that*
  customers can track it, with no illegal backward transitions (§5.7); every change in the audit log (§5.9).

**Gate G2 — async BA review.** ✅ stories are INVEST-shaped; acceptance criteria are concrete and testable.

---

## S3 · Governance & Risk → **Governance Check**  (`governance-agent`)  → **`blocked`**

The agent **flags, does not fix**. On the §1–13 input it surfaces:

| Type | Flag | Where seen |
|------|------|-----------|
| `pii_flag` | email, phone, name, address collected with **no per-field inventory / lawful basis / retention** | §2.2, §4.2–4.3, §6.7 |
| `compliance_flag` | **Legal/DPO absent** on a flow touching PII, consent, customer-facing copy, and a named market (Thailand) | whole doc |
| `compliance_flag` | **retention period unstated** for PII, orders, audit log | §6.6–6.7 |
| `compliance_flag` | **regulatory citations unresolved** (Thai PDPA/CCA/CPA/Revenue Code named obligations not cited) | §6, §8.2 |
| `compliance_flag` | **dual-approval owner missing** for admin cancellation / manual refund | §4.10, §5.7, §6.5 |
| `compliance_flag` | **compensating action missing** for paid-but-cancelled (refund is "manual", no SOP) | §4.10, §6.5 |
| `compliance_flag` | **customer-facing copy risk** — payment-failure / out-of-stock wording must not imply fraud/risk | §4.8, §12.4 |
| `blocker` | each of the above → `resolve_owner: Legal / DPO / Compliance / Finance / Ops` | — |

`verdict: blocked` → **Gate G3 fires.** The pipeline **cannot** proceed to feasibility or handoff.

### Human resolution (the loop-back) — this is the document's §14–24

A 4-week workshop with **named owners** resolves each blocker (illustrative names from the fixture):

| Blocker | Resolution | Owner | §ref |
|---------|-----------|-------|------|
| Legal/DPO absent | Legal Counsel + DPO + Compliance engaged | Khun Somchai / Khun Apinya / Khun Niran | §14.1 |
| PII inventory missing | per-field inventory: class, lawful basis, retention, residency, masking | DPO | §15.1 |
| Retention unstated | retention schedule (5y Revenue-Code envelope; cart 30d; tokens 90d) | DPO + Finance | §15.2, §20.1 |
| Citations unresolved | full statute pack (PDPA §19/§23/§30/§33/§37, CCA §26, CPA, DSDMA, Revenue Code, PCI-DSS v4.0) | Compliance + Legal | §14.4 |
| Dual-approval owner | refunds > 3,000 THB need Finance + Merchant Owner; pre-packing cancel = Ops Lead | Finance / Ops | §17.2–17.3 |
| Compensating action | manual-refund SOP with idempotency key | Finance | §17.2 |
| Customer-copy risk | neutral payment-failure / out-of-stock copy, Legal-reviewed | Legal + UX | §19.8 |
| "fast" unquantified (from S1) | SLO table (p50/p95/p99 per surface) | (Eng) | §18 |

Sign-offs recorded (§24). Resolved decisions are appended → the **affected stages re-run** with the enriched input.

---

## S3 (re-run) → **`clear`**

With §14–24 folded in, the Governance Check re-runs: every blocker now has a named resolution and owner; the
customer-facing copy passes the wording review. `verdict: clear`. This matches the source document's own closing
prediction (line 1192): re-elicitation yields `blocks_tl_handoff: false`, `status: ready-for-tl`.

---

## S4 · Feasibility & Scope → **Feasibility Note**  (`feasibility-agent`)

Consumes the Story Set + the (now `clear`) Governance Check **+ the raw requirement**.

| Field | Value (excerpt) |
|-------|-----------------|
| `options[]` | (a) atomic DB-row stock decrement at confirm — simple, fits MVP; (b) reservation table + TTL sweep — more moving parts, needed for the §5.5 hold window. Pros/cons each. |
| `dependencies[]` | mock payment provider (later Omise, §16); mock courier; AWS Singapore residency (§15.7); e-Tax broker for VAT (§21.4). |
| `risks[]` | last-item race (mitigate: atomic decrement + integration test per §12.5); webhook double-delivery (mitigate: idempotency key per `Omise-Event-ID`, §16.4); price-snapshot drift (mitigate: copy price/name into order at creation, §6.8). |
| `spikes[]` | `{ "stock reservation TTL & sweep", 2 days }`; `{ "idempotent webhook handler", 1 day }`. |
| `verdict` | `buildable` (MVP scope; Phase-2 items explicitly deferred). |

**Gate G4 — TL verdict.** ✅ `buildable`.

---

## S5 · TL Handoff → **Handoff Bundle**

What the Tech Lead receives and signs for:

| Bundle field | Content |
|--------------|---------|
| `raw_requirement` | the full `ecommerce_mvp_business_only.md` (provenance — the TL sees the original ask) |
| `scope_sheet` | S1 above |
| `story_set` | S2 above (full set) |
| `governance_check` | S3 **re-run**, `verdict: clear` |
| `feasibility_note` | S4 above, `verdict: buildable` |
| `open_items[]` | PM/Sponsor-accepted deferrals: cancelled-order review eligibility, partial refund, dormant-product archival (§23) |
| `state` | `ready-for-tl` |
| `accepted_by` | _<Tech Lead name + date>_ |

**Gate G5 — TL accepts (sync named approval).** On acceptance the **TL becomes the accountable owner of record**
for everything built from this bundle.

---

## What this demonstrates

- **Surface-don't-repair**: the seven governance gaps were *flagged*, never auto-fixed; a named human cleared each.
- **The blocker loop is the safety mechanism**: nothing reached the TL while `blocked`.
- **Raw requirement travels to the TL** — not just the distilled contracts.
- **One trace id** (`REQ-shoppilot-mvp`) threads all five stages; each emit is an inspectable contract.
- The end state matches the source document's own prediction — a useful fidelity check on the design.
