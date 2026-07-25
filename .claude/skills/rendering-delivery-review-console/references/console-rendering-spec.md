# Console rendering spec (offline / determinism / injection contract)

Binding rules for assembling the **Delivery Review Console** `delivery-review.html`: one self-contained,
**offline** HTML file that renders a whole pipeline run (discovery, brief, epics and stories, UX pack,
design and ADRs, plan review, the Quality-Gate Board, and muted pending stubs) for human review. It is
**presentation-only and re-derivable** — the JSON contract stays authoritative on any conflict, exactly
like the BA-research viewer. Assembly is **deterministic** (no `now()` / randomness): the same run
directory produces a byte-identical console. This generalizes the single-stage `viewer-rendering-spec.md`
to a multi-stage, menu-per-stage console.

## Template

Assemble into **`templates/delivery-review.template.html`** (ships a small SAMPLE multi-stage PACK so the
template renders standalone). Do **not** hand-author the HTML/CSS/JS — reuse the template verbatim and
replace only the data object. The template is an **app-shell** generalized from the BA-research viewer: a
left sidebar (brand, menu/story search, collapsible stage nav-tree with gate dots, legend, expand-all +
light/dark toggle), a topbar breadcrumb + meta pills, a reading-width content column rendering an Overview
menu plus one section per stage menu, and a slide-in reader (stories and gate drill-downs). Light + dark
themes; **system font stack only**.

## Injection contract

The template's data module is a single `<script>` whose body is:

```
/* INJECT  ...one-line note (this comment must NOT contain the comment-terminator sequence except its own)... */
window.PACK = { ...sample pack... };
```

The build script (`scripts/build_review_console.py`) replaces the object assigned to `window.PACK` with the
**assembled run PACK** (below). Keep the leading `/* INJECT ... */` marker comment; never place a
comment-terminator sequence inside its body (a stray terminator closes the comment early and breaks the
console). Do **not** pre-escape strings: the render module HTML-escapes every value through `esc()` at
render time; pre-escaping double-encodes. The render module guards missing fields, so partial packs degrade
gracefully rather than throwing.

The script bakes the PACK with `json.dumps(pack, ensure_ascii=False, sort_keys=True)` and replaces `</`
with `<\/` so no sequence can break the surrounding `<script>` element. `sort_keys=True` (dicts) +
read-order (lists) gives stable, deterministic ordering.

## Assembled PACK shape

Build `window.PACK` deterministically from the run's per-stage artifacts — nothing is invented:

```jsonc
{
  "run": {
    "run_id", "project", "stage_span", "produced_by", "schemaVersion", "generated_from",
    "renderer": { "renderer_skill", "renderer_version", "pack_schema_version" },
    "audit_index": [ { "stage", "audit_id", "skill", "status"? } ],
    "gate_ledger": [ { "stage", "gate", "owner" } ]      // the L3 sync-named gates
  },
  "menus":    [ { "id", "label", "stage", "order", "present": true|false } ],
  "sections": [ { "id", "menu", "sub_of"?, "title", "kind",
                  "status"?, "tier"?, "verdict"?, "audit_id"?, "source_path", "payload" } ]
}
```

| Key | Source |
|---|---|
| `run` | run header: folder name as `run_id` (also `generated_from` — never an absolute workstation path); `project`/`produced_by`/`schemaVersion` from the S1b INDEX/brief ONLY; `renderer` = this tool's own envelope (skill name, version, pack schema version); `audit_index` built from the AUTHORITATIVE artifacts (stage outputs + gate evidence — ids copied verbatim, `skill` = bare producer skill name; section-envelope scan is only a fallback for unknown layouts; the renderer never generates an audit id, and an artifact id is not an `events.jsonl` attempt id); `gate_ledger` = the design's L3 sync-named gates (S2, S2.5, S4c, T10, S5, S6, S7). |
| `menus` | one per pipeline stage; `present:true` when its artifact exists, `present:false` for the README-only stub stages (S0, S3, S4, S5, S6, S7). `order` drives nav + page order. |
| `sections` | one per renderable artifact within a menu; `payload` carries only the fields the renderer reads. `source_path` is the relative artifact path shown as a chip. |

Section `kind` to renderer to source is tabulated in `section-kinds.md`. Absent stages contribute no
present menu (the stub stays `pending`); a present menu with no readable artifact also renders `pending`.

## Offline + safety invariants (re-check before writing the file)

- **Self-contained & offline:** the written HTML contains none of `http://`, `https://`, `src=`,
  `@import`, `@font-face`, `url(`, `<link`, `<img`, `<script src`. System font stack only — no embedded or
  linked webfonts. Web/data-borne URLs are sanitized to **bare host text** by `bare_host()` (the scheme is
  stripped) over every string value before baking. The script **fails closed** (refuses to write) if any
  forbidden token survives. (Same rule as `squad-delivery-dashboard.standalone.html`.)
- **Inline-SVG exception:** the diagram preview is the **one** trusted-markup field. The `.drawio` to
  `<svg>` transcoder (`drawio_to_svg.transcode()`) emits an offline-clean inline `<svg>` (no `xmlns` URI, no
  `src=`/`url(`/`<image>`). It is **re-asserted** offline-clean before baking; a diagram whose SVG carries a
  forbidden token **FAILS the build** rather than ship. The render module inserts `diagram_svg.svg` via
  innerHTML; **everything else** goes through `esc()`.
- **No comment-terminator inside the `/* INJECT ... */` body** (only its own terminator).
- **`esc()` retained** in the render module; never strip it and never pre-escape the data.
- **Determinism:** identical run directory implies byte-identical `delivery-review.html`. No clock, no
  randomness; `os.walk` results are sorted; dict keys baked sorted.
- **Graceful partial:** a missing stage/file/field never throws — the section is omitted or rendered
  `pending`. Never fabricate stage content.
- **PII:** the pack carries no raw PII values (redaction is applied upstream by the stage skills); never
  inject raw PII.

## Output

Write `delivery-review.html` into the run directory (default) or to `-o`. It carries `run.run_id` and the
per-stage `audit_index` for the audit trail and is the single human-view for the whole run. Relationship to
the per-stage viewers: this console **supersedes** them for review; `rendering-contract-debug-viewer`
remains for one-off single-file debug. Neither is a contract — both are re-derivable presentation surfaces.
