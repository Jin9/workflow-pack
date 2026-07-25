# Markdown Tree Shape Assertions

> Validates that the rendered Markdown directory tree emitted by `scripts/render_markdown_tree.py` matches the canonical structure in `references/markdown-rendering-spec.md`. Run after schema validation passes AND after the renderer has been invoked.

## Purpose

Schema validation (`schemas/output.json`) enforces the JSON contract. INVEST / Gherkin / banking-grade assertions enforce semantic story quality. This assertion file enforces **tree-shape compliance** — every required file is present, every emitted file is reachable from `README.md`, every story id is addressable via stable file path, and every cross-link resolves.

The tree is mechanically derived from the JSON; failures here are renderer defects, not content defects.

## Severity Semantics

- **must-pass** = test case fails on violation. Counts toward `must_pass_failures`.
- **should-pass** = warning logged; test case status becomes `pass-with-warnings`.

## Rule Table

| # | Rule | Severity | Source |
|---|---|---|---|
| T-1 | **Output directory exists**: `output-{idem8}/` exists where `{idem8}` = first 8 chars of `frontmatter.idempotency_key`. | must-pass | spec §1.1 |
| T-2 | **Root files (success)**: for `output_type ∈ {brief, blocked_partial_brief, partial_brief}` — `README.md`, `output.json`, `00-BRIEF.md`, `01-governance-gaps.md`, `02-open-questions.md`, `03-assumptions.md`, `04-glossary.md`, `05-pii-inventory.md`, `06-regulatory-dependencies.md`, `07-processing-metadata.md`, `08-audit-trace.md` all exist at the root of `output-{idem8}/`. | must-pass | spec §1.1, §3.5 |
| T-3 | **Per-epic EPIC.md**: for every entry in `output.json.epics[]` (or the single `output.json.epic`), `epics/{epic.id}/EPIC.md` exists. | must-pass | spec §3.3 |
| T-4 | **Per-story STORY-*.md**: for every entry in `output.json.stories[]`, `epics/{epic_id}/stories/STORY-{N}-{slug}.md` exists where `{N}` is the trailing integer from `story.id` and `{slug}` is derived per the slug algorithm in spec §2. `epic_id` is the prefix of `story.id` (everything before the trailing `-N`) or `story.epic_id` if present. | must-pass | spec §2, §3.4 |
| T-5 | **Frontmatter present**: every emitted `.md` file begins with a YAML frontmatter block delimited by `---` lines, and the frontmatter contains an `artifact_type` key. Valid values: `ba-brief-index`, `ba-brief-summary`, `ba-epic`, `ba-story`, `ba-governance`, `ba-oq`, `ba-assumptions`, `ba-glossary`, `ba-pii`, `ba-reg-deps`, `ba-metadata`, `ba-audit-trace`, `ba-failure`. | must-pass | spec §3 |
| T-6 | **Story id ⇔ path match**: every `STORY-*.md` file's frontmatter `story_id` equals the trailing-integer-aware id derived from its filesystem path (`epics/{X}/stories/STORY-{N}-...md` ⇒ `story_id` ends in `-{N}` and starts with `{X}`). | must-pass | spec §3.4 |
| T-7 | **Cross-links resolve**: every relative Markdown link (`](path.md...)`) emitted in any file under `output-{idem8}/` resolves to an existing file inside `output-{idem8}/`. Particularly enforced for `01-governance-gaps.md` and `02-open-questions.md`, which MUST link affected stories. | must-pass | spec §5 |
| T-8 | **Failure-shape exclusivity**: for `output_type ∈ {needs_clarification, preprocessing_failure, pii_echo_blocked, schema_validation_failure, meta_response}` — only `README.md`, `output.json`, `FAILURE.md` exist; no `00-`–`08-*.md` files exist; no `epics/` directory exists. | must-pass | spec §1.2 |
| T-9 | **Banking-grade rows force-filled**: every `STORY-*.md` body contains a `## Banking-Grade Concerns` table with exactly 7 rows whose first column is, in order, `pii_fields`, `audit_events`, `idempotency`, `reversibility`, `authn_authz`, `regulatory`, `tipping_off`. | must-pass | spec §3.4; FM-11 |
| T-10 | **DoR checklist completeness**: every `STORY-*.md` body contains a `## Definition of Ready` section with exactly 8 checkbox lines matching the canonical DoR keys (`format_clear`, `happy_path_present`, `error_path_present`, `banking_grade_evaluated`, `priority_set`, `dependencies_identified`, `sizing_done`, `no_blocking_ambiguities`). | must-pass | spec §3.4 |
| T-11 | **Idempotency**: rendering the same `output.json` twice produces byte-identical trees (`diff -r run1 run2` empty). | must-pass | spec §4 |
| T-12 | **Spec-correct file count for e-commerce holdout**: `output.json` with 9 epics × 2 stories yields exactly 38 files: 1 `README.md` + 1 `output.json` + 1 `00-BRIEF.md` + 8 cross-cutting `0N-*.md` + 9 `EPIC.md` + 18 `STORY-*.md`. | should-pass | acceptance §10 #8 (note: `00-BRIEF.md` was missing from the original "37 total" arithmetic; spec-correct count is 38) |
| T-13 | **`09-hidden-requirements.md` conditional emit (v1.2.0+)**: file exists at root iff `processing_metadata.hidden_requirements_sweep.total_findings > 0` OR any OQ/assumption carries `provenance: hidden_frame_sweep`. When absent it MUST be absent (no empty file). When present it MUST have `artifact_type: ba-hidden-requirements` frontmatter. | must-pass | spec §3 + `hidden-requirements-frames.md` §Output shape |
| T-14 | **Provenance/frame tag integrity (v1.2.0+)**: every `open_question` and `assumption` carrying `provenance: hidden_frame_sweep` MUST also carry a `frame` field with integer value 1..10. Inverse also holds: any `frame` field present implies `provenance` is set. Mismatched pairs are a schema-and-content defect. | must-pass | `schemas/output.json` OpenQuestion + assumptions_made.items optional fields |

