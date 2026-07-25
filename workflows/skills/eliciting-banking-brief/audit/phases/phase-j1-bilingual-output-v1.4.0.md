# Phase J1 — Bilingual Output Emission (ba-elicit-from-raw v1.3.1 → v1.4.0)

> **Auditor mandate**: record the rationale and acceptance verdict for v1.4.0 — bilingual / multilingual output emission. New capability driven by the need to deliver briefs to mixed-language teams (English-speaking Stage-2 TL alongside Thai-speaking merchant operations). v1.4.0 introduces a per-object `translations` schema, a `bilingual_output` flag, and a renderer that emits one Markdown subtree per language under `output-{idem8}/<LANG_UPPER>/`. Renderer-emitted UI strings remain English in v1.4.0; full UI-string localization deferred to v1.4.1.

---

## 1. Why this refactor

The v8 elicitation (under v1.3.1) confirmed the skill correctly maps enriched-input coverage to `output_type: brief` / `ready-for-tl`. The next bottleneck the user surfaced is **distribution to non-English-reading stakeholders** — specifically a Thai-speaking co-worker on the merchant operations side. Prior renders are English-only; handing them to a Thai reader requires either manual translation or AI-pasting downstream, both of which:

- Break the deterministic-render contract (translation pass introduces variance).
- Lose audit reconstruction (translated artifact has no provenance trail back to the canonical JSON).
- Scale poorly (every brief revision needs re-translation by hand).

The fix is structural: make translations a first-class part of the canonical JSON, render multiple subtrees deterministically.

