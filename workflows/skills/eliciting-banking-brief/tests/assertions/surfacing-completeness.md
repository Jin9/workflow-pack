# Surfacing Completeness Assertions (v1.2.1+)

> Validates the surfacing-polish behaviors introduced in v1.2.1. Run after schema validation passes AND after the renderer has emitted the directory tree.

## Purpose

v1.2.1 introduced three derived surfaces to make a Product Owner's path forward visible without re-reading the full brief:

1. **README "Why this is blocked"** must lead with a DoR-failure bullet when `ba_compliance_checklist.definition_of_ready_met: false`.
2. **README "Minimum unblock set"** must appear when `blocks_tl_handoff: true` (and only then).
3. **`02-open-questions.md` "At a glance"** must appear immediately under the H1 with non-zero counts matching the JSON.

These assertions verify the renderer wired all three behaviors correctly without changing the underlying brief content.

## Severity Semantics

- **must-pass** = test case fails on violation. Counts toward `must_pass_failures`.
- **should-pass** = warning logged; case status becomes `pass-with-warnings`.

## Rule Table

| # | Rule | Severity | Source |
|---|---|---|---|
| S-1 | **DoR bullet iff DoR=false (under blocking)**: when `blocks_tl_handoff: true`, the README "Why this is blocked" section contains a bullet matching `^- \*\*definition_of_ready_met: false\*\*` IFF `ba_compliance_checklist.definition_of_ready_met == false`. When DoR=true, no such bullet appears. When `blocks_tl_handoff: false`, the entire "Why this is blocked" section is absent (pre-v1.2.1 behavior preserved). | must-pass | spec §3.1 item 5 (v1.2.1+) |
| S-2 | **Minimum unblock set iff blocking**: when `blocks_tl_handoff: true`, the README contains a `## Minimum unblock set` section between "Why this is blocked" and "Provenance". When `blocks_tl_handoff: false`, the section is absent (no empty heading). | must-pass | spec §3.1 item 6 (v1.2.1+) |
| S-3 | **At-a-glance with non-zero counts matching JSON**: `02-open-questions.md` contains `## At a glance` immediately under the `# Open Questions` H1. The counts line `P1: {n} · P2: {n} · P3: {n} · Total: {N}` reports values that match the per-severity counts in `output.json.open_questions[]`. Total `N == P1 + P2 + P3`. When `open_questions[]` is empty, the line still appears with all-zero counts. | must-pass | spec §3.5.1 (v1.2.1+) |
| S-4 | **At-a-glance theme line shape**: the line begins with `**By theme:** Frame ` and contains exactly three `Frame N (Name): count` entries followed by `Prose ambiguity: count`. All four counts are non-negative integers. Frame names match the canonical `FRAME_NAMES` mapping (1=Scale & capacity, 2=Time & timing, …, 10=Customer experience). | must-pass | spec §3.5.1 |
| S-5 | **At-a-glance most-impacted stories**: the line begins with `**Most-impacted stories:**` and contains up to 5 entries of the form `` `STORY-ID` (N) `` where N is the count of OQs mentioning the story in `related_story_ids`. Ranking is descending by count, tiebreak by story_id lexical ascending. | must-pass | spec §3.5.1 |
| S-6 | **At-a-glance recommended-first anchors resolve**: the line begins with `**Recommended first:**` and contains up to 5 entries of the form `[OQ-id](#oq-id)`. Every linked anchor must resolve to an `<a id="oq-id"></a>` anchor on a `### ` OQ heading in the same file. | must-pass | spec §3.5.1 |
| S-7 | **Minimum unblock set computation matches spec**: the set rendered in README equals the deterministic union of (gov-gaps with `blocks_tl_handoff=true`) ∪ (P1 OQs) ∪ (gov-gaps of type `pii_inventory_missing`, `regulatory_citation_unresolved`, or `retention_policy_unstated` regardless of their own `blocks_tl_handoff`). No items outside this union appear; every item in the union appears under exactly one resolver group. | must-pass | spec §3.1 item 6 |
| S-8 | **Minimum unblock set resolver-group ordering**: when the section emits, the group headings appear in this fixed order (skipping empty groups): `PM`, `Legal`, `DPO`, `Finance`, `Compliance`, `Ops`, `InfoSec`, `other`. Each item appears under exactly one group (the first matching keyword). | must-pass | spec §3.1 item 6 |
| S-9 | **Idempotency**: rendering the same `output.json` twice produces byte-identical `README.md` and `02-open-questions.md`. (Existing T-11 covers the full tree; S-9 narrows to the two files this assertion polices.) | must-pass | renderer determinism contract |

