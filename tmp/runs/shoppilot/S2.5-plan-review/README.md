# S2.5 · Plan-Review gate

| | |
|---|---|
| **Owner** | Tech Lead |
| **Skill** | `red-teaming-implementation-plan 0.1.0` (adversarial red-team) |
| **Tier / Gate** | T1 · `gate` (loop-back cap 1 → HardFail) |
| **Consumes → Emits** | `ba.brief · tl.design` → `plan.reviewed` |
| **Input** | S1 brief (epic·stories·gaps) + S2 `tl-design` (component_map·api_contracts) |
| **Output contract** | `plan-review.json` — `verdict` (PROCEED/REVISE/BLOCK) + `findings[]` + `audit_id` |
| **Human-view** | `plan-review-findings.md` (markdown today; HTML viewer planned) |
| **State** | ✅ produced (2026-06-04) · **PROCEED** after one loop-back · skill-schema PASS |

Red-teams the BA+TL plan **before** the expensive S3/S4 fan-out (cheap to reverse, high blast radius
→ it gates). Caps at 1 loop; `REVISE`/`BLOCK` reroute to `tl-design`; cap exceeded → `HardFail`
(no fan-out, human reviews).

## Files

```
plan-review.json          final verdict — PROCEED (round 2, reviewed S2 v2 with ADR-008)
plan-review-round1.json   round-1 verdict — REVISE (reviewed S2 v1, drove the ADR-008 loop-back)
plan-review-findings.md   human-view: verdict, loop trace, findings table, bias mitigation
README.md                 this file
```

## Outcome

**PROCEED (confidence 0.75)** after exactly **one** loop-back (cap respected). Round-1 **REVISE** was
driven by RT-2 (non-atomic dual write); the Tech-Lead loop-back added **ADR-008** (transactional outbox
+ idempotent retry); round-2 returned **PROCEED** with only low, owned findings. Backend fan-out (S3/S4a)
is cleared; **frontend (S4b) is gated on UX maturity ≥ 2** (RT-4).

## Caveats

- **Same-model self-review.** The S2 design author and this critic are both Opus 4.8 — not a
  heterogeneous reviewer. Confidence is capped and a cross-model re-review (Codex `gpt-5.5` / Gemini) is
  **recommended before the human L3 sign-off**. (Both recorded in `bias_checks`.)
- **Boundary-schema gap.** `schemas/plan-review.json` is referenced by the YAML but **absent**; validated
  against the skill's `schemas/output.json` + node `required_fields`.
- **Stop point.** This is where the run stops — S3 `contract-design` and downstream are **not** run.
