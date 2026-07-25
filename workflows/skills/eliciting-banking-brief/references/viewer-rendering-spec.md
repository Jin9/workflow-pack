# Viewer rendering spec (Step 13 — offline human-view)

Binding rules for emitting the S1 **human-view viewer** `ba-research-viewer.html`: one self-contained,
**offline** HTML file that renders the S1 four-layer pack (discovery → brief → epics → stories) for human
review. It is **presentation-only and re-derivable** — the JSON (`schemas/output.json`) stays authoritative on
any conflict, exactly like the Markdown tree (Step 12). Emission is **deterministic** (no `now()` / randomness):
the same assembled pack produces a byte-identical viewer, consistent with the skill's idempotency contract.

## Template

Inject into **`templates/ba-research-viewer.template.html`** (ships a small SAMPLE 2-epic / 3-story pack so the
template renders standalone). Do **not** hand-author the HTML/CSS/JS — reuse the template verbatim and replace
only the data object. The template is an **app-shell**: a left sidebar (brand · epic/story search · collapsible
nav-tree · legend · expand-all + light/dark toggle), a topbar breadcrumb + meta-pills, a reading-width content
column rendering the four layers, and a slide-in story reader. Light + dark themes; **system font stack only**.

## Injection contract

The template's data module is a single `<script>` whose body is:

```
/* INJECT  ...one-line note (this comment must NOT contain the sequence star-slash except its terminator)... */
window.PACK = { ...sample pack... };
```

Replace the object assigned to `window.PACK` with the **assembled four-layer pack** (below). Keep the leading
`/* INJECT ... */` marker comment; never place a `*/` inside its body (a stray terminator closes the comment early
and breaks the viewer — write `EPIC-(DOMAIN)`, not the literal epic-glob with a star). Do **not** pre-escape
strings: the template's render module HTML-escapes every value through `esc()` at render time; pre-escaping
double-encodes. The render module reads exactly four top-level keys — `meta`, `discovery`, `brief`, `pack` — and
guards missing fields, so partial packs degrade gracefully rather than throwing.

## Assembled pack shape

Build `window.PACK` deterministically from the artifacts of the S1 composite chain — nothing is invented here:

| Key | Source |
|---|---|
| `meta` | run header: `task_id`, `stage` (`S1`), `state`, `confidence`, `owner`, `produced_by`, `tier`, `audit_id`, `layers`, and an optional `project` label for the breadcrumb (falls back to `task_id`). |
| `discovery` | the upstream S1a artifact `discovery.json` (`researching-ba-problem-space`): `problem_framing`, `opportunities[]`, `assumptions[]`, `regulatory_regimes[]`, `recommendation`. Advisory provenance only. |
| `brief` | this skill's brief summary from `output.json`: `title`, `summary`, `scope_kind`, `status`, `ba_confidence`, `tier`, `blocks_tl_handoff`, `epic_ids`, `counts`, `regulatory`, `pii_fields`. |
| `pack` | the 3-level ref chain materialized: `count_check`, `governance_gaps[]`, `open_questions[]`, `epics[]` (each `EPIC-(DOMAIN).json`), and `stories{}` keyed by story id (each `STORY-(DOMAIN)-NN-(slug).json`). |

`count_check` ( `epics`, `stories`, `story_files`, `index_rows`, `discovery_present`, `brief_present`, `holds` )
must reflect the actual injected counts so the consistency badge reads true; on any FM-14 mismatch the JSON is
authoritative and the viewer badge must surface `holds: false` rather than be hand-corrected.

## Offline + safety invariants (re-check before writing the file)

- **Self-contained & offline:** no `http://` / `https://`, no `src=`, no CDN host, no `@import`, no `@font-face`,
  no `url(...)` font/asset reference. System font stack only — no embedded or linked webfonts. Web citations are
  bare host text. (Same rule as `squad-delivery-dashboard.standalone.html`.)
- **No `*/` inside the `/* INJECT ... */` body** (only its terminator).
- **`esc()` retained** in the render module; never strip it and never pre-escape the data.
- **Determinism:** identical assembled pack ⟹ byte-identical `ba-research-viewer.html`.
- **PII:** the pack carries no raw PII values (Step 4 redaction already applied upstream); never inject raw PII.

## Output

Write `ba-research-viewer.html` beside the brief artifacts (the run's `S1b-ba-brief/` folder). It carries
`meta.audit_id` for the audit trail and is the single human-view for all four layers. Relationship to Step 12:
both the Markdown tree and this viewer are derived presentation surfaces; neither is a contract.
