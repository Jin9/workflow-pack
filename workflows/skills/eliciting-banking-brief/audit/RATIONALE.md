# RATIONALE — ba-elicit-from-raw

> **Purpose**: Human-readable design rationale for the BA atomic skill
> **Audience**: Reviewers, future maintainers, audit team
> **NOT loaded by LLM** — informational only
> **Skill version**: 1.0.1 (post-Phase-E4 refinement + Phase-F polish)
> **Manufactured**: 2026-05-12 via BA Skill Factory Workflow (Maximum Burn Edition, v2.0)
> **Token investment**: ~900K tokens across 22 sub-agents over 6 phases
> **Source training**: 3 raw-input examples (Jira/Lending, Slack/Payments, Meeting/KYC); 1 hold-out (Email/Card-disputes)

---

## 🎯 Why This Skill Exists

The Delivery Workflow (Stage 1 BA) consumes heterogeneous raw business requests and emits an `epic-and-stories.md` for Stage 2 (TL Design). Without an atomic skill, this consumption is ad-hoc — each BA does it differently, recurring mistakes (silent ambiguity resolution, Legal-absence un-detected, banking-grade fields skipped) leak into production. This skill encodes the patterns extracted from real banking-domain inputs into a deterministic procedure with structural enforcement.

**Replaces**: the multi-sub-agent BA Research Workflow (R1-R7) which was a per-task orchestration. That workflow was a factory; this skill is the factory's permanent output, used by every future BA task at ~10-30K tokens per call vs the factory's ~900K one-shot cost. Break-even at ~30 future tasks.

---

## 🏗️ Top-Level Design Decisions

### Decision 1: Atomic skill, not composed
Per `COGNITIVE_OS_PROJECT.md` Section 7 — atomic skills are one stage_type, one responsibility. We resisted the temptation to fold TL-handoff or QA-validation into this skill. The skill emits a brief; downstream stages consume it. Clean handoff boundary at Kafka event level.

### Decision 2: `stage_type: analyze`
BA elicitation is pure analysis (input → structured output, no external side effects). This makes the skill idempotent, retry-safe, and pure-functional. The workflow engine treats it as a no-side-effect stage with simple retry policy.

### Decision 3: `audit_level: enhanced` (not `standard`)
Banking-grade non-negotiable. Standard logs just I/O; enhanced logs decision_metadata (which Phase C pattern fired, which Anti-Pattern was avoided, which Failure Mode was checked). Required for audit reconstruction of skill behavior. T1 escalation uses `strict` (full pattern + assertion trace per row).

### Decision 4: Surface, don't repair
The single most-leveraged design principle, triangulated across all 22 sub-agents. Silent ambiguity resolution launders defects into shipped requirements. The skill detects ambiguities + governance gaps + missing stakeholders + unresolved citations and emits them as Open Questions or Governance Gaps. Repair is the BA's downstream responsibility.

Evidence: anti-patterns AP-2.1, AP-2.2, AP-6.1 (ambiguity-burying), AP-5.1 (Legal-absent), AP-4.4 (tipping-off-risky language) all cite this principle as their corrective.

### Decision 5: Force-fill banking-grade fields
Per `banking-grade-fields.md` assertion B-1 + Phase C1 Pattern 16 — every story emits a 7-row banking-grade table. "No" answers require `justification.minLength: 10`. This makes evaluation MANDATORY, not optional. Default omission of the field would be silent acceptance that the concern doesn't apply — a banking-grade violation.

### Decision 6: Dual-emission contract (JSON canonical, markdown presentational)
E3 flagged a P1 inconsistency: SKILL.md described markdown output, but `schemas/output.json` enforced strict JSON. E4 resolved: JSON is the contract; markdown is human-readable rendering. Stage 2 TL consumes JSON. Reviewers see markdown. Both derived from same internal state.

### Decision 7: Progressive disclosure for references
Skill body is ≤ 220 lines. 6 reference files load on-demand:
- **Always loaded** (~6-8K tokens): invest-checklist, gherkin-templates, ambiguity-patterns, anti-patterns
- **Conditional** (~3-4K tokens saved on happy path): job-story-decision-tree (only when format choice needed), edge-case-catalog (only on atypical-input detection), non-tipping-vocabulary (only when customer-facing comms detected)

