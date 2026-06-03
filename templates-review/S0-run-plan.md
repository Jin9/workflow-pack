<!-- TEMPLATE · stage S0 Intake · owner: Delivery Ops · produced-by: orchestrator + Iteration-Planner · audit_id: <audit_id:UUID> -->
# S0 Intake — Run Plan

> **Dual output.** This stage emits **two** artifacts:
> 1. **JSON contract → next node** (machine handoff, schema-validated): [`../schemas/delivery-pipeline-input.json`](../schemas/delivery-pipeline-input.json) — required fields `raw_request`, `requester`, `idempotency_key`; plus the normalized run-plan object.
> 2. **This human-review document** (rendered from this template) — the light plan sign-off gate (owner: Delivery Ops).
>
> Fill every `<…>` / `TBD-<what>-<who>`. Never invent values; never echo real PII (redact as `<PII:REDACTED:CLASS=…>`). Carries `audit_id` for the audit trail.

## Normalized intake
- **Requester:** `<name / team>`
- **Idempotency key:** `<idempotency_key>`  ·  **Run id (= audit_id):** `<audit_id:UUID>`
- **Raw request (verbatim, redacted):** `<raw_request>`
- **One-line restatement:** `<what we believe is being asked>`

## Scope & tier
- **Domain / data class:** `<banking-regulated | production | internal>` → tier `<T1 | T2 | T3>`
- **In scope:** `<…>`
- **Explicitly out of scope:** `<…>`  *(empty is suspicious — justify)*

## Stage plan (which stages run, and why)
| Stage | Run? | Owner | Note |
|---|---|---|---|
| S1 BA · S1.5 UX · S2 TL · S2.5 Plan-Review | `<yes/no>` | … | … |
| S3 Contracts · S4a/S4b Impl · S4*-r Review | `<yes/no>` | … | … |
| S4c QA-design · S5 QA-exec · S6 Deploy · S7 Prod | `<yes/no>` | … | deferred stages flagged here |

## Risk flags & open questions
- `<risk / unknown>` → `TBD-<question>-<who-answers>`

## Approval (plan sign-off — Delivery Ops)
- **Approver:** `<name / role>`
- **Verdict:** ☐ Approve ☐ Approve-with-caveats ☐ Reject
- **Date:** `<YYYY-MM-DD>`  ·  **audit_id:** `<audit_id:UUID>`
- **Notes:** `<…>`
