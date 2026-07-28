# Anti-Patterns Catalog

> 26 anti-patterns across 8 buckets. Loaded by `SKILL.md` Step 9 (conflict arbitration) and Step 12 (final guardrails).

## Purpose: Surface, Don't Repair

Anti-patterns = **things the skill MUST NOT do**. Unifying principle: **Surface, don't repair.** When an anti-pattern fires, emit an Open Question + risk flag rather than silently rewriting the input. Repair is the BA's downstream responsibility. Silent repair launders ambiguity into shipped requirements and breaks audit reconstruction.

Sources: Phase C2 §§1-8 (all 26 APs); C2 §9 (enforcement); C2 §10 (severity index).

## 1. Wrong Inferences

- **AP-1.1 — Inferring lifecycle policy from process labels.** *Detection*: skill writes "documents auto-deleted after N days" without verbatim Compliance quote or attached policy. *Correct*: emit `retention.status: unknown_p2` + dependency `policy_doc_attachment`. Never copy retention number across inputs. *Severity*: P2 (P1 on T1).
- **AP-1.2 — Inferring priority from label vocabulary.** *Detection*: input label `urgent` becomes `priority: P1` / `MoSCoW: Must` without SLA / deadline / pain quote. *Correct*: surface label as assumption-to-document; compute priority from quantified evidence (call volume, regulator deadline, sponsor authority). *Severity*: P3.
- **AP-1.3 — Inferring tier from explicit label while ignoring content** [HANDOFF BLOCK]. *Detection*: meta-label says T2 but content carries regulator + dual approval + Compliance directive + tipping-off + Legal absent. *Correct*: re-infer tier from content; when inferred > label by ≥1 step, emit `tier.inferred > tier.manual` with firing signals + require human override. Multi-epic: tier per epic. A v1.5.0 `discovery.tier_signal` is a **floor only** (`max(inferred, tier_hint, tier_signal)`) — it can raise (subject to this same override) but never lower an inferred tier. *Severity*: **Handoff block**.

## 2. Common Skill Failures

- **AP-2.1 — Silently resolving ambiguity instead of surfacing.** *Detection*: source AC has embedded contradiction (`"replaced (or maybe kept as version? unclear)"`) and output picks one branch without OQ. *Correct*: split into AC (most-evidenced reading) + OQ (P2) referencing both alternatives + suggested resolver. *Severity*: P2.
- **AP-2.2 — Burying ambiguity in an "Assumptions" section.** *Detection*: ≤2 P2 OQs and ≥5 assumptions each requiring named-authority decision (Compliance / Legal / Risk). *Correct*: if resolution requires a person's authority → Open Questions. If answerable by data → Assumptions. *Severity*: P2.
- **AP-2.3 — Treating anonymous commenter as if named.** *Detection*: `Anonymous (likely Raj) — N could be 3` encoded as hard policy parameter in AC. *Correct*: tag `attribution: anonymous`; refuse numeric/policy binding; emit `proposed_value, requires_named_owner: true`. *Severity*: P2.

## 3. Forbidden Simplifications

- **AP-3.1 — Collapsing internal SLA disparity into one customer-facing ETA without flagging.** *Detection*: single customer-facing ETA (e.g., "up to 5 business days") with no OQ surfacing underlying internal SLAs (24-72h compliance vs same-day 95% ops). *Correct*: emit `eta_flattening_observed: true` with both internal SLAs + OQ requiring named authority decision. *Severity*: P2.
- **AP-3.2 — Treating Compliance as Legal** [P1 IF REGULATORY]. *Detection*: skill records "Legal sign-off: complete" because Compliance gave an opinion. *Correct*: disjoint Compliance vs Legal slots. Compliance rule mode binds implementation but does NOT discharge Legal-engagement on customer-facing language, regulator citations, biometric contracts, retention variances. Emit `legal_status` independently. *Severity*: **P1 if regulatory**.
- **AP-3.3 — Squashing multi-epic initiative into one epic to fit template.** *Detection*: 4+ workstreams under one epic header. *Correct*: detect scope-kind first; ≥3 distinct workstreams each with ≥2 ACs → `scope_kind: multi-epic` with one epic per workstream. Never compress under template-fit pressure. *Severity*: P2 (structural).

## 4. Banking-Grade Violations

