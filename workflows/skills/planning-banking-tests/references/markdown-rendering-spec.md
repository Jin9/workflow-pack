# Markdown Rendering Specification — `planning-banking-tests` v1.0.0

> Loaded by `SKILL.md` at **Step 12 only**. Renderer: `scripts/render_test_plan_tree.py`. Sibling docs: `coverage-rubric.md`, `anti-patterns.md`, `test-case-id-rules.md`.

---

## 1. Purpose

This document is the authoritative specification for the deterministic markdown tree emitted by `scripts/render_test_plan_tree.py`. The renderer is pure-Python, has no LLM calls, no system-clock reads outside the audit-trace passthrough, and no random or UUID generation. Given identical `output.json`, the renderer produces byte-identical tree output (modulo OS line endings) on any host. Determinism is load-bearing: Validation Scenario 1 (re-run determinism) compares two renders with `diff -ur`.

---

## 2. Tree shape (success branch)

For `output_type` in `{test_plan, blocked_test_plan, partial_test_plan}`, the renderer emits the following directory tree under `out/test-plan-{idem8}/` where `{idem8}` is the first 8 hex chars of the input `idempotency_key`:

```
test-plan-{idem8}/
├── README.md
├── output.json
├── 00-STRATEGY.md
├── 01-environments.md
├── 02-test-data.md
├── 03-coverage-matrix.md
├── 04-nfr-tests.md
├── 05-compliance-tests.md
├── 06-execution-order.md
├── 07-signoff-criteria.md
├── 08-coverage-gaps.md
├── 09-tl-design-dependencies.md
├── 10-audit-trace.md
└── epics/
    └── EPIC-{NAME}/
        ├── EPIC-test-plan.md
        └── stories/
            └── STORY-{N}-{slug}-test-plan.md
```

One `epics/EPIC-{NAME}/` directory per entry in `epics[]`. Inside each, one `stories/STORY-{N}-{slug}-test-plan.md` per story whose `epic_id` matches.

---

## 3. Failure tree shape

For `output_type == "failure_shape"`, the renderer emits a reduced 3-file tree:

```
test-plan-{idem8}/
├── README.md          ← failure banner + escalation pointer
├── output.json        ← full output.json including failure_state, failure_reason, escalate_to_skill
└── FAILURE.md         ← human-readable failure narrative + remediation
```

No `epics/`, no numbered sections. README.md carries a prominent `> FAILURE` blockquote banner at the top and links to `FAILURE.md`.

---

## 4. Slug rules

1. **Story slugs**: `slug = slugify(title)` where `slugify`:
   - lowercases the input;
   - replaces every run of non-alphanumeric characters with a single hyphen;
   - strips leading and trailing hyphens;
   - truncates to **60 characters** maximum, then re-strips trailing hyphens.
2. **Epic directory names**: literal `epics[].id` from BA brief (e.g., `EPIC-CART-CHECKOUT`). No transformation — IDs come from BA pre-validated as `^EPIC-[A-Z0-9_-]+$`.
3. **Story file names**: `STORY-{N}-{slug}-test-plan.md` where `N` is the story's `sequence_in_epic` (1-indexed, sorted by `story_id` lexicographic ascending).
4. **Slug collision**: not possible within a single epic because `N` is the disambiguator. Two stories with identical titles produce distinct file names via `N`.

---

## 5. Frontmatter conventions per file

Every emitted markdown file carries YAML frontmatter delimited by `---` lines at top of file. Frontmatter keys are sorted alphabetically (determinism). Per-file conventions:

1. **`README.md`** — routing frontmatter:
   - `test_plan_id` (string, from `output.frontmatter.id`)
   - `brief_id` (string, from BA brief frontmatter)
   - `brief_idempotency_key` (string, the input idem key)
   - `workload_tier` (T1 / T2 / T3)
   - `status` (`ready-for-execution` / `blocked` / `partial` / `failed`)
   - `blocks_qa_execution` (boolean)
2. **`00-STRATEGY.md` and `01-environments.md` through `10-audit-trace.md`** — artifact frontmatter:
   - `artifact_type` (literal: `strategy`, `environments`, `test_data`, `coverage_matrix`, `nfr_tests`, `compliance_tests`, `execution_order`, `signoff_criteria`, `coverage_gaps`, `tl_design_dependencies`, `audit_trace`)
   - `parent_test_plan_id` (string, same as `README.test_plan_id`)
