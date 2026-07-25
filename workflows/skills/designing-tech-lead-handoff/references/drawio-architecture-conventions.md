# Consolidated architecture `.drawio` conventions (scaffold-v1.1 §9-drawio)

Loaded at **step 8.5**. The TL handoff emits **one** consolidated, offline, byte-deterministic
draw.io file with **four pages (tabs)** — doc-altitude L1→L4 — driven by a structured
`architecture.spec.json`. **Never hand-author the `.drawio` XML**; the LLM writes the spec, and the
deterministic generator `scripts/spec_to_drawio.py` renders the file:

```bash
python3 scripts/spec_to_drawio.py \
  --input  diagrams/<system>-architecture.spec.json \
  --output diagrams/<system>-architecture.drawio
```

Same spec → byte-identical `.drawio` (no `now()`/`random`/`uuid`; every collection is sorted once;
every cell id derives from sorted spec keys). The four pages each author their own coordinate frame;
the review-console transcoder (`rendering-delivery-review-console`) stacks them vertically, and native
draw.io shows four tabs.

## The four pages

| Page id | Tab name | Shows |
|---|---|---|
| `L1-context` | **L1 System Context** | actors → the system (decomposed into bounded-context chips) → external systems |
| `L2-containers` | **L2 High-Level Design (Containers)** | services, datastores, cache, Kafka bus, externals — **rich vector mxgraph icons**; sync/async topology edges |
| `L3-components` | **L3 Components & Aggregates** | per bounded context: the aggregates each owns + any process manager (Orchestrator) |
| `L4-er-boundaries` | **L4 ER & Aggregate→Table Boundaries** | ER tables (`shape=table`) **nested inside labeled DDD aggregate-boundary containers** — the centerpiece: which aggregate scopes which tables. FK edges classed intra / composition / cross |
| `legend-standard` | **Legend / Standard Template** | the hivemind house-style key: component status colours, connection types, database states (static, spec-independent, offline) |

This realises the house philosophy *1 Domain → ≥1 microservice → ≥1 aggregate boundary → ≥1 table*
(see `templates/erd.md`) as a single visual: L1 domain → L2 service → L3 aggregate → L4 table.

## House standard (hivemind "Standard Template")

The house Legend/Standard Template page (see `legend-standard` above) defines these conventions:

- **Component status colours** (`fill`/`stroke`): **New `#03CCFF`** · **Enhanced `#92D14F`** ·
  **Existing `#BFBFBF`** · **External `#EF7D30`**. Drive them with an optional **`status`** field on
  `services[]` / `datastores[]` (`new|enhanced|existing|external`, default `new`); every entry in
  `externals[]` is External. L1 context chips, L2 service/db boxes, and L3 aggregate boxes are coloured
  by status; L4 ER tables keep the root=green / child=blue data convention; the Kafka bus stays a
  distinct infra colour. The L3 context containers and L4 aggregate boundaries keep a **per-context
  border tint** for grouping (independent of status).
- **Connection types**: `topology[].kind` → **`sync`** solid classic arrow · **`async`** dashed classic ·
  **`system_internal`/`authorization`** double-block. Sample arrows + DB states are shown on the Legend page.

## `architecture.spec.json` schema

A single JSON object. Field aliases accepted by `normalize()`: `external_systems`→`externals`,
`connections`→`topology`, `orchestrators`→`process_aggregates`, `root_table`→`root`.

```jsonc
{
  "system": "ShopPilot MVP",                 // L1/L2/title label
  "subtitle": "S2 TL design — L1–L4",         // optional, informational
  "contexts":  [ { "id": "checkout", "label": "Checkout", "epic": "EPIC-CHECKOUT" } ],
  "actors":    [ { "id": "customer", "label": "Customer\n(shopper)", "uses": "auth", "edge": "browse · checkout" } ],
  "externals": [ { "id": "mock-psp", "label": "Mock PSP", "from": "checkout", "edge": "capture (mock)" } ],
  "services":  [ { "id": "web", "label": "web", "context": null, "role": "client" },
                 { "id": "checkout-service", "label": "checkout-service", "context": "checkout" } ],
  "datastores":[ { "id": "checkout-db", "label": "MySQL\nshoppilot-checkout", "context": "checkout", "kind": "db" },
                 { "id": "redis", "label": "Redis", "context": "auth", "kind": "cache" },
                 { "id": "events", "label": "Kafka event bus", "kind": "bus" } ],
  "topology":  [ { "from": "checkout-service", "to": "inventory-service", "kind": "sync",  "label": "reserve" },
                 { "from": "checkout-service", "to": "events",            "kind": "async", "label": "order.created" } ],
  "aggregates":[ { "id": "cart", "label": "Cart", "context": "checkout", "root": "cart", "tables": ["cart","cart_item"] } ],
  "process_aggregates": [ { "id": "checkout-proc", "label": "Checkout (process)", "context": "checkout", "note": "ADR-007" } ],
  "tables": {
    "cart":      { "rows": [ ["PK","cart_id : UUID"], ["FK","customer_id : UUID"], ["","status : ENUM(OPEN,CONVERTED)"] ] },
    "cart_item": { "rows": [ ["PK","cart_item_id : UUID"], ["FK","cart_id : UUID"], ["","quantity : INT"] ] }
  },
  "fks": [ { "from": "cart_item", "from_col": "cart_id", "to": "cart", "class": "composition" } ]
}
```