- **AP-4.1 — Marking PII = none without explicit reasoning** [HANDOFF BLOCK T1/T2]. *Detection*: `pii_fields: []` for story involving documents / applicants / customers / IDs / biometrics. *Correct*: produce `pii_inventory` per field. If truly none, emit `status: not_applicable, justification: <workflow class + reason>`. Schema rejects empty justification. *Severity*: **Handoff block**.
- **AP-4.2 — Producing acceptance criteria without testability check.** *Detection*: `Then` contains `happy`, `satisfied`, `fast`, `improved`, `consistent`, `compliant` without measurable predicate; `Given the system / a user`. *Correct*: pass every AC through testability filter; replace soft language with observable predicates; if none derivable, emit OQ. *Severity*: P2.
- **AP-4.3 — Skipping idempotency evaluation on customer-notification or state-change ops.** *Detection*: state transition / notification / replace op with no `idempotency` row or `not_applicable` without justification. *Correct*: default-fill row for every side-effect story with `idempotency_key_strategy` + Gherkin replay scenario. *Severity*: P1 (T1/T2).
- **AP-4.4 — Allowing tipping-off-risky language in customer-facing comms unflagged** [P1 + HANDOFF BLOCK]. *Detection*: customer-facing AC contains `sanctions / AML / flagged / suspicious / compliance hold / fraud review / PEP / adverse media` OR "compliance is reviewing your transfer" as customer copy. *Correct*: run `tipping_off_scan`; on hit emit P1 + non-tipping safe phrasing + `formal_signoff_pending: legal`. Block TL handoff until Legal sign-off recorded. *Severity*: **P1 + handoff block**.

## 5. Stakeholder Neglect

- **AP-5.1 — Listing only named stakeholders, not detecting Legal absence** [HANDOFF BLOCK]. *Detection*: Stakeholders block omits `legal_status` field OR treats `[Apologies: Legal — Sundar K.]` as informational. *Correct*: always emit `legal_status`; when ≠ `present` AND scope touches regulatory → P1 governance block. Run same check for Privacy/DPO, Security Reviewer, SAR Liaison, Model Owner, Migration Owner. *Severity*: **P1 + handoff block**.
- **AP-5.2 — Over-weighting Owner who lacks domain authority.** *Detection*: "approved by Sarah Lim" on a retention/PII/customer-comms item where decision requires Compliance / Legal / Security / Data sign-off. *Correct*: schema each authority as `{topic_class, named_authority, authority_mode}`. Attach topic-appropriate approver per AC. Owner is structural, not substitute for SME sign-off. *Severity*: P2.
- **AP-5.3 — Treating note-taker's paraphrase as authoritative as original speaker.** *Detection*: Priya's compliance directive quoted verbatim via Aisha note-taker without `attribution_confidence: paraphrase, mediated_via: Aisha` flag. *Correct*: tag every quoted statement `attribution_confidence: paraphrase`; for P1/P2 emit "verbatim verification with <original speaker>" action item before binding. *Severity*: P2.

## 6. Ambiguity-Burying

- **AP-6.1 — Silently picking one stakeholder's answer when commenters disagree.** *Detection*: output records single resolution where two commenters made incompatible claims (Jenny "web first" vs Sarah Khoo "web, then agent, then mobile") with no OQ referencing both quotes. *Correct*: per-entity decision ledger; OQ (P2) listing both quotes + attribution + timestamps. Accept latest authoritative quote as working answer but preserve conflict ledger. *Severity*: P2.
- **AP-6.2 — Resolving modal ambiguity ("should/may") as binding requirement.** *Detection*: "the system MUST X" where source said "should NOT" or "we may need" or "might slip". *Correct*: tokenize modals; apply authority-mode override: Compliance speaker in regulatory context → rule mode (MUST); PM/Eng hedge → proposal mode (OQ). Never collapse modal force in either direction silently. *Severity*: P2 (P1 if compliance rule).
- **AP-6.3 — Treating quantifier ambiguity ("many", "most", "a LOT") as quantified.** *Detection*: "approximately 142 cases/week" where source said "a LOT". *Correct*: maintain quantifier word-list; emit assumption-to-document per unbound occurrence on banking-grade metric. Pair with adjacent numerics when present. Count >5 → completeness penalty. *Severity*: P3 (cluster → P2).

## 7. Story Granularity

