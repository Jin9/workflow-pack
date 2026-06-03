# The self-extracting `__bundler` bundle format

`squad-delivery-dashboard.standalone.html` is a single offline HTML file. Its assets live in
three `<script>` blocks the page's own JS reads at load time:

| Script tag | Holds |
|---|---|
| `<script type="__bundler/manifest">` | A one-line JSON object, keyed by UUID, of every asset: `{"mime", "compressed", "data"}` where `data` is base64 of (optionally gzipped) bytes. **No integrity hash.** |
| `<script type="__bundler/ext_resources">` | `[]` (unused). |
| `<script type="__bundler/template">` | The page HTML as a JSON string. |

## Manifest entries (17 total)

| UUID | What | Compressed |
|---|---|---|
| `c7f43bda-1a41-4a72-a2aa-5fac3269ac6d` | **DATA module** — the structures this skill owns | gzip |
| `c022aabb-11d4-4f03-81ec-4bab63460cb0` | RENDER module — DOM/render code (do not touch) | gzip |
| 15 others | woff2 fonts | no |

## The DATA module

Pure data plus a small merge tail. Top-level declarations, in this order:

```
const TIER       = {...};   // tier labels
const stages     = [...];   // RAW per-stage rows (the keys in dashboard-data.json)
const EVENTS     = {...};   // keyed by stage id: { consumes[], emits, sdlc }
const TEMPLATES  = {...};   // keyed by stage id: { p, f }
const JSON_ONLY  = new Set([...]);  // stage ids that are JSON-only
const tests      = [...];
const skillmap   = [...];
```

Then **3 merge statements** run at load time, folding the lookup tables INTO each stage:

```js
stages.forEach(s=>Object.assign(s, EVENTS[s.id]));
stages.forEach(s=>{ const t=TEMPLATES[s.id]; if(t){ s.template=t.p; s.fmt=t.f; } });
stages.forEach(s=>{ if(JSON_ONLY.has(s.id)) s.jsonOnly=true; });
```

So at runtime a stage carries the **derived** keys `consumes, emits, sdlc, template, fmt, jsonOnly`
on top of its raw fields. The RENDER module reads the enriched `stages` (plus `tests`, `skillmap`)
and merges by `s.id`.

### Why the contract stores RAW stages

`dashboard-data.json` keeps stages raw and the lookup tables (`events`, `templates`, `json_only`)
separate — each datum lives in exactly one place. `extract.py` strips the derived keys back off;
`build.py` re-emits the 3 merge statements verbatim (`MERGE_JS`). If the upstream merge logic ever
changes, update `MERGE_JS` in `build.py` to match.

## Editing safely

- Edit `dashboard-data.json`, never the base64. Then `build.py` validates and regenerates.
- `build.py` re-gzips with **mtime=0, level 9** (byte-deterministic) and **splices only** the
  `c7f43bda` `data` value — every other entry (render + 15 fonts) stays byte-identical.
- There is **no checksum** to recompute (manifest entries carry none).
- The original DATA module was hand-formatted; the first `build.py` run re-encodes it with
  `json.dumps` formatting. This is a one-time canonicalization with **zero data/render change**
  (proven by deep-equality of the post-merge structures); every subsequent no-op rebuild is
  byte-identical.

## Verifying an edit

1. `build.py --check` — schema + cross-reference + offline gates, no write.
2. `build.py` — regenerate the bundle.
3. `node --check` on the decoded DATA module (syntax).
4. `extract.py` again → diff against `dashboard-data.json` (lossless round-trip).
5. Confirm only `c7f43bda` changed in the manifest; open the HTML offline to eyeball the render.
