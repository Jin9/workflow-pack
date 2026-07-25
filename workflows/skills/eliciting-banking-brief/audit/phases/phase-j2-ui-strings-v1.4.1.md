# Phase J2 — UI-String Localization (ba-elicit-from-raw v1.4.0 → v1.4.1)

> **Auditor mandate**: record the rationale and acceptance verdict for v1.4.1 — renderer-emitted UI strings (section headings, labels, table headers like `# Open Questions`, `**Why it matters:**`, `## At a glance`) are now localized via `references/ui-strings.json` instead of remaining English across all language subtrees. Closes the v1.4.0 documented caveat (`references/bilingual-emission.md` §5 prior wording: "UI strings stay English"). Driver: user request — "under the v9 in TH mode, translate into TH too" — observed that Thai readers were seeing Thai content under English section headings, which the v1.4.0 audit doc had explicitly flagged as a v1.4.1 candidate.

---

## 1. Why this refactor

v1.4.0 shipped bilingual emission (EN/TH subtrees) and v9 elicitation confirmed end-to-end functionality on content fields (OQ, assumption, story, epic, glossary, PII, regulatory dependency). The remaining gap: renderer-emitted UI strings (~70 distinct strings across 15 render_* functions) stayed English regardless of which language tree was being rendered, producing trees like:

```
# Open Questions   ← English heading
## P2
### OQ-1 — เป้าหมาย DAU หลังเปิดบริการ ...   ← Thai content
**Why it matters:** การคาดการณ์ปริมาณ ...   ← English label + Thai content
```

This was documented in the v1.4.0 audit doc (phase-j1 §5) as a caveat and §2 decision #6 as deferred. The user's "translate into TH too" message escalated the deferral into the current cycle.

## 2. Design decisions

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | Where do UI-string translations live? | **`references/ui-strings.json`** — single file, keyed `{strings: {lang: {english_key: translated_value}}}` | Co-located with other reference data. Loaded once at renderer import via `_load_ui_strings()`. Mirrors the `frame-rule-data.json` lift pattern from v1.3.0. |
| 2 | Lookup mechanism | **Module-level `_CURRENT_LANG` + `t(key)` helper.** `_render_language_tree()` sets `_CURRENT_LANG = lang` before each per-language render pass (via try/finally to guarantee reset). | Threading a `lang` parameter through 15 render_* functions would have been ~50 signature changes and made the diff large. The module-level approach is single-threaded-safe (renderer is single-threaded) and keeps the render_* function signatures unchanged. |
| 3 | Fallback for missing translations | **Return the English source key.** | Graceful — never breaks emission. Adding a new emission site doesn't require an immediate `ui-strings.json` update; the new key just stays English in non-EN trees until the JSON catches up. Prevents UI-string completeness from becoming a brittle gate on renderer evolution. |
| 4 | Which strings to localize? | **All emission-site UI strings**: section headings (`# Open Questions`, `## At a glance`), bold labels (`**Why it matters:**`, `**Suggested resolver:**`), table column headers, status banners (`Blocked for TL handoff`, `Ready for TL handoff`, `Draft`, `Failed`), empty-state messages (`No governance gaps`, `No PII identified`). | Comprehensive coverage — the user-visible English bits inside Thai trees disappear. |
| 5 | What NOT to localize? | **Frontmatter values, file paths, IDs, statute codes, enum values** — these stay canonical English/Latin across all languages. | Same discipline as the content-translation contract: machine-readable identifiers stay stable across locales. Thai legal documents conventionally mix Thai prose with English/Latin statute codes; this matches that convention. |
| 6 | Variable-name collision | `render_story` had a loop variable `for t in ac.get("then", [])` that shadowed the module-level `t()` helper. **Renamed to `then_step`** with an inline comment explaining the v1.4.1 motivation. | Hidden bug; pure lint without functional impact pre-v1.4.1. Caught during refactor. |
| 7 | Version stamp | **v1.4.1** (patch) | Additive within the v1.4.0 bilingual-emission contract; no schema change; UI improvement only. |

### Counter-points considered

- **"Use thread-local context"** — rejected. The renderer is single-threaded; module-level state is simpler. Try/finally guarantees reset.
- **"Inject UI strings into the data structure"** — rejected. Would require touching every render_* function to consult `data["_ui"][key]`. The thread-local approach is less invasive.
- **"Post-render substitution"** — rejected. Fragile: English strings may also appear in user content (OQ titles, glossary terms), so blind replace is unsafe.
- **"Do half the UI strings now and finish later"** — rejected. Half-localized trees are visibly worse than the v1.4.0 status quo. Comprehensive coverage in one cycle.

## 3. Diff scope

| File | Status | Change |
|---|---|---|
| `references/ui-strings.json` | **new** | 118 entries × 2 languages (en + th). Includes section headings, labels, table headers, status banners, empty-state messages. |
| `scripts/render_markdown_tree.py` | modified | `SKILL_VERSION` 1.4.0 → 1.4.1; module docstring gains v1.4.1 paragraph; new `_CURRENT_LANG` module variable + `find_ui_strings_path()` + `_load_ui_strings()` + `UI_STRINGS` constant + `t(key)` helper; `_render_language_tree()` split into outer wrapper (sets `_CURRENT_LANG` via try/finally) + `_render_language_tree_inner()`; every render_* function's hardcoded UI strings wrapped in `t(...)`; `render_story` loop variable `t` renamed to `then_step` to avoid shadowing the helper. |
| `SKILL.md` | modified | Frontmatter `version: 1.4.0` → `1.4.1`. Output Contract's "Bilingual emission" paragraph updated to describe v1.4.1 UI-string localization. References list gains `ui-strings.json` entry. |
| `references/bilingual-emission.md` | modified | §5 rewritten — was "v1.4.0 caveat: UI strings stay English"; now "v1.4.1+ localized: UI strings localized via `ui-strings.json` consulted by `t(key)`; English fallback for missing keys". |
| `audit/phases/phase-j2-ui-strings-v1.4.1.md` | **new** | This doc. |
| `e-commerce-v9/output-15e221f4/` | regenerated | Re-rendered under v1.4.1 against the unchanged `/tmp/ba-brief-v9.json`. EN/ subtree byte-equivalent modulo version stamp; TH/ subtree headings now Thai (e.g., `# คำถามที่ยังเปิดอยู่`, `**เหตุใดจึงสำคัญ:**`, `## ภาพรวมโดยย่อ`). |