## Per-Rule Pseudo-Check

### T-1 Output directory exists

```
idem8 = output.json.frontmatter.idempotency_key[:8].lower()
assert exists(f"output-{idem8}/")
```

### T-2 Root files (success)

```
if output_type in SUCCESS_TYPES:
    for f in [
      "README.md", "output.json", "00-BRIEF.md",
      "01-governance-gaps.md", "02-open-questions.md", "03-assumptions.md",
      "04-glossary.md", "05-pii-inventory.md", "06-regulatory-dependencies.md",
      "07-processing-metadata.md", "08-audit-trace.md"
    ]:
        assert exists(f"output-{idem8}/{f}")
```

### T-3 Per-epic EPIC.md

```
epics = output.json.epics or [output.json.epic]
for epic in epics:
    assert exists(f"output-{idem8}/epics/{epic.id}/EPIC.md")
```

### T-4 Per-story STORY-*.md

```
for story in output.json.stories:
    N = re.search(r"-(\d+)$", story.id).group(1)
    epic_id = story.id.rsplit("-", 1)[0]
    slug = slugify(story.title)   # per spec §2
    path = f"output-{idem8}/epics/{epic_id}/stories/STORY-{N}-{slug}.md"
    # Allow collision-guard variant: STORY-{N}-{slug}-{N}.md (if duplicate slug)
    assert exists(path) or exists(collision_guard_path(epic_id, story))
```

### T-5 Frontmatter present

For each emitted `.md` file:
- Read first 2 KB.
- Assert starts with `---\n`.
- Find next `---\n`.
- Parse intermediate block as YAML.
- Assert `artifact_type` key present AND its value is in the allowed set.

### T-6 Story id ⇔ path match

For each `STORY-*.md`:
- Parent dir: `output-{idem8}/epics/{X}/stories/`.
- Filename: `STORY-{N}-*.md` (regex `^STORY-(\d+)-.*\.md$`).
- Frontmatter `story_id` must equal `f"{X}-{N}"`.

### T-7 Cross-links resolve

```
for f in glob("output-{idem8}/**/*.md"):
    for match in re.findall(r"\]\((?!https?:)([^)]+\.md)(#[^)]*)?\)", read(f)):
        target = (f.parent / match[0]).resolve()
        assert exists(target)
```

### T-8 Failure-shape exclusivity

```
if output_type in FAILURE_TYPES:
    root_files = listdir(f"output-{idem8}/")
    assert sorted(root_files) == ["FAILURE.md", "README.md", "output.json"]
    assert not exists(f"output-{idem8}/epics/")
```

### T-9 Banking-grade rows force-filled

```
for f in glob("output-{idem8}/epics/*/stories/STORY-*.md"):
    body = read(f)
    table_section = extract_section(body, "## Banking-Grade Concerns")
    rows = re.findall(r"^\| `([a-z_]+)` \|", table_section, re.M)
    assert rows == [
      "pii_fields", "audit_events", "idempotency",
      "reversibility", "authn_authz", "regulatory", "tipping_off"
    ]
```

