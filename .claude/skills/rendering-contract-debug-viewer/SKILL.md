---
name: rendering-contract-debug-viewer
description: >
  Render one pipeline JSON contract artifact into a single self-contained, offline HTML viewer styled in
  the squad-delivery dashboard theme (light plus dark), for local debugging and inspection. Use when the
  user asks to "visualize this JSON contract", "render output.json as a readable offline viewer", "make a
  debug viewer for this pipeline artifact or run folder", or "open this discovery, INDEX, or plan-review
  JSON in the dashboard theme". Contract-aware: highlights audit_id, output_type, status, verdict,
  recommendation, severity, priority, tier, maturity, findings, governance gaps and processing metadata,
  and degrades to a generic collapsible tree on any JSON. Do NOT use to edit the dashboard's own data or
  bundle (use roundtripping-dashboard-data-contract), to author pipeline stage skills under
  workflows/skills, or to generate the JSON contract itself.
compatibility: claude-code, codex, opencode; requires python3 (stdlib only)
metadata:
  author: workflow-pack
  version: 1.0.0
---

# Rendering Contract Debug Viewer

## Purpose

Turn one pipeline JSON **contract** artifact into a single self-contained, **offline** HTML viewer —
themed like `squad-delivery-dashboard.standalone.html` — so a human can read and debug it quickly. The
render is deterministic and delegated to a script; the agent locates the input, runs it, and verifies.
The viewer is built for human readability: summary-first, deep nesting collapsed by default, a one-click
pretty-printed **View source**, and it can be opened straight in the browser — so a human reads a dense
contract without scanning raw JSON.

## When to use this skill

- Use when: the user asks to "visualize this JSON contract" or "open this JSON in the dashboard theme".
- Use when: the user asks to "render output.json as a readable offline viewer" for inspection or debug.
- Use when: the user asks to "make a debug viewer for this pipeline artifact" (discovery, INDEX, ux/tl
  `output.json`, `plan-review.json`, a boundary schema, or any JSON).
- Use when: a human needs to read or inspect a dense, deeply-nested, or unfamiliar JSON contract and the
  raw file is hard to scan — **proactively suggest** rendering it instead of pasting raw JSON.
- Do NOT use when: the goal is to edit the dashboard's own data/bundle — use
  `roundtripping-dashboard-data-contract`.
- Do NOT use when: the goal is to author a pipeline stage skill (those live under `workflows/skills`), or
  to **produce** the JSON contract itself (a stage skill does that). This skill only renders existing JSON.

## Core workflow

1. **Locate the input JSON.** Confirm the exact file the user means (one file per run). If they name a
   stage/run folder, pick the contract file in it (e.g. `output.json`, `INDEX.json`, `plan-review.json`).
   - Input: a path to one JSON file. Output of this step: a confirmed input path.
2. **Render.** Run the script:
   - `python3 scripts/render_contract_viewer.py INPUT.json [-o OUT.html] [--title TITLE] [--theme auto|light|dark]`
   - Default output: the input path with a `.viewer.html` suffix (e.g. `output.json` produces
     `output.viewer.html`) next to the input. Default theme `auto` (follows the OS, with an in-page toggle).
   - The script reads the file, bakes the JSON inline, and writes one HTML file. It exits non-zero on
     invalid JSON (2), a forbidden external reference in the authored shell (3), or a write error (4).
3. **Verify offline + readable.** Confirm the script exited 0, then check the output is offline-clean
   (the authored markup contains no `http`/`src=`/`@import`; data values are escaped text).
4. **Open for the human.** Offer to open the viewer in the default browser so it can be read immediately —
   macOS `open OUT.html`, Linux `xdg-open OUT.html`, Windows `start OUT.html`. Only after the offline-clean
   check; if the user did not ask to open it, suggest the command rather than opening unprompted.
5. **Report.** State the output path and the detected contract kind, and point the human at the in-page
   controls — "View source" for the pretty-printed JSON, the theme toggle, and expand/collapse-all. Do not
   commit or move the file.

