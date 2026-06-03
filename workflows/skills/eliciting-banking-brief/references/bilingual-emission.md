# Bilingual Emission Contract (v1.4.0+)

> **Purpose**: when a brief must be delivered to readers in more than one language (e.g., English-speaking Stage-2 TL + Thai-speaking merchant operations co-worker), the BA emits a canonical JSON with per-object `translations` maps. The renderer (`scripts/render_markdown_tree.py`) emits one Markdown subtree per language under `output-{idem8}/<LANG_UPPER>/`. This document defines the contract: which fields require translation, how to structure the maps, fallback behavior, and the per-language verification checklist.

> **When this reference is loaded**: at Step 12 (output assembly), whenever the brief's `processing_metadata.bilingual_output` lists more than one language code.

## 1. Opt-in flag

Set in `processing_metadata`:

```json
"processing_metadata": {
  "parsing_mode": "...",
  "bilingual_output": ["en", "th"]
}
```

- `bilingual_output` is **optional**. When absent or `null`, the default is `["en"]` → renderer emits only `output-{idem8}/EN/...`.
- Codes are lowercase ISO-639-1 (2 letters). Common targets: `en`, `th`, `zh`, `ja`, `ms`, `id`, `vi`.
- The **first** entry is the canonical source language. v1.4.0 expects `en` first; all source text fields are written in English; `translations` maps carry the other languages.
- The order in the list does NOT affect output dir naming (which is just `<LANG_UPPER>`) but downstream consumers may read order as preference.

## 2. The `translations` sub-object

Every text-bearing object in the schema accepts an optional `translations` property keyed by language code, whose value is an object mapping the SAME-NAMED fields of the parent object to their translated strings. Shape:

```json
{
  "id": "OQ-1",
  "severity": "P1",
  "question": "What is the PDPA lawful basis for each PII field?",
  "why_matters": "PDPA requires a documented lawful basis per data category. ...",
  "suggested_resolver": "DPO + Legal Counsel",
  "translations": {
    "th": {
      "question": "ฐานทางกฎหมายตาม PDPA ของแต่ละฟิลด์ PII คืออะไร?",
      "why_matters": "PDPA กำหนดให้ต้องมีฐานทางกฎหมายที่บันทึกไว้สำหรับแต่ละหมวดข้อมูล ..."
    }
  }
}
```

**Rules:**

- Inner keys MUST match parent-object field names exactly. `question` → `question`; `why_matters` → `why_matters`. Unknown keys are silently ignored by the renderer.
- Only `string`-typed fields can be translated. Numeric, boolean, enum, and ID fields stay in the canonical source unchanged.
- Inner-key entries are optional per field. A `translations.th.question` may exist without a `translations.th.why_matters`; the missing field falls back to the English source.
- **Do NOT nest** `translations` inside `translations.<lang>`. The renderer strips the outer key in each language tree.

## 3. Which fields require translations

For full bilingual rendering, populate `translations[<lang>]` on every customer-facing text field across these object containers:

| Container | Translatable fields |
|---|---|
| `open_questions[]` (`OpenQuestion`) | `question`, `why_matters`, `suggested_resolver` |
| `assumptions_made[]` | `assumption`, `why_made`, `default_revisit_trigger` |
| `governance_gaps[]` (`GovernanceGap`) | `evidence[]` items, `required_action` (collapse the array into a `\n`-joined string if needed; or use the field name with the array index as a separate key, e.g., `evidence_0`, `evidence_1` — the renderer does not yet support per-index inner translation, so collapsing to a joined string is the v1.4.0 convention) |
| `glossary[]` (`GlossaryEntry`) | `canonical_form` (only if it differs from a Latin-script ID), `definition` |
| `pii_inventory[]` | `treatment`, `retention_rule`, `residency_rule`, `masking_rule`, `access_audit` |
| `regulatory_dependencies[]` | `regulator` (e.g., translate the human-readable name; statute code stays canonical), `revision`, `promisor` |
| `epics[]` / `epic` (`Epic`) | `title`, `problem_statement`, `why_now`, `hypothesis`, `legal_status` (only when narrative, not enum) |
| `stories[]` (`Story`) | `title`, `context`; each `acceptance_criteria[]` item's `scenario_name` and the Gherkin step strings (`given[]`, `when`, `then[]`) |

Fields explicitly **NOT to translate** (keep canonical English / enum / ID values across all languages):

- Identifiers: `id`, `epic_id`, `story_id`, `frame`, indices.
- Enums: `severity` (P1/P2/P3), `tier` (T1/T2/T3), `output_type`, `format`, `priority`, `pii_sensitivity`, `category`.
- Dates: `due_date`, `created_at`.
- Hashes / keys: `idempotency_key`, `prev_hash`, `event_id`.
- Statute codes: `PDPA s.19`, `CCA §26`, `PCI-DSS req. 10.5`. The renderer treats these as proper nouns.
- File paths and cross-references.

## 4. Fallback behavior

For each language subtree, the renderer walks the input data and:

1. If a dict has `translations[<lang>][<field>]`, substitutes that value into `<field>`.
2. Otherwise keeps the original `<field>` value (English source).
3. Strips the `translations` key from the localized copy before rendering.

**Implication for partial translations**: a brief that only translates the OQ `question` field but not `why_matters` will produce a TH tree where each OQ has a Thai `question` and an English `why_matters` heading. This is graceful but visibly mixed; aim for complete coverage when the audience needs uniformity.

## 5. Renderer-emitted UI strings (v1.4.1+ localized)

