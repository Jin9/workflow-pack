# Markdown Rendering Spec — eliciting-banking-brief v1.2.1

Authoritative reference for the deterministic Markdown directory tree emitted alongside the canonical `output.json`. Implemented by `scripts/render_markdown_tree.py`. Loaded at Step 12 only.

The JSON contract (`schemas/output.json`) is load-bearing; the Markdown tree is mechanically derived and carries no contractual weight independent of the JSON. On any conflict, the JSON wins.

---

## 1. Directory shape

### 1.1 Success shapes (`brief`, `blocked_partial_brief`)

For `output_type ∈ {brief, blocked_partial_brief}`, the renderer writes to a directory named `output-{idem8}/` where `{idem8}` is the first 8 characters of `frontmatter.idempotency_key` (the UUID v4). The tree is identical shape for `single-epic`, `multi-story`, `single-story`, `story_within_epic`, and `multi-epic` — only the count of children under `epics/` varies.

```
output-{idem8}/
├── README.md                          ← Status banner, blocker count, navigation index
├── output.json                        ← Canonical JSON (verbatim, schema-validated)
├── 00-BRIEF.md                        ← Initiative-level synthesis (or epic-level for single-epic)
├── 01-governance-gaps.md              ← All P1/P2 governance gaps; drives blocks_tl_handoff
├── 02-open-questions.md               ← All OQs grouped by severity, linked to story IDs
├── 03-assumptions.md                  ← All assumptions_made with why_made
├── 04-glossary.md                     ← Domain terms (canonical_form, definition, pii_sensitivity, regulatory_tie)
├── 05-pii-inventory.md                ← Per-field treatment table
├── 06-regulatory-dependencies.md      ← Regulators, codes, citation status, promisors
├── 07-processing-metadata.md          ← tier_decisions, chunking, parsing_mode, ground_truth_stripped, language_inventory, hidden_requirements_sweep summary
├── 08-audit-trace.md                  ← BA reasoning trace + ba_compliance_checklist
├── 09-hidden-requirements.md          ← CONDITIONAL: emitted only when hidden_requirements_sweep has ≥1 finding. Lists OQs and assumptions tagged with provenance=hidden_frame_sweep, grouped by frame.
└── epics/
    └── EPIC-{NAME}/                   ← One directory per epic, named after epic.id
        ├── EPIC.md                    ← problem / why_now / success_criteria / scope / stakeholders / tier_signals
        └── stories/
            ├── STORY-1-{slug}.md      ← Story whose id ends in `-1`
            ├── STORY-2-{slug}.md
            └── STORY-N-{slug}.md
```

`blocked_partial_brief` follows this same shape — stories still exist, just with `blocks_tl_handoff: true` flagged in `README.md` and `00-BRIEF.md`.

### 1.2 Failure shapes

For `output_type ∈ {needs_clarification, preprocessing_failure, pii_echo_blocked, schema_validation_failure, meta_response}`, no stories exist, so the tree is reduced to three files at root:

```
output-{idem8}/
├── README.md                          ← Prominent FAILURE banner with mode + reason
├── output.json                        ← Canonical JSON with failure_state
└── FAILURE.md                         ← failure_state translated to human-readable, with recommended next action
```

No `epics/` subtree, no cross-cutting `0N-*.md` files. The failure cause and recommended next action live in `FAILURE.md`; `README.md` carries only the high-level banner and pointer.

---

## 2. Slug generation rules

Story filenames are `STORY-{N}-{slug}.md` where:

- `{N}` is the trailing integer extracted from `story.id` via regex `-(\d+)$`. Example: `EPIC-AUTH-1` → `1`.
- `{slug}` is derived from `story.title` by the algorithm below.

**Algorithm:**

1. Lowercase the title.
2. Replace every non-alphanumeric character with a hyphen.
3. Collapse runs of hyphens to a single hyphen.
4. Tokenize on hyphens.
5. Drop tokens matching this fixed stopword set: `a, an, the, and, or, with, for, of, to, in, on, at, by, from`.
6. Rejoin remaining tokens with a single hyphen.
7. Truncate to 60 characters maximum.
8. Strip any trailing hyphen left by truncation.

