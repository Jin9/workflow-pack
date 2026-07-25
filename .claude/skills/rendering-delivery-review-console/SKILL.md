---
name: rendering-delivery-review-console
version: 1.2.0
description: >
  Assemble one run-scoped, offline, byte-deterministic delivery-review.html "Delivery Review Console"
  from a pipeline run directory: a single standalone document whose left-nav menus are pipeline stages
  (Epics and Stories, UX Brief, Design and ADRs, Plan Review, Quality), superseding the per-stage viewers.
  Diagrams embed as offline inline SVG via the deterministic drawio transcoder plus a path chip, and the
  twelve test gates roll into a Quality-Gate Board with a worst-of R/A/G roll-up over complete evidence.
  Use when the user asks to "build the delivery review console for
  this run", "render the whole run folder into one offline review page", "give me one review surface for
  all stages", or "roll the test gates into a quality board". Do NOT use to render one single JSON
  contract for debug (that is rendering-contract-debug-viewer), to author pipeline stage skills under
  workflows/skills, or to edit the squad-delivery dashboard data or bundle (that is
  roundtripping-dashboard-data-contract).
compatibility: claude-code, codex, opencode; requires python3 (stdlib only) and node only for the optional JS self-check
---

# Rendering Delivery Review Console

## Purpose

Assemble one **run-scoped**, **offline**, **byte-deterministic** `delivery-review.html` — the **Delivery
Review Console** — from a pipeline run directory. Its left-nav menus are **pipeline stages across the whole
S0–S7 spine** (S0 Intake, Epics & Stories, UX Brief, Design & ADRs, Plan Review, Contracts, Impl & Reviews,
QA Test Design, QA Validation, Release Handoff, Prod Validation) plus the **Quality-Gate Board** (T1–T12),
so a reviewer reads every stage's work in one place instead of opening a viewer per stage. It supersedes
the per-stage viewers for review. Each stage builder renders its contract richly when present and degrades
to an honest "pending" (or "unreadable-or-malformed") card otherwise.

Diagrams are embedded as **offline inline SVG** (produced by the deterministic `.drawio` to `<svg>`
transcoder) plus a relative-path chip; a failed transcode surfaces as a visible diagnostic card, never a
silent skip. The render is delegated to a stdlib-only script; the agent locates the run dir, runs it, and
verifies offline + determinism. The JSON contract stays authoritative on any conflict — the console is
**review tooling, never pipeline operation**.

## When to use this skill

- Use when: the user asks to "build the delivery review console for this run" or "assemble one review page
  for the whole run folder".
- Use when: the user asks to "give me one offline review surface across all stages" (discovery, brief,
  epics and stories, UX pack, design and ADRs, plan review, gates) instead of one viewer per stage.
- Use when: the user asks to "roll the test gates into a quality board" or "show the R/A/G gate roll-up for
  this run".
- Use when: the user asks to "embed the architecture and ER diagrams inline and offline in the review page".
- Do NOT use when: the goal is to render **one** JSON contract for one-off debug inspection — that is
  `rendering-contract-debug-viewer` (this skill assembles a multi-stage run, not a single file).
- Do NOT use when: the goal is to **author** a pipeline stage skill (those live under `workflows/skills`)
  or to **produce** the stage JSON contracts (a stage skill does that). This skill only reads existing
  artifacts.
- Do NOT use when: the goal is to edit the squad-delivery dashboard's own data or bundle — that is
  `roundtripping-dashboard-data-contract`.

## Input contract

This is a tooling skill: there is **no skill or boundary schema, no YAML pin, no adapter payload, and no
engine-injected keys** — the contract below is prose, enforced by the script's exit behavior.

- **Required:** the path to **one existing, readable pipeline run directory** (per-stage subfolders such
  as `S1b-ba-brief/`, `S2-tl-design/`, optionally a canonical `gates/` dir).
- **Optional:** `-o OUT.html` output path (default `RUN_DIR/delivery-review.html`); every stage artifact
  is optional — absent stages render pending cards.
- **Precondition — sensitivity:** run artifacts must already be pre-redacted and secret-free (placeholder
  form `PII:REDACTED:CLASS=...`). The console embeds stories and gate details verbatim, so the HTML
  inherits the artifacts' full sensitivity; `bare_host()` only strips URL schemes — **the renderer is not
  a PII or secret sanitizer**. If sensitive values are suspected, STOP and request a redacted copy.