3. **`epics/EPIC-{NAME}/EPIC-test-plan.md`** — epic frontmatter:
   - `epic_id` (string)
   - `test_tier` (T1 / T2 / T3)
   - `downstream_consumer` (literal: `qa-execution-stage`)
   - `parent_test_plan_id` (string)
4. **`epics/EPIC-{NAME}/stories/STORY-{N}-{slug}-test-plan.md`** — full QA per-story frontmatter (per design brief §4.3):
   - `story_id`, `epic_id`, `parent_test_plan_id`, `test_tier`, `owner_sdet`, `scenario_count`, `test_case_count`, `banking_grade_tags[]`, `pii_fields[]`, `regulator_codes[]`, `blocking_oqs[]`, `smoke_subset_count`, `quarantine_count`, `coverage_status`.

All boolean values are rendered as YAML lowercase (`true` / `false`). All arrays are rendered with sorted elements where the array is a set (tags, codes); preserved order where the array is sequence-significant (execution order).

---

## 6. Cross-link conventions

1. **Relative paths only** — every link inside the tree uses a relative path from the linking file's directory. Absolute paths and `file://` URIs are forbidden.
2. **Section anchors** — section links use `#section-slug` where `section-slug` is the GitHub-style auto-slug of the heading (lowercase, hyphenated, alphanumerics + hyphens only).
3. **Cross-file references** — a story plan that references the coverage matrix uses `../../03-coverage-matrix.md#story-{story_id}`. An epic plan referencing audit trace uses `../../10-audit-trace.md#epic-{epic_id}`.
4. **Outbound references** — references to external artifacts (BA brief, TL design) use opaque IDs only (no URLs); the renderer does not embed runtime URLs.

---

## 7. Determinism rules

The renderer must satisfy all of the following invariants:

1. **JSON canonicalisation** — `output.json` is re-serialised with `json.dumps(..., sort_keys=True, separators=(",", ": "), indent=2, ensure_ascii=False)` before write. Keys are sorted recursively at every level.
2. **Sorted iteration** — `epics[]`, `stories[]`, `test_cases[]`, `nfr_tests[]`, `compliance_tests[]`, `coverage_gaps[]`, `test_data_specs[]` are iterated by sorted `id` (lex ascending) before rendering. The renderer does not preserve the LLM's array order.
3. **Timestamps** — ISO 8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`), only inside `processing_metadata.audit_trace[].ts` fields. The renderer copies these values through; it does not invent timestamps and does not call `datetime.now()`.
4. **No LLM calls** — the renderer is pure Python with `json`, `pathlib`, `re`, `textwrap` only. No HTTP, no subprocess, no anthropic SDK import.
5. **No random / UUID generation** — every ID (test_plan_id, test_case_id, NFR_id, COMP_id, GAP_id) is consumed from `output.json`. If a required ID is missing, the renderer fails fast with a non-zero exit and a `RENDERER_E_MISSING_ID` message.
6. **Line endings** — `\n` only. Files are written with `newline=""` and explicit `\n` joins.
7. **File encoding** — UTF-8, no BOM.
8. **Sort stability of tags / codes** — set-typed arrays (tags, regulator codes, PII field names) are sorted ascending before render to absorb LLM-side ordering jitter.

Together, these rules guarantee: same `output.json` ⟹ same `find . -type f | xargs sha256sum` across hosts.

---

## 8. Cross-reference back to renderer script

The above rules are implemented in `scripts/render_test_plan_tree.py`. The renderer's public entry point is:

```
render_test_plan_tree(output_json_path: Path, output_dir: Path) -> RenderResult
```

The renderer reads `output.json`, dispatches on `output_type`, applies determinism rules from Section 7, and writes the tree shape from Section 2 or Section 3. Any deviation between this spec and the renderer is a renderer bug; this document is the authority.

Validation Scenario 3 (renderer stub walk, per the design plan §Verification step 3) exercises a 20-line minimal stub against this spec to confirm the tree shape before the full renderer is implemented.

---

## 9. Cross-references

- `coverage-rubric.md` — feeds `08-coverage-gaps.md` content.
- `anti-patterns.md` — AP detection failures emit `failure_shape` and trigger Section 3 failure tree.
- `test-case-id-rules.md` — supplies ID patterns enforced in Section 7.5.
- SKILL.md Step 12 — the only step that invokes the renderer.
