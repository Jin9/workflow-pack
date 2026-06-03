# Phase D2 — References Folder Design (`ba-elicit-from-raw`)

> **Role**: References Folder Designer, BA Skill Factory
> **Mission**: Design content outlines for the six `references/*.md` files supporting `skills/ba-elicit-from-raw/SKILL.md`. E1 authors the actual files.
> **Inputs**: phase-c1 (30 patterns), phase-c2 (26 anti-patterns), phase-c3 (18 ECs + 13 FMs), phase-d1 (SKILL.md design), `references/ba-best-practices.md`.
> **Constraints**: Each file ≤ 200 lines; progressive disclosure; cite Phase C sources.

---

## 0. Design Orientation

SKILL.md body ≤ 220 lines (D1 §2), so depth lives in six on-demand reference files. A seventh data file (`non-tipping-vocabulary.md` — designed in D1 §4) is referenced by files 2 and 5 but not redesigned here. Cross-cutting principle: **surface, don't repair** (C2 §9.5) — detectors fire, severity is assigned, the issue is recorded; the BA repairs downstream.

---

## 1. File 1 — `references/invest-checklist.md`

**Purpose**: INVEST per-letter logic + split patterns. Loaded by SKILL.md Step 7 (splitting) and Step 10 (testability check).

### 1.1 Outline

| § | Heading | Lines | Purpose |
|---|---|---|---|
| 1 | `# INVEST Checklist` | 1 | Title |
| 2 | `## Purpose & When to Apply` | 6-8 | Run on every story candidate; flag-don't-force |
| 3 | `## Per-Letter Detail` (six sub-sections I/N/V/E/S/T) | 80-90 | Pass / fail signals / fix per letter |
| 4 | `## Split Patterns Table` | 25-30 | 8 split axes for failing `S` |
| 5 | `## Anti-Pattern — Layer-Based Splitting` | 8-10 | Forbidden axis (AP-7.1) |
| 6 | `## INVEST + Banking-Grade Interaction` | 10-12 | `T` interlocks with banking-grade scenarios |
| 7 | `## Cross-References` | 4-6 | Links out |
| **Total** | | **~150-175** | |

### 1.2 Section Purpose

- **§2** — Trigger on every story candidate at Step 7, every story whose AC count > 7 (AP-7.3), every split decision. Restate ba-best-practices §1 pro tip: flag for TL, don't force-fit.
- **§3** — Each letter sub-section: Pass criteria / Fail signals (pilot example phrases) / Common failure example (banking-flavored) / Fix strategy.
- **§4** — Eight rows: Workflow steps / Business rule variations / Happy vs alternate / Data variations / CRUD / Roles / Optimize-later / Spike. Each row cites C25-C28.
- **§5** — Forbidden axis: frontend / backend / DB. Violates Independent + Valuable. Cross-link AP-7.1.
- **§6** — `T` auto-fails when banking-grade scenarios (idempotency-replay, audit-emission) are missing. Cross-link AP-8.4.

### 1.3 Key Content Highlights

- Six pass-criteria micro-templates with banking examples.
- Eight-row split-pattern table; tech-layer forbidden.
- Self-check: "Can a tester write an automated test from this scenario?"
- `T` enforcement: missing banking-grade scenarios → automatic fail.
- "Flag for TL, don't force-fit" preserved.

### 1.4 Cross-References

→ `gherkin-templates.md` §3.6 (testability + banking-grade templates). → `anti-patterns.md` §7 (AP-7.1/7.2/7.3). → `ba-best-practices.md` §1, §5, §6.

### 1.5 Sources

C9, C10, C25-C28, C29, C30; AP-7.1, AP-7.2, AP-7.3, AP-8.4; ba-best-practices §1, §5, §7.

### 1.6 Progressive Disclosure

**Always loaded** alongside SKILL.md — Steps 7 and 10 run on every input.

---

