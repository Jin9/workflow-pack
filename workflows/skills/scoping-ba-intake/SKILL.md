---
name: scoping-ba-intake
version: 2.0.0
description: The S0 intake stage of the delivery pipeline: ingest a raw requirement (Jira, email, meeting notes, document) and emit the run-plan artifact — a PII-redacted normalized_request string, a typed run_plan (tier floor, stage span, expected epics, human gates), and a typed Scope Sheet (business goal, explicit in-scope and out-of-scope, quantified NFRs, stable open questions, assumptions, risk flags) — ready for BA discovery. Use when the user is running the delivery pipeline and asks to "do intake", "produce the Scope Sheet", "scope this for the pipeline", or "normalize this request for the pipeline". Do NOT use outside the delivery pipeline. Do NOT use for problem-space discovery (use researching-ba-problem-space). Do NOT draft epics or stories here (use breaking-down-ba-scope).
stage_type: analyze
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: enhanced, pii_handling: redact, tier_default: T2, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 180
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, gemini-cli, opencode
---

# scoping-ba-intake

## Purpose

Stage **S0 (`intake`)** of the delivery pipeline. Turn a raw requirement into the run-plan artifact: a
normalized request string every downstream stage reads, a run plan that bounds the work, and a typed
**Scope Sheet** — bounded scope, quantified NFRs, surfaced open questions. This is a black-box node: it
depends only on the workflow's raw request and emits one contract. Its successor is `s1-discovery`.

## When to use this skill

- Use when: the delivery pipeline is running and the raw request needs normalizing/scoping — *"do
  intake"*, *"produce the Scope Sheet"*, *"scope this for the pipeline"*.
