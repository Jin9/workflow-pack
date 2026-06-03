# Test Case 003 — Meeting Notes (KYC — Enhanced Due Diligence)

> **Manifest**: Test fixture #003 for `ba-elicit-from-raw`
> **Source type**: meeting-notes
> **Domain**: KYC / customer onboarding / enhanced due diligence
> **Input file**: `../../../../inputs/raw-request-003.md`
> **Use in training**: YES (Phase A training example #3)

## Synthesized Skill Input

```json
{
  "raw_content": "<full content of inputs/raw-request-003.md, ground-truth-stripped>",
  "source_type": "meeting-notes",
  "idempotency_key": "test-003-9z8y-7x6w-5v4u-3t2s1r0q9p8o",
  "tier_hint": null,
  "audit_mode": "enhanced",
  "ground_truth_strip_mode": "auto"
}
```

## Coverage Goals

- **Source-type detection**: meeting-notes (`========` banner; `Meeting:`/`Date:`/`Note-taker:`/`Attendees:` quartet; `[Apologies: …]`; numbered agenda `## 1. … ## 8.`; `[Owner] task — due` bracketed action-items)
- **Note-taker mediation**: Aisha paraphrases — `Phase C2` AP "Treating note-taker summary as authoritative" must be avoided; flag confidence downgrade
- **Multi-epic detection**: This is 5-6 separate epics, NOT a single epic — skill must use `epics[]` form, not `epic{}`
- **Legal-absent EXPLICITLY noted** (`[Apologies: Legal — Sundar K., conflict with board prep]`) — strongest signal in any input — P1 immediately
- **Tier escalation candidacy**: T1 candidate (PEP, sanctions, AML, MAS regulator citation, dual approval, adverse media) — skill should flag T1 review even if labeled T2
- **Regulator citation incomplete**: "MAS-AML-1A revision" — flag as P2 (David action item pending)
- **Adverse media vendor**: "vendor (?)" in Karim's comment — name unresolved — P2
- **Risk engine threshold uncalibrated**: 0.75 not yet calibrated — P2 hard dependency
- **Acuant biometric**: security review path = spike — P2 with vendor-DPA hint
- **Stakeholder ownership unclear**: Aisha owns BA brief (late assignment); David owns migration workstream (TBD)

## Expected Output Skeleton

See companion `003-meeting-kyc.expected.md`.

## Critical Assertions

- Output: `multi_epic_brief` or `blocked_partial_brief` (Legal absent + multi-epic complexity)
- 5-6 epics emitted (or single epic with explicit "needs splitting" flag and multi-epic warning)
- Tier: T2 with `tier_escalation_candidate: T1` flag and reason
- Governance gaps: ≥3 P1 (Legal absent, regulator citation pending, multi-epic-not-decomposed if single-epic emitted)
- Open questions: 8-10 P2 (MAS citation, risk-engine calibration, vendor unnamed, security review timing, PII retention abandoned, NPS target acceptance, mobile scope, in-flight migration owner)
- Stakeholder absent: Legal (Sundar K. apologies — DIFFERENT from absent — should still flag), Customer Support, Migration owner, Data team owner
- Anti-pattern check: `note_taker_paraphrase` confidence downgrade applied