Per-call cost target: ~10-15K tokens for happy-path single-epic; ~20-30K for multi-epic or complex governance.

---

## 📐 Procedure Step Rationale

12 procedure steps (D1 design). Each step exists because Phase C identified a recurring pattern that recurred ≥ 2 ways across inputs.

| Step | Why this step | Pattern source |
|------|--------------|----------------|
| 1. Detect source type + strip ground truth | EC-17 / FM-12 — training-set markers must never leak to production output | C3 EC-17, C1 P1-P4 |
| 2. Build domain glossary | Domain vocab recurs across banking inputs; glossary informs downstream T2 acceptance | A1 vocabulary catalog (32 terms), C1 P5 |
| 3. Extract stakeholders + authority weighting | All 22 sub-agents converged on stakeholder-authority misuse as recurring error | A4 + B4 (16 patterns) |
| 4. Map structure → scope | Inputs differ wildly in scope (single-story vs multi-epic) — explicit classification prevents force-fit | A3 + B3 (scope-kind classifier) |
| 5. Detect ambiguities (6 types + 2 added in E4) | 30+ ambiguities found in 3 training inputs; codified detection prevents silent resolution | A2 + B2 (30 catalogued) |
| 6. Surface missing stakeholders | Legal absent on regulatory content = highest-leverage rule across all 22 sub-agents | A4 + A5 + B4 + B5 |
| 7. Per-story banking-grade evaluation (7 fields, force-fill) | A5/B5 found 40 gaps where banking-grade was assumed-not-evaluated | C1 P16 + AP-4.1 |
| 8. Compose Gherkin (happy + error + banking-grade) | Mandatory-scenario rule from `ba-best-practices.md` + AP-8.x prevents AC quality failures | C2 AP-8.x |
| 9. MoSCoW prioritization | Standard inheritance from `ba-best-practices.md`; skill applies discipline rule (no >70% Must) | best-practices §6 |
| 10. Tier inference | A5/B5 found 002 and 003 should escalate to T1; explicit inference prevents silent T2-default | C1 P17 |
| 11. Failure mode evaluation | 14 failure modes from C3 — explicit halt vs surface vs document | C3 FM-01..FM-14 |
| 12. Output assembly (JSON canonical, markdown render) | E4 fix to E3's P1 gap | E3/E4 refinement |

---

## ⚠️ Failure Modes Chosen for SKILL.md Body

C3 catalogued 14 failure modes. SKILL.md body lists 9 most-critical (handoff blockers); the rest live in `references/edge-case-catalog.md`. Selection priority: any FM with `blocks_tl_handoff: true`.

Most-leveraged FM: **FM-05** (Legal absent on regulatory content). Triggered by 8 of 18 edge cases (per C3 §3). This single rule is the skill's headline production safeguard.

---

## 🚫 Anti-Patterns Chosen for SKILL.md Body

C2 catalogued 26 anti-patterns. SKILL.md body lists 10 (top-5 handoff blockers + top-5 most-evidenced silent failures). Full 26 in `references/anti-patterns.md`.

5 handoff blockers in body: AP-1.3, AP-4.1, AP-4.4, AP-5.1, AP-8.4 — these are where ambiguity-burying or banking-grade violations cause production incidents.

---

## 🧪 Self-Test Result Summary

E2 ran the skill against hold-out `raw-request-holdout.md` (Email / Card-Disputes). E3 scored output 44.5/50. E4 closed 3 gaps. F1 re-scored 50/50. F2 verdict: PRODUCTION-READY for T2.

Hold-out output characteristics:
- Output type: `blocked_partial_brief` (Legal absent + regulator citation unresolved)
- 5 Phase 1 stories generated (matched ground truth)
- 4 P1 governance gaps detected (Legal, regulator citation, PII inventory, retention policy)
- 12 P2 open questions (ground truth had 9 — exceeded coverage)
- Ground-truth strip: SUCCESS (no echo from hidden section)