## 4. Acceptance verdict

Verification matrix:

| Check | Procedure | Expected | Result |
|---|---|---|---|
| V1 | Renderer parses cleanly under v1.4.1 | `import render_markdown_tree` exits without SyntaxError | ✅ PASS (one f-string escape issue found + fixed during patching) |
| V2 | `t(key)` smoke-test: EN identity, TH lookup, fallback for missing key | All 3 cases | ✅ PASS |
| V3 | Re-render `/tmp/ba-brief-v9.json` (existing v9 JSON, unchanged content) into `e-commerce-v9/` under v1.4.1 | 63 files: 31 EN + 31 TH + 1 output.json at root; renderer exit 0 | ✅ PASS |
| V4 | TH subtree headings are in Thai | Inspect 02-open-questions.md, README.md, 01-governance-gaps.md, 04-glossary.md, 05-pii-inventory.md, 06-regulatory-dependencies.md, an epic file, a story file. Visually confirm Thai text. | ✅ PASS — `# คำถามที่ยังเปิดอยู่`, `## ภาพรวมโดยย่อ`, `**เหตุใดจึงสำคัญ:**`, `# อภิธานศัพท์`, `# รายการ PII`, `# การพึ่งพากฎระเบียบ`, `# Epic: ...`, `## ปัญหาที่ต้องการแก้`, `## ทำไมต้องทำตอนนี้` all rendered correctly |
| V5 | Skillify gates: `quick_validate.py` + `check_links.py` | Both exit 0 | ✅ PASS |
| V6 | F-7 drift check | exit 0 (no regression on prior cycles) | ✅ PASS |
| V7 | `_CURRENT_LANG` resets after each render pass | Inspecting at module level after a TH render shows back to "en" | ✅ PASS (try/finally invariant) |

## 5. Out-of-scope (carry-forward to v1.4.2+)

- **Story / epic slug filenames differ across language subtrees** because the title field is translated and slugify produces different outputs from Thai vs English text (e.g., `STORY-1-customer-confirms-order-...` EN vs `STORY-1-server.md` TH where the Thai title's Latin-letter portion is shorter). This is **pre-existing v1.4.0 behavior**, not a v1.4.1 regression — the per-language `find_story_path_map` was computed from localized titles since v1.4.0 first shipped. **Carry-forward candidate**: derive story slugs from the canonical English title regardless of localization, to keep filename symmetry across EN/TH/etc. Defer to v1.4.2.
- **Frontmatter values still English** in TH subtree files (e.g., `status: ready-for-tl`, `output_type: brief`, `workload_tier: T2`). These are machine-readable enums; intentional that they stay canonical.
- **Status banner inline numbers** — when v1.4.1 emits `> **สถานะ:** ฉบับร่าง — 8 P2 open question(s) require BA decision`, the "P2 open question(s) require BA decision" tail is still English because it's an inline f-string with a count interpolation. Could extract into a separate localized phrase. v1.4.2 polish.
- **Statute citation phrases** that the BA-authored TH translations include (e.g., `พ.ร.บ. คุ้มครองข้อมูลส่วนบุคคล มาตรา 19`) — these come from the BA's `translations[<lang>]` content, not the renderer's UI strings. Out of scope for v1.4.1 (BA controls).
- **Additional languages** (zh, ja, vi, ms, id) — adding requires authoring per-language translations in `ui-strings.json`. v1.4.x as needed.

## 6. Risk register

| Risk | Mitigation | Residual |
|---|---|---|
| New emission site added without updating `ui-strings.json` | `t(key)` returns the English source key unchanged → graceful degradation; never breaks emission | Acceptable — visible to reviewers as a mixed-language artifact. v1.4.x may add a coverage warning. |
| `_CURRENT_LANG` leaks across calls (e.g., test code calls render functions directly without going through `_render_language_tree()`) | Try/finally in `_render_language_tree()` resets to "en" after each pass; the module default is "en" so unwrapped callers see EN. | Solid. Test code calling render functions directly will see EN — that's the right default. |
| Variable-name collision in render_* functions with `t()` helper | One existing collision fixed (`render_story` loop var `t` → `then_step`). New collisions could appear if future render_* functions use `t` as a local name. | Lint-class. Future devs will see immediate runtime/TypeError if they try to use `t(...)` as a translation while `t` is bound to non-callable. |
| Translation quality of authored UI strings | Authored by me; manual review by a Thai-fluent reviewer recommended before widespread deployment | First v1.4.1 ship may benefit from a quick TH-fluent QA pass. Documented; not blocking. |

## 7. Carry-forward to Phase J3 (v1.4.2)

Recommended next item: address the story-slug-symmetry issue (out-of-scope item 1) so file paths match across language subtrees regardless of title translation. Then revisit v1.3.2 cleanup (F-8 hard-fail promotion + F-7 CI hook + markdown regen) which has been deferred through the v1.4 arc.

The v9 datapoint now demonstrates end-to-end bilingual emission with localized UI — a Thai-fluent operations co-worker can read the TH/ subtree standalone for comprehension. This was the original user request.
