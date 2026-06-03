# Phase I1 — Frame-Rule Data-File Lift (ba-elicit-from-raw v1.2.2 → v1.3.0)

> **Auditor mandate**: record the rationale and acceptance verdict for v1.3.0, the first cycle of the v1.3 arc. Internal refactor with one new dev-time assertion (F-7); no behavior change on the FM-17 enforcement path.

---

## 1. Why this refactor

v1.2.2 shipped FM-17 (Frame 4 sub-topic coverage enforcement) but left the rule data duplicated in two places:

- **Renderer constant** — `scripts/render_markdown_tree.py:63-101`, a `Dict[str, List[Tuple[str, List[str]]]]` with 5 triggers × 22 sub-topics × keyword lists.
- **Reference doc table** — `references/hidden-requirements-frames.md:183-207`, a 4-column markdown table that *adds* a jurisdiction-note column the renderer constant doesn't carry.

Every keyword-list edit required syncing both files by hand. Three v1.3 backlog items depend on this lift before they can ship cheaply:

| Backlog # | Item | Dependency |
|---|---|---|
| #1 | This lift | — |
| #2 | Enforce 4 v1.3-pending Frame 4 triggers (children, health_medical, financial_lending, telecom_sms_marketing) | Without #1, each new trigger costs 2 file edits |
| #4 | Apply FM-17 pattern to Frame 6 (failure & edge cases) — split-brain / replay attack / partial-success / credential stuffing / TOCTOU | Same shape; this lift establishes the data-file pattern |
| #5 | Tier-aware sub-topic coverage (T1 banking requires MAS/FATF/dual-approval/sanctions; T3 prototype skips more) | Adds a `tier` dimension to the rule data; trivial in JSON, painful in a Python tuple |

Doing #1 first means each subsequent rule becomes a JSON edit, not a Python edit + doc edit.

---

## 2. Design decisions

The 8-question decision matrix produced during planning:

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | File format | **JSON** | Renderer already uses `json` stdlib (line 39); no new dep. Dict is 22 shallow entries — JSON readability is acceptable. |
| 2 | Location | `references/frame-rule-data.json` | Matches backlog wording; colocated with the narrative doc it mirrors. |
| 3 | Loader timing | Module-level eager load | Preserves byte-identical call-site semantics at the two existing FRAME4_SUBTOPIC_RULES consumers. Fails fast at import on malformed data — CI-friendly. |
| 4 | Markdown ↔ data sync | Data file is source-of-truth + runnable drift-check script (`scripts/check_frame_rule_data_drift.py`) | Markdown regen deferred to v1.3.1. The check is executable, not just prose. Drift register: `(trigger, sub_topic_id, frozenset(lowercased+stripped keywords), jurisdiction_note)`. |
| 5 | Jurisdiction notes | Include in JSON | Makes JSON lossless source-of-truth; renderer ignores the field; future markdown regen needs them. |
| 6 | Data-file schema | No `frame-rule-data.schema.json` for v1.3.0 | Loader does structural validation (known triggers, required keys). External schema is appropriate when external callers consume; defer. |
| 7 | v1.3-pending triggers in JSON | **Omit** | The 4 pending triggers (children / health_medical / financial_lending / telecom_sms_marketing) have *only* activation heuristics drafted in `hidden-requirements-frames.md:225-234`, no keyword libraries. Adding an empty `_v1_3_pending_triggers` stub is scope creep with no functional value. They land alongside detection logic in v1.3.1+. |
| 8 | Version stamp | **v1.3.0** | Changes the renderer's startup contract (now reads an additional file) and adds a new assertion (F-7). Patch bumps in this arc were behavior-preserving polish; v1.3.0 opens the door for backlog items #2-#9. |

### 2.1 Counter-points considered

- **YAML over JSON**: rejected. YAML wins on readability for nested lists, but the dict is 22 entries shallow and JSON is fine; adding pyyaml violates the v1.0.2-era zero-runtime-dep posture established for the renderer (only `json`, `re`, `shutil`, `pathlib`, `typing`).
- **Lazy load**: rejected. Deferring the load to per-render time forces signature changes on `validate_frame4_subtopics()`, makes errors render-time instead of import-time, and complicates testing. Module-level eager load surfaces config errors immediately.
- **Parse the markdown table at runtime**: rejected. Markdown parsing is fragile; the drift-check script parses it only at dev time, not on every render.
- **Markdown-table regen script**: deferred. Bidirectional sync is a v1.3.1 nice-to-have; v1.3.0 ships the data file + drift check so the markdown table stays accurate by hand-edit until the regen lands.

---

## 3. Diff scope

| File | Status | Change |
|---|---|---|
| `references/frame-rule-data.json` | **new** | Source-of-truth: 5 triggers × 22 entries × `{sub_topic_id, coverage_keywords, jurisdiction_note}`. Keywords byte-equivalent to the deleted dict literal; jurisdiction notes copied from the markdown table's 4th column. |
| `scripts/render_markdown_tree.py` | modified | `SKILL_VERSION` `1.2.2` → `1.3.0`; module docstring gains a v1.3.0 paragraph; lines 63-101 (the FRAME4_SUBTOPIC_RULES literal) replaced with `find_frame_rule_data_path()` + `_load_frame4_subtopic_rules()` + module-level `FRAME4_SUBTOPIC_RULES = _load_frame4_subtopic_rules()`. Tuple shape preserved (`List[Tuple[str, List[str]]]`). |
| `scripts/check_frame_rule_data_drift.py` | **new** | ~130 LOC dev-time drift check. Parses markdown table at lines 183-207 + the JSON; asserts set-equality on normalized rows. Exits 1 with structured diff on drift. Runnable: `python3 scripts/check_frame_rule_data_drift.py`. |
| `tests/assertions/frame-coverage-completeness.md` | modified | Title gains `(refined v1.3.0)`; F-7 added to the rule table + per-rule pseudo-check + per-tree-report sample; cross-references list expanded with `frame-rule-data.json` and `check_frame_rule_data_drift.py`. |
| `references/hidden-requirements-frames.md` | modified | Line 181 intro to the sub-topic table now points to `frame-rule-data.json` as the runtime source-of-truth; line 234 (v1.3-pending forward-planning bullet) updated to acknowledge the lift has shipped. |
| `SKILL.md` | modified | Frontmatter `version: 1.2.2` → `1.3.0`; References section gains a `frame-rule-data.json` entry noting the renderer-load + the drift-check pairing. |