Field rules:
- **`datastores[].kind`**: `db` (cylinder) · `cache` (red cylinder) · `bus` (wide box spanning the L2 row).
- **`topology[].kind`**: `sync` (solid blue arrow) · `async` (dashed purple arrow). `label` optional.
- **`tables`** is a **map** `name → { rows: [[flag, "col : TYPE"], …] }`. `flag` ∈ `PK | FK | ""`. The
  `"col : TYPE"` string is split on `" : "` into the name / type columns; a row with no `" : "` (e.g.
  `["","+ audit cols"]`) renders the whole string as the name. Map iteration never drives layout
  (tables are placed via `aggregates[].tables[]`), so order is irrelevant.
- **`fks[].class`**: `intra` (green, same aggregate/context) · `composition` (blue diamond, parent→child)
  · `cross` (dashed red, cross-aggregate by-id reference — never a DB-enforced cross-service FK; see
  `templates/erd.md` Negative #2).

### Aggregate↔table ownership (fail-closed)
`normalize()` **rejects** the spec (non-zero exit) if: an `aggregates[].tables[]` entry names an
unknown table; a table is claimed by two aggregates; or a table is owned by **no** aggregate. Every
table must sit inside exactly one aggregate boundary — nothing silently unscoped. The aggregate whose
`root` equals a table name marks that table `«root»` and tints it green; non-root tables are blue.

## Offline icon allow-list

L2 uses rich draw.io shapes for editor quality, but the file MUST stay offline (workspace rule) and
transcoder-safe. **Allowed** (pure vector, style-string only):
- `shape=mxgraph.kubernetes.icon;prIcon=pod` (services; orange stroke `#EF7D30` for externals)
- `shape=cylinder3` (datastores / cache)
- `shape=table` + `shape=partialRectangle` (L4 ER tables)
- plain `rounded=1` rects, `rhombus` (process managers)

**Forbidden:** `image=http(s)://…`, `src=`, any CDN/`@import`/`@font-face`. The generator emits
style strings only — no image URLs — so the source `.drawio` is offline by construction. In the review
console, unrecognised icon shapes degrade to a labeled rounded rect (the transcoder's E2 fallback);
native draw.io shows the full icon.

## Edge routing — no arrow crosses a component box

Every edge carries fixed **exit/entry anchors** (so draw.io routes orthogonally from box edges, not
centres) **plus explicit waypoints** routed through clear inter-layer gutters (so the offline console
transcoder's centre-to-centre polyline also stays out of other boxes). L2 is laid out left→right
(web │ services │ datastores │ externals, Kafka bus as a bottom channel); each edge category
(`web→service`, `service→db`, `service→service`, `service↔bus`, `service↔external`) routes through its
own gutter channel, and parallel edges in a channel **stagger** so lines and labels don't pile up.
Anchors/waypoints are pure functions of computed node geometry, so determinism holds. (L4 FK lines use
side anchors; ER relationship lines may still cross tables — conventional for ER diagrams.)

## Determinism contract

- The generator is a pure function of the spec: `build(spec)` returns identical bytes on every call.
- No `now()` / `random` / `uuid` / unsorted set or dict iteration in any output path.
- Verify with a double-build diff (step 14 gate):
  `python3 scripts/spec_to_drawio.py -i <spec> -o - | …` twice, then `diff` — must be empty.

## Output threading

Record in the JSON output (`schemas/output.json` `diagrams` block; present-or-absent, never `null`):
```jsonc
"diagrams": {
  "architecture_drawio": "diagrams/<system>-architecture.drawio",
  "architecture_spec":   "diagrams/<system>-architecture.spec.json",
  "erd_consolidated":    "diagrams/<system>-architecture.drawio",  // the L4 page IS the ER pack
  "offline": true
}
```
The optional `data_model` block is emitted **only** once the per-service split ER pack exists — its
`index` (path to `design/data-model/INDEX.json`) is mandatory, mirroring the boundary
`workflows/schemas/tl-design.json`. That split pack stays **deferred**; until then
`diagrams.erd_consolidated` (the L4 page) carries the consolidated ER and satisfies the boundary hook.