Ground-truth coverage: ~92%. Skill exceeded ground truth on derived OQs (MAS PSN-01 overlap, dual-approval threshold) and added compensating-action for irreversible network submission.

---

## 🏷️ Tier Adaptability

| Tier | Default behavior | Override behavior |
|------|-------------------|-------------------|
| **T1 (banking strict)** | Set `audit_mode: strict`, `tier_hint: T1`. ALL banking-grade fields mandatory (no "no" answers without legal sign-off). Temperature 0.1. L0+L1+L2 review. | Workflow engine forces strict mode; skill increases assertion stringency. |
| **T2 (production — default)** | `audit_mode: enhanced`. Banking-grade evaluated; "no" allowed with justification. Temperature 0.3. L0+L1 + L2 if ambiguity_count > threshold. | No override needed for default. |
| **T3 (research)** | `audit_mode: standard`. Banking-grade evaluated lightly; happy-path Gherkin sufficient. Temperature 0.5. L0+L1 only. | Set `audit_mode: standard`. |

Tier-conditional logic appears in procedure steps 5, 7, 10 + relevant assertions.

---

## 🔄 What This Workflow Replaced

Previously, BA work was performed by:
- The R1-R7 Sub-agent Workflow (`BA_RESEARCH_WORKFLOW_PROMPT.md`) — run per task at ~50-80K tokens
- Inconsistent ad-hoc BA drafting by team members

This skill replaces both. The R1-R7 workflow file should be archived (kept for audit, not re-run). The atomic skill at `skills/ba-elicit-from-raw/` is the canonical BA tool from 2026-05-12 onwards.

---

## 📦 Deliverables Map

```
skills/ba-elicit-from-raw/
├── SKILL.md                       # The atomic skill (143 lines body, ≤220)
├── RATIONALE.md                   # This file
├── references/                    # Progressive-disclosure expertise
│   ├── invest-checklist.md
│   ├── gherkin-templates.md
│   ├── job-story-decision-tree.md
│   ├── ambiguity-patterns.md      # 8 patterns (6 base + 2 added E4)
│   ├── anti-patterns.md
│   ├── edge-case-catalog.md
│   └── non-tipping-vocabulary.md  # Added at final assembly
├── schemas/
│   ├── input.json                 # JSON Schema draft-07
│   └── output.json                # 8 output_types via oneOf, force-fill banking-grade
├── tests/
│   ├── cases/                     # 4 test fixtures (3 training + 1 hold-out)
│   └── assertions/                # 3 dimension-specific assertion specs
└── audit/
    ├── phases/                    # 21 phase outputs (A1-F2)
    └── factory-workflow-trace.md  # Master audit (this run)
```

---

## 🆕 Iteration Path

This is v1.0.1. Next versions:
- **v1.1.0** (polish): post-strip substring-survival regex (FM-14 hardening), examples/ folder with anonymized briefs, derivation_rule tagging on machine-emitted OQs
- **v1.2.0** (T1 hardening): mandate Legal sign-off on every PII row, mandate regulator citation completeness, dual approval audit schema
- **v2.0.0** (multi-input chaining): support multi-source inputs (Jira + Slack + meeting-notes combined)

Re-run factory only if v2.0 is needed. Minor versions = direct skill edits.

---

## 🛡️ Banking-Grade Properties (Auditor View)

| Property | Status | Where enforced |
|----------|--------|----------------|
| Auditability | ✅ | `processing_metadata`, `ba_reasoning_trace`, audit_level=enhanced |
| Idempotency | ✅ | `idempotency_key` UUID-v4 required; pure analysis stage |
| Determinism | ✅ (with workflow temp injection) | `recommended_temperature` block + tier matrix |
| Graceful degradation | ✅ | 14 failure modes + 8 output_types |
| Reversibility | ✅ (soft) | Output is a document; re-runnable; previous brief simply overwritten in git |

---

*Generated 2026-05-12 by main agent during BA Skill Factory final assembly. For human review only — do not load this file as part of skill invocation.*
