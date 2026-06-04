# Plan-Review Findings — ShopPilot (S2.5 · adversarial red-team)

> Human-view for the `plan-review` gate. Skill `red-teaming-implementation-plan 0.1.0`. A critic
> separate from the plan's author, steelman-first, with reviewer-bias mitigation. Machine contracts:
> `plan-review-round1.json` (REVISE) and `plan-review.json` (final, PROCEED).

## Final verdict: **PROCEED** (confidence 0.75) — after one loop-back

The gate caps at **1 loop**. It used it: round-1 **REVISE** → Tech-Lead revision (ADR-008) → round-2 **PROCEED**. The cap was not exceeded, so no HardFail/abort.

## Loop trace

| Round | Reviewed | Verdict | Driver |
|---|---|---|---|
| 1 | S2 design (sync orchestration per ADR-007, **no outbox**) | **REVISE** | RT-2 (medium): non-atomic dual write / partial-failure window. 3 mediums, 2 lows, no blocking high. |
| — | **Loop-back to tl-design** (1 of 1) | — | TL adds **ADR-008**: transactional outbox + idempotent `order.create`/capture retry; TTL backstop. |
| 2 | S2 design v2 (**with ADR-008**) | **PROCEED** | RT-2 resolved; RT-1/3/4/5 downgraded to low, all owned/tracked. |

## Findings (final state)

| ID | Sev | Category | Status after loop | Owner / where tracked |
|---|---|---|---|---|
| RT-1 | low | architecture | Accepted MVP deviation (ADR-007), crash-safe via ADR-008 | TL — revisit on 2nd journey |
| RT-2 | — | data | **Resolved** (ADR-008 outbox + idempotent retry) | TL |
| RT-3 | low | operability | Tracked as OQ-3 (numeric SLOs) | PM + TL |
| RT-4 | low | requirements | Gate S4b frontend on UX maturity ≥ 2 | TL / UX |
| RT-5 | low | contract | Catalog/cart scope to BA; flag for QA | BA |

## Verdict policy applied

BLOCK if any `high` on a required path · REVISE if `medium`s but no blocking `high` · PROCEED if only `low`s.
Round 1 had mediums (no high) → REVISE. Round 2 had only lows → PROCEED.

## Reviewer-bias mitigation (recorded in the JSON)

- Steelman written **before** findings.
- **Heterogeneity caveat:** the design's author and this critic are the **same model** (Opus 4.8) — not a heterogeneous reviewer. Confidence is capped at 0.75 and a true cross-model re-review (Codex `gpt-5.5` / Gemini) is **recommended before the human L3 sign-off**.
- Dropped 2 unfalsifiable/hallucinated candidates (Kafka-overkill, Redis-SPOF).
- Verified RT-2 is genuinely closed by ADR-008 (event committed in the same DB tx), not merely renamed.

## Caveat — boundary schema

`workflows/delivery-pipeline.yaml` names `schemas/plan-review.json` for this node, but that file does
**not exist** in `workflows/schemas/`. Validated against the skill's own `schemas/output.json` + the
node `required_fields` `[verdict, findings, audit_id]`.