## 2. File 2 — `references/gherkin-templates.md`

**Purpose**: Gherkin format rules + banking-grade scenario library. Loaded by SKILL.md Step 8 (banking-grade auto-emission) and Step 10 (AC composition).

### 2.1 Outline

| § | Heading | Lines | Purpose |
|---|---|---|---|
| 1 | `# Gherkin Templates` | 1 | Title |
| 2 | `## Purpose & When to Apply` | 5-7 | Loaded on every AC composition |
| 3 | `## Format Rules` | 12-15 | Given / When / Then / And |
| 4 | `## Concrete-Value Enforcement` | 10-12 | Replace vague placeholders |
| 5 | `## Mandatory Scenario Types Per Story` | 8-10 | Happy + Error + Banking-grade (table) |
| 6 | `## Banking-Grade Scenario Templates` (four sub-sections) | 55-70 | Idempotency replay / Audit emission / Tipping-off-safe rejection / Authorization boundary |
| 7 | `## Anti-Patterns in Gherkin` | 15-18 | Vague Given / multi-action When / vague Then / merged happy+error |
| 8 | `## Testability Self-Check` | 6-8 | The tester-can-write-test question + remediation |
| 9 | `## Cross-References` | 4-6 | Links out |
| **Total** | | **~125-160** | |

### 2.2 Section Purpose

- **§3** — Given = state/preconditions only; When = one trigger per scenario; Then = observable outcome; And chains Given or Then only.
- **§4** — Replace `valid amount` → `amount = 50000`; resolve `EOW` via C4; resolve `N=3` from anonymous via C16+C24; replace `$Xk` with TBD + named owner (AP-2.3).
- **§5** — Three-row table: Happy / Error / Banking-grade (auto-emitted per C29).
- **§6** — Four full Gherkin templates with fill-in slots and one banking example each. Tipping-off template includes forbidden-terms inset (sanctions/AML/flagged/suspicious/regulated/SAR/PEP/adverse media/EDD) + pointer to `non-tipping-vocabulary.md`. Audit-emission required payload `{event, actor, ts, before, after, reason, idem_key}` (C18 field 2). AuthZ template hooks role-matrix (C18 field 5).
- **§7** — Four sub-bullets: AP-8.1 / AP-8.2 / AP-8.3 / AP-7.2; detection + rewrite each.
- **§8** — Self-check question; if NO → rewrite or convert to Open Question (AP-4.2).

### 2.3 Key Content Highlights

- Four full banking-grade Gherkin templates (idempotency, audit, tipping-off, authZ).
- Concrete-value enforcement with pilot-corpus examples.
- Forbidden-terms inset on tipping-off template.
- Audit-emission required payload schema.
- AuthZ role-matrix hook.

### 2.4 Cross-References

→ `invest-checklist.md` §3.6 (`T`). → `anti-patterns.md` §8 (AP-8.1..AP-8.4). → `ambiguity-patterns.md` §3 (modal/vague rewrites). → `non-tipping-vocabulary.md` (§6.3). → `ba-best-practices.md` §2.

### 2.5 Sources

C18, C20, C21, C29, C30; AP-4.2, AP-4.3, AP-4.4, AP-7.2, AP-8.1, AP-8.2, AP-8.3, AP-8.4; ba-best-practices §2.

### 2.6 Progressive Disclosure

**Always loaded** alongside SKILL.md — Steps 8 and 10 run on every story.

---

## 3. File 3 — `references/job-story-decision-tree.md`

**Purpose**: Decide Job Story vs Classic User Story per candidate. Loaded by SKILL.md Step 7 when format choice ambiguous.

### 3.1 Outline