No call sites of `FRAME4_SUBTOPIC_RULES` change (`_detect_frame4_triggers()` at lines 1313-1382 and `validate_frame4_subtopics()` at lines 1385-1432 both consume the lifted constant with identical tuple shape).

---

## 4. Acceptance verdict

Verification matrix (all 5 steps passed before this audit doc was written):

| Check | Procedure | Expected | Result |
|---|---|---|---|
| V1 | `python3 scripts/check_frame_rule_data_drift.py` | exit 0, "22 rows agree" | ✅ PASS |
| V2 | Import-time sanity: `len(FRAME4_SUBTOPIC_RULES) == 5`; total sub-topics `== 22`; tuple shape preserved; trailing-space `"scc "` keyword preserved | All asserts pass | ✅ PASS |
| V3 | Byte-identity render: render `/tmp/ba-brief-v122-clean.json` under v1.3.0 → diff against v1.2.2 baseline | zero diff (or `SKILL_VERSION`/`CREATED_BY` lines only — version stamps are expected to differ) | ✅ PASS (only `created_by` provenance lines differ — expected) |
| V4 | Negative drift: temporarily edit one keyword in `frame-rule-data.json`, re-run drift script | exit 1 with structured diff; revert restores PASS | ✅ PASS |
| V5 | Negative loader: temporarily rename `frame-rule-data.json`, run renderer import | RuntimeError at import with mention of v1.3.0+ | ✅ PASS |

The v1.2.2-stamped renders (`/tmp/ba-brief-v4.json`, `/tmp/ba-brief-v5.json`) continue to fail under v1.3.0 for the *same* FM-16/FM-17 reasons documented in `[[project_holdout_briefs]]` — no regression introduced.

---

## 5. Out-of-scope (carry-forward to later cycles)

- **4 v1.3-pending Frame 4 triggers** (children / health_medical / financial_lending / telecom_sms_marketing). Their detection logic must land in `_detect_frame4_triggers()` simultaneously with their keyword libraries in `frame-rule-data.json` and rows in `hidden-requirements-frames.md`. Backlog item #2; separate v1.3.1+ cycle.
- **FM-18 + FM-19** (audit-emission + tipping-off-check auto-emits) — same defect class as FM-16, mandated by AP-4.3 line 1. Independent of the data lift. Backlog item #3.
- **Markdown-table regeneration script** — bidirectional sync. Backlog item #1 follow-on; v1.3.1+.
- **`schemas/frame-rule-data.schema.json`** — defer until external callers consume the data file.
- **Frame 6 sub-topic library** (split-brain / replay attack / partial-success / credential stuffing / TOCTOU) — follows this lift's pattern. Backlog item #4.
- **Tier-aware sub-topic coverage** — adds a `tier` dimension to `frame-rule-data.json`. Backlog item #5.
- **`frame_4_cap_exception` protocol** — when activated sub-topics exceed Frame 4's cap of 10. Backlog item #6.
- **FM-16 in `jsonschema`-disabled environments** — the schema if/then half remains dead code without the library. Backlog item #7.
- **Renderer slug-efficiency cleanup** — `find_story_path_map` calls `slugify()` 3× per story; dead `seen_slugs` variable. Backlog item #9; non-correctness.

---

## 6. Risk register carried forward

| Risk | Mitigation in v1.3.0 | Residual |
|---|---|---|
| `frame-rule-data.json` hand-edit produces malformed JSON | `_load_frame4_subtopic_rules()` raises `RuntimeError` on missing keys or unknown triggers; F-7 drift script catches set mismatches | If someone edits the JSON in a way that breaks the dict shape but matches the markdown table after the same edit, both checks pass but a third file (e.g., `validate_frame4_subtopics()` keyword usage) might diverge. Mitigated by V2 + V3 in CI. |
| Markdown table drifts silently from JSON | F-7 is runnable but not automatic per render; relies on CI invocation | Add to CI/pre-commit in v1.3.1. |
| v1.3-pending triggers added to JSON without detection logic | `_load_frame4_subtopic_rules()` raises on unknown trigger keys | Solid: rejecting at import-time forces the JSON + `_detect_frame4_triggers()` to move together. |
| Loss of trailing-space keyword `"scc "` during edits | Test V2 explicitly asserts `'scc ' in pii['cross_border_transfer']` | Test will catch it. |

---

## 7. Carry-forward to Phase I2 (next v1.3.x cycle)

Recommended next item: **backlog #2** (enforce the 4 v1.3-pending triggers). The data file now accepts them as new top-level `triggers` keys, the markdown table needs new rows, and `_detect_frame4_triggers()` needs activation heuristics (already drafted in prose at `hidden-requirements-frames.md:229-232`). Drift check F-7 will validate the JSON↔markdown sync automatically.

Avoid bundling #2 with #4 (Frame 6) — different frames, different review surfaces, separate cycles preserve audit clarity per the v1.0.2→v1.2.2 cadence established in Phases G1, H1, H2.
