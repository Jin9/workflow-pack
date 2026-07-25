# Ambiguity Patterns

> 8 ambiguity types + P1/P2/P3 severity engine + conflict-resolution rules. Loaded by `SKILL.md` Step 9 on every input.

## Purpose & When to Apply

Run all 8 detectors over every text segment. **Anti-patterns compose — never deduplicate flags across detectors.** A single phrase can carry multiple flag types (banking-grade + linguistic ambiguity + stakeholder-mode); each fires independently.

Sources: C22, C23, C24; AP-6.1, AP-6.2, AP-6.3; A2 §5; B2 HC1/HC2/HC5/HC6; B5 C1/C6.

## 8 Ambiguity Types

### 3.1 Lexical

- **Definition**: vague word without testable predicate.
- **Detection**: words `urgent`, `reasonable`, `appropriate`, `piecemeal`, `happy`, `compliant`, `improved`, `consistent` appear without adjacent measurable predicate.
- **Default severity**: P3; **P2 if in AC**; P2 cluster-promoted when >5 in one input.
- **Rewrite example**: `Compliance is happy` → `Given a document replacement event, When the audit event is emitted, Then it contains {actor, ts, doc_id, before_hash, after_hash, reason} AND Compliance Officer can retrieve the trail via the audit dashboard within 5 seconds.`

### 3.2 Syntactic

