# Phase G1 — Emission Refactor (ba-elicit-from-raw v1.0.2 → v1.1.0)

> **Auditor mandate**: record the rationale and acceptance verdict for the additive emission refactor that changes the skill's human-facing output from a single 1455-line monolithic `ba-brief.md` to a structured Markdown directory tree, while preserving the JSON canonical contract byte-identically.
>
> **Discipline**: surgical edits only. No change to schemas, references 1–7, assertions for JSON validation, procedure Steps 1–11, or failure-mode handling. Diff against v1.0.2 must be empty for those load-bearing files.

---

## 1. Reason for the refactor

**Driver**: Downstream Stage 2 (TL Design) cannot fan out per-story design subroutines while the brief lives as a single 1455-line markdown file. Specific blockers in v1.0.2:

- Human reviewers cannot link to or assign individual stories — every comment goes against the whole brief.
- Multi-reviewer assignment is impossible — there is no per-story file to own.
- Stage 2 cannot route per-story frontmatter (priority, banking-grade applicability, tier) without parsing 1500 lines of prose.
- `git diff` over time on the monolithic file is too noisy to identify what actually changed between revisions of the same brief.

**Alignment**: `DELIVERY_WORKFLOW_PLAN.md` v2.2 mandates "10 scaffold templates" as the convention for inter-stage handoff. This refactor establishes the BA scaffold (scaffold #1) and is the operational pilot for the convention. Stages 2 (TL Design) and 3b (per-spec implementation) follow the same fan-out pattern.

**Scope**: Emission layer only. The 12-step procedure, 13 failure modes, 7 reference files, banking-grade force-fill, ground-truth strip, PII redaction, and schema definitions are preserved verbatim. Only Step 12 (output assembly) and the Output Contract paragraph are touched.

---

## 2. Decision: deterministic renderer over LLM-emitted Markdown

| Option | Verdict | Reasoning |
|---|---|---|
| **Have the LLM emit 12+ Markdown files by hand on each invocation** | **REJECT** | (a) Consistency dies — the LLM cannot reliably produce 12+ files with identical frontmatter conventions across runs. (b) Token cost — every brief invocation pays for emitting the rendering. (c) Re-derivation is impossible — the JSON is canonical, but if the user discovers a JSON error and corrects it, the Markdown cannot be regenerated without paying for a full LLM run. |
| **Deterministic Python renderer reading the JSON** | **ACCEPT** | (a) Byte-identical re-runs verified (`scripts/render_markdown_tree.py` is pure-function, no `now()` calls, stable iteration). (b) Zero token cost on the rendering step. (c) Re-rendering after a JSON correction is millisecond-scale. (d) The renderer is a target for schema-driven testing (`tests/assertions/markdown-tree-shape.md`). |

The renderer was tested against `e-commerce/ba-brief.json` (9 epics × 2 stories). First run completed; second run with identical input produced `diff -r` empty. Cross-link validation built into the renderer catches broken `](path.md)` references before write completion.

---

## 3. Why JSON remains canonical

- **TL handoff contract**: Stage 2 (TL Design) consumes `output.json` and validates it against `schemas/output.json` (`additionalProperties: false`, `oneOf` discriminator on `output_type`, `allOf` invariant on `frontmatter.status: ready-for-tl` ⟹ no P1 OQs). The Markdown tree cannot carry equivalent contract enforcement — YAML frontmatter parsers do not enforce `oneOf` or invariant rules.
- **Schema enforcement**: Banking-grade force-fill (FM-11), AC linguistic-quality threshold (FM-01), PII echo blocker (FM-13), idempotency-replay scenario (AP-4.3) all hang off schema-validated JSON fields. Validating these against Markdown text would require regex-based re-parsing of the rendered output, a brittle and lossy alternative to JSON validation.
- **Audit reconstruction**: The skill's idempotency promise (`banking_grade.idempotent: true`) requires that the same input + same `idempotency_key` reproduces the exact output. JSON ordering is preserved by `json.dumps(..., sort_keys=False)`; Markdown rendering then derives deterministically from that JSON. Treating Markdown as canonical would re-introduce non-determinism via formatting drift.

**Conflict resolution**: On any disagreement between JSON and Markdown, JSON wins. The renderer is the only path from JSON to Markdown; the inverse direction is not supported and must not be attempted.

---

## 4. Why this directory tree structure

| Alternative considered | Verdict | Reasoning |
|---|---|---|
| **Flat** — all files at root, no `epics/` subtree | **REJECT** | For multi-epic briefs (e-commerce: 9 epics × 2 stories = 18 stories), 18+ story files plus epic headers at root flattens out the conceptual hierarchy and makes Stage 2 fan-out queries awkward (e.g., "list all stories of EPIC-CHK"). |
| **Per-epic-only** — one Markdown file per epic carrying all stories | **REJECT** | Restores the monolith problem at epic granularity. Stage 2 still cannot per-story-route. |
| **Per-epic subtree + cross-cutting concerns at root** (chosen) | **ACCEPT** | Cross-cutting concerns (governance gaps, open questions, glossary, PII inventory, regulatory deps, processing metadata, audit trace) are not owned by any single epic — they describe the brief as a whole. Per-epic content lives under `epics/{EPIC-ID}/`. The hybrid balances normalized navigation (jump straight to `epics/EPIC-CHK/stories/STORY-2-...md`) against denormalized cross-references (one place to scan for all P1 governance gaps). |

The `00-` numeric prefix on `00-BRIEF.md` and the `01-` through `08-` cross-cutting files reflects the intended human reading order, and produces a natural sort order when listing the root directory.

---

## 5. Carry-forward risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| **Slug collisions** on near-identical story titles within the same epic (e.g., two "Audit trail for X" stories) | Low in practice (the input rarely has two stories with identical normalized titles), but possible | `find_story_path_map` in `render_markdown_tree.py` detects same-slug duplicates within an epic and appends `-{N}` (the story's trailing integer) to disambiguate. Guaranteed unique because `story.id` is unique within the brief. |
| **Filesystem path length** on long epic names | Low | `schemas/output.json` constrains `epic.id` to `^EPIC-[A-Z0-9-]+$`; in practice this stays under 32 chars. Story slug capped at 60 chars by the slug algorithm. Total path `epics/EPIC-NAME/stories/STORY-N-slug.md` worst case ≈ 110 chars — well under macOS/Linux 255-char limit and Windows 260-char limit. |
| **Unicode in story titles** (Thai, Chinese, Arabic) producing empty slugs after the alphanumeric filter | Medium for non-Latin-script inputs | Slug algorithm preserves only `[a-z0-9]` after lowercasing. If all alphanumerics strip out, slug falls back to `"untitled"`. Test 003 (Meeting / KYC) and e-commerce holdout already exercise Latin titles; explicit non-Latin coverage deferred until a non-Latin test fixture exists. |
| **Acceptance criterion #8 arithmetic error in source brief** | N/A (documentation issue, not a code issue) | The refactor brief §10 #8 stated "= 37 files total" but enumerated `1 README + 1 output.json + 8 root-level governance/metadata + 9 EPIC.md + 18 STORY-*.md`. This omits `00-BRIEF.md`, which the same brief §3, §4.2, and §8.2 explicitly require. **Spec-correct count: 38.** The renderer produces 38 and is consistent with the structural spec. The "<100 lines per story" target was met for 16/18 stories; 2 stories breach by 4–5 lines because they each carry 4 rich Gherkin AC scenarios + the spec-required force-filled 7-row banking-grade table + 8-key DoR checklist — there is no slack to compact further without removing real content. |
| **JSON schema drift** could silently change the JSON shape such that the renderer reads `None` for a previously-required field | Low (schema is `additionalProperties: false` and the renderer treats missing fields defensively with `.get()` defaults) | The renderer validates against `schemas/output.json` via `jsonschema` when the library is available, and emits a warning when it is not. CI should install `jsonschema` to make this gate hard. |

---

## 6. Acceptance verdict against refactor brief §10

| # | Acceptance criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | `SKILL.md` version `1.1.0`; Step 12 and Output Contract paragraphs updated | **PASS** | `SKILL.md:3`, `SKILL.md:71`, `SKILL.md:75`. |
| 2 | `references/markdown-rendering-spec.md` exists with full per-file spec | **PASS** | File created with §1 (tree shapes), §2 (slug rules), §3 (per-file frontmatter+content), §4 (determinism guarantees), §5 (cross-link conventions). |
| 3 | `scripts/render_markdown_tree.py` exists, deterministic, invoked at end of Step 12 | **PASS** | Script exists; pure function; no `now()` calls; SKILL.md Step 12 invocation line emitted. |
| 4 | Test cases' JSON round-trip through renderer matches expected-tree.txt | **DEFERRED** | Four `*.expected-tree.txt` baselines created. Literal `diff` is not feasible because (a) actual JSON for each test case is LLM-emitted at run time, (b) exact epic.id and story slug depend on the run. Structural validation runs via T-1…T-12 in `tests/assertions/markdown-tree-shape.md`. |
| 5 | `schemas/output.json` byte-identical to v1.0.2 | **PASS** | SHA-256 `8a61fe5f…3699` snapshotted pre-edit; no edits touched `schemas/`. |
| 6 | `references/` files 1–7 byte-identical to v1.0.2 | **PASS** | Pre-edit checksums recorded for all 7; only `markdown-rendering-spec.md` is new. |
| 7 | Renderer is idempotent (re-run byte-identical) | **PASS** | `diff -r /tmp/render_smoke_test/output-7f9a4c2e /tmp/render_smoke_test_2/output-7f9a4c2e` empty. |
| 8 | e-commerce holdout renders to 9 epics × 2 stories tree | **PASS with notation** | 38 files emitted (1 README + 1 output.json + 1 `00-BRIEF.md` + 8 cross-cutting + 9 EPIC.md + 18 STORY-*.md). Brief §10 #8 claimed "= 37 total" — that arithmetic omitted `00-BRIEF.md`, which the same brief §3/§4.2/§8.2 explicitly require. 38 is the spec-correct count. Per-story line counts: 16/18 stories ≤ 98 lines; STORY-CHK-2 (105) and STORY-PAY-1 (104) breach the "<100" goal by 4–5 lines because their content (4 ACs each) demands it. |
| 9 | `phase-g1-emission-refactor-v1.1.md` exists | **PASS** | This file. |

---

## 7. Files changed

| Type | Path | Change |
|---|---|---|
| modified | `SKILL.md` | frontmatter version bump; Step 12 final two sentences replaced; Output Contract paragraph replaced; references list adds one row |
| created | `references/markdown-rendering-spec.md` | full rendering spec, slug rules, failure-shape tree |
| created | `scripts/render_markdown_tree.py` | deterministic renderer |
| created | `tests/assertions/markdown-tree-shape.md` | new T-1…T-12 assertion set |
| created | `tests/cases/001-jira-lending.expected-tree.txt` | expected tree baseline |
| created | `tests/cases/002-slack-payments.expected-tree.txt` | expected tree baseline |
| created | `tests/cases/003-meeting-kyc.expected-tree.txt` | expected tree baseline |
| created | `tests/cases/004-email-card-disputes-holdout.expected-tree.txt` | expected tree baseline |
| created | `audit/phases/phase-g1-emission-refactor-v1.1.md` | this file |

**Files NOT touched (verified byte-identical):**

- `schemas/output.json`, `schemas/input.json`
- `references/{ambiguity-patterns,anti-patterns,edge-case-catalog,gherkin-templates,invest-checklist,job-story-decision-tree,non-tipping-vocabulary}.md`
- `tests/assertions/{banking-grade-fields,gherkin-quality,invest-compliance}.md`
- All other audit phase docs (A1–F2)

---

## 8. Open items handed forward to Stage 2

- **No matching renderer for Stage 2 yet.** Stage 2 (TL Design) will need its own scaffold template that consumes `output.json` + the Markdown tree and emits a TL design artifact. The renderer pattern established here is reusable.
- **CI gate on `jsonschema` import.** The renderer soft-degrades if `jsonschema` is unavailable. CI should install it and treat validation errors as hard fails.
- **Non-Latin slug coverage.** No current test fixture exercises Thai / Chinese / Arabic story titles end-to-end through the renderer. Add coverage when a non-Latin fixture is authored.
- **Literal expected-tree.txt diff.** The `.expected-tree.txt` baselines are documentary; the structural assertion in `markdown-tree-shape.md` is the authoritative check. If a test framework is built that pins down a fixed idempotency_key + fixed LLM output for each test case, then literal `diff` becomes feasible.