| § | Heading | Lines | Purpose |
|---|---|---|---|
| 1 | `# Job Story vs Classic User Story Decision Tree` | 1 | Title |
| 2 | `## Purpose & Default` | 5-7 | Default = Job Story unless role-dominant |
| 3 | `## Decision Tree` | 28-36 | 10-15 binary nodes |
| 4 | `## Job Story Format + Examples` | 22-28 | Template + 3 banking examples |
| 5 | `## Classic User Story Format + Examples` | 18-24 | Template + 2 banking examples |
| 6 | `## Quality Criteria Per Format` | 18-24 | Per-format checklist |
| 7 | `## Default Rule & Override Conditions` | 8-10 | "Job Story unless role-dominant" + when to override |
| 8 | `## Mixed-Format Anti-Pattern` | 5-7 | Don't switch mid-epic without justification |
| 9 | `## Cross-References` | 4-6 | Links out |
| **Total** | | **~110-145** | |

### 3.2 Section Purpose

- **§3 Decision Tree** — 10-15 binary nodes. Sample branches: (1) Permission/role primary differentiator? → Classic. (2) Multiple roles could use same capability? → Job. (3) Trigger drives behavior more than role? → Job. (4) Single dominant persona, no situational variation? → Classic. (5) Banking workflow with trigger conditions (rate-limit, hold-type, retry-count)? → Job. (6) Admin-vs-user permission split? → Classic. (7) Compliance officer reviewing case? → Classic. (8) Customer experiencing rejection? → Job. (9) Tie? → Default Job. Output = format + confidence.
- **§4** — Template: `When [situation/trigger], I want to [capability], So I can [outcome/benefit].` Banking examples: re-upload after verification fail (001), wire on additional review (002), EDD intake (003).
- **§5** — Template: `As a [role], I want [capability], so that [benefit].` Examples: compliance officer reviewing high-risk case; senior approver dual-signoff.
- **§6** — Job: trigger concrete (not "when needed"), capability bounded, outcome observable. Classic: role named with authority scope, capability permission-scoped, benefit role-specific.
- **§7** — Override only when role is clearly primary; document override in BA Reasoning Trace.

### 3.3 Key Content Highlights

- 10-15-node decision tree producing format + confidence.
- Five banking-flavored format examples (3 Job + 2 Classic).
- Per-format quality checklists.
- Default-Job rule preserved; override path documented.
- Mixed-format anti-pattern called out.

### 3.4 Cross-References

→ `invest-checklist.md` §3 (V + N). → `ba-best-practices.md` §3. → `epic-and-stories.template.md` (both formats).

### 3.5 Sources

ba-best-practices §3; C9 (story boundaries informs role-dominance); A4 §1, §2 (stakeholder role types).

### 3.6 Progressive Disclosure

**Conditional load** — only when Step 7 needs format choice: (a) multiple candidate roles, (b) concrete weighty trigger, (c) no author format signal. Skip when format is obvious (e.g., admin-vs-user → Classic).

---

## 4. File 4 — `references/ambiguity-patterns.md`

**Purpose**: 6 ambiguity types + P1/P2/P3 severity engine + conflict-resolution rules. Loaded by SKILL.md Step 9 (ambiguity detection).

### 4.1 Outline

| § | Heading | Lines | Purpose |
|---|---|---|---|
| 1 | `# Ambiguity Patterns` | 1 | Title |
| 2 | `## Purpose & When to Apply` | 5-7 | Loaded on every input at Step 9 |
| 3 | `## 6 Ambiguity Types` (six sub-sections) | 70-82 | Lexical / Syntactic / Pragmatic / Pronominal / Quantifier / Modal |
| 4 | `## Severity Assignment Rules (P1/P2/P3)` | 26-32 | Severity table with context-lift rules |
| 5 | `## Anonymous Comment Downgrade Rule` | 8-10 | Anonymous + numeric → P2 floor |
| 6 | `## Conflicting Commenter Resolution` | 14-18 | Latest-claim wins + ledger preserved |
| 7 | `## Mandatory-Vagueness Exception` | 6-8 | Regulator-required vague language |
| 8 | `## Placeholder Token Class` | 6-8 | `(?)`, `TBD`, `$Xk` |
| 9 | `## Cross-References` | 4-6 | Links out |
| **Total** | | **~140-175** | |