**Test vector:** "Register customer account with unique email and hashed password" → `register-customer-account-unique-email-hashed-password`.

**Collision handling:** if two stories in the same epic produce the same slug, append `-{N}` (the story-id integer) before truncation — guarantees uniqueness because `story.id` is unique within the brief. The renderer detects collisions before writing.

---

## 3. Per-file frontmatter and content spec

All Markdown files carry YAML frontmatter sufficient for a downstream Stage 2 agent to route without parsing the JSON.

### 3.1 `README.md` — the entry point

**Frontmatter:**

```yaml
---
artifact_type: ba-brief-index
brief_id: {frontmatter.id from JSON}
idempotency_key: {full UUID v4}
workload_tier: T1|T2|T3
output_type: brief|blocked_partial_brief|needs_clarification|...
scope_kind: single-epic|multi-epic|...
status: ready-for-tl|blocked|draft
blocks_tl_handoff: true|false
created_at: {ISO-8601}
created_by: eliciting-banking-brief-v1.2.1
source_type: jira|slack|email|meeting-notes|doc|mixed
downstream_consumer:
  stage: 2-tl-design
  role: tech-lead
---
```

**Content sections (in this order):**

1. `# BA Brief — {initiative.title OR epic.title}`
2. **Status banner** — single line at the top calling out one of:
   - `Ready for TL handoff`
   - `Blocked for TL handoff — N P1 governance gap(s) unresolved`
   - `Draft — N P2 open question(s) require BA decision`
   - `Failed — see FAILURE.md`
3. **At a glance** — small table: tier, scope_kind, epic count, story count, P1/P2/P3 OQ counts, governance gap count, PII field count.
4. **Navigation** — bulleted index of every file in the tree with one-line description. Each item is a relative Markdown link.
5. **If `blocks_tl_handoff: true`** — a "Why this is blocked" section listing each P1 governance gap with a link to `01-governance-gaps.md#{anchor}`. **DoR-failure bullet rule (v1.2.1+)**: if `blocks_tl_handoff: true` AND `ba_compliance_checklist.definition_of_ready_met: false`, emit a DoR-failure bullet as the FIRST item in the why-blocked list, preceding governance-gap bullets. Bullet format: `- **definition_of_ready_met: false** — see [08-audit-trace.md](08-audit-trace.md#ba-compliance-checklist) for the per-checklist breakdown`. If DoR is `true`, render no extra bullet (v1.2.0 behavior preserved).
6. **If `blocks_tl_handoff: true`** — a "Minimum unblock set" section (v1.2.1+) listing the smallest set of OQs and governance gaps that, when resolved together, flip `blocks_tl_handoff` from true to false. Section placement: between the why-blocked section (item 5) and the provenance section (item 7). Omitted entirely when `blocks_tl_handoff: false` (no empty heading). **Computation rule (verbatim — auditable from this spec):**

   ```
   unblock_set = (governance_gaps where blocks_tl_handoff == true)
               ∪ (open_questions where severity == "P1")
               ∪ (governance_gaps of type ∈ {
                    "pii_inventory_missing",
                    "regulatory_citation_unresolved",
                    "retention_policy_unstated"
                  } — included regardless of their own blocks_tl_handoff value,
                  because they are structural blockers)
   ```

   Each item renders as one line: ID, one-sentence summary, suggested resolver, relative link to canonical file (gov gaps → `01-governance-gaps.md#{anchor}`; OQs → `02-open-questions.md#{oq-id-lowercased}`). Items are grouped by resolver in this fixed order (a single item is assigned to the FIRST matching group): `PM`, `Legal`, `DPO`, `Finance`, `Compliance`, `Ops`, `InfoSec`, `other`. Within a resolver group, gov gaps appear before OQs; otherwise insertion order (JSON array order) is preserved for determinism.
7. **Provenance** — `source_type`, `idempotency_key` (full), `created_at`, skill version.

### 3.2 `00-BRIEF.md` — executive synthesis

**Frontmatter:** `artifact_type: ba-brief-summary` plus the same routing fields as `README.md` (`brief_id`, `idempotency_key`, `workload_tier`, `output_type`, `scope_kind`, `status`, `blocks_tl_handoff`, `created_at`, `created_by`, `source_type`, `downstream_consumer`).

