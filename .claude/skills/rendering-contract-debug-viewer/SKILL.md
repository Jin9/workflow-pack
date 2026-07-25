---
name: rendering-contract-debug-viewer
version: 1.1.0
description: >
  Render one pipeline JSON contract artifact into a single self-contained, offline HTML viewer styled in
  the squad-delivery dashboard theme (light plus dark), for local debugging and inspection. Use when the
  user asks to "visualize this JSON contract", "render output.json as a readable offline viewer", "make a
  debug viewer for this pipeline artifact", or "open this discovery, INDEX, or plan-review JSON in the
  dashboard theme". Contract-aware: highlights audit_id, output_type, status, verdict, recommendation,
  severity, priority, tier, maturity, findings, governance gaps and processing metadata, and degrades to
  a generic collapsible tree on any JSON. Do NOT use to review a whole run folder as one surface (use
  rendering-delivery-review-console), to edit the dashboard's own data or bundle (use
  roundtripping-dashboard-data-contract), to author pipeline stage skills under workflows/skills, or to
  generate the JSON contract itself.
compatibility: claude-code, codex, opencode; requires python3 (stdlib only)
---

# Rendering Contract Debug Viewer

## Purpose

Turn one pipeline JSON **contract** artifact into a single self-contained, **offline** HTML viewer —
themed like `squad-delivery-dashboard.standalone.html` — so a human can read and debug it quickly. The
render is deterministic and delegated to a script; the agent locates the input, runs it, and verifies.
The viewer is built for human readability: summary-first, deep nesting collapsed by default, a one-click
**View normalized JSON** panel, and it can be opened straight in the browser — so a human reads a dense
contract without scanning raw JSON.

## When to use this skill

- Use when: the user asks to "visualize this JSON contract" or "open this JSON in the dashboard theme".
- Use when: the user asks to "render output.json as a readable offline viewer" for inspection or debug.
- Use when: the user asks to "make a debug viewer for this pipeline artifact" (discovery, INDEX, ux/tl
  `output.json`, `plan-review.json`, a boundary schema, or any JSON).
- Use when: a human needs to read or inspect a dense, deeply-nested, or unfamiliar JSON contract and the
  raw file is hard to scan — **proactively suggest** rendering it instead of pasting raw JSON.
- Do NOT use when: the goal is one review surface for a whole run folder — that is
  `rendering-delivery-review-console`. This skill renders **one** artifact; a directory is only a
  discovery aid once the user has identified which stage/artifact they mean.
- Do NOT use when: the goal is to edit the dashboard's own data/bundle — use
  `roundtripping-dashboard-data-contract`.
- Do NOT use when: the goal is to author a pipeline stage skill (those live under `workflows/skills`), or
  to **produce** the JSON contract itself (a stage skill does that). This skill only renders existing JSON.

## Input contract

This is a tooling skill: there is **no skill schema** (`schemas/` is absent by design), it performs no
pipeline or boundary-schema validation, and no `idempotency_key` is injected — the contract below is
prose, enforced by the script's exit codes.

- **Required:** the path to **one existing, readable, UTF-8, strict-JSON file** (the contract artifact).
  Strict means: no duplicate object keys, no `NaN`/`Infinity` constants — the script rejects both
  (exit 2) rather than silently normalizing them.
- **Optional:** `-o OUT.html` output path (default: input path with a `.viewer.html` suffix);
  `--title TITLE` header title (default: input filename); `--theme auto|light|dark` (default `auto`).
- **Precondition — sensitivity:** the source JSON must already be free of unredacted PII and secrets
  (workspace redaction rule). The viewer embeds **every** value, so the generated HTML inherits the
  source's full sensitivity. If unredacted PII or a secret is suspected, STOP and ask for a redacted
  copy — never mutate the source.
- **Stop conditions:** the path is missing/unreadable/not valid strict JSON; the output path resolves to
  the input file (exit 2 — the write would destroy the contract); the user pointed at a directory and
  zero or more than one candidate JSON file remains after they identify the stage/artifact — stop and
  ask, never pick one silently.

## Output contract

Exactly **one** self-contained HTML file (default `INPUT.viewer.html`, or the `-o` path) plus one
diagnostic line on stdout (`wrote OUT (N bytes) from INPUT`). Nothing else is created, moved, or edited;
the input is read-only.

- Offline: CSS/JS inline, JSON baked in as escaped data, system font stack, no external references.
  Forbidden lexemes (`http(s)://`, `src=`, `@import`) inside data values are neutralized with equivalent
  Unicode escapes, so the **saved bytes** pass an offline token scan while rendering identically.
- Deterministic: byte-identical output for identical (input bytes, input basename, title, theme,
  renderer version). Browser-local theme preference affects presentation only, never the saved file.
- Header shows the detected kind + top-level `audit_id` chip and a summary chip row; deep nesting is
  collapsed by default. The `audit_id` chip is reserved for **top-level** `data.audit_id` (the artifact's
  provenance id); a `processing_metadata.audit_id` stays visible at its own path — the viewer never
  creates, validates, or equates audit ids (an artifact id is distinct from an engine attempt id in
  `events.jsonl`).
