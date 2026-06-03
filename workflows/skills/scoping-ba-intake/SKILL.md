---
name: scoping-ba-intake
description: >
  Stage 1 of the BA pipeline: ingest a raw requirement (Jira, email, meeting notes, document) and emit a typed Scope Sheet contract wrapped in the pipeline's shared envelope, ready for the BA/PM scope-confirm gate (G1) before stories are drafted. Produces business goal, in-scope and out-of-scope, quantified NFRs, open questions, assumptions, risk flags, and a ready-for-stories or needs-clarification state. Use when the user is running the BA pipeline and asks to "do intake", "produce the Scope Sheet", "scope this for the pipeline", or "is this requirement ready for stories". Do NOT use for standalone requirement scoping outside the pipeline (use scoping-technical-requirements); do NOT draft user stories here (use drafting-ba-stories).
compatibility: claude-code, codex, gemini-cli, opencode
---

# scoping-ba-intake

## Purpose
Stage 1 (`intake-agent`) of the BA pipeline. Turn a raw requirement into a typed **Scope Sheet** — a bounded scope
with quantified NFRs and surfaced open questions — wrapped in the shared envelope, ready for Gate G1. This is a
black-box node: it depends only on the raw requirement and emits one contract.

## When to use
- Triggers: *"do intake"*, *"produce the Scope Sheet"*, *"scope this for the pipeline"*, *"is this requirement ready for stories"*.
- **Not this skill:** standalone requirement scoping outside the pipeline → `scoping-technical-requirements`; drafting the user stories → `drafting-ba-stories`.

## Model & cost
Runs on a **mid** model (e.g. Sonnet 4.6 / Gemini 3 Pro), medium reasoning effort — structuring and NFR derivation, no deep trade-offs.

## Input
- The raw requirement (Jira ticket, email thread, meeting notes, business doc, or mixed prose).
- Optional: expected scale/volume, current system context, deadline.

## Output
A **Scope Sheet** contract — the shared envelope plus the S1 fields. Fill every field; surface gaps, do not guess.

```
# Scope Sheet — <task_id>
## envelope
task_id: REQ-<slug>            # the one trace id for this requirement
stage: S1
intent: scope the raw requirement
state: ready-for-stories | needs-clarification
confidence: high | medium | low          # low forces async human review
provenance: { raw_ref: <source doc/ticket>, upstream_contract_ref: none }
produced_by: intake-agent
owner: BA lead
schemaVersion: 1.0
created_at: <RFC-3339>
## contract
business_goal: <one sentence>
in_scope:       [ ... ]                   # explicit
out_of_scope:   [ ... ]                   # explicit — prevents scope creep
nfrs:           [ { kind: volume|latency|growth|cost|security|privacy, target } ]   # quantified, not vibes
open_questions: [ { id, question, for: BA|PM|SME } ]    # id = OQ-n (dense from 1, doc order); authoritative — downstream references it verbatim
assumptions:    [ ... ]
risk_flags:     [ unclear | likely-to-change | legacy-coupled ]
```

## Decision rules
1. Derive **NFRs from expected volume first** — no NFRs means not ready.
2. Turn every ambiguity into an **open question** with a stable id — `OQ-1`, `OQ-2`, … dense from 1 in document order — never a silent assumption. This id is **authoritative**: every downstream stage references it verbatim and never renumbers it (do not reuse the raw ticket's own numbering).
3. List **in-scope and out-of-scope** explicitly; name deferred / Phase-2 items as out-of-scope.
4. Flag **unclear / likely-to-change / legacy-coupled** in `risk_flags`.
5. Keep it **simple-first (YAGNI)** — capture the minimal requirement; defer nice-to-haves.
6. **Redact any real PII** to `<PII:REDACTED:CLASS=...>` before writing the contract.
7. If the input is too thin to scope, set `state: needs-clarification` and return it to the requester — do not invent scope.

## Checklist
- [ ] `business_goal` restated in one sentence
- [ ] `in_scope` and `out_of_scope` both explicit
- [ ] `nfrs` quantified (volume, latency, growth, cost, security, privacy as relevant)
- [ ] `open_questions` each carry an owner (`for: BA|PM|SME`)
- [ ] `assumptions` and `risk_flags` set
- [ ] Envelope complete (`task_id`, `schemaVersion`, `confidence`); `state` recorded
- [ ] No real PII in the contract

## Anti-patterns (never do)
- Convert ambiguity into a buried assumption instead of an open question.
- Emit unquantified NFRs ("fast", "scalable") without a target — flag them as open questions instead.
- Gold-plate the scope (add what is not needed yet).
- Draft stories here — that is `drafting-ba-stories`.
- Reuse the raw ticket's own question numbering — assign fresh `OQ-n` ids dense from 1 so downstream stages reference them stably.

## Example (ShopPilot MVP)
**Input:** a business-only e-commerce MVP spec (storefront + back office), Thai market.
**Output (excerpt):** *business_goal:* "let customers buy end-to-end on the web and let admins run catalog / stock /
orders from one back office". *out_of_scope:* real payment provider, returns/refunds, loyalty, multi-currency.
*nfrs:* the spec says "fast" with **no number** → logged as an open question, not accepted. *open_questions:* 6
(e.g. stock-reservation TTL, cancelled-order review eligibility). *risk_flags:* `unclear` (NFR), `likely-to-change`
(Phase-2). *state:* `ready-for-stories`.

## Human approval gate (G1)
**Stop.** BA / PM confirm `in_scope` vs `out_of_scope` and answer the blocking open questions before the requirement
advances to `drafting-ba-stories`. The Scope Sheet anchors all downstream work, so a named human signs it — the agent
never finalizes scope on its own confidence.