### 4.2 Section Purpose

- **§3 Six Types** — Each sub-section: definition / detection signals (regex / patterns / pilot example phrases) / default severity / escalation conditions / one rewrite example. From C22 + A2 §5.
- **§4 Severity Rules** — **P1 (blocker)**: Legal absent on regulatory; regulator named without citation; tipping-off violation; missing PII inventory on T1; missing compensating action on funds movement; calibration debt on risk routing. **P2 (must-address)**: self-contradicting AC; anonymous policy parameter; modal hedge in commitment; placeholder token unattached to regulator; AC vs comment-thread conflict. **P3 (assumption-to-document)**: pronoun across sentence boundary (non-AC); quantifier without quantity (non-cluster); urgent-label-without-SLA. **Context lift**: relative-date + regulator citation = P2 not P3 (B5 C6). **Cluster penalty**: > 5 quantifier-without-quantity → completeness penalty.
- **§5 Anonymous Downgrade** — Anonymous + numeric policy parameter = automatic P2 (promoted from P3 per C16 + B2 C1 + B5 C1). Refuse to bind; emit `proposed_value` + `requires_named_owner: true`.
- **§6 Conflicting Commenters** — Per-entity decision ledger; same field + ≥2 speakers + incompatible content. Rules: (a) compliance rule-mode beats PM AC (C15 + B3 C6); (b) when AC and compliance rule-mode comment conflict, comment wins — original AC → "Assumption Overridden" with both `source_quote`s; (c) latest authoritative quote = working answer; (d) never drop earlier conflicting one.
- **§7 Mandatory-Vagueness Exception** — Regulator-required vague language is correct (e.g., tipping-off-safe rejection text). Do NOT flag as P2 lexical. Disambiguate via authority-mode: Compliance rule mode + customer-facing comm scope = mandatory-vagueness.
- **§8 Placeholder Tokens** — `(?)`, `TBD`, `???`, `$Xk`, `N attempts`, single-capital-letter numeric slot. Default P2; P1 when attached to regulator or PII-vendor parameter.

### 4.3 Key Content Highlights

- Six types with detection signals + default severity + rewrite example.
- Three-tier severity matrix with context-lift rules.
- Anonymous downgrade rule: numeric/policy → P2 floor.
- Conflict resolution: latest-claim wins, ledger preserved, compliance rule-mode override.
- Mandatory-vagueness exception (regulator-required vague text is correct).
- Placeholder token class with P1 escalation paths.

### 4.4 Cross-References

→ `anti-patterns.md` §6 (AP-6.1/6.2/6.3). → `gherkin-templates.md` §4. → `edge-case-catalog.md` (EC-02, EC-14, EC-15). → `non-tipping-vocabulary.md`.

### 4.5 Sources

C22, C23, C24; AP-6.1, AP-6.2, AP-6.3; A2 §5 (30+ catalog); B2 HC1/HC2/HC5/HC6; B5 C1/C6.

### 4.6 Progressive Disclosure

**Always loaded** alongside SKILL.md — Step 9 runs on every input.

---

## 5. File 5 — `references/anti-patterns.md`

**Purpose**: 26-entry anti-pattern catalog from Phase C2. Loaded by SKILL.md Step 9 (conflict arbitration) and Step 12 (final guardrails).

### 5.1 Outline