## Per-Rule Pseudo-Check

### S-1 DoR bullet iff DoR=false (under blocking)

```python
data = load_json(output_json_path)
readme = read("README.md")
dor_met = data["ba_compliance_checklist"]["definition_of_ready_met"]
blocks = data["blocks_tl_handoff"]
has_dor_bullet = bool(re.search(r"^- \*\*definition_of_ready_met: false\*\*", readme, re.M))
has_why_blocked_section = "## Why this is blocked" in readme

if not blocks:
    assert not has_why_blocked_section, "Why-blocked section appears on a non-blocking brief"
    assert not has_dor_bullet, "DoR bullet appears outside a blocking brief"
else:
    assert has_why_blocked_section
    assert has_dor_bullet == (dor_met is False), \
        f"DoR bullet presence ({has_dor_bullet}) must match DoR=false ({dor_met is False})"
    if has_dor_bullet:
        # DoR bullet must be the FIRST bullet under "Why this is blocked"
        section = readme.split("## Why this is blocked", 1)[1].split("##", 1)[0]
        first_bullet = next(line for line in section.splitlines() if line.strip().startswith("- "))
        assert "definition_of_ready_met: false" in first_bullet, \
            "DoR bullet exists but is not the first bullet in why-blocked"
```

### S-2 Minimum unblock set iff blocking

```python
has_section = "## Minimum unblock set" in readme
assert has_section == blocks, \
    f"Minimum-unblock-set section presence ({has_section}) must match blocks_tl_handoff ({blocks})"
if has_section:
    # Section must be between Why-blocked and Provenance
    why_idx = readme.index("## Why this is blocked")
    unblock_idx = readme.index("## Minimum unblock set")
    prov_idx = readme.index("## Provenance")
    assert why_idx < unblock_idx < prov_idx, "Minimum-unblock-set out of order"
```

### S-3 At-a-glance counts match JSON

```python
oq_md = read("02-open-questions.md")
assert "# Open Questions" in oq_md
assert "## At a glance" in oq_md
# At-a-glance must appear immediately after H1, before any "## P1"/"## P2"/"## P3" severity heading
h1_idx = oq_md.index("# Open Questions")
glance_idx = oq_md.index("## At a glance")
first_sev_idx = min(
    (oq_md.find(f"## {sev}") for sev in ("P1", "P2", "P3") if f"## {sev}" in oq_md),
    default=len(oq_md),
)
assert h1_idx < glance_idx < first_sev_idx

# Counts match JSON
oqs = data.get("open_questions") or []
counts = {"P1": 0, "P2": 0, "P3": 0}
for oq in oqs:
    sev = oq.get("severity")
    if sev in counts: counts[sev] += 1
expected_total = sum(counts.values())
counts_line = re.search(
    r"^P1: (\d+) · P2: (\d+) · P3: (\d+) · Total: (\d+)$",
    oq_md, re.M
)
assert counts_line, "At-a-glance counts line missing or malformed"
p1, p2, p3, tot = map(int, counts_line.groups())
assert (p1, p2, p3, tot) == (counts["P1"], counts["P2"], counts["P3"], expected_total)
```

### S-4 Theme line shape

```python
theme_line = re.search(r"^\*\*By theme:\*\* (.+)$", oq_md, re.M)
assert theme_line, "Theme line missing"
parts = [p.strip() for p in theme_line.group(1).split("·")]
assert len(parts) == 4, f"Expected 3 Frame entries + Prose ambiguity, got {len(parts)}"
for i, part in enumerate(parts[:3]):
    m = re.match(r"^Frame (\d+) \(.+\): (\d+)$", part)
    assert m, f"Theme entry {i} malformed: {part}"
    assert 1 <= int(m.group(1)) <= 10
assert re.match(r"^Prose ambiguity: (\d+)$", parts[3])
```

### S-5 Most-impacted stories shape

```python
mis_line = re.search(r"^\*\*Most-impacted stories:\*\* (.+)$", oq_md, re.M)
assert mis_line
content = mis_line.group(1).strip()
if content != "_(none)_":
    entries = [p.strip() for p in content.split("·")]
    assert len(entries) <= 5
    for entry in entries:
        assert re.match(r"^`[A-Z0-9-]+` \(\d+\)$", entry), f"Bad entry: {entry}"
```

