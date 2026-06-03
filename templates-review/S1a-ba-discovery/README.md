<!-- TEMPLATE · stage S1a BA Discovery · owner: BA lead · produced-by: researching-ba-problem-space ^1.0.0 · audit_id: <audit_id:UUID> -->
# S1a · BA Discovery — Discovery review doc (problem-space layer)

The **first half** of the S1 composite. `researching-ba-problem-space ^1.0.0` **AI-drafts** a discovery artifact
from the raw request — problem framing · opportunities · the **four product risks** · regulatory regimes · a
**proceed / needs-work / do-not-build** recommendation — and a **named human decides** on that recommendation at
the gate. Only **`proceed`** releases [`S1b · BA Brief`](../S1b-ba-brief/); `needs-work` loops back,
`do-not-build` stops the pipeline. This is the irreversible-decision boundary, surfaced as its own card in
`squad-delivery-dashboard.standalone.html` (`S1a · BA Discovery`).

## Dual output
- **Machine handoff → next node (S1b brief):** `discovery.json`, validated by
  [`../../schemas/discovery.json`](../../schemas/discovery.json) (required: `problem_framing`, `assumptions`,
  `recommendation`, `audit_id`). On `proceed` it carries an optional `handoff_to_intake` block — an **advisory**
  typed handoff merged into S1b's `input.discovery`.
- **Human view:** a **discovery review doc** (problem-space layer). The discovery layer is also rendered as
  **Layer 0** of S1b's unified `ba-research-viewer.html`, so the named human reads framing · risks · regimes ·
  recommendation in one offline page before deciding.

## Template in this folder
| File | Role |
|---|---|
| `discovery.template.json` | the discovery contract (mirrors `researching-ba-problem-space/schemas/output.json`): `problem_framing` · `opportunities[]` · `assumptions[]` (each tagged `risk_type` ∈ value/usability/feasibility/viability — the four product risks) · `regulatory_regimes[]` · `recommendation` · optional `handoff_to_intake` · `audit_id` |

## The gate (supervision boundary)
- **Gate:** async-peer (L2) — **BA lead**; queue `ba-discovery-review`; `max_retries 0` (no auto-retry — a
  recommendation is a human judgment).
- **proceed_when:** `recommendation == proceed`. A regulatory hard-blocker → human gate; `recommendation ≠ proceed`
  blocks S1b.
- **AI drafts; the named human owns the decision** and remains the accountable owner of record.

## `handoff_to_intake` — advisory only
Emitted **only** when `recommendation == proceed` (the nested `recommendation` must be `proceed`; its `audit_id`
**must equal** the top-level `audit_id` — one audit identity across the discovery→brief chain). Intake may use it
to **seed** (regime hints → pending-citation rows, absent-stakeholder hints, a tier **floor** via `tier_signal`),
but it **never** suppresses a detector, lowers a tier, or discharges a governance gate (e.g. Legal-absence). On
**RB-01** (the raw request is *already* a structured requirement) discovery emits **no** handoff.

## Conventions
- Frame the **opportunity, not a solution**; no real PII — redact to `<PII:REDACTED:CLASS=…>`.
- Mark **"Not in play"** regimes explicitly (e.g. KYC/AML) so intake does not assume a financial-crime regime.
- `audit_id` threads `discovery.json`, this review doc, and the S1b handoff to one run for the audit trail.

## Producer / status
`researching-ba-problem-space ^1.0.0` (matured from draft to banking-grade) emits the discovery JSON; the discovery
layer renders into S1b's unified viewer. **Wired live in `workflows/delivery-pipeline.yaml`** as node `s1-discovery`
(GAP-05 closed).

## Sign-off (BA lead — async L2 gate on `recommendation`)
- **Reviewer:** `<named human>`  ·  **Decision:** ☐ proceed ☐ needs-work ☐ do-not-build
- **Date:** `<YYYY-MM-DD>`  ·  **audit_id:** `<audit_id:UUID>`  ·  **Notes:** `<…>`