| § | Heading | Lines | Purpose |
|---|---|---|---|
| 1 | `# Anti-Patterns Catalog` | 1 | Title |
| 2 | `## Purpose: Surface, Don't Repair` | 7-9 | Cross-cutting principle; skill-MUST-NOT |
| 3 | `## 1. Wrong Inferences` | 16-20 | AP-1.1, 1.2, 1.3 |
| 4 | `## 2. Common Skill Failures` | 16-20 | AP-2.1, 2.2, 2.3 |
| 5 | `## 3. Forbidden Simplifications` | 16-20 | AP-3.1, 3.2, 3.3 |
| 6 | `## 4. Banking-Grade Violations` | 20-24 | AP-4.1..4.4 |
| 7 | `## 5. Stakeholder Neglect` | 16-20 | AP-5.1, 5.2, 5.3 |
| 8 | `## 6. Ambiguity-Burying` | 16-20 | AP-6.1, 6.2, 6.3 |
| 9 | `## 7. Story Granularity` | 16-20 | AP-7.1, 7.2, 7.3 |
| 10 | `## 8. AC Quality` | 20-24 | AP-8.1..8.4 |
| 11 | `## Top 5 Handoff Blockers (Quick Reference)` | 8-10 | AP-1.3, 4.1, 4.4, 5.1, 8.4 |
| 12 | `## Cross-Cutting Enforcement Notes` | 8-10 | Composition + severity escalation |
| 13 | `## Cross-References` | 4-6 | Links out |
| **Total** | | **~180-220** (compress micro-template if overflow) | |

### 5.2 Section Purpose

- **§2** — Anti-patterns = "things the skill MUST NOT do". Principle: **Surface, don't repair**. When fired, emit Open Question + risk flag; do NOT silently rewrite.
- **§§3-10 Eight Buckets** — Each entry compressed 4-5-line micro-template: Name (`AP-X.Y — <label>`) / Detection signal (1 line) / Correct alternative (1-2 lines) / Severity if fired (P1 / P2 / P3 / handoff-block).
- **§11 Top 5 Handoff Blockers** — Quick reference: AP-1.3 (tier from label) / AP-4.1 (PII none unjustified) / AP-4.4 (tipping-off unflagged) / AP-5.1 (Legal absence) / AP-8.4 (missing banking-grade scenarios). One line each.
- **§12 Enforcement Notes** — Five meta-rules from C2 §9: (1) anti-patterns compose — never deduplicate; (2) severity escalates by context (P3→P2 on regulatory; P2→P1 on rule-mode authority); (3) handoff blockers override high quality scores; (4) every guard needs a positive-test disable path (e.g., `pii.status: not_applicable, justification`); (5) surface-don't-repair as unifying rule.

### 5.3 Key Content Highlights

- All 26 anti-patterns across 8 buckets (full Phase C2 coverage).
- Compressed micro-template keeps file ≤ 200 lines.
- Top 5 handoff blockers promoted to quick-reference block.
- Five cross-cutting enforcement meta-rules.
- "Surface, don't repair" as unifying principle.

### 5.4 Cross-References

→ `invest-checklist.md` §5 (AP-7.1). → `gherkin-templates.md` §7 (AP-8.1..8.4). → `ambiguity-patterns.md` §5+§6 (AP-2.3, AP-6.1). → `edge-case-catalog.md` (AP-1.3↔EC-17, AP-5↔EC-15..16). → `non-tipping-vocabulary.md` (AP-4.4).

### 5.5 Sources

Phase C2 §§1-8 (all 26 APs); C2 §9 (enforcement notes); C2 §10 (severity index); D1 §6 (top-10 selection — full 26 live here).

### 5.6 Progressive Disclosure

**Always loaded** alongside SKILL.md — Steps 9 and 12 consult this file on every run. SKILL.md body's top-10 preview does not replace the full catalog.

---

## 6. File 6 — `references/edge-case-catalog.md`

**Purpose**: 18 edge cases (C3 Part 1) + 13 failure modes (C3 Part 2). Loaded by SKILL.md Steps 1, 4, 5, and 12 conditionally.

### 6.1 Outline

