# INVEST Checklist

> Per-letter pass/fail rules for every story candidate. Loaded by `SKILL.md` Step 7 (splitting) and Step 10 (testability).

## Purpose & When to Apply

Run this checklist on every story candidate emitted by Step 7 of `SKILL.md`. Run again on any story whose AC count exceeds 7 (AP-7.3). Run on every split decision. **Pro tip from ba-best-practices §1: flag for TL, don't force-fit.** If a story doesn't pass INVEST cleanly, surface the failure as a `split_recommendation` or an Open Question — never silently rewrite.

Sources: C9, C10, C25-C28, C29, C30; AP-7.1, AP-7.2, AP-7.3, AP-8.4; ba-best-practices §1, §5, §7.

## Per-Letter Detail

### I — Independent

- **Pass**: each `depends_on[]` entry resolves to an in-brief story id OR appears in `processing_metadata.external_dependencies`. Story can be delivered alone (or marked dependency).
- **Fail signals**: `depends_on: ["frontend Story 2", "backend Story 3"]` — tech-layer chain. Or implicit "needs the API first" with no explicit edge.
- **Common failure**: "Re-upload UI" depends on "Re-upload API" — neither delivers user value alone (tech-layer split — AP-7.1).
- **Fix**: re-split by workflow step (submit / verify / approve), business rule, or role. UI+API together as one workflow-step story.

### N — Negotiable

- **Pass**: no tech-layer prescription in `title` / `card`. Spike stories whitelisted.
- **Fail signals**: title contains `API`, `endpoint`, `DB schema`, `frontend component`, `microservice`, `lambda`.
- **Common failure**: "Implement /reupload POST endpoint with idempotency-key header" — prescribes implementation, removes negotiation room.
- **Fix**: re-frame as user behavior ("Re-upload corrected document"); leave implementation to TL.

### V — Valuable

- **Pass**: `card.so_i_can` (or `so_that`) length ≥ 12 chars AND contains a value-word (complete / verify / track / comply / resolve / submit / receive / approve / understand / recover).
- **Fail signals**: "so I can use the system"; "so that the API works"; soft generic outcomes.
- **Common failure**: "So I can interact with the workflow" — no concrete value.
- **Fix**: trace back to the affected stakeholder concern (Compliance verifies retention; customer completes re-upload; agent resolves the case).

### E — Estimable

- **Pass**: `sizing.story_points ∈ {1,2,3,5,8,13}` OR `"TBD_by_TL"` (requires `split_required: true`).
- **Fail signals**: story points 21 / 34 / "?"; complexity "unknown" without spike-story whitelist.
- **Common failure**: 13 SP with `split_required: false` — boundary case left unsplit.
- **Fix**: spike-precede if dependency unknown; split-precede if too large.

### S — Small

- **Pass**: `sizing.story_points ≤ 8` OR `sizing.split_required: true`.
- **Fail signals**: 13 SP with no split-axis identified; AC count > 7 with `split_required: false`.
- **Common failure**: a single story covers Compliance + Eng + UX + Ops concerns (AP-7.3).
- **Fix**: split along legitimate axes (see Split Patterns Table below). Never tech-layer.

### T — Testable

- **Pass**: `acceptance_criteria.length ≥ 3` AND every AC is well-formed Gherkin (see `gherkin-templates.md` §3 + §8).
- **Fail signals**: AC says "Compliance is happy" / "the system handles it correctly" / "user is satisfied". `Given the system` without state.
- **Common failure**: missing banking-grade scenarios on a state-change story → automatic `T` fail (AP-8.4).
- **Fix**: rewrite per `gherkin-templates.md`; if no measurable predicate exists, convert AC to Open Question (AP-4.2).

## Split Patterns Table

When `S` fails, use one of these 8 split axes. Never the 9th (tech layer).

| Axis | When to use | Example | Source |
|---|---|---|---|
| Workflow steps | State machine with ≥2 named states | Re-upload happy → verify → escalate | C25 |
| Business-rule variations | Rules differ by data class / customer tier / risk class | Re-upload regular doc vs sensitive NRIC (archive-vs-delete diverges) | C26 |
| Happy vs alternate path | Distinct error / loop / escalation flows | Re-upload happy / retry-limit / abandon | AP-7.2 |
| Data variations | PII vs non-PII; biometric vs identity-doc | Document re-upload generic vs NRIC photo | C27 |
| CRUD operations | Create vs read vs update vs delete differ in authority | Case lookup (R) vs case escalation (U) | best-practices §5 |
| Roles | Customer UI vs agent UI; analyst vs senior approver | Wire status — customer-facing vs agent-UI | C28 |
| Optimize-later | Defer perf/scale concerns to follow-on story | MVP re-upload + later "re-upload with progress bar" | best-practices §5 |
| Spike | Pure investigation with no AC commitment | "Spike: validate Acuant SLA under load" | best-practices §5 |

## Anti-Pattern — Layer-Based Splitting

**Forbidden axis**: frontend / backend / DB / API. Violates `Independent` (UI has no value without API; API has no value without UI) and `Valuable` (neither layer delivers user outcome alone). See AP-7.1 in `anti-patterns.md`.

If a split feels forced and the only available axis is technical layer, **flag for TL** rather than force-fitting INVEST.

## INVEST + Banking-Grade Interaction

The `T` (Testable) letter auto-fails when banking-grade scenarios are missing on a stateful or notification op:

- State change (document replace / wire status update / case escalation) → must have ≥1 `banking_grade_idempotency` scenario.
- Notification (email / push / in-app) → must have ≥1 `banking_grade_audit` scenario + (if customer-facing) ≥1 `banking_grade_tipping_off` check.
- Funds movement / external write → must have ≥1 `banking_grade_reversibility` scenario with `compensating_action`.

Reference AP-8.4 in `anti-patterns.md` and §6 of `gherkin-templates.md` for templates.

## Self-Check

For every AC, ask: **"Can a tester write an automated test from this scenario without asking questions?"** If NO → rewrite or convert to Open Question (AP-4.2).

## Cross-References

- `gherkin-templates.md` §3 (format), §6 (banking-grade templates), §8 (testability self-check)
- `anti-patterns.md` §7 (AP-7.1 / 7.2 / 7.3) + §8 (AP-8.4)
- `ba-best-practices.md` §1 (INVEST), §5 (split patterns), §7 (Definition of Ready)