- **Stop conditions (exit non-zero, nothing written):** run dir missing; output not a `.html` path, inside
  the skill directory, resolving to any consumed run artifact, or an existing file that is neither the
  default console nor marked as one; unreadable template; ambiguous fallback gate evidence (duplicate
  filenames with no canonical `gates/<file>`); a forbidden token surviving into the final HTML.

## Output contract

Exactly **one** self-contained HTML file (default `RUN_DIR/delivery-review.html`) plus one stdout summary
line (`wrote OUT (N bytes) · P/12 menus present · gate rollup X`) on exit 0. The write is atomic (temp
sibling + replace) — a failed build never truncates an existing console. Offline: CSS/JS inline, the
assembled `window.PACK` baked in as escaped data, system font stack, diagrams as offline inline `<svg>`.

The `window.PACK` contract is additive — absent stages render pending sections, never crash:

```
{ run: { run_id, project, stage_span, produced_by, schemaVersion, generated_from,
         renderer: { renderer_skill, renderer_version, pack_schema_version },
         audit_index[], gate_ledger[] },
  menus: [ { id, label, stage, order, present } ],
  sections: [ { id, menu, sub_of?, title, kind, status?, tier?, verdict?, audit_id?, source_path, payload } ] }
```

- `present: true` means "a recognized artifact parsed as a JSON object" — **never** schema validity; only
  separate `engine validate-run --strict` evidence establishes schema conformance. Absent and
  unreadable-or-malformed artifacts are distinguished on the pending card.
- `audit_index[]` is built from the **authoritative artifacts** (stage outputs + gate evidence), each entry
  `{stage, audit_id, skill, status?}` with `skill` the bare producer skill name. Audit ids are **copied
  verbatim producer-stamped provenance** — this tool never generates one, and an artifact id is distinct
  from the per-attempt audit id in `events.jsonl`.
- The Quality-Gate Board payload carries `expected_count: 12`, `evidence_count`, `missing_gates[]`,
  `evidence_complete`, and `worst_observed`. The roll-up shows an unqualified GREEN/AMBER/RED **only over
  complete evidence** (12 readable recognized verdicts); otherwise `INCOMPLETE` (or `PENDING` with no
  evidence at all). The board is **presentation-only** — it proves neither a release-blocking barrier nor
  production readiness.
- `produced_by` / `schemaVersion` come only from the S1b INDEX; `generated_from` is the run id (never an
  absolute workstation path). Determinism is defined over (normalized source bytes, options, template,
  renderer version).

Section `kind` to renderer to source is tabulated in `references/section-kinds.md`; unknown kinds fall
through to a generic collapsible tree.

## Procedure

1. **Locate the run directory.** Confirm the run folder the user means (the one holding per-stage
   subfolders such as `S1a-ba-discovery/`, `S1b-ba-brief/`, `S2-tl-design/`, and optionally `gates/`).
2. **Build.** With `SKILL_DIR` = the directory containing this `SKILL.md`:
   - `python3 "$SKILL_DIR/scripts/build_review_console.py" "$RUN_DIR" [-o OUT.html]`
   - `RUN_DIR` and the output path resolve from the current working directory. The script discovers the
     present stages, reads each stage's authoritative files, builds `window.PACK`, transcodes each
     `.drawio` to inline SVG, guards the output path, runs the offline self-check on the final HTML, and
     writes atomically.
   - Gate evidence precedence: canonical `gates/<file>` is authoritative; recursive filename discovery is
     a legacy fallback used only when the canonical file is absent and exactly one candidate exists —
     multiple candidates stop the build with an ambiguity diagnostic.
3. **Verify offline + deterministic.** Confirm exit 0, then:
   - Offline grep on the OUTPUT returns zero matches for
     `http://|https://|src=|@import|@font-face|url\(|<link|<img|<script src`.
   - Build twice to two paths and `diff` — byte-identical.
   - Optional: extract each inline `<script>` body and `node --check` it.
4. **Open for the human.** Offer to open the console — macOS `open OUT.html`. Only after the offline-clean
   check; if the user did not ask to open it, suggest the command rather than opening unprompted.
