# LEAN_DECISION — document-contract leaning

> **Workflow:** `workflows/delivery-pipeline.yaml` · **Date:** 2026-05-31
> **Decision authority:** **Claude is the final decision-maker.** Codex (GPT-5.5, effort xHigh) ran as an
> **advisory** read-only brainstorm; Claude weighed it and owns the applied set; a named human signs off below.
> **Mechanism:** keep-but-mark-advisory — **no template is deleted**; leaned stages are flagged JSON-only (the
> readable doc becomes optional). **The JSON contract is never dropped.**

## Lean rule
A stage is **JSON-only** iff it has **no human verify/sign-off gate** AND its only consumer is a machine node.
Signed review docs at human gates are banking audit evidence and stay dual-output.

## Final decision (Claude) — agreed JSON-only set
**`S3a/3b Contracts (BE/FE)` · `S4a Backend Impl` · `S4b Frontend Impl`** → **JSON-only (doc advisory)**.
All 11 human-gate stages (S0, S1, S1.5, S2, S2.5, S4a-r, S4b-r, S4c, S5, S6, S7) → **keep dual-output**.

Claude ↔ Codex **agree fully** (no disagreement; conservative default not needed). Claude adopts Codex's contrarian
refinement: the human-inspectable evidence for the leaned stages is produced at the **adjacent gates** — S2 TL Design
(api_contracts) covers S3, and S4a-r / S4b-r reviews cover the impl manifests — so no human-review evidence is lost.

## Per-stage verdict
| Stage | Verdict | Why |
|---|---|---|
| S0 Intake | KEEP-READABLE | auto + plan sign-off (human verify) |
| S1 BA Research | KEEP-READABLE | async L2 human gate |
| S1.5 UX Intake | KEEP-READABLE | async L2 human gate |
| S2 TL Design | KEEP-READABLE | sync named L3 |
| S2.5 Plan-Review | KEEP-READABLE | decision gate (HardFail HITL) |
| **S3a/3b Contracts** | **JSON-ONLY** | auto · no verify · machine-consumed; evidence at S2 / reviews |
| **S4a Backend Impl** | **JSON-ONLY** | auto · sandboxed · manifest+code; evidence at S4a-r |
| S4a-r Backend Review | KEEP-READABLE | async L2 human gate |
| **S4b Frontend Impl** | **JSON-ONLY** | auto · sandboxed · manifest+code; evidence at S4b-r |
| S4b-r Frontend Review | KEEP-READABLE | async L2 human gate |
| S4c QA Test Design | KEEP-READABLE | sync conditional-go L3 |
| S5 QA Validation | KEEP-READABLE | sync L3 |
| S6 Deploy | KEEP-READABLE | sync named L3, mandatory, irreversible |
| S7 Prod Validation | KEEP-READABLE | sync L3, named rollback decision |

## Codex brainstorm (advisory, verbatim) — `model: gpt-5.5 · effort: xhigh · read-only · 2026-05-31`

> **Final JSON-ONLY set:** `S3a/3b Contracts BE/FE`, `S4a Backend Impl`, `S4b Frontend Impl`.
> Every other stage → KEEP-READABLE (each has a human verify/sign-off gate, so the signed doc is audit evidence).
>
> **Contrarian / edge:** "If contract or implementation stages are directly inspected by humans for compliance,
> architecture governance, or external API approval, they are no longer 'machine-only' consumers; keep them
> JSON-first but generate readable evidence in the adjacent review/gate stage rather than re-adding per-stage docs."
>
> **Banking audit caveat:** "Dropping readable docs is acceptable only for non-gated machine-only stages; every
> human verify/sign-off gate must retain signed, immutable, traceable review evidence."

## Sign-off
- **Final decision by:** Claude (synthesis · owner of the applied set)
- **Named human approver:** `<name / role>`  ·  **Verdict:** ☐ Approve ☐ Adjust set ☐ Reject
- **Date:** `<YYYY-MM-DD>`  ·  **Notes:** `<…>`
