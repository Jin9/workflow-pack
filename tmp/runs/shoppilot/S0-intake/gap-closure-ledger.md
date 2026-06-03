# Gap-closure ledger — ShopPilot raw requirement → happy-path

How `ecommerce_mvp_business_only.gap-closed.md` closes every gap/open question in the raw
`ecommerce_mvp_business_only.v3.md`, and **why that makes the whole flow run as a happy case**: each closed gap
clears a specific gate in S1 (`eliciting-banking-brief`) so the brief emits `ready-for-tl` with no P1 blocker, and
nothing loops back to a human downstream.

Resolution values are **canonical** — reused verbatim from
`.archive/agentic-delivery-pipeline/reference/integration/examples/shoppilot-gold-banking-grade.md`; the
blocker→resolution→owner mapping follows `reference/plan/worked-example-shoppilot.md` (the pipeline's Stage-3
governance table).

## Governance gaps → resolution → S1 gate cleared

| # | Raw gap (v3) | Resolution (gap-closed §) | Owner | S1 gate it clears |
|---|---|---|---|---|
| 1 | **Legal / DPO absent** on a PII + Thai-market flow (whole doc) | §14 RACI — Legal, DPO, Compliance named, engaged, signed | Khun Somchai / Khun Apinya / Khun Niran | **FM-05** `legal_absent_on_regulatory` (fires on 100% of regulatory-scope pilots) |
| 2 | **PII inventory missing** (§6.7, §8.2 list PII by example only) | §15 per-field inventory: class · lawful basis · retention · residency · masking | DPO (Khun Apinya) | `pii_inventory_missing` (AP-4.1 hard block) |
| 3 | **Retention unstated** (§6.7) | §16 schedule — customer/orders/audit **5y**, cart **30d**, tokens **90d** | DPO + Finance | P1 retention gap (FM-02 set) |
| 4 | **Regulatory citations unresolved** (§6, §8.2) | §18 — PDPA B.E. 2562 (§19/§23/§24/§30/§33/§37), CCA §26, CPA, Revenue Code, PCI-DSS v4.0 | Compliance + Legal | `regulatory_citation_unresolved` (FM-04) |
| 5 | **Dual-approval owner missing** for refund / admin-cancel (§4.10, §6.5) | §17 — refund **> 3,000 THB** = Finance + Merchant Owner; pre-packing cancel = Ops Lead | Finance / Ops | `dual_approval` (FM-02 set) |
| 6 | **Compensating action missing** for paid-but-cancelled (§4.10, §6.5) | §17 — stock release + **manual-refund SOP with idempotency key** | Finance (Khun Decha) | reversibility / compensating-action gap |
| 7 | **Customer-facing copy risk** — payment-failure / out-of-stock wording (§4.8, §12) | §18 — neutral copy ("payment was not completed" / "this item is no longer available"), Legal+UX reviewed | Legal + UX | **FM-06** tipping-off / unsafe customer-string |
| 8 | **"fast" NFR unquantified** (§8.3) | §20 SLO table — listing p50≤300/p95≤800; confirm p50≤500/p95≤1,200/p99≤2,000; detail p95≤800 ms | Tech Lead (Khun Anan) | unquantified-NFR → avoids a P2 open question |

## Open questions (§10) → answer → owner

| # | Open question | Answer | Owner | Gap-closed § |
|---|---|---|---|---|
| 1 | Cancelled-order review eligibility | **Not eligible** — review only after a `delivered` order | PM (Khun Pim) | §4.8 · §4.5 |
| 2 | Partial refund in MVP? | **Out of scope (Phase 2)** — manual refund SOP in MVP | Finance + PM | §17 · §12 |
| 3 | Abandoned-cart policy | **Purge after 30 days** inactivity | DPO + PM/Marketing | §16 |
| 4 | Coupon expiry mid-session | **Reject at confirm** (server re-validates; no grace period) | Marketing + Legal/UX | §4.4 · §4.7 · §18 |
| 5 | Delivered-confirmation actor | **Admin marks delivered**; customer-confirm deferred | PM + Ops | §4.5 |
| 6 | Stock-reservation TTL | **30 minutes** | Operations Lead (Khun Mali) | §19 |

These were P3-level decisions (business choices), never P1 blockers — they are recorded so the brief carries **no
undecided P1 open question**.

## Net effect on the S1 contract (happy path)

With every row above closed, `eliciting-banking-brief` on this input emits:

```json
{
  "output_type": "brief",
  "frontmatter": { "status": "ready-for-tl", "ba_confidence": "high", "blocks_tl_handoff": false },
  "governance_gaps": [],
  "open_questions": [ /* only P3/P2, none blocking */ ]
}
```

→ no `human-queue`, no loop-back at S1; the design/dev/QA stages proceed (subject to their own review gates) — the
whole flow can run as a **happy case**.

**Consistency check:** the already-delivered S1 pack in `../S1b-ba-brief/` (`INDEX.json` / `brief.json`) shows this
state — `status: ready-for-tl`, `ba_confidence: high`, `governance_gaps: []`, only `OQ-1`/`OQ-2` at **P3**, and **no
`blocks_tl_handoff` flag set** (absent ⇒ non-blocking) — confirming this gap-closed `raw_request` reproduces the
achieved happy-path brief.

> **Next step (not done here):** run the whole flow end-to-end with `squad-engine`
> (`.archive/agentic-delivery-pipeline/reference/engine/`): `validate` → `run --executor mock` (deterministic, free)
> or `--executor claude` (billed). Deferred per the "close gaps first" decision.