| § | Heading | Lines | Purpose |
|---|---|---|---|
| 1 | `# Edge Case + Failure Mode Catalog` | 1 | Title |
| 2 | `## Purpose & Loading Conditions` | 5-7 | When the skill consults this file |
| 3 | `## Edge Case Groups` (six sub-groups) | 100-120 | 18 ECs organized by 6 themes |
| 4 | `## Failure Mode Table` | 22-28 | 13 FMs in compressed table |
| 5 | `## EC × FM Decision Matrix` | 18-24 | Which FMs each EC triggers |
| 6 | `## Cross-References` | 4-6 | Links out |
| **Total** | | **~150-185** | |

### 6.2 Section Purpose

- **§2** — Loaded only when: (a) source confidence < 0.5 at Step 1; (b) PII detected at Step 4; (c) stakeholder absence/leave at Step 5; (d) ground-truth block detected (loads EC-17/FM-12 section); (e) Step 12 in `audit` mode. Happy-path runs skip.
- **§3 Edge Case Groups** — Each EC: 3-4-line micro-template (Name / Detection / Behavior / Output adjustment). Six groups:
  - **§3.1 Input Quality** — EC-01 Empty/minimal, EC-04 Very long, EC-05 Very short, EC-07 Broken structure / paraphrase, EC-10 Multi-epic.
  - **§3.2 Input Structure** — EC-11 Sub-ticket chain, EC-12 Slack-only signal, EC-13 Email inversion.
  - **§3.3 Stakeholder Issues** — EC-02 Conflicting commenters, EC-14 Anonymous, EC-15 Note-taker paraphrase, EC-16 Stakeholder on leave/handoff.
  - **§3.4 Hidden Ground Truth** — EC-17 standalone (unique safety guard; fail-closed via FM-12).
  - **§3.5 Scope & Language** — EC-03 Multi-language, EC-09 Meta-request (returns `meta_response`), EC-18 Regulator named without citation.
  - **§3.6 PII & Sensitive Data** — EC-06 Unattached cited docs, EC-08 PII in body (never echo).
- **§4 Failure Mode Table** — 13 FMs compressed: Failure mode / Detection / Severity / Skill output / Escalation. From C3 Part 2.
- **§5 EC × FM Decision Matrix** — C3 Part 3 matrix in compact form (`Y` / `Y?` cells) with reading notes: EC-12 multi-FM generator; EC-17 unique-triggers-FM-12; FM-05 fired by 8 ECs.

### 6.3 Key Content Highlights

- 18 ECs in 6 groups (full C3 Part 1 coverage).
- 13 FMs in compressed table (full C3 Part 2).
- EC × FM decision matrix preserved compact.
- EC-17 / FM-12 ground-truth strip standalone for safety prominence.
- Reading-the-matrix interpretation notes.

### 6.4 Cross-References

→ `anti-patterns.md` (AP-1.3↔EC-17, AP-2.3↔EC-14, AP-3.2↔EC-15, AP-3.3↔EC-10, AP-5.1↔FM-05, AP-5.3↔EC-15). → `ambiguity-patterns.md` §5+§6 (EC-02, EC-14). → SKILL.md Failure Modes table (9-row subset of the 13 here).

### 6.5 Sources

C3 Part 1 (EC-01..EC-18); C3 Part 2 (FM-01..FM-13); C3 Part 3 (matrix); D1 §5 (body FM subset).

### 6.6 Progressive Disclosure

**Conditional load** — only on the five triggers in §2 above. Standard happy-path runs skip this file.

---

## 7. Cross-File Dependency Map

The six files form a small DAG. SKILL.md is the root; arrows show "consults / cross-links to":

