# S1a · BA Discovery — problem-space discovery + recommendation gate

> The first half of the S1 composite. `researching-ba-problem-space` **AI-drafts** a discovery
> artifact from the raw request; a **named human decides** on its `recommendation` at the gate. Only
> **`proceed`** releases the brief node ([`../S1b-ba-brief/`](../S1b-ba-brief/)).

| | |
|---|---|
| **Stage** | S1a · BA Discovery |
| **Skill** | `researching-ba-problem-space 1.0.0` *(re-run/re-stamped 2026-06-04; output unchanged)* |
| **Owner** | BA lead |
| **Input** | `../S0-intake/ecommerce_mvp_business_only.gap-closed.md` (the raw request) |
| **Output contract** | [`workflows/schemas/discovery.json`](../../../../workflows/schemas/discovery.json) |
| **YAML node** | `s1-discovery` in `workflows/delivery-pipeline.yaml` |
| **Gate** | ⏸ async peer (L2) — recommendation gate; queue `ba-discovery-review` |
| **Recommendation** | **proceed** (this fixture) |

## The recommendation gate

`discovery.json` carries a `recommendation ∈ {proceed | needs-work | do-not-build}`. This is the
**irreversible-decision boundary** of S1, surfaced as its own stage:

- **`proceed`** → releases `../S1b-ba-brief/` (the `eliciting-banking-brief` node runs).
- **`needs-work`** → loops back for more discovery.
- **`do-not-build`** → stops the pipeline.

A regulatory hard-blocker is never auto-resolved — it routes straight to the `ba-discovery-review`
human queue (`max_retries: 0`).

## Files

```
discovery.json          the discovery artifact — problem framing · opportunities · the four product
                        risks (value / usability / feasibility / viability) · regulatory regimes ·
                        recommendation (+ optional handoff_to_intake)
discovery-input.json    the discovery skill input (provenance)
README.md               this file
```

## Caveats

- **RB-01 provenance.** The discovery layer was derived **retrospectively** from an already-structured
  requirement (the gap-closed spec is already sections 1–20: RACI, PII inventory, retention, SLOs), so
  it reads as a derived problem-space record rather than true upstream discovery. Full note inside
  `discovery.json`'s `problem_framing`.
- **No real PII** — personas are synthetic; redact any sensitive class as `<PII:REDACTED:CLASS=…>`.

## Handoff → S1b

On `proceed`, the discovery normally emits a `handoff_to_intake` block passed as an **advisory**
typed input into `eliciting-banking-brief` (it may seed pending-citation rows, stakeholder hints and
a tier *floor*, but never suppress a detector, lower a tier, or satisfy a citation). **For this
fixture, RB-01 applies** — the source is already a fully-structured requirement — so per the skill
contract **no `handoff_to_intake` is emitted** (`discovery.json` carries none), and the brief node
runs on `raw_content` alone. With the discovery handoff absent, the `eliciting-banking-brief 1.5.0`
node is behaviour-identical to v1.4.x. The brief, epics and stories are materialised in
[`../S1b-ba-brief/`](../S1b-ba-brief/).