The renderer EMITS its own headings and labels (e.g., `# Open Questions`, `**Why it matters:**`, `## At a glance`, `**Suggested resolver:**`). **As of v1.4.1**, these are localized per language via `references/ui-strings.json` (consulted by the renderer's `t(key)` helper). Each emission site calls `t("Open Questions")` which:

- Returns the English source unchanged when the active language is `en`.
- Looks up `strings[<active_lang>][<key>]` in `ui-strings.json` for any other language.
- Falls back to the English source key when the language has no entry or the key is missing (graceful — never breaks emission).

Adding support for a new language (e.g., `zh`, `ja`, `vi`) requires:

1. Adding a new top-level key under `strings` in `ui-strings.json` with the translated UI strings.
2. Listing the new language code in the `languages` array.
3. Briefs requesting that language set `processing_metadata.bilingual_output: ["en", "<new>"]`.

Adding a new emission site in the renderer requires no change to `ui-strings.json` immediately — the new key will fall back to English in non-English trees until the JSON is updated. This is intentional: it prevents UI-string completeness from becoming a brittle gate on renderer evolution.

**v1.4.0 → v1.4.1 caveat retired**: prior to v1.4.1 these strings stayed English across all language subtrees, producing trees that mixed Thai content with English headings. v1.4.1 fully resolves this.

## 6. Sub-agent prompt addendum for bilingual elicitation

When spawning a BA sub-agent for a multilingual brief, append this contract block to the existing elicitation prompt:

```
BILINGUAL EMISSION (v1.4.0+):

This brief must be delivered in {EN, TH}. Set processing_metadata.bilingual_output: ["en", "th"]. For every text-bearing object listed in references/bilingual-emission.md §3, populate a `translations` map under the object. Inner shape: {"th": {"<field_name>": "<Thai translation>"}}. Translations must be:

- Faithful (preserve regulatory/legal/numeric specifics; cite Thai statute names in Thai when standard, e.g., พ.ร.บ. คุ้มครองข้อมูลส่วนบุคคล for PDPA)
- Self-contained (each translated field reads correctly on its own; do not assume the reader has the English text alongside)
- Stylistically business-appropriate (formal but readable; avoid AI-translation tics)

Do NOT translate: enum values, IDs (OQ-N, EPIC-X, STORY-N), dates, statute codes, file paths, hashes.

After authoring, verify by inspecting any one translated OQ + assumption + governance gap + story end-to-end: does the Thai text alone (without the English source) communicate the same information?
```

## 7. Verification checklist

After rendering a bilingual brief, confirm:

- [ ] `output-{idem8}/output.json` exists (canonical, single file, contains both source + translations).
- [ ] `output-{idem8}/EN/` subtree exists with all expected files (00-BRIEF.md, 01–09, epics/, README.md).
- [ ] `output-{idem8}/<OTHER_LANG_UPPER>/` subtree exists with the same file structure (count must match EN).
- [ ] At least one OQ + one assumption + one governance gap + one story in the non-EN subtree displays the translated text (visually inspect 4-5 files).
- [ ] Identifiers (OQ-N, EPIC-X) appear identically across language subtrees (not translated).
- [ ] Renderer-emitted UI strings remain English in v1.4.0 (this is the documented caveat; not a defect).
- [ ] Cross-links within a single language subtree resolve (`_finalize()` link check exits 0 per subtree).
- [ ] Re-running the renderer on the same JSON produces byte-identical output (idempotency invariant per `tests/assertions/markdown-tree-shape.md`).

## 8. Worked example (excerpt)

Input JSON fragment:

```json
{
  "open_questions": [
    {
      "id": "OQ-1",
      "severity": "P1",
      "question": "What is the data retention schedule for customer PII?",
      "why_matters": "PDPA s.37 requires documented retention period per data class.",
      "suggested_resolver": "DPO + Legal Counsel",
      "translations": {
        "th": {
          "question": "กำหนดเวลาเก็บรักษาข้อมูล PII ของลูกค้าคืออะไร?",
          "why_matters": "พ.ร.บ. คุ้มครองข้อมูลส่วนบุคคล มาตรา 37 กำหนดให้ระบุเวลาเก็บรักษาตามประเภทข้อมูล",
          "suggested_resolver": "DPO + ที่ปรึกษากฎหมาย"
        }
      }
    }
  ],
  "processing_metadata": {
    "parsing_mode": "generic_prose_fallback",
    "bilingual_output": ["en", "th"]
  }
}
```

Renderer produces:

```
output-{idem8}/
├── output.json   (the JSON above, both source + translations)
├── EN/
│   ├── 02-open-questions.md   (uses English question/why_matters/suggested_resolver)
│   └── ...
└── TH/
    ├── 02-open-questions.md   (uses Thai question/why_matters/suggested_resolver)
    └── ...
```

## 9. Cross-references

- `schemas/output.json` — `#/definitions/Translations` and per-object `translations` properties.
- `scripts/render_markdown_tree.py` — `localize_data()`, `_apply_translations_in_place()`, `_strip_translations_in_place()`, `_render_language_tree()`.
- `audit/phases/phase-j1-bilingual-output-v1.4.0.md` — design rationale + verification verdict for the v1.4.0 cycle.
- `tests/assertions/markdown-tree-shape.md` — tree-shape invariants (updated for the EN/ subdir prefix in v1.4.0).
- v1.4.1 candidate (carry-forward): UI-string localization via a `references/ui-strings.json` map consumed by the renderer.
