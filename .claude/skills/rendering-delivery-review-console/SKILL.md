---
name: rendering-delivery-review-console
description: >
  Assemble one run-scoped, offline, byte-deterministic delivery-review.html "Delivery Review Console"
  from a pipeline run directory: a single standalone document whose left-nav menus are pipeline stages
  (Epics and Stories, UX Brief, Design and ADRs, Plan Review, Quality), superseding the per-stage viewers.
  Diagrams embed as offline inline SVG via the deterministic drawio transcoder plus a path chip, and the
  twelve test gates roll into a Quality-Gate Board with a worst-of R/A/G roll-up. Use when the user asks
  to "build the delivery review console for this run", "render the whole run folder into one offline review
  page", "give me one review surface for all stages", or "roll the test gates into a quality board". Do NOT
  use to render one single JSON contract for debug (that is rendering-contract-debug-viewer), to author
  pipeline stage skills under workflows/skills, or to edit the squad-delivery dashboard data or bundle
  (that is roundtripping-dashboard-data-contract).
compatibility: claude-code, codex, opencode; requires python3 (stdlib only) and node only for the optional JS self-check
metadata:
  author: workflow-pack
  version: 1.0.0
---

# Rendering Delivery Review Console

## Purpose

Assemble one **run-scoped**, **offline**, **byte-deterministic** `delivery-review.html` — the **Delivery
Review Console** — from a pipeline run directory. Its left-nav menus are **pipeline stages** (menu1 Epics
and Stories, menu2 UX Brief, menu3 Design and ADRs, menu4 Plan Review, menu7 Quality, plus pending stubs),
so a reviewer reads every stage's work in one place instead of opening a viewer per stage. It supersedes
the per-stage viewers for review.

Diagrams are embedded as **offline inline SVG** (produced by the deterministic `.drawio` to `<svg>`
transcoder) plus a relative-path chip. The 12 test and security gates (T1 to T12) roll into a
**Quality-Gate Board** with a **worst-of R/A/G** roll-up. The render is delegated to a stdlib-only script;
the agent locates the run dir, runs it, and verifies offline + determinism. The JSON contract stays
authoritative on any conflict — the console is **review tooling, never pipeline operation**.

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

## Core workflow

1. **Locate the run directory.** Confirm the run folder the user means (the one holding per-stage
   subfolders such as `S1a-ba-discovery/`, `S1b-ba-brief/`, `S1.5-ux-intake/`, `S2-tl-design/`,
   `S2.5-plan-review/`, and optionally a `gates/` dir).
   - Input: a path to one run directory. Output of this step: a confirmed run-dir path.
2. **Build.** Run the script:
   - `python3 scripts/build_review_console.py RUN_DIR [-o OUT.html]`
   - Default output: `RUN_DIR/delivery-review.html`. The script discovers the present stages, reads each
     stage's authoritative files, builds `window.PACK`, transcodes each `.drawio` to inline SVG, runs the
     offline and determinism self-checks, and writes the one HTML file. Missing stages render as muted
     "pending" cards; they never crash the build.
3. **Verify offline + deterministic.** Confirm the script exited 0, then:
   - Offline grep on the OUTPUT returns zero matches for
     `http://|https://|src=|@import|@font-face|url\(|<link|<img|<script src`.
   - Build twice to two paths and `diff` — byte-identical (same RUN_DIR gives the same HTML).
   - Optional: extract each inline `<script>` body and `node --check` it (no syntax errors).
4. **Open for the human.** Offer to open the console — macOS `open OUT.html`. Only after the offline-clean
   check; if the user did not ask to open it, suggest the command rather than opening unprompted.
5. **Report.** State the output path, how many menus are present versus pending, and the gate-board roll-up.
   Do not commit or move the file.

## Output format

One self-contained HTML file (default `RUN_DIR/delivery-review.html`). It loads no external resources: CSS
and JS are inline, the assembled `window.PACK` is baked in as escaped data, fonts are a system stack, and
each diagram is an offline inline `<svg>`. It has a sidebar (brand, search, stage nav-tree with gate dots,
legend, expand-all, light/dark toggle), a topbar breadcrumb + meta pills, an Overview menu (gate ledger +
audit index), one section per present stage menu, muted pending cards for stub stages, the Quality-Gate
Board, and a slide-in reader for stories and gate drill-downs.

```
RUN_DIR/delivery-review.html        # the only artifact; self-contained and offline
```

The `window.PACK` contract is additive — absent stages omit their sections, never crash:

```
{ run: { run_id, project, stage_span, produced_by, schemaVersion, generated_from, audit_index[], gate_ledger[] },
  menus: [ { id, label, stage, order, present } ],
  sections: [ { id, menu, sub_of?, title, kind, status?, tier?, verdict?, audit_id?, source_path, payload } ] }
```