5. **Report.** State the output path, menus present vs pending, and the gate-board roll-up **including
   whether evidence is complete** (never report an INCOMPLETE board as green). Do not commit or move the
   file.

### Example: build the console for a full run

**User says**: "build the delivery review console for the ShopPilot run"

1. Confirm the run dir: `tmp/runs/shoppilot`.
2. `python3 "$SKILL_DIR/scripts/build_review_console.py" tmp/runs/shoppilot`
3. Confirm exit 0, offline-clean grep returns nothing, a second build diffs identical.
4. Report: `tmp/runs/shoppilot/delivery-review.html`, 12/12 menus present, gate rollup GREEN
   (evidence_complete: true). Offer `open tmp/runs/shoppilot/delivery-review.html`.

### Example: a run with partial gate evidence

**User says**: "render the review console for a run where only T1 has run"

1. `python3 "$SKILL_DIR/scripts/build_review_console.py" "$RUN_DIR"`
2. Report: gate rollup `INCOMPLETE` (evidence 1/12, missing gates listed); the one green cell renders,
   the others show "no evidence yet". Never summarize this run as green.

## Failure modes

| Condition | Behavior |
|---|---|
| Run dir missing | exit 2, nothing written |
| Output path unsafe (not `.html`, inside the skill dir, resolves to a consumed artifact, or existing non-console file) | exit 2, nothing written — the write would destroy an input |
| Ambiguous fallback gate evidence (duplicate filename, no canonical `gates/<file>`) | exit non-zero with a diagnostic naming the candidates — never a silent first-pick |
| Stage artifact absent / present-but-malformed | honest pending card with status `pending` / `unreadable-or-malformed`; never fabricated content |
| `.drawio` transcode failure | visible diagnostic card for that diagram; build continues |
| Forbidden token in the final HTML | build refuses to write (fail closed) |
| Suspected unredacted PII/secret in artifacts | STOP (agent-enforced precondition) — request a redacted copy |

## Constraints

- MUST ALWAYS be **offline**: the written HTML contains none of `http://`, `https://`, `src=`, `@import`,
  `@font-face`, `url(`, `<link`, `<img`, `<script src`. Data-borne URLs are sanitized to **bare host text**
  before baking. The script fails closed if any forbidden token survives.
- MUST ALWAYS treat the transcoder SVG as the **one** trusted-markup exception: only `diagram_svg.svg` is
  inserted via innerHTML; every other value goes through `esc()`. The SVG is re-asserted offline-clean
  before baking; a diagram whose SVG carries a forbidden token FAILS the build rather than ships.
- MUST ALWAYS be **deterministic**: no clock, no randomness, stable key ordering. Same (RUN_DIR bytes,
  options, template, renderer version) gives byte-identical HTML.
- MUST ALWAYS **degrade gracefully on partial input**: a missing stage, file, or field never throws — it
  renders as an honest pending/malformed card. Never fabricate stage content, and never let partial gate
  evidence roll up to an unqualified colour.
- MUST keep the `/* INJECT ... */` marker in the template and never place the comment-terminator sequence
  inside its body (it would close the comment early and break the console).
- DO NOT reimplement the `.drawio` to `<svg>` transcoder — import and call `drawio_to_svg.transcode()`.
- DO NOT add network features, analytics, web fonts, or external libraries (stdlib only).
- DO NOT modify, move, or reformat the run's input artifacts (read-only on the run).
- DO NOT write the console inside a skill folder or commit it; write it into the run dir or to `-o`.
- Validation checklist before finalizing: exit 0 + one HTML at the expected path; offline grep clean;
  re-build byte-identical; present menus render with badges and inline `<svg>` diagrams; pending/malformed
  stages show muted cards; the gate board reports evidence completeness honestly.

## References

- For the offline / determinism / injection contract and the full `window.PACK` shape (a generalization of
  the BA-research `viewer-rendering-spec.md`): see `references/console-rendering-spec.md`.
- For the `kind` to renderer to source table and the badge vocabulary (it points at the donor
  `rendering-contract-debug-viewer/references/contract-field-map.md` rather than duplicating it): see
  `references/section-kinds.md`.