### S-6 Recommended-first anchors resolve

```python
rf_line = re.search(r"^\*\*Recommended first:\*\* (.+)$", oq_md, re.M)
assert rf_line
content = rf_line.group(1).strip()
if content != "_(none)_":
    anchors = re.findall(r"\[([^\]]+)\]\(#([^)]+)\)", content)
    assert len(anchors) <= 5
    for oq_id, anchor in anchors:
        assert f'<a id="{anchor}"></a>' in oq_md, f"Anchor #{anchor} for {oq_id} not found"
```

### S-7 Minimum unblock set membership matches spec

```python
if blocks:
    expected_gap_types = set()
    for g in data.get("governance_gaps", []) or []:
        if g.get("blocks_tl_handoff") or g.get("type") in {
            "pii_inventory_missing",
            "regulatory_citation_unresolved",
            "retention_policy_unstated",
        }:
            expected_gap_types.add(g.get("type"))
    expected_oq_ids = {
        oq.get("id") for oq in (data.get("open_questions") or [])
        if oq.get("severity") == "P1"
    }
    section = readme.split("## Minimum unblock set", 1)[1].split("\n## ", 1)[0]
    for t in expected_gap_types:
        assert t in section, f"Expected gap type {t} not in Minimum unblock set"
    for oq_id in expected_oq_ids:
        assert oq_id in section, f"Expected P1 OQ {oq_id} not in Minimum unblock set"
```

### S-8 Resolver-group ordering

```python
if blocks and "## Minimum unblock set" in readme:
    section = readme.split("## Minimum unblock set", 1)[1].split("\n## ", 1)[0]
    expected_order = ["PM", "Legal", "DPO", "Finance", "Compliance", "Ops", "InfoSec", "other"]
    headings = re.findall(r"^### (\w+)$", section, re.M)
    # Filter to recognized groups; verify their order is a subsequence of expected_order
    recognized = [h for h in headings if h in expected_order]
    idxs = [expected_order.index(h) for h in recognized]
    assert idxs == sorted(idxs), f"Resolver-group order violated: got {headings}"
```

### S-9 Idempotency on README + 02-OQ

```python
import subprocess, tempfile
with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
    subprocess.run(["python3", "render_markdown_tree.py",
                    "--input", output_json_path, "--output-dir", t1], check=True)
    subprocess.run(["python3", "render_markdown_tree.py",
                    "--input", output_json_path, "--output-dir", t2], check=True)
    idem8 = data["frontmatter"]["idempotency_key"][:8]
    for fname in ("README.md", "02-open-questions.md"):
        a = open(f"{t1}/output-{idem8}/{fname}", "rb").read()
        b = open(f"{t2}/output-{idem8}/{fname}", "rb").read()
        assert a == b, f"{fname} not byte-identical on re-run"
```

## Pass/Fail Interpretation

- **All must-pass rules pass** → case status = `pass`.
- **All must-pass rules pass AND ≥1 should-pass warning** → case status = `pass-with-warnings`.
- **≥1 must-pass rule fails** → case status = `fail`. Accumulate `must_pass_failures: [{rule_id, file_path, evidence}]`.

## Per-Tree Report Format

```json
{
  "assertion_file": "surfacing-completeness.md",
  "tree_root": "output-c4d8a3e7/",
  "rule_results": [
    { "rule_id": "S-1", "status": "pass" },
    { "rule_id": "S-2", "status": "pass" },
    { "rule_id": "S-3", "status": "pass" },
    { "rule_id": "S-4", "status": "pass" },
    { "rule_id": "S-5", "status": "pass" },
    { "rule_id": "S-6", "status": "pass" },
    { "rule_id": "S-7", "status": "pass" },
    { "rule_id": "S-8", "status": "pass" },
    { "rule_id": "S-9", "status": "pass" }
  ]
}
```

## Cross-References

- `references/markdown-rendering-spec.md` §3.1 (README content sections, items 5+6) and §3.5.1 (02-open-questions.md At-a-glance header)
- `scripts/render_markdown_tree.py` — implementing renderer (v1.2.1+)
- `markdown-tree-shape.md` — sibling assertion file covering tree structure; surfacing-completeness focuses on README + 02-OQ content
- `invest-compliance.md`, `gherkin-quality.md`, `banking-grade-fields.md` — orthogonal assertions on story content