## Output format

One self-contained HTML file (default `INPUT.viewer.html`, or the `-o` path). It loads no external
resources: CSS and JS are inline, the JSON is baked in as escaped data, fonts are a system stack. It has
a light and a dark theme (toggle + OS-auto), a header showing the detected kind and `audit_id`, a summary
chip row, and a collapsible tree. Contract-aware fields are color-coded (see
`references/contract-field-map.md`); the palette mirrors the dashboard (see `references/theme-tokens.md`).

Readability defaults keep it scannable: the header is **summary-first** (kind + `audit_id` + key chips),
deep nesting is **collapsed by default** (with expand/collapse-all), and a one-click **View source** shows
the pretty-printed JSON for when the raw shape is needed.

```
INPUT.viewer.html        # the only artifact; self-contained and offline
```

## Constraints & anti-patterns

- MUST ALWAYS keep the viewer offline: no `http(s)`, no `src=`, no `@import`, no CDN, no web fonts. The
  script fails closed (exit 3) if its authored shell breaks this.
- MUST ALWAYS render data values as escaped text — never as markup or as a clickable/auto-loading URL.
- MUST ALWAYS be deterministic: no timestamps, clock, or randomness — same JSON in produces the same HTML
  out (the header uses the filename and `audit_id`, not a render time; the View-source panel is produced
  in-browser, so the saved file stays byte-identical).
- MUST ALWAYS keep the human view simple and scannable: summary-first header, deep nesting collapsed by
  default, and a one-click pretty-printed view-source — never present the whole tree fully expanded.
- DO NOT modify, move, or reformat the input JSON (read-only on the input).
- DO NOT write the viewer inside a skill folder or commit it; write it next to the input or to `-o`.
- DO NOT add network features, analytics, or external libraries to the renderer (stdlib only).

## Examples

### Example 1: debug a review verdict

**User says**: "make a debug viewer for the plan-review output"

**Action**:
1. Confirm the file: `tmp/runs/shoppilot/S2.5-plan-review/plan-review.json`.
2. `python3 scripts/render_contract_viewer.py tmp/runs/shoppilot/S2.5-plan-review/plan-review.json`
3. Confirm exit 0 and offline-clean.

**Result**: `tmp/runs/shoppilot/S2.5-plan-review/plan-review.viewer.html` — header shows kind `plan-review`
+ `audit_id`; `verdict: PROCEED` renders as a green badge; each finding's `severity` shows a colored dot.
Offer to open it (`open tmp/runs/shoppilot/S2.5-plan-review/plan-review.viewer.html`); "View source" shows
the pretty-printed JSON.

### Example 2: inspect a tech-lead design contract in dark mode

**User says**: "open the S2 output.json in the dashboard theme, dark"

**Action**:
1. `python3 scripts/render_contract_viewer.py tmp/runs/shoppilot/S2-tl-design/output.json --theme dark`
2. Verify and report the path.

**Result**: `tmp/runs/shoppilot/S2-tl-design/output.viewer.html` opens dark by default; `output_type:
design` is a badge, `component_map`/`api_contracts`/`adrs` are collapsible groups, `*_path` values are
monospace chips.

## Validation checklist

Before finalizing, verify:
- [ ] The script exits 0 and writes exactly one HTML file at the expected path.
- [ ] The output markup is offline-clean (no `http(s)`/`src=`/`@import`); data-borne URLs appear only as
      escaped text.
- [ ] Rendering the same input twice yields byte-identical HTML (determinism).
- [ ] The header shows the detected kind and `audit_id`; known fields are color-coded; unknown JSON still
      renders as a generic tree.
- [ ] The viewer offers a readable pretty-printed "View source" toggle and can be opened in a browser.

## References

- For the baked theme palette (light and dark CSS variables, tier/status/severity/gate colors, fonts):
  see `references/theme-tokens.md`.
- For the recurring contract fields, their value vocabularies, and color mapping (extend the classifier
  here): see `references/contract-field-map.md`.