**Content:**

- For multi-epic: render `initiative.title`, `initiative.summary`, the per-epic tier map (table with `epic_id`, `tier`, `justification`), and a one-paragraph "what's in scope across all epics" synthesis.
- For single-epic / single-story / multi-story / story_within_epic: render the epic-level header (title, problem_statement, why_now, hypothesis if present, success_criteria table) — the executive summary before drilling into the epic file.
- Always include: `processing_metadata.tier_decisions` table at the bottom, with the rationale for the inferred tier per epic.

### 3.3 `epics/EPIC-{NAME}/EPIC.md` — per-epic header

**Frontmatter:**

```yaml
---
artifact_type: ba-epic
epic_id: EPIC-AUTH
brief_id: EPIC-SHOPPILOT-MVP
title: "Authentication and Account"
workload_tier: T2
inferred_tier: T2
manual_tier: T2
inferred_higher_than_manual: false
legal_status: present|scheduled|mentioned_only|absent
story_count: 2
story_ids: [EPIC-AUTH-1, EPIC-AUTH-2]
blocks_tl_handoff: false
downstream_consumer:
  stage: 2-tl-design
  role: tech-lead
---
```

**Content sections:**

1. `# Epic: {title}`
2. One-line summary banner: `**Tier**: {tier} · **Legal status**: {legal_status} · **Stories**: {n}`
3. `## Problem Statement` — from `epic.problem_statement`
4. `## Why Now` — from `epic.why_now`
5. `## Hypothesis` — from `epic.hypothesis` if present (omit section if absent)
6. `## Success Criteria` — table from `epic.success_criteria[]`
7. `## Scope` — three subsections: `### In`, `### Out (explicit)`, `### Out (deferred)` from `epic.scope.in[]`, `epic.scope.out_explicit[]`, `epic.scope.out_deferred[]`
8. `## Stakeholders` — table from `epic.stakeholders[]` with absent rows visually bolded (per existing monolithic-MD pattern)
9. `## Tier Signals` — bulleted list of `epic.tier_signals[]`, each rendered as `- **{signal}** (weight: {weight}) — "{evidence_quote}"`

### 3.4 `epics/EPIC-{NAME}/stories/STORY-{N}-{slug}.md` — per-story

**Frontmatter:**

```yaml
---
artifact_type: ba-story
story_id: EPIC-AUTH-1
epic_id: EPIC-AUTH
brief_id: EPIC-SHOPPILOT-MVP
title: "Register customer account with unique email and hashed password"
format: classic_user_story|job_story
priority: Must|Should|Could|Won't
story_points: 3|TBD_by_TL
complexity: trivial|low|medium|high|unknown
workload_tier: T2                    # inherited from epic
depends_on: []                        # array of story IDs
blocks: [EPIC-AUTH-2, EPIC-CART-1]
banking_grade_applies:               # which rows have status=applies (helps TL filter)
  - pii_fields
  - audit_events
  - authn_authz
related_open_questions: [OQ-10]      # any OQ IDs this story is tied to
dor_ready: true|false
downstream_consumer:
  stage: 2-tl-design
  role: tech-lead
---
```

**Content sections:**

1. `# Story {story_id}: {title}`
2. One-line meta banner: `**Format**: {format} · **Priority**: {priority} · **Sizing**: {story_points} SP ({complexity})`
3. The user-story or job-story card:
   - Classic: `As a {role}, I want {capability} so that {benefit}.`
   - Job: `When {trigger}, I want to {motivation} so I can {outcome}.`
4. `## Context` — from `story.context`
5. `## Acceptance Criteria` — one fenced ` ```gherkin ` block per scenario in `acceptance_criteria[]`, with the `[scenario_type]` tag in the comment header:

   ```
   # [scenario_type] scenario_name
   Given …
   When …
   Then …
   ```
6. `## Banking-Grade Concerns` — 7-row table (Concern / Status / Justification). All 7 rows MUST be emitted regardless of status (force-fill per FM-11).
7. `## Dependencies` — `**Depends on**: {ids or —} · **Blocks**: {ids or —}`
8. `## Definition of Ready` — checklist from `story.dor_checklist` (8 boolean keys rendered as checkbox lines; `true` → `[x]`, `false` → `[ ]`)