Section `kind` to renderer to source is tabulated in `references/section-kinds.md`. Each unknown `kind`
falls through to a generic collapsible tree.

## Constraints & anti-patterns

- MUST ALWAYS be **offline**: the written HTML contains none of `http://`, `https://`, `src=`, `@import`,
  `@font-face`, `url(`, `<link`, `<img`, `<script src`. Data-borne URLs are sanitized to **bare host text**
  (the `bare_host()` sanitizer strips the scheme) before baking. The script fails closed (refuses to write)
  if any forbidden token survives.
- MUST ALWAYS treat the transcoder SVG as the **one** trusted-markup exception: only `diagram_svg.svg` is
  inserted via innerHTML; every other value goes through `esc()`. The SVG is re-asserted offline-clean
  before baking, and a diagram whose SVG ever carries a forbidden token FAILS the build rather than ships.
- MUST ALWAYS be **deterministic**: no clock, no randomness, stable key ordering (dict keys sorted, list
  read-order preserved). Same RUN_DIR gives byte-identical HTML on re-run.
- MUST ALWAYS **degrade gracefully on partial input**: a missing stage, file, or field never throws — the
  section is omitted or rendered as a muted "pending — not yet produced" card. Never fabricate stage content.
- MUST keep the `/* INJECT ... */` marker in the template and never place the comment-terminator sequence
  inside its body (it would close the comment early and break the console).
- DO NOT reimplement the `.drawio` to `<svg>` transcoder — import and call `drawio_to_svg.transcode()`.
- DO NOT add network features, analytics, web fonts, or external libraries (stdlib only).
- DO NOT modify, move, or reformat the run's input artifacts (read-only on the run).
- DO NOT write the console inside a skill folder or commit it; write it into the run dir or to `-o`.

## Examples

### Example 1: build the console for a full run

**User says**: "build the delivery review console for the ShopPilot run"

**Action**:
1. Confirm the run dir: `tmp/runs/shoppilot`.
2. `python3 scripts/build_review_console.py tmp/runs/shoppilot`
3. Confirm exit 0, offline-clean grep returns nothing, and a second build diffs identical.

**Result**: `tmp/runs/shoppilot/delivery-review.html` — left-nav menus for Epics and Stories, UX Brief,
Design and ADRs, Plan Review (all present), the architecture and ERD diagrams embedded as inline SVG, the
seven not-yet-run stages as muted pending cards, and a Quality-Gate Board showing the honest "pending — no
gate evidence yet" empty state. Offer to open it (`open tmp/runs/shoppilot/delivery-review.html`).

### Example 2: a run that has gate evidence

**User says**: "render the review console for a run that has the test gates"

**Action**:
1. `python3 scripts/build_review_console.py RUN_DIR`
2. Verify and report the gate-board roll-up.

**Result**: the Quality-Gate Board shows a grid of 12 cells with a worst-of roll-up (any RED gives RED,
else any AMBER gives AMBER, else GREEN). Each gate's verdict maps through its own `verdict_map` — T10
`pass|conditional|fail` to G|A|R, T12 `promote|hold|rollback` to G|A|R, all others `PASS|FAIL|ERROR` to
G|R|R — and each cell drills into its baked JSON in the slide-in reader.

## Validation checklist

Before finalizing, verify:
- [ ] The script exits 0 and writes exactly one HTML file at the expected path.
- [ ] Offline grep on the OUTPUT returns zero matches for the forbidden tokens; data-borne URLs appear only
      as bare host text.
- [ ] Building the same RUN_DIR twice yields byte-identical HTML (determinism).
- [ ] Each inline `<script>` body passes `node --check` (or, if node is unavailable, a brace/paren balance
      sanity holds and the reused template JS is unchanged from the base where reused).
- [ ] The present-stage menus render (Epics, UX, Design, Plan Review), diagrams appear as inline `<svg>`
      with path chips, the recommendation and verdict badges show, and stub stages render as muted pending
      entries.
- [ ] The Quality-Gate Board rolls up worst-of R/A/G when gate evidence exists, and shows the honest
      "pending — no gate evidence yet" empty state when it does not.

## References

- For the offline / determinism / injection contract and the full `window.PACK` shape (a generalization of
  the BA-research `viewer-rendering-spec.md`): see `references/console-rendering-spec.md`.
- For the `kind` to renderer to source table and the badge vocabulary (it points at the donor
  `rendering-contract-debug-viewer/references/contract-field-map.md` rather than duplicating it): see
  `references/section-kinds.md`.