- **AP-7.1 — Splitting by frontend / backend / DB layer instead of by user value.** *Detection*: stories "Re-upload UI", "Re-upload API", "Re-upload DB schema". *Correct*: split using workflow steps / business rules / happy-vs-error / data variations / CRUD / roles / spike. Tech-layer forbidden. If splitting feels forced, flag for TL. *Severity*: P2 (re-split).
- **AP-7.2 — Merging happy path + error path into one story / scenario.** *Detection*: single scenario contains `Then user sees success` AND `Then user sees error if X` chained with `And`. *Correct*: one happy-path scenario + one error/edge-case scenario as mandatory minimum. Distinct error paths become separate scenarios. If AC count >7, split story. *Severity*: P2 (re-split).
- **AP-7.3 — Not splitting when AC count exceeds 7.** *Detection*: 8+ Gherkin scenarios in one story; or story description with 10+ bullet points each implying distinct AC. *Correct*: when >7 scenarios or >5 distinct stakeholder concerns, emit `split_recommendation` with proposed axis. *Severity*: P2 (re-split).

## 8. AC Quality

- **AP-8.1 — Vague `Given` clauses.** *Detection*: `Given the system`, `Given a user`, `Given the application`. *Correct*: each `Given` references concrete actor + concrete state + concrete input data. Soft preconditions trigger rewrite or OQ. *Severity*: P2 (rewrite).
- **AP-8.2 — Multiple actions in one `When`.** *Detection*: `When the user clicks submit and the system validates and the notification fires`. *Correct*: one trigger action per `When`. Split into two scenarios with different `Given` setups. `And` chains `Given` / `Then` only. *Severity*: P2 (rewrite).
- **AP-8.3 — `Then` clauses without observable outcome.** *Detection*: `Then the user is happy`, `Then compliance is satisfied`. *Correct*: each `Then` references UI element change / DB state with field+value / outbound message with required payload / downstream event with schema. Subjective predicates → rewrite or OQ. *Severity*: P2 (rewrite).
- **AP-8.4 — Missing banking-grade scenarios on stateful or notification operations** [HANDOFF BLOCK T1/T2]. *Detection*: state change / notification / replace op without idempotency-replay AND audit-emission scenarios. *Correct*: auto-emit per `gherkin-templates.md` §6: idempotency-replay + audit-emission + (if customer-facing) tipping-off-safe scenarios. *Severity*: **Handoff block**.

## Top 5 Handoff Blockers (Quick Reference)

| AP | One-line |
|---|---|
| **AP-1.3** | Tier from label, ignoring content — re-infer; emit `inferred > manual` |
| **AP-4.1** | PII = none without justification — force `pii_inventory` or `not_applicable + justification` |
| **AP-4.4** | Tipping-off-risky language unflagged — `tipping_off_scan` + safe phrase + Legal sign-off |
| **AP-5.1** | Legal-absence not detected — always emit `legal_status`; P1 gap on regulatory |
| **AP-8.4** | Missing banking-grade scenarios — auto-emit idempotency + audit + (if customer-facing) tipping-off |

## Cross-Cutting Enforcement Notes

1. **Anti-patterns compose** — one source phrase can fire multiple guards. "We may need to split" by anonymous commenter on compliance topic fires AP-2.3 + AP-6.2 + AP-5.1. Each fires independently — **never deduplicate** (B5 §6 decision 2).
2. **Severity escalates by context** — P3 escalates to P2 when topic is regulatory; P2 escalates to P1 when authority-mode is rule (B2 C4).
3. **Handoff blockers override quality scores** — AP-1.3, AP-4.1, AP-4.4, AP-5.1, AP-8.4 prevent TL handoff even when other scores are high.
4. **Pair-with-positive-test** — every guard needs a disable path (e.g., AP-4.1 disabled by explicit `pii.status: not_applicable, justification: <reason>`). Without disable-path, guards become noise.
5. **Surface, don't repair** — unifying rule. Skill detects + structurally enforces; BA repairs downstream.

## Cross-References

- `invest-checklist.md` §5 (AP-7.1 tech-layer split)
- `gherkin-templates.md` §7 (AP-8.1 / 8.2 / 8.3 / 8.4)
- `ambiguity-patterns.md` §5 + §6 (AP-2.3 anonymous; AP-6.1 conflict)
- `edge-case-catalog.md` (AP-1.3 ↔ EC-17 ground-truth; AP-5.x ↔ EC-15/16)
- `non-tipping-vocabulary.md` (AP-4.4 forbidden terms + approved phrases)