- **Definition**: parenthetical aside negates main clause (self-contradiction).
- **Detection**: patterns `\([^)]*\b(or|maybe|unclear|but|though)\b[^)]*\)` adjacent to main clause; explicit `(?)` or `(unclear)` markers.
- **Default severity**: **P2** (self-contradicting AC is the canonical surface-don't-resolve pattern — AP-2.1).
- **Rewrite example**: `Old document is replaced (or maybe kept as version? unclear)` → AC1 `Then old document is replaced (most-evidenced reading)` + OQ-1 P2 `Resolve: replace vs version-archive on document re-upload — both readings present in source (line 54). Suggested resolver: Priya (Compliance).`

### 3.3 Pragmatic

- **Definition**: context-dependent reference requiring domain knowledge to resolve.
- **Detection**: bare demonstratives `that's regulated comms`, `that's the rule`, `that's the workflow`; named-without-definition tokens like `the policy`, `the standard`, `the bucket`.
- **Default severity**: P2 if in AC; P3 otherwise. **Mandatory-vagueness exception** (§7) when regulator-required vague language.
- **Rewrite example**: `that's regulated comms` → glossary entry `regulated_comms` (definition + regulator citation) + AC `Then customer message MUST conform to non-tipping vocabulary per MAS-AML-1A` + P1 OQ if citation unresolved.

### 3.4 Pronominal

- **Definition**: pronoun referring across >1 sentence boundary.
- **Detection**: `this`, `it`, `they`, `that`, `those`, `same thing` with antecedent distance >1 sentence or window >5 messages (Slack).
- **Default severity**: P3 in non-AC context; **P2 in AC**.
- **Rewrite example**: `they should send the doc — they = applicant or compliance?` → OQ-N P2 `Resolve antecedent of "they" in line 84: applicant or compliance officer?`

### 3.5 Quantifier

- **Definition**: vague quantifier without adjacent numeric.
- **Detection**: word-list `some`, `several`, `a few`, `many`, `most`, `lots of`, `a LOT`, `multiple`, `often`, `sometimes`, `frequently`, `rare`, `typically`. Count occurrences; **>5 in one input → completeness penalty** (AP-6.3).
- **Default severity**: P3. **Banking-grade-relevant metric → P2** (audit-defensibility gap per A5 G-F).
- **Rewrite example**: `getting a LOT of escalations` → fact `escalations_unquantified: true` + OQ-N P2 `Quantify escalation rate per week to compute baseline for success metric.`

### 3.6 Modal

- **Definition**: closed-class hedge in prescriptive section.
- **Detection**: tokens `may`, `might`, `could`, `should`, `would`, `probably`, `maybe`, `possibly`, `perhaps`, `ideally`, `tentatively`, `hopefully` in `Acceptance Criteria` / `Decisions` / `Action Items` sections.
- **Default severity**: P2 per occurrence. **Authority-mode override** (per AP-6.2): Compliance speaker in regulatory context → rule mode → bind to MUST; PM/Eng with hedge → proposal/preference mode → emit OQ.
- **Rewrite example**: `should NOT just be deleted` (Compliance speaker, retention topic) → AC `MUST NOT be deleted; document MUST be archived for 7 years per retention policy`. `might slip a sprint` (PM hedge) → OQ-N P2 `Confirm sprint commitment for agent-UI changes.`

### 3.7 Commitment-Conditionality

- **Definition**: stakeholder agrees subject to a not-yet-met precondition — the commitment LOOKS firm but is structurally contingent.
- **Detection**: patterns `\b(yes|ok|sure|agree|will|put .* on .* list)\b.{0,40}\b(pending|subject to|once|after|if|assuming|provided|contingent on)\b`; explicit phrases `pending Phase 1 scoping`, `subject to TL design`, `once budget approved`, `if [precondition]`.
- **Default severity**: **P2** — soft commitments routinely harden into firm scope under planning pressure without the precondition ever being met.
- **Rewrite example**: Yvonne: `I can put this on the Q3 candidate list pending Phase 1 scoping` → OQ-N P2 `Q3 commitment for [item] is conditional on Phase 1 scoping completion. Confirm: (a) what gates the scoping; (b) who decides Q3 lock-in once scoping done; (c) fallback if scoping slips past Q3 commit deadline.` Also emit `assumptions_made[]` entry recording the conditionality. Never encode the soft "yes" as firm scope.

### 3.8 Phase-Boundary Drift

- **Definition**: work split into Phase 1 / Phase 2 / future-phase, where Phase 2 items risk being pulled forward under pressure OR Phase 1 items risk slipping.
- **Detection**: presence of explicit phasing tokens (`Phase 1`, `Phase 2`, `phase one`, `next phase`, `deferred to Q4`, `future iteration`, `out of this scope, but later`) + ≥2 items deferred + customer/regulatory pressure signals on a deferred item.
- **Default severity**: **P2** OQ on boundary-drift risk + **P3** assumption documenting current commitment-status of deferred phases.
- **Rewrite example**: Input has Phase 1 = 5 stories, Phase 2 = customer comms templates + packet auto-assembly + win-loss analytics → OQ-N P2 `Phase 1 / Phase 2 boundary drift risk: which Phase 2 items are at highest pull-forward risk under customer-attrition pressure? Define a guard rule (e.g., "no Phase 2 work admitted to Phase 1 without re-tier + capacity re-plan"). Suggested resolver: Yvonne + Felix.` + A-N P3 `Phase 2 items currently catalogued but not commitment-status confirmed; treat as Q4/Q1 candidates pending Phase 1 burn-down.`

## Severity Assignment Rules (P1/P2/P3)

| Severity | Triggers | Action |
|---|---|---|
| **P1 (blocker)** | Legal absent on regulatory; regulator named without citation; tipping-off violation; missing PII inventory on T1; missing compensating action on funds movement; calibration debt on risk routing | Block TL handoff. `governance_gaps[]` + `blocks_tl_handoff: true`. |
| **P2 (must-address)** | Self-contradicting AC; anonymous policy parameter; modal hedge in commitment; placeholder token unattached to regulator; notification-matrix gap; AC vs comment-thread conflict; mobile parity deferral on regulated workflow; emoji-only sign-off on compliance topic; **commitment-conditionality (§3.7)**; **phase-boundary drift (§3.8)** | Surface as `open_questions[].severity: P2`. Must resolve before sprint planning. |
| **P3 (assumption-to-document)** | Pronoun across sentence boundary (non-AC); quantifier without quantity (non-cluster); urgent-label-without-SLA; pragmatic shorthand in non-regulatory context | Document in `assumptions_made[]`. Move on. |

**Context lift rules**:

- Relative-date + regulator citation = P2 (not P3) — B5 C6.
- Quantifier on banking-grade metric = P2 (not P3) — A5 G-F.
- Cluster of >5 quantifier-without-quantity in one input = completeness penalty + P2 promotion.
- P3 detectors escalate to P2 when topic is regulatory; P2 escalates to P1 when authority-mode is rule (B2 C4).

## Anonymous Comment Downgrade Rule

Anonymous commenter + numeric policy parameter = **automatic P2 floor** (promoted from P3 per C16 + B2 C1 + B5 C1).

Triggers:

- Speaker `Anonymous`, `Anonymous (likely X)`, `Unknown`, `(group, N min)`.
- Utterance proposes numeric policy default: `N=3`, `retention = 30 days`, `score threshold = 0.75`, `EDD bucket = 5 days`.

Action: **refuse to bind** as AC. Emit `proposed_value: 3, attribution: anonymous_guessed_raj, status: requires_named_owner_P2`. Link to deference graph for who should formally own. Never encode anonymous numeric as policy parameter.

## Conflicting Commenter Resolution

Maintain per-entity decision ledger. Conflict triggers: same field/decision + ≥2 speakers + incompatible content.

Resolution rules (apply in order):

1. **Compliance rule-mode beats PM AC** — when AC and compliance rule-mode comment conflict, the comment wins. Original AC becomes "Assumption Overridden" with both `source_quote`s preserved (per C15 + B3 C6).
2. **Compliance proposal-mode does NOT auto-beat data/eng feasibility** — when compliance suggests (e.g., "0.75 threshold") and data/eng challenges on feasibility grounds, escalate to joint sync (per A4 §3.5).
3. **Latest authoritative quote = working answer** — but never drop the earlier conflicting one. Both quotes go into `open_questions[].conflict_evidence[]`.
4. **Anonymous claim never wins** — see Anonymous Downgrade Rule (§5).

Output: `open_questions[].conflict_evidence: [{speaker, quote, line_ref, authority_mode}]`, `recommended_resolution_path`. Working answer empty or "TBD pending <resolver>" until resolved (per FM-03).

## Mandatory-Vagueness Exception

Regulator-required vague language is **correct**, not a P2 lexical defect. Example: tipping-off-safe rejection text MUST be vague ("transfer could not be completed; please contact the sender") because regulation prohibits revealing the real reason.

Detection: compliance speaker in rule mode + customer-facing-comm scope + forbidden-term substitution. Disambiguate via authority-mode (§3.6): Compliance rule-mode + customer-facing-comm scope = mandatory-vagueness; do NOT flag as P2 lexical ambiguity. Cross-reference `non-tipping-vocabulary.md` for approved vague phrasings.

## Placeholder Token Class

Tokens: `(?)`, `TBD`, `???`, `$Xk`, `N attempts`, single capital in numeric slot, `<TODO>`.

- **Default severity**: P2.
- **Escalation to P1**: when attached to regulator citation, PII-vendor parameter, retention duration, or compensating-action specification.
- **Action**: surface as OQ with placeholder context preserved. Require named owner before binding to AC.

## Cross-References

- `anti-patterns.md` §6 (AP-6.1 silent pick; AP-6.2 modal as binding; AP-6.3 quantifier as quantified) + §2 (AP-2.1 silently resolving; AP-2.3 anonymous as named)
- `gherkin-templates.md` §4 (concrete-value enforcement) + §7 (anti-patterns in Gherkin)
- `edge-case-catalog.md` (EC-02 conflicting commenters, EC-14 anonymous, EC-15 note-taker paraphrase)
- `non-tipping-vocabulary.md` (mandatory-vagueness approved phrases)