```
SKILL.md
  ├── invest-checklist.md ──┬──> gherkin-templates.md (T ↔ banking-grade)
  │                         └──> anti-patterns.md (§5 → AP-7.1)
  ├── gherkin-templates.md ─┬──> anti-patterns.md (§7 → AP-8.1..8.4)
  │                         ├──> ambiguity-patterns.md (§4 rewrites)
  │                         └──> non-tipping-vocabulary.md (§6.3)
  ├── job-story-decision-tree.md ──> invest-checklist.md (V + N)
  ├── ambiguity-patterns.md ┬──> anti-patterns.md (§6 → AP-6.1..6.3)
  │                         ├──> edge-case-catalog.md (EC-02, EC-14, EC-15)
  │                         └──> non-tipping-vocabulary.md (mandatory-vagueness)
  ├── anti-patterns.md ─────┬──> invest-checklist.md (AP-7 bucket)
  │                         ├──> gherkin-templates.md (AP-8 bucket)
  │                         ├──> ambiguity-patterns.md (AP-2, AP-6)
  │                         ├──> edge-case-catalog.md (handoff blockers)
  │                         └──> non-tipping-vocabulary.md (AP-4.4)
  └── edge-case-catalog.md ─┬──> anti-patterns.md (handoff-blocker links)
                            └──> ambiguity-patterns.md (EC-02, EC-14 rules)
```

**Hub files**: `anti-patterns.md` and `gherkin-templates.md` are the highest-fanout nodes (each ≥ 3 sibling references plus SKILL.md). **No circular dependencies** — cross-references are bidirectional only at the meta level via "Cross-References" sections, never via mandatory-loading semantics.

---

## 8. Progressive Disclosure Strategy

| File | Load mode | Trigger | Token cost (est.) |
|---|---|---|---|
| `invest-checklist.md` | **Always loaded** | Steps 7 + 10 — every input | ~1.4-1.8k |
| `gherkin-templates.md` | **Always loaded** | Steps 8 + 10 — every story | ~1.5-2.0k |
| `ambiguity-patterns.md` | **Always loaded** | Step 9 — every input | ~1.5-1.9k |
| `anti-patterns.md` | **Always loaded** | Steps 9 + 12 — every input | ~1.8-2.2k |
| `job-story-decision-tree.md` | **Conditional** | Step 7 when format ambiguous (~40% inputs) | ~1.0-1.3k |
| `edge-case-catalog.md` | **Conditional** | Source confidence < 0.5, PII present, stakeholder leave, ground-truth, audit mode (~25% inputs) | ~1.6-2.0k |
| `non-tipping-vocabulary.md` | **Conditional** | Tipping-off term detected (~30% of customer-comm stories) | ~0.6-0.9k |

**Always-loaded core** = 4 files (~6.2-7.9k tokens) — irreducible (every run needs INVEST + Gherkin + ambiguity + anti-patterns).

**Conditional savings** = up to ~3.2-4.2k tokens on happy-path runs. Matters for D1 §1.1 P95 < 30s/stage SLA.

**Audit mode**: When the skill runs in `audit` mode (training harness), all conditional files load unconditionally to maximize EC × FM matrix coverage.

---

## 9. Validation Checklist for E1

- [ ] Six files exist at `references/*.md` paths declared in SKILL.md.
- [ ] Each file ≤ 200 lines.
- [ ] Outline matches §§1-6 of this design (headings, groups, triggers).
- [ ] Cross-references resolve (every link points to existing file + section).
- [ ] `non-tipping-vocabulary.md` exists (per D1 §4); referenced by gherkin-templates §6.3 + anti-patterns AP-4.4.
- [ ] Phase C source citations preserved (every section cites ≥ 1 C-pattern / AP / EC / FM).
- [ ] No file inlines another file's content — cross-references only.
- [ ] Anti-patterns micro-template (4-5 lines/entry) holds across all 26.
- [ ] Edge-case micro-template (3-4 lines/entry) holds across all 18.
- [ ] EC × FM decision matrix preserved in §5 of edge-case-catalog.
- [ ] "Surface, don't repair" stated explicitly in anti-patterns §2.
- [ ] Top 5 handoff blockers promoted to quick-reference in anti-patterns §11.

---

*End of Phase D2 References Folder Design. E1 writes the six reference files following this design and the validation checklist.*