### 3.5 Cross-cutting files (`01-` through `09-`)

Same content as the corresponding sections in a monolithic BA brief, lifted into separate files. Files `01-` through `08-` use a **minimal** frontmatter; `09-hidden-requirements.md` carries **full routing** frontmatter (same as `README.md` / `00-BRIEF.md`) because Stage 2 routes off it directly.

**Minimal frontmatter (files `01-` through `08-`):**

```yaml
---
artifact_type: ba-{governance|oq|assumptions|glossary|pii|reg-deps|metadata|audit-trace}
brief_id: {id}
idempotency_key: {uuid}
---
```

**Full-routing frontmatter (file `09-hidden-requirements.md`):**

```yaml
---
artifact_type: ba-hidden-requirements
brief_id: {id}
idempotency_key: {uuid}
workload_tier: T1|T2|T3
output_type: brief|blocked_partial_brief|...
scope_kind: single-epic|multi-epic|...
status: ready-for-tl|blocked|draft
blocks_tl_handoff: true|false
coverage_score: complete|partial|skipped
created_at: {ISO-8601}
created_by: eliciting-banking-brief-v1.2.1
source_type: ...
downstream_consumer:
  stage: 2-tl-design
  role: tech-lead
---
```

Specifically:

| File | `artifact_type` | Source JSON | Content |
|---|---|---|---|
| `01-governance-gaps.md` | `ba-governance` | `governance_gaps[]` | All gaps grouped by severity (P1, then P2, then P3). Each entry: type, severity, reason, resolver, link back to affected story files. |
| `02-open-questions.md` | `ba-oq` | `open_questions[]` | All OQs grouped by severity (P1, then P2, then P3). Each entry: question, severity, blocking flag, suggested resolver, link to story files it concerns. **At-a-glance header (v1.2.1+, see §3.5.1).** |
| `03-assumptions.md` | `ba-assumptions` | `assumptions_made[]` | All assumptions with `why_made`, source, and confidence level. |
| `04-glossary.md` | `ba-glossary` | `glossary[]` | Domain term table: `canonical_form`, `surface_form`, `definition`, `pii_sensitivity`, `regulatory_tie`. |
| `05-pii-inventory.md` | `ba-pii` | `pii_inventory[]` | Per-field treatment table. |
| `06-regulatory-dependencies.md` | `ba-reg-deps` | `regulatory_dependencies[]` | Regulator + code + revision + citation_status + promisor + due_date. |
| `07-processing-metadata.md` | `ba-metadata` | `processing_metadata` | `tier_decisions`, `chunking`, `parsing_mode`, `ground_truth_stripped`, `language_inventory`, `tipping_off_scan` summary. |
| `08-audit-trace.md` | `ba-audit-trace` | `ba_reasoning_trace`, `ba_compliance_checklist` | Reasoning trace narrative + 10-key compliance checklist as ✅/❌ list. |
| `09-hidden-requirements.md` | `ba-hidden-requirements` | `open_questions[]` + `assumptions_made[]` filtered by `provenance == hidden_frame_sweep`; `processing_metadata.hidden_requirements_sweep` summary | **Conditional** — emitted only when `hidden_requirements_sweep.total_findings > 0`. Groups by `frame` (1–10) with frame name as section header. Each finding shows question/assumption, severity, frame, default_revisit_trigger (assumptions only), related story IDs (relative-link). Trailing section "Frame coverage" renders the `frames_applied` / `frames_skipped` summary. |

For `01-governance-gaps.md` and `02-open-questions.md`: every entry MUST cross-link back to the story file(s) it concerns, using relative paths (e.g. `[STORY-1](epics/EPIC-AUTH/stories/STORY-1-register-customer-account.md)`). This is how Stage 2 navigates from a gap to the affected stories.

### 3.5.1 `02-open-questions.md` executive summary header (v1.2.1+)

After the YAML frontmatter, the file's body begins with the `# Open Questions` H1, immediately followed by a `## At a glance` subsection. Choice rationale: H1 stays the document title; the summary is a labeled subsection (standard document structure of title → summary → content).

The summary contains four lines, in this exact order:

