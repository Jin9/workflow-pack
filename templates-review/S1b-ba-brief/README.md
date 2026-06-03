# S1b · BA Brief — four-layer epic & story PACK

The **second half** of the S1 composite. On a **`proceed`** decision from
[`S1a · BA Discovery`](../S1a-ba-discovery/), `eliciting-banking-brief ^1.5.0` turns the requirement into a
**four-layer pack** — discovery (Layer 0, carried from S1a) · brief (Layer 1) · epics (Layer 2) · stories
(Layer 3) — with **stories nested under their epic**, a lightweight JSON manifest for the machine handoff, and
**one self-contained HTML viewer for humans**.

## Inputs
- **`raw_request`** + intake's `normalized_request`.
- **`discovery` (advisory, optional)** — the `handoff_to_intake` block from S1a (`researching-ba-problem-space
  ^1.0.0`). v1.5.0 may use it to **seed** (regimes → pending-citation rows, stakeholder hints, a tier **floor**)
  but **never** to suppress a detector, lower a tier, or satisfy a citation. Idempotency keys on
  `(raw_content, discovery)`; an **absent `discovery` is byte-identical to v1.4.x**.

## Dual output
- **Machine handoff → next node (S2 TL):** a **ref chain** — `INDEX.json` (the manifest, validated by
  [`../../schemas/ba-brief.json`](../../schemas/ba-brief.json)) links the **discovery + brief layers**
  (`discovery_file` · `brief_file` · `layers{}`) and lists the epics + per-story **file refs**; each
  **`EPIC-<DOMAIN>.json`** holds epic metadata + its **story refs** (`story_refs[]`); each story is its own
  **`STORY-<DOMAIN>-NN-<slug>.json`** file. **Nothing is inlined.** A downstream node reads the manifest and loads
  **only the files it needs** — never one giant JSON (context-window efficient).
- **Human view:** **`ba-research-viewer.html`** — a self-contained, **offline** page (no network) that renders
  **all four layers**: Layer 0 discovery (framing · 4 product risks · regimes · recommendation), Layer 1 brief,
  then collapsible **epics → their story files** (card · Gherkin AC · banking-grade concerns · DoR), governance
  gaps, open questions, count-check, sign-off. HTML, not Markdown — for visualization.

## Run-output layout
```
S1b-ba-brief/
  INDEX.json                       # the manifest (= ba-brief.json content) — links discovery_file + brief_file + layers{}
  brief.json                       # Layer 1 — the boundary brief (initiative · scope · governance · PII inventory)
  ba-research-viewer.html          # human view — all four layers (PACK injected by the deterministic render)
  EPIC-<DOMAIN>/                    # one folder per epic (a requirement may split into many epics)
    EPIC-<DOMAIN>.json              # epic data — metadata + story_refs[] (NO inline story bodies)
    STORY-<DOMAIN>-01-<slug>.json   # story data, STORY- prefix, under its epic
    STORY-<DOMAIN>-02-<slug>.json
# Layer 0 discovery lives next door at ../S1a-ba-discovery/discovery.json (INDEX.discovery_file points at it).
```

## Templates in this pack
| File | Role |
|---|---|
| `INDEX.template.json` | the manifest/catalog: envelope · `discovery_file` · `brief_file` · `layers{}` · `epics[]` · `story_files[]` · `governance_gaps[]` · `open_questions[]` (`OQ-n`) · `count_check` · `viewer_file` |
| `epic.template.json` | per-epic data contract (mirrors `eliciting-banking-brief` Epic) — epic metadata + `story_refs[]` (refs to its `STORY-*` files; **no inline story bodies**) |
| `story.template.json` | per-story data contract (`STORY-*`; mirrors the Story schema) |
| `ba-research-viewer.html` | the offline HTML human-view; renders the **four discrete layers** (ships sample discovery + brief + epics/stories; the `INJECT` marker shows where the render replaces `PACK`) |

> Layer 0 discovery has no template here — its contract is
> [`../S1a-ba-discovery/discovery.template.json`](../S1a-ba-discovery/discovery.template.json).

## Conventions (reused from the archived `business-analyse` + squad-flow-v0.7)
- **IDs:** epic `^EPIC-[A-Z0-9-]+$` (e.g. `EPIC-AUTH`); story `^STORY-[A-Z0-9-]+-\d+$` (e.g. `STORY-AUTH-01`), dense within its epic; a story traces to its epic via `epic_id` (shared `<DOMAIN>` segment).
- **Slug:** deterministic pure function of (id, title) — lowercase, punctuation dropped, spaces→`-`, ASCII, ≤8 words. **No `now()` / randomness** — same input ⇒ byte-identical filenames.
- **`OQ-n`** open-question IDs are stable from S1 through S5 — never renumbered or invented downstream.
- **Count-check invariant:** `epics`, `stories`, `story_files`, and INDEX rows must agree (`count_check.holds=true`).
- **Exactly-one-writer** per file; **status + change_log** per epic/story (accepted records are immutable — supersede, don't edit).
- **Traceability:** requirement → epic → story → AC → (downstream) test, via stable IDs + `requirement_refs`.

## Reuse — do NOT duplicate
- The canonical per-story field set lives in the **archived** `business-analyse/.../drafting-ba-stories/templates/user-story-template.md` (sibling `../archive/`, bilingual EN/TH, **byte-identical invariant**) — reference it via the live skill `eliciting-banking-brief`, never copy it here.
- The authoritative machine schema is `workflows/skills/eliciting-banking-brief/schemas/output.json`; `../../schemas/ba-brief.json` is the permissive pipeline boundary.
- No real PII — redact to `<PII:REDACTED:CLASS=…>`.

## Producer / status
`eliciting-banking-brief ^1.5.0` emits the rich JSON; a **deterministic render** (the `render_markdown_tree.py`
pattern from the archived `business-analyse`) emits this pack + the viewer. **Wired live in
`workflows/delivery-pipeline.yaml`** as node `ba-research` (GAP-05 **closed**). Residual: `render_ba_pack.py` does
not yet emit the four-layer pack + unified viewer natively.

## Roadmap — HTML human-view standard
This pack establishes the **HTML-viewer human-view** (offline, self-contained, renders the JSON pack). It is the
**new standard**; the review / evidence / maturity stages (S1.5 · S2.5 · S4a-r · S4b-r · S4c · S5 · S7) — currently
Markdown templates — **migrate to HTML viewers next**.