- Do NOT use: **outside the delivery pipeline** (this stage exists to feed it).
- Do NOT use: for problem-space discovery — "should we build this at all" is
  `researching-ba-problem-space` (S1a, which consumes this stage's output).
- Do NOT use: to draft epics/stories — that is `breaking-down-ba-scope` (S1b).

## Input contract

`schemas/input.json` is **ENFORCED** — the engine validates the ASSEMBLED payload against it before this stage runs (fail-closed); the
schema documents the POST-adapter payload assembled at stage `intake`. Required: `raw_request` (the
raw requirement prose), `requester`, and the engine-injected `idempotency_key`. There are **no**
`upstream_artifacts` or `loop_back_feedback` — S0 has no producer and no loop-back path.

Scale, current-system context, and deadlines are **not separate fields**: the strict workflow input
never supplies them, so whatever exists lives inside `raw_request`. Redact real PII as
`[PII:REDACTED:CLASS=...]` before writing anything.

**Example (validates against schemas/input.json):**

```json
{
  "raw_request": "A single Thai merchant wants a B2C storefront plus an admin back office covering browse, cart, checkout, mock payment and delivery tracking. Must be extensible to a real PSP later.",
  "requester": "shoppilot-demo",
  "idempotency_key": "req-2026-07-12-shoppilot-001"
}
```

## Output contract

Validate against `schemas/output.json`. Required: `normalized_request`, `run_plan`, `scope_sheet`, and
`audit_id`; `human_view` optional.

- **`normalized_request`** — a non-empty, PII-redacted **string** that restates the request preserving
  every stated constraint and inventing no answers. This is what `s1-discovery` and `ba-research`
  consume. (It is never an object — the structured breakdown lives in `scope_sheet`.)
- **`run_plan`** — `tier_floor` (T1|T2|T3 — a **floor** downstream may raise, never lower, derived from
  the request's stated money/PII/regulatory exposure), `stage_span`, `epics_expected` (integer ≥ 0
  derived from the distinct capability areas named; **0 = not yet estimable**, never a guess); optional
  `pipeline` and `human_gates[]` (copied from the pipeline's gate configuration, not invented).
- **`scope_sheet`** — `envelope` (`stage: S0`, `state: ready-for-discovery`, confidence, provenance,
  produced_by, owner, schemaVersion) + `contract` (`business_goal`, explicit `in_scope`/`out_of_scope`,
  `nfrs[{kind,target}]` quantified, `open_questions[{id: OQ-n, question, for}]`, `assumptions`,
  unique `risk_flags`).
- **`audit_id`** — the **sole artifact identity** (there is no `task_id`):
  `UUIDv5(HOUSE_NS, "intake:{idempotency_key}")`,
  `HOUSE_NS = uuid5(NAMESPACE_URL, "https://squad-delivery/audit")` — distinct from the engine's
  per-attempt audit id in `events.jsonl`.

`OQ-n` ids are stable **within** this Scope Sheet and its human review. Downstream stages do **not**
receive the scope sheet today (the pipeline passes only `normalized_request`) — make no cross-stage
traceability promise.

**Example (validates against schemas/output.json):**

```json
{
  "normalized_request": "Build a single-merchant Thai-market B2C storefront plus an admin back office covering browse, cart, checkout, payment, fulfilment and tracking, extensible to a real payment provider.",
  "run_plan": {"tier_floor": "T2", "stage_span": "S0-S7 + T1-T12", "epics_expected": 4},
  "scope_sheet": {
    "envelope": {"stage": "S0", "intent": "scope the raw requirement", "state": "ready-for-discovery", "confidence": "high", "provenance": {"raw_ref": "requirement.md", "upstream_contract_ref": "none"}, "produced_by": "intake-agent", "owner": "BA lead", "schemaVersion": "1.0"},
    "contract": {
      "business_goal": "Let customers buy end-to-end on the web and let admins run catalog, stock and orders from one back office.",
      "in_scope": ["customer auth", "checkout with server-computed totals", "admin fulfilment"],
      "out_of_scope": ["real payment provider", "returns and refunds", "loyalty"],
      "nfrs": [{"kind": "volume", "target": "<= 5k orders/day at MVP; design headroom 4x"}],
      "open_questions": [{"id": "OQ-1", "question": "What is the stock-reservation TTL?", "for": "BA"}],
      "assumptions": ["Thai-market single merchant"],
      "risk_flags": ["unclear", "likely-to-change"]
    }
  },
  "audit_id": "82ca53e0-2bfd-56ef-bed1-dffa9ff88ba2"
}
```

## Procedure

1. **Normalize the request.** Restate `raw_request` as one PII-redacted string that preserves every
   stated constraint and invents no answers. Entry: the raw prose. Exit: `normalized_request`.
2. **Derive the run plan — never guess.** `tier_floor` from the money/PII/regulatory exposure the
   request *states*; `stage_span` from the delivery shape it implies; `epics_expected` by counting the
   distinct capability areas named (**0** when the request names none clearly — 0 means "not yet
   estimable", not "none"). `human_gates` are copied from the pipeline's configured gates.
3. **Derive NFRs from expected volume first** — no NFRs means not ready. An unquantified NFR ("fast",
   "scalable") becomes an **open question**, never an accepted target.
4. **Turn every ambiguity into an open question** with a stable id — `OQ-1`, `OQ-2`, … dense from 1 in
   document order (do not reuse the raw ticket's numbering) — never a silent assumption.
5. **Bound the scope explicitly:** `in_scope` and `out_of_scope` both listed; deferred/Phase-2 items are
   out-of-scope. Keep it simple-first (YAGNI). Flag `unclear` / `likely-to-change` / `legacy-coupled` in
   `risk_flags`.
6. **Emit** the artifact with `state: ready-for-discovery` and the house `audit_id`. Stop — the next
   stage is `s1-discovery`.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| INTAKE-01 | the request is too thin to scope at all | **NO artifact** — the stage fails | routed to `delivery-intake-pending` for a named human; never a schema-valid "needs-clarification" artifact that the auto gate would wave through |
| INTAKE-02 | ambiguity within a scopable request | artifact emitted with the ambiguity as an `OQ-n` open question | resolved by the named owner (`for: BA|PM|SME`) |

## Constraints

- DO NOT invent scope, NFR targets, epic counts, or answers — a gap is an open question, not an
  assumption.
- DO NOT emit unquantified NFRs ("fast", "scalable") as targets.
- DO NOT gold-plate (add what is not needed yet) or draft stories here.
- DO NOT reuse the raw ticket's question numbering — assign fresh dense `OQ-n` ids.
- DO NOT echo real PII — redact as `[PII:REDACTED:CLASS=...]` before writing the contract.
- DO NOT claim downstream stages reference the Scope Sheet: only `normalized_request` is passed today.
- The Scope Sheet anchors downstream work — a named human reviews it; the agent never finalizes scope
  on its own confidence.

## Example (ShopPilot MVP)

**Input:** a business-only e-commerce MVP requirement (storefront + back office), Thai market.
**Output (excerpt):** *business_goal:* "let customers buy end-to-end on the web and let admins run
catalog / stock / orders from one back office". *out_of_scope:* real payment provider, returns/refunds,
loyalty, multi-currency. *nfrs:* the request says "fast" with **no number** → logged as an open
question, not accepted. *open_questions:* 6 (e.g. stock-reservation TTL). *risk_flags:* `unclear`,
`likely-to-change`. *state:* `ready-for-discovery`.