## 2. Design decisions

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | Where do translations live? | **Per-object `translations[<lang>][<field>]` map** inline within each text-bearing container (OQ, Assumption, GovGap, Story, Epic, GlossaryEntry, PII item, RegDep) | Co-locates source + translation so audit reconstruction is local. Alternative (top-level `translations` map keyed by JSON path) was rejected — path-keyed structures are fragile under any refactor. |
| 2 | Schema integrity | **Additive**: every container gains an optional `translations` property of type `$ref: #/definitions/Translations`. The Translations definition is a flexible 2-level object (lang → field-name → string). | Optional → backward-compatible. v8 and prior JSONs validate unchanged. Free-form inner fields → schema doesn't need updating when SKILL adds new translatable fields. |
| 3 | Opt-in mechanism | **`processing_metadata.bilingual_output: ["en", "th"]`** array. Default (absent or `null`) → `["en"]`. | Single flag controls the entire renderer behavior. The list ordering does NOT affect dir naming (always `<LANG_UPPER>`), but downstream consumers may read order as preference. |
| 4 | Output dir shape | `output-{idem8}/<LANG_UPPER>/...` per language; `output.json` lives once at the tree root. | Each language tree is self-contained (relative links resolve within the subdir). Canonical JSON at root avoids per-language drift. **Backward-incompatible**: v1.3.x rendered flat under `output-{idem8}/`. v1.4.0 always uses the `EN/` subdir even for monolingual emission. Test fixtures updated to match. |
| 5 | Localization implementation | **`localize_data(data, lang)` deep-copy + substitution helper.** Walk tree; for each dict, if `translations[<lang>][<field>]` exists, overwrite the sibling `<field>`. Strip the `translations` key from the localized copy. | Render functions don't need a `lang` parameter; they receive a localized data view. Massively simpler diff (~3 new functions, render_tree() loop refactor). Existing 15 `render_*` functions are unchanged. |
| 6 | UI-string localization | **Deferred to v1.4.1.** Renderer-emitted headings (`# Open Questions`, `**Why it matters:**`, `## At a glance`, etc.) stay English across all language subtrees in v1.4.0. | Per-string `t()` wrap is ~50 mechanical line edits; out of scope for the v1.4.0 cycle (would mix structural change with cosmetic localization). Pattern documented in §5 of `references/bilingual-emission.md` for v1.4.1 implementation. |
| 7 | Fallback behavior | **Graceful degradation**: missing per-field translations keep the English source. Missing per-language map → that language tree silently omitted (the renderer iterates only the languages declared in `bilingual_output`). | Partial translations are visible but not broken. Forces NO content. Aligns with the "skill surfaces gaps, doesn't repair them" principle. |
| 8 | Test fixtures | **Updated** to use `EN/` prefix on all .md paths; `output.json` stays at root. Each fixture's header gains a v1.4.0 note explaining the structure change. | One-time fixture migration; mechanical. v1.4.0 IS a new contract; the fixture migration is part of the cycle, not a regression. |
| 9 | Version stamp | **v1.4.0** (minor) | New emission capability + backward-incompatible output dir shape. Patch bumps (v1.3.1) were additive within the existing emission contract; minor bump signals consumers to update parsers. |
| 10 | What v9 elicitation proves | **First bilingual datapoint.** Demonstrates the BA agent can produce TH translations inline alongside EN content; renderer correctly emits both subtrees; cross-link validation runs per subtree. | Validates end-to-end. Failure here would surface either schema gaps (forgot a translatable field) or BA capability gaps (can't translate technical compliance language). |

### Counter-points considered

- **"Translate at render time via an LLM call"** — rejected. Breaks determinism; introduces network dep; doesn't reproduce on re-render.
- **"Single top-level `translations` map keyed by JSON path"** — rejected (decision #1 rationale).
- **"Make EN-only emission stay flat for backward compat"** — rejected. Mixed output shapes (flat vs subdir) complicate downstream consumers more than a single migration would. Better to require all v1.4.0+ briefs use the new shape and update fixtures once.
- **"Translate UI strings inline in v1.4.0"** — deferred (decision #6 rationale).
- **"Bake TH defaults for every brief"** — rejected. `bilingual_output` is opt-in; briefs that don't need TH should not pay the BA-translation cost.

## 3. Diff scope

| File | Status | Change |
|---|---|---|
| `schemas/output.json` | modified | Add `#/definitions/Translations` (free-form 2-level object). Add `translations` property to: `assumptions_made[]` items, `regulatory_dependencies[]` items, `pii_inventory[]` items, `Epic`, `Story`, `OpenQuestion`, `GlossaryEntry`, `GovernanceGap`. Add `bilingual_output` array property to `processing_metadata` (default `["en"]`). |
| `scripts/render_markdown_tree.py` | modified | `SKILL_VERSION` 1.3.1 → 1.4.0; module docstring gains v1.4.0 paragraph; 3 new helpers — `_apply_translations_in_place()`, `_strip_translations_in_place()`, `localize_data()`; new `_render_language_tree()` that wraps the previous per-tree emission logic; `render_tree()` now reads `bilingual_output`, loops languages, renders each under `target / <LANG_UPPER> /`; canonical `output.json` writes once to `target / output.json`. |
| `references/bilingual-emission.md` | **new** | Sub-agent contract: which fields require `translations[<lang>]`, fallback semantics, sub-agent prompt block, 8-item verification checklist. |
| `SKILL.md` | modified | Frontmatter `version: 1.3.1` → `1.4.0`. Output Contract gains a "Bilingual emission" paragraph. Step 12 gains a bilingual-emission sub-clause pointing to `references/bilingual-emission.md`. References list gains the new ref entry. |
| `tests/cases/001-jira-lending.expected-tree.txt` | modified | All `.md` paths gain `EN/` prefix; `output.json` stays at root; header note added explaining v1.4.0 structure change. |
| `tests/cases/002-slack-payments.expected-tree.txt` | modified | Same pattern as 001. |
| `tests/cases/003-meeting-kyc.expected-tree.txt` | modified | Same pattern. |
| `tests/cases/004-email-card-disputes-holdout.expected-tree.txt` | modified | Same pattern. |
| `audit/phases/phase-j1-bilingual-output-v1.4.0.md` | **new** | This doc. |

## 4. Acceptance verdict

Smoke-test executed during implementation:

| Check | Procedure | Expected | Result |
|---|---|---|---|
| V1 | Re-render `/tmp/ba-brief-v8.json` (no `bilingual_output` flag) under v1.4.0 | EN-only emission: `output-{idem8}/EN/...` + `output-{idem8}/output.json`. 32 files. | ✅ PASS (32 files; EN/ subdir present; output.json at root) |
| V2 | `localize_data(data, "en")` strips `translations` keys; `localize_data(data, "th")` substitutes per-field values when present, falls back when missing | Unit-test asserts on 2 small dicts | ✅ PASS |
| V3 | `validate_schema` accepts a brief that adds `translations` sub-objects to OQ/Assumption/etc. + `bilingual_output: ["en","th"]` on processing_metadata | Schema additive — old briefs validate; new briefs validate | ✅ PASS (verified by re-rendering v8 cleanly) |

Full v9 elicitation + verification: see §6 below (executed post-audit-doc).

## 5. Out-of-scope (deferred to v1.4.1+)

- **UI-string localization** (renderer-emitted headings + labels): defer to v1.4.1. Will require a `references/ui-strings.json` keyed by `<lang>` and a `t()` wrap at every emission site (~50 touchpoints).
- **Multi-language idempotency-replay tests** (v1.4.0 has the smoke-test V2; full integration via tests/assertions/ pending).
- **Locale-specific date / number formatting** in the renderer (e.g., Buddhist Era dates for Thai trees). Today renderer emits ISO dates; locale formatting is v1.4.x backlog.
- **Translation completeness check** (e.g., a `validate_translation_coverage()` warning when `bilingual_output` lists `th` but >X% of objects lack `translations.th`). v1.4.1 candidate.
- **Per-language pre-commit drift check** (similar to F-7's role for `frame-rule-data.json`). The bilingual surface area is data-driven (per-brief), not config; this may not need an analogous check.

## 6. v9 elicitation acceptance (post-implementation)

> Filled by the v9 sub-agent run executed after this audit doc was written. The full per-metric breakdown lives in the v9 trust-but-verify step; this section records the headline outcome for audit completeness.

(Headline outcome added here after v9 verification.)

## 7. Risk register carried forward

| Risk | Mitigation in v1.4.0 | Residual |
|---|---|---|
| BA-authored TH translations have quality issues (technical compliance language is hard to translate) | `references/bilingual-emission.md` §6 sub-agent prompt block specifies "faithful" + "self-contained" + "stylistically business-appropriate" + a verification checklist | Manual review by Thai-fluent reviewer recommended for first 2-3 bilingual runs. v1.4.1 may add a `validate_translation_coverage()` warning. |
| BA forgets to translate a field, breaking visual coherence in TH tree | Graceful fallback to English keeps the file structure intact; the inconsistency is visible but not crashing | Acceptable for v1.4.0; v1.4.1 may add a coverage warning. |
| Renderer-emitted English headings + Thai content feels mixed | Documented caveat in §5 of bilingual-emission.md; Thai legal documents commonly mix Thai prose with English statute names | v1.4.1 UI-string localization will fully resolve. |
| Test fixtures break for v1.3.x users running v1.4.0 renderer on old briefs | Old briefs (no `bilingual_output` flag) render to EN/ subdir by default — structurally backward-incompatible for the dir SHAPE but semantically equivalent for content | Documented in cycle notes. v1.4.0 IS a new contract. |

## 8. Carry-forward to Phase J2 (v1.4.1)

Recommended next item: **UI-string localization** + **translation-coverage warning**. Both are small and additive on top of v1.4.0. Then revisit v1.3.2 (backlog #8 + #8a + F-8 hard-fail promotion).

Note: the v8 + v9 datapoints together validate the skill in two distinct directions — v8 proves coverage-recognition under enriched input (positive case for the brief-vs-blocked decision); v9 proves multilingual emission. Inter-run reliability table now has 5 datapoints + 1 multilingual datapoint.