### T-10 DoR checklist completeness

```
for f in glob("output-{idem8}/epics/*/stories/STORY-*.md"):
    body = read(f)
    dor_section = extract_section(body, "## Definition of Ready")
    keys = re.findall(r"^- \[[ x]\] (\w+)$", dor_section, re.M)
    assert keys == [
      "format_clear", "happy_path_present", "error_path_present",
      "banking_grade_evaluated", "priority_set", "dependencies_identified",
      "sizing_done", "no_blocking_ambiguities"
    ]
```

### T-11 Idempotency

```
run("render_markdown_tree.py --input fixture.json --output-dir /tmp/r1")
run("render_markdown_tree.py --input fixture.json --output-dir /tmp/r2")
assert subprocess.run(["diff", "-r", "/tmp/r1", "/tmp/r2"]).returncode == 0
```

### T-12 Spec-correct file count (e-commerce holdout)

```
files = list_recursive(f"output-{idem8}/")
assert len(files) == 38
buckets = {
  "README.md": 1, "output.json": 1, "00-BRIEF.md": 1,
  "0[1-8]-*.md": 8, "EPIC.md": 9, "STORY-*.md": 18,
}
for pattern, expected in buckets.items():
    assert count_matching(files, pattern) == expected
```

### T-13 Conditional `09-hidden-requirements.md`

```
data = load_json(output_json_path)
sweep = data.get("processing_metadata", {}).get("hidden_requirements_sweep", {})
tagged_oqs = [oq for oq in data.get("open_questions", [])
              if oq.get("provenance") == "hidden_frame_sweep"]
tagged_assumptions = [a for a in data.get("assumptions_made", [])
                      if a.get("provenance") == "hidden_frame_sweep"]
should_exist = (sweep.get("total_findings", 0) > 0
                or len(tagged_oqs) > 0
                or len(tagged_assumptions) > 0)
file_path = f"output-{idem8}/09-hidden-requirements.md"
assert exists(file_path) == should_exist
if should_exist:
    frontmatter = parse_frontmatter(read(file_path))
    assert frontmatter["artifact_type"] == "ba-hidden-requirements"
```

### T-14 Provenance/frame tag integrity

```
for collection_key in ("open_questions", "assumptions_made"):
    for item in data.get(collection_key, []):
        prov = item.get("provenance")
        frame = item.get("frame")
        if prov == "hidden_frame_sweep":
            assert isinstance(frame, int) and 1 <= frame <= 10, \
                f"hidden_frame_sweep without valid frame: {item}"
        if frame is not None:
            assert prov in ("hidden_frame_sweep",), \
                f"frame set without provenance=hidden_frame_sweep: {item}"
```

## Pass/Fail Interpretation

- **All must-pass rules pass** → case status = `pass`.
- **All must-pass rules pass AND ≥1 should-pass warning** → case status = `pass-with-warnings`.
- **≥1 must-pass rule fails** → case status = `fail`. Accumulate `must_pass_failures: [{rule_id, file_path, evidence}]`.

## Per-Tree Report Format

```json
{
  "assertion_file": "markdown-tree-shape.md",
  "tree_root": "output-7f9a4c2e/",
  "rule_results": [
    { "rule_id": "T-1", "status": "pass" },
    { "rule_id": "T-2", "status": "pass" },
    { "rule_id": "T-3", "status": "pass" },
    { "rule_id": "T-4", "status": "pass" },
    { "rule_id": "T-5", "status": "pass" },
    { "rule_id": "T-6", "status": "pass" },
    { "rule_id": "T-7", "status": "pass" },
    { "rule_id": "T-8", "status": "pass" },
    { "rule_id": "T-9", "status": "pass" },
    { "rule_id": "T-10", "status": "pass" },
    { "rule_id": "T-11", "status": "pass" },
    { "rule_id": "T-12", "status": "pass" },
    { "rule_id": "T-13", "status": "pass" },
    { "rule_id": "T-14", "status": "pass" }
  ]
}
```

## Cross-References

- `references/markdown-rendering-spec.md` (canonical tree structure, frontmatter, slug rules, cross-link conventions)
- `scripts/render_markdown_tree.py` (the renderer this assertion file validates)
- `invest-compliance.md` (per-story INVEST checks — orthogonal to tree shape)
- `gherkin-quality.md` (Gherkin AC checks — orthogonal to tree shape)
- `banking-grade-fields.md` (banking-grade force-fill checks — JSON side; T-9 here is the rendering-side mirror)
