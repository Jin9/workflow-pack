# Test Case 002 — Slack (Payments — Wire Transfer Status)

> **Manifest**: Test fixture #002 for `ba-elicit-from-raw`
> **Source type**: slack
> **Domain**: payments / wire transfers (inbound)
> **Input file**: `../../../../inputs/raw-request-002.md`
> **Use in training**: YES (Phase A training example #2)

## Synthesized Skill Input

```json
{
  "raw_content": "<full content of inputs/raw-request-002.md, ground-truth-stripped>",
  "source_type": "slack",
  "idempotency_key": "test-002-1a2b-3c4d-5e6f-7a8b9c0d1e2f",
  "tier_hint": null,
  "audit_mode": "enhanced",
  "ground_truth_strip_mode": "auto"
}
```

## Coverage Goals

- **Source-type detection**: slack (`#ops-payments — Slack channel` banner; `Name (Role) — Today HH:MM`; emoji reactions; 📎 Linked)
- **Conversational parsing**: extract decisions from interleaved chat (eg "ok let me draft. so the asks are roughly: 1. ... 2. ... 3. ... 4.")
- **Decision-by-emoji**: 👍 acceptance pattern — flag as P2 ambiguity (not formal approval)
- **Tipping-off detection**: tipping-off language explicit in chat (Mei: "we MUST NOT show... sanctions context"); skill must scan customer-facing comms; this is a load-bearing safety guard
- **Ground-truth strip**: detect + strip
- **Multi-story split**: 5-6 stories (customer-facing "additional review" status, internal back-office state, agent UI, customer notifications, rejection messaging, mobile-deferred)
- **Mobile-vs-web scope ambiguity**
- **Legal-absent on tipping-off content**: P1 governance gap
- **ETA bucket conflation**: single bucket for compliance-hold (24-72h) + ops-review (same-day) — P2 granularity loss

## Expected Output Skeleton

See companion `002-slack-payments.expected.md`.

## Critical Assertions

- INVEST: all stories pass
- Gherkin: tipping-off-safe rejection scenarios per `gherkin-templates.md` §6.3
- Banking-grade: idempotency on customer notifications (don't email twice on same state change)
- Tipping-off scan: explicitly should NOT be clean — sanctions context in chat — `processing_metadata.tipping_off_scan_clean: false`
- Output type: `blocked_partial_brief` (Legal absent + tipping-off risk P1)
- Governance gaps: ≥2 (Legal absent on regulatory content; tipping-off risk requiring Legal review of customer-facing language)
- Tier: T2-bordering-T1 (sanctions exposure mentioned but customer-facing only) — skill should flag tier escalation candidacy
- Open questions: 5-8 P2 (ETA conflation, notification policy, legal-review-timeline, mobile scope, tipping-off PEP/adverse-media coverage)
- Anonymous commenters: none (all named — Jenny, Tom, Mei, Raj, Sarah)
