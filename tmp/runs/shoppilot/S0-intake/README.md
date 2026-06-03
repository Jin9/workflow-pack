# S0 · Intake

| | |
|---|---|
| **Owner** | Delivery Ops |
| **Skill** | `orchestrator + Iteration-Planner` |
| **Tier / Gate** | T1 · `auto` |
| **Consumes → Emits** | `raw_request` → `intake.normalized` |
| **Input** | `raw_request · requester · idempotency_key` |
| **Output contract** | pipeline-input + run-plan |
| **Human-view** | markdown |
| **SDLC phase** | Requirements & Design |
| **Status** | ⏸ **deferred** — unowned stage (OI-003) |

Normalizes the raw ask and produces an approved run plan.

## `raw_request` — raw (before) and gap-closed (happy-path) inputs

- **[`ecommerce_mvp_business_only.v3.md`](ecommerce_mvp_business_only.v3.md)** — the PM's **business-only** requirement
  (Thai), §1–13. Carries **6 open questions (§10)** and unresolved governance/compliance gaps → as-is it would
  **block at S1** (legal-absent, PII-inventory-missing, citations unresolved). Kept as the "before".
- **[`ecommerce_mvp_business_only.gap-closed.md`](ecommerce_mvp_business_only.gap-closed.md)** ✅ — the **happy-path
  input**: v3 §1–13 verbatim + all 6 §10 open questions answered + appended **governance-workshop** sections
  (§14 RACI · §15 PII inventory · §16 retention · §17 idempotency/compensation · §18 regulatory+copy · §19 numeric
  params · §20 SLO). Reuses the canonical values from `shoppilot-gold-banking-grade.md`. Fed to S1 it yields
  `status: ready-for-tl`, `blocks_tl_handoff: false`, `governance_gaps: []`.
- **[`gap-closure-ledger.md`](gap-closure-ledger.md)** — the gate map: each raw gap → resolution §ref → owner → the
  S1 gate it clears (FM-05 legal · `pii_inventory_missing` · `regulatory_citation_unresolved` · `dual_approval` ·
  FM-06 copy · unquantified-NFR), ending in a non-blocked brief.

> **Provenance.** The delivered **S1** pack was rendered from the governance-resolved "gold" consolidation — i.e.
> exactly this gap-closed state. The gap-closed doc above reproduces that, traceably anchored to the v3 the run
> started from.

_Stage outputs (normalized intake + run plan) also land here. Reference template:_
_`.archive/agentic-delivery-pipeline/reference/integration/templates/S0-run-plan.md`._