- **View normalized JSON** shows a parse-and-reserialize of the input (key order/number formatting
  normalized) — it is not the original bytes.

## Procedure

1. **Locate the input JSON.** Confirm the exact file the user means (one file per run). If they name a
   stage/run folder, have them identify the stage/artifact, then use the directory only to find that one
   file (e.g. `output.json`, `INDEX.json`, `plan-review.json`); zero or multiple candidates → stop and ask.
2. **Render.** With `SKILL_DIR` = the directory containing this `SKILL.md`:
   - `python3 "$SKILL_DIR/scripts/render_contract_viewer.py" INPUT.json [-o OUT.html] [--title TITLE] [--theme auto|light|dark]`
   - Input/output paths resolve from the current working directory (repo root in examples below).
   - Theme precedence: explicit `light`/`dark` overrides any stored browser preference; `auto` follows a
     stored viewer preference when present, else the OS `prefers-color-scheme`.
3. **Verify offline + readable.** Confirm the script exited 0. The script itself scans the **final
   assembled HTML** for forbidden tokens before writing (exit 3 on violation) and writes via a temporary
   sibling + atomic replace, so a failed run never truncates an existing viewer.
4. **Open for the human.** Offer to open the viewer in the default browser — macOS `open OUT.html`,
   Linux `xdg-open OUT.html`, Windows `start OUT.html`. If the user did not ask to open it, suggest the
   command rather than opening unprompted.
5. **Report.** State the output path and the detected contract kind, and point the human at the in-page
   controls — "View normalized JSON", the theme toggle, and expand/collapse-all. Do not commit or move
   the file.

### Example: debug a review verdict

**User says**: "make a debug viewer for the plan-review output"

1. Confirm the file: `tmp/runs/shoppilot/S2.5-plan-review/plan-review.json`.
2. `python3 "$SKILL_DIR/scripts/render_contract_viewer.py" tmp/runs/shoppilot/S2.5-plan-review/plan-review.json`
3. Confirm exit 0; report `plan-review.viewer.html` — kind `plan-review` + `audit_id` in the header,
   `verdict: PROCEED` as a green badge, per-finding `severity` dots. Offer
   `open tmp/runs/shoppilot/S2.5-plan-review/plan-review.viewer.html`.

### Example: inspect a tech-lead design contract in dark mode

**User says**: "open the S2 output.json in the dashboard theme, dark"

1. `python3 "$SKILL_DIR/scripts/render_contract_viewer.py" tmp/runs/shoppilot/S2-tl-design/output.json --theme dark`
2. Verify exit 0 and report the path — opens dark (forced; stored preference ignored), `output_type:
   design` badged, `component_map`/`api_contracts`/`adrs` collapsible, `*_path` values as monospace chips.

## Failure modes

| Exit | Meaning | Action |
|------|---------|--------|
| 2 | Input missing/unreadable, not strict JSON (duplicate keys, `NaN`/`Infinity`, parse error), or output path resolves to the input file | Fix the path or obtain a valid contract; never edit the input to "make it parse". |
| 3 | The **final saved HTML** would violate the offline contract (forbidden token survived assembly, e.g. via a pathological filename in the source label) | Rename the offending file/title; the script refuses to write. |
| 4 | Output not writable (permissions, missing directory) | The temporary sibling is cleaned up; no partial/truncated viewer is left behind. |

Suspected unredacted PII/secret in the source is a STOP (ask for a redacted copy), not an exit code —
the script cannot classify PII; the agent enforces this precondition.

## Constraints

- MUST ALWAYS keep the viewer offline: no `http(s)`, no `src=`, no `@import`, no CDN, no web fonts. The
  script fails closed (exit 3) scanning the final assembled document — data included, not just the shell.
- MUST ALWAYS render data values as escaped text — never as markup or a clickable/auto-loading URL.
- MUST ALWAYS be deterministic: no timestamps, clock, or randomness — same (input bytes, basename, title,
  theme, renderer version) produces byte-identical HTML; the normalized-JSON panel is produced in-browser
  so the saved file stays byte-identical.
- MUST ALWAYS keep the human view simple and scannable: summary-first header, deep nesting collapsed by
  default — never present the whole tree fully expanded.
- DO NOT modify, move, or reformat the input JSON (read-only on the input; output==input is exit 2).
- DO NOT write the viewer inside a skill folder or commit it; write it next to the input or to `-o`.
- DO NOT add network features, analytics, or external libraries to the renderer (stdlib only).
- Validation checklist before finalizing: exit 0 + exactly one HTML at the expected path; re-render is
  byte-identical; header shows kind + top-level `audit_id`; unknown JSON still renders as a generic tree.

## References

- For the baked theme palette (light and dark CSS variables, tier/status/severity/gate colors, fonts):
  see `references/theme-tokens.md`.
- For the recurring contract fields, their value vocabularies, and color mapping (extend the classifier
  here): see `references/contract-field-map.md`.
