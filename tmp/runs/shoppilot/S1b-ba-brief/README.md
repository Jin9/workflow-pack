# S1b · BA Brief — brief + epics + stories (3-level ref chain)

> The second half of the S1 composite. It runs **only after** the [`../S1a-ba-discovery/`](../S1a-ba-discovery/)
> recommendation gate clears `proceed`. `eliciting-banking-brief` takes the discovery (advisory) and
> produces the boundary brief + a 3-level epic/story ref chain. Together with S1a this is the
> **four-layer pack** (discovery → brief → epics → stories), rendered for humans by one unified viewer.

| | |
|---|---|
| **Stage** | S1b · BA Brief |
| **Skill** | `eliciting-banking-brief 1.5.0` *(re-run/re-stamped 2026-06-04; output unchanged)* |
| **Owner** | BA lead |
| **Input** | `../S0-intake/ecommerce_mvp_business_only.gap-closed.md` + the discovery from `../S1a-ba-discovery/` (advisory) |
| **Output contract** | [`workflows/schemas/ba-brief.json`](../../../../workflows/schemas/ba-brief.json) (INDEX manifest → `EPIC-*` files → `STORY-*` files) |
| **YAML node** | `ba-research` in `workflows/delivery-pipeline.yaml` (id retained so S1.5 / S2 / S2.5 / S4c consume it unchanged) |
| **State** | `ready-for-tl` · confidence `high` · tier `T2` |
| **Human-view** | `ba-research-viewer.html` — one offline viewer, all four layers |

## The four-layer ref chain

`INDEX.json` is the manifest that ties the whole pack together; a downstream node reads it and loads **only the layers it needs**. Layer L0 lives in the sibling `../S1a-ba-discovery/` folder; L1–L3 live here.

| Layer | File(s) | Produced by | Role |
|---|---|---|---|
| **L0 · discovery** | `../S1a-ba-discovery/discovery.json` (+ `discovery-input.json`) | `researching-ba-problem-space 1.0.0` | problem framing · opportunities · the four product risks (value/usability/feasibility/viability) · regulatory regimes · `recommendation` |
| **L1 · brief** | `brief.json` | `eliciting-banking-brief 1.5.0` | the boundary brief (initiative, scope, governance, PII inventory, regulatory deps) |
| **L2 · epics** | `EPIC-<DOMAIN>/EPIC-<DOMAIN>.json` | ↳ + deterministic render | one epic file per epic, holding `story_refs[]` |
| **L3 · stories** | `EPIC-<DOMAIN>/STORY-<DOMAIN>-NN-<slug>.json` | ↳ + deterministic render | one file per story (card · Gherkin AC · banking-grade concerns · DoR) |

`INDEX.json` carries `discovery_file` (→ `../S1a-ba-discovery/`), `brief_file`, `viewer_file`, a `layers{}` descriptor, the `epics[]`/`story_files[]` rows, and a `count_check` (also `discovery_present` / `brief_present`). Counts: **4 epics · 8 stories**, `holds: true`.

## Files

```
INDEX.json              manifest tying all four layers (discovery_file → ../S1a-ba-discovery/)
brief.json              L1 boundary brief
EPIC-AUTH/ EPIC-CHECKOUT/ EPIC-ORDER/ EPIC-INVENTORY/   L2 epic files + L3 story files
ba-research-viewer.html one unified offline viewer: Discovery → Brief → Epics → Stories (data baked in)
README.md               this file
```

The L0 discovery layer (`discovery.json` + `discovery-input.json`) lives in [`../S1a-ba-discovery/`](../S1a-ba-discovery/). The unified viewer bakes all four layers inline, so it renders offline regardless of where the layer files sit.

## Caveats

- **Hand-applied extension — do not re-render blindly.** The `discovery`/`brief` manifest refs and this unified viewer are added by hand on top of `render_ba_pack.py`'s 3-level output. Re-running `render_ba_pack.py` would **overwrite** them (it rewrites `INDEX.json` + `ba-research-viewer.html` and deletes `EPIC-*`). Updating the renderer to emit the four-layer pack natively is the next (skills) phase.
- **S1 contract reconciled, and now split per stage.** `squad-delivery-dashboard.standalone.html` models S1 as the discovery→brief composite **as two cards** (`S1a · BA Discovery` → gate → `S1b · BA Brief`); this run folder mirrors that with two folders. The live `workflows/schemas/ba-brief.json` carries `discovery_file`/`brief_file`/`layers`, with a sibling `workflows/schemas/discovery.json`; the single canonical `workflows/delivery-pipeline.yaml` wires the two-skill chain through the human recommendation gate. This fixture is now produced by the pinned skills `researching-ba-problem-space 1.0.0` → `eliciting-banking-brief 1.5.0` (re-run/re-stamped 2026-06-04). The substantive four-layer content is unchanged from the pre-promotion (`^0.1.0` / `^1.4.1`) render: the S1 skills are idempotent, and RB-01 suppresses the discovery handoff so the `eliciting-banking-brief 1.5.0` node runs on `raw_content` alone — behaviour-identical to v1.4.x. Only the version-provenance stamps moved to the exact pins.
- **RB-01 provenance.** The discovery layer was derived retrospectively from an already-structured requirement (full note inside `../S1a-ba-discovery/discovery.json`'s `problem_framing`).

## Skills/tooling phase — status

1. **Pending** — update `render_ba_pack.py` to emit the four-layer manifest + unified viewer natively. The renderer is archived, so this fixture's manifest/viewer stay hand-applied (see the first caveat).
2. **Done** — `workflows/schemas/ba-brief.json` carries optional `discovery_file` / `brief_file` / `layers`, and a sibling `workflows/schemas/discovery.json` boundary schema was added.
3. **Done** — the skill chain (`researching-ba-problem-space` discovery → human gate → `eliciting-banking-brief` brief + epics + stories) is wired in the single canonical `workflows/delivery-pipeline.yaml`, and the overview's S1 contract is reconciled to the composite.
4. **Pending / blocked** — propagate the structure into the canonical `.../templates/S1-ba-research/` (that tree is under the sibling `../archive/`, off-limits).
