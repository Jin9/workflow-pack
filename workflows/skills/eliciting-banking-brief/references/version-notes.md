# Version Notes — Behavior Maturity Timeline

Which behaviors and enforcement gates landed in which `metadata.version`. The
`SKILL.md` body states the *current* contract; this file records *when* each
piece arrived and its current enforcement maturity. None of this changes the
current behavior — it is provenance for audit reconstruction.

## Hidden-requirements sweep (Step 9.5)

- **v1.2.0+** — FM-15 sweep-coverage gate introduced. `coverage_score` must be
  `complete` for `output_type: brief`; `partial` allowed only for
  `blocked_partial_brief` with a P2 OQ recording the gap.
- **v1.2.2+** — sub-topic coverage enforcement added on Frame 4 (FM-17). Frame 4
  activated triggers must cover their required sub-topics per
  `hidden-requirements-frames.md`. Also added FM-16 idempotency-replay
  enforcement (every story declaring `bgc.idempotency.status: applies` MUST carry
  a `banking_grade_idempotency` AC scenario, enforced by schema if/then AND
  renderer runtime check).
- **v1.3.0+** — `references/frame-rule-data.json` lifted to runtime
  source-of-truth for FM-17 Frame 4 sub-topic coverage rules; mirrored in
  `hidden-requirements-frames.md` for human readability (drift caught by
  `scripts/check_frame_rule_data_drift.py`, assertion F-7).
- **v1.3.1+** — cap-exception protocol added. Mandatory FM-17 sub-topic coverage
  on Frame 4 takes precedence over the soft cap of 10; when it does, declare the
  overshoot in `processing_metadata.hidden_requirements_sweep.cap_exceptions["4"]`
  with `{cap, observed_count, reason (>=8 chars)}`. This is **warning-grade in
  v1.3.1** (assertion F-8) and is **promoted to must-pass in v1.3.2**.

## Bilingual emission (Step 12 + Output Contract)

- **v1.4.0+** — bilingual emission introduced. When the input requires output in
  multiple languages, set `processing_metadata.bilingual_output: ["en", "th"]`
  (or wider) AND populate per-object `translations[<lang>]` maps for every
  text-bearing object (open_questions, assumptions_made, governance_gaps,
  glossary, pii_inventory, regulatory_dependencies, epics, stories) per
  `references/bilingual-emission.md`. The renderer emits one subtree per language
  under `output-{idem8}/<LANG_UPPER>/`; the canonical JSON lives once at the root.
  Per-field translations missing in `translations[<lang>]` fall back to the
  English source (graceful degradation).
- **v1.4.1+** — UI-string localization added. The renderer also localizes
  renderer-emitted UI strings (section headings, labels, table headers — e.g.,
  `# Open Questions` → `# คำถามที่ยังเปิดอยู่`, `**Why it matters:**` →
  `**เหตุใดจึงสำคัญ:**`) via `references/ui-strings.json`, looked up by the
  `t(key)` helper with English-source fallback for any missing key. The BA must
  produce content translations for every customer-facing text field per
  `references/bilingual-emission.md` when emitting bilingual; UI strings are
  handled automatically by the renderer.

## Typed discovery handoff (Input + Steps 1/3/5–6/11/12)

- **v1.5.0+** — optional typed `discovery` input added for the S1 composite chain
  (`researching-ba-problem-space` → human gate → this skill). It is an **advisory**
  object (`{audit_id, problem_framing, opportunities[], assumptions[],
  regulatory_regimes[], stakeholder_hints[], tier_signal, recommendation}`) that may
  only *add* findings/rows or *raise* a tier floor — never suppress a detector, lower
  a tier, satisfy a citation, or replace `raw_content`. All 17 failure modes are
  unchanged (each still fires from `raw_content`). Consumed at Step 3 (regimes →
  `pending` citation rows — leads, not citations), Steps 5–6 (stakeholder hints →
  absent rows), Step 11 (tier floor + needs-work/do-not-build P2 OQ), Step 12
  (`upstream_refs.discovery_audit_id` provenance). FM-12 firewall: `discovery` is
  never scanned/stripped. **Idempotency-contract refinement:** the contract now reads
  "same `idempotency_key` + same `raw_content` + same `discovery` → same output"; a
  cache keyed on `idempotency_key` alone is a bug (the squad-engine input-hash key is
  already correct). When `discovery` is absent, output is **byte-identical to v1.4.1**
  (the existing test cases prove this).