1. **Counts line** — `P1: {n} · P2: {n} · P3: {n} · Total: {N}` where N is the sum of P1+P2+P3 counts in `open_questions[]`. Use `·` (middle dot, U+00B7) as separator.
2. **By theme line** — `**By theme:** Frame {a} ({frame_name}): {count} · Frame {b} ({frame_name}): {count} · Frame {c} ({frame_name}): {count} · Prose ambiguity: {n}` where {a}, {b}, {c} are the three frame numbers with the highest count of OQs carrying `provenance: hidden_frame_sweep`, ranked descending then by frame number ascending for tiebreaks. The trailing `Prose ambiguity` count is the number of OQs with `provenance: prose_ambiguity`. Frame names come from the canonical list in `references/hidden-requirements-frames.md` (mirrored in renderer constant `FRAME_NAMES`).
3. **Most-impacted stories line** — `**Most-impacted stories:** {story_id} ({count}) · {story_id} ({count}) · …` up to 5 entries. `count` is the number of `open_questions[]` entries whose `related_story_ids[]` contains this story_id. Rank descending by count, tiebreak by story_id lexical order.
4. **Recommended first line** — `**Recommended first:** [OQ-id](#oq-id) · [OQ-id](#oq-id) · …` up to 5 entries. Source: the top 5 OQ IDs (governance_gaps excluded) from the Minimum-unblock-set computation in §3.1 item 6, ranked by severity (P1 > P2 > P3), within severity by descending `len(related_story_ids)`, tiebreak by OQ ID lexical order. Anchor links target the OQ headings within the same file; each OQ heading carries an explicit `<a id="oq-{lowercased-id}"></a>` anchor for stable linking.

The summary is purely derived from `open_questions[]`, `stories[].id`, and `governance_gaps[]` — no new JSON fields are required.

Render `## At a glance` even when the brief has zero OQs (in which case the counts line reads `P1: 0 · P2: 0 · P3: 0 · Total: 0` and subsequent lines list nothing after their bold-label prefix). Empty-state rendering keeps the structure predictable for downstream consumers.

### 3.6 `FAILURE.md` (failure shapes only)

**Frontmatter:** `artifact_type: ba-failure` plus `brief_id`, `idempotency_key`, `output_type`, `created_at`, `created_by`.

**Content:**

1. `# Failure — {output_type}`
2. **Reason** — from `failure_state.reason` or equivalent field.
3. **Failure code** — from `failure_state.failure_code` (e.g., `ground_truth_strip_failed`, `quality_below_threshold`).
4. **Detected by** — which failure mode (FM-01 / FM-11 / FM-12 / FM-13 / EC-09).
5. **Recommended next action** — from `failure_state.recommended_action` or `unblock_actions[]`.
6. **Do-not-proceed flag** — if `do_not_proceed: true`, render a prominent block.

---

## 4. Determinism guarantees

The renderer is a pure function `output.json → directory tree`. Specific guarantees:

- **No `now()` calls.** Every timestamp emitted into frontmatter MUST come from the JSON (`frontmatter.created_at`), never from system time.
- **Stable ordering.** Iteration over `epics[]`, `stories[]`, `open_questions[]`, etc. follows array order in the JSON. Set-like collections (e.g. governance gap deduplication) sort by deterministic key.
- **Byte-identical re-runs.** Running the renderer twice with the same input JSON MUST produce byte-identical files (verified by `diff -r` returning empty).
- **Schema validation first.** Before writing any file, the renderer validates the input JSON against `schemas/output.json`. If validation fails, the renderer exits non-zero and writes nothing.
- **No LLM calls.** The renderer is a pure templating step. All judgment was already encoded in the JSON.

---

## 5. Cross-link conventions

- All intra-tree links are relative paths from the file containing the link.
- Story references in cross-cutting files use the form `[STORY-{N}](epics/EPIC-{NAME}/stories/STORY-{N}-{slug}.md)`.
- Anchor links to governance gaps use `01-governance-gaps.md#{kebab-cased-gap-type}` (e.g. `#legal-absent-on-regulatory`).
- The renderer MUST verify every emitted cross-link resolves to an existing file before completing. A broken link is a renderer bug and exits non-zero.
