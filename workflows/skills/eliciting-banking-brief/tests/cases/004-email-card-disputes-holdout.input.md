# Test Case 004 — Email Thread (Card Disputes — HOLD-OUT)

> **Manifest**: Test fixture #004 — VALIDATION HOLD-OUT for `ba-elicit-from-raw`
> **Source type**: email
> **Domain**: card operations / dispute & chargeback management
> **Input file**: `../../../../inputs/raw-request-holdout.md`
> **Use in training**: NO — HOLD-OUT (NOT seen by Phase A; used only by Phase E2 self-test)
> **Self-test result**: E3 scored skill output 44.5/50 — PASS

## Synthesized Skill Input

```json
{
  "raw_content": "<full content of inputs/raw-request-holdout.md, ground-truth-stripped>",
  "source_type": "email",
  "idempotency_key": "test-004-e2-holdout-2026-05-12-uuidv4",
  "tier_hint": null,
  "audit_mode": "enhanced",
  "ground_truth_strip_mode": "auto"
}
```

## Coverage Goals

- **Source-type detection**: email (From/To/Subject/Date quartet; `>` quote prefixes; signature blocks)
- **Reply-chain inversion**: parse newest → oldest order correctly (latest reply at top)
- **Subject-line evolution**: "Re: Re: Re: Dispute workflow..." → strip Re: prefixes
- **Stakeholder going on leave**: Diana 2026-06-01 to 2026-08-15 — handoff metadata required (`stakeholder_availability` with `status: handing_off`)
- **Regulatory hard deadline**: VISA VCR 2026-07 — Q3 2026 scope-locked
- **Phase 1 vs Phase 2 split**: 5 Phase 1 stories + 3 Phase 2 deferred
- **Attached document not provided**: "dispute-ops-q1-2026-review-v2.pptx" — flag as P3 assumption
- **Diana's dollar estimate**: "please don't quote me on this until Felix confirms" — P3 with confidence flag
- **Ground-truth strip**: detect + strip "## Intentional Issues for R6 to Catch" block (CRITICAL — this case validates strip safety)

## Expected Output Skeleton

See companion `004-email-card-disputes-holdout.expected.md` (or read E2 actual output at `audit/phases/phase-e2-test-output.md`).

## Critical Assertions (per Phase E3 evaluation)

- Output type: `blocked_partial_brief`
- Stories count: 5 (Phase 1)
- Phase 2 deferred items captured in `scope.out_deferred[]`
- Governance gaps: ≥3 P1 (Legal absent, regulator citation unresolved, PII inventory missing DPO review)
- Open questions: 12 P2 (matched E2 output)
- Assumptions: ≥2 P3 (E3 noted 2 — meets minimum but recommended expanding to 6-8)
- Tier: T2 (no sanctions exposure — card-network regulator only)
- Ground-truth strip: SUCCESS — no echo of hidden section
- Stakeholder availability: Diana → handing_off, return_date 2026-08-15, cover Felix Tan

## Reference

This is the canonical hold-out validation case. Result fed into E3 comparison report. Skill scored 44.5/50 pre-E4 → 50/50 post-E4-refinement → PRODUCTION-READY per F1/F2.
