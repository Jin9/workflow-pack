# workflows-ui Binding Design — delivery-pipeline data plane → HELL FACTORY office sim

> **STATUS: DESIGN-ONLY.** This document is the system-design blueprint for binding the
> delivery-pipeline backend into the `workflows-ui/` browser sim. Every component marked
> **PLANNED** does not exist yet. Nothing under `workflows-ui/src/` was modified when this
> design was produced. Structured by the `designing-tech-lead-handoff` scaffold
> (contracts → components → topology → ADRs → diagram); its BA-brief pre-flight gates do
> not apply (this is a workspace design exercise, not a pipeline run).

Companion diagram (generated, never hand-written — see ADR-007 in spirit / workspace rule):
`reference/plan/diagrams/workflows-ui-binding-architecture.drawio`
(from `reference/plan/diagrams/workflows-ui-binding-architecture.spec.json` via
`workflows/skills/designing-tech-lead-handoff/scripts/spec_to_drawio.py`).

---

## 1. Purpose & scope

Bind the **static delivery-pipeline data plane** (`workflows/delivery-pipeline.yaml`,
`dashboard-data.json`, `workflows/schemas/`, the deterministic ShopPilot run under
`tmp/runs/shoppilot/`) into the **HELL FACTORY office sim** (`workflows-ui/`) as:

1. **STRUCTURE** — rooms and agents become stage-aware: the 27 pipeline stages
   (15 S-stages + 12 T-gates), their owners, tiers, and gate types are bound to the sim's
   10 agents and 18 rooms.
2. **RUN REPLAY** — the sim plays the ShopPilot run: agents act out stages in DAG order,
   the feed shows real stage events (audit_id, verdict, output_type), and a
   **Quality-Gate Board** rolls up T1–T12 worst-of R/A/G, mirroring the Delivery Review
   Console semantics.

**Not in scope / not possible:** live pipeline execution. The Rust `squad-engine` is
archived; everything here is data-driven visualization of static, schema-validated
artifacts. The replay is a *playback*, never an *operation* — design artifacts recommend
and record; they never operate the pipeline.

## 2. Bounded contexts & layer presence

Contexts split by workstream (never tech-layer):

| Context | Workstream | Contents |
|---|---|---|
| `pipeline-data-plane` | Authoring & validating the pipeline | `delivery-pipeline.yaml`, `dashboard-data.json`, `workflows/schemas/` (30), `tmp/runs/shoppilot/` (+ `gates/`), and the two existing review surfaces (squad dashboard, delivery-review console) as sibling consumers |
| `binding-adapter` | Build-time transformation | **PLANNED** `build_pipeline_pack.py` + its output `pipeline-pack.json` (THE contract) |
| `office-sim` | Runtime visualization | `workflows-ui/` sim core (BUILT) + **PLANNED** binding modules (pipeline-adapter, replay-controller, gate-board, Sidebar/Feed remount) |

Layer-presence (canonical 4-layer house style), with non-"following the pattern" rationale:

| Layer | Present? | Where | Rationale |
|---|---|---|---|
| Gateway | **No** | — | No network boundary exists: sources are local files, the sim is an in-browser app served statically by Vite. A gateway would be pure ceremony. |
| Orchestrator | **Yes (one)** | `replay-controller` (PLANNED, office-sim) | Signal 3 (temporal control) fires: the replay sequences the DAG-ordered timeline against the sim tick, with pause/speed. Signals 1–2 do not fire here — multi-aggregate coordination and compensation (`release-handoff`→`handoff-revoke`) live in the pipeline data plane, not in playback. The replay-controller answers "what's next?", never "is this correct?" — correctness was settled when the artifacts were validated. |
| Domain Processor | **Yes** | `build_pipeline_pack.py` (PLANNED, binding-adapter) | Owns the binding's correctness invariants: triple-key join, topo-order validation, owner normalization, gate roll-up. Fail-closed. |
| Protocol Adapter | **Yes** | `pipeline-adapter` (PLANNED, office-sim) | Anti-corruption layer: loads + validates `pipeline-pack.json` and translates it into sim-native shapes (`world`, `ROOMS` ids, `STATES`). The sim core never sees backend field names. |

## 3. THE integration contract — `pipeline-pack.json` (PLANNED)

The **single seam** between backend and sim. One build-time artifact; the UI consumes
nothing else (ADR-001, ADR-003). Byte-deterministic: no timestamps, no randomness;
`generated_from` carries source paths + sha256 content hashes (house pattern of
`_sim/simulate.py` and the dashboard `build.py`).

Top-level shape:

```
{
  pack_version: "1.0.0",
  generated_from: [ { path, sha256 } ],          // dashboard-data.json · delivery-pipeline.yaml · run folder
  stages: [ 27 × StageBinding ],
  dag: { edges: [{from,to}], topo_order: [27 ids] },
  roster: [ OwnerBinding ],
  rooms:  [ StageRoomBinding ],
  replay: { timeline: [ ReplayStep ] },
  gates:  { board: [ 12 × GateRow ], rollup: "G"|"A"|"R" }
}
```

### 3.1 `stages[27]` — StageBinding (the triple-key join)

```
{ id, yaml_id, run_dir|null, gate_file|null,
  name, owner, agent, room, tier, gate,
  skill, skill_version, depends_on[],
  failure_policy, human_queue, compensation|null, deferred }
```

The three id spaces are joined **here, once**, so no consumer ever improvises a mapping:

| Dashboard `id` | YAML `yaml_id` | Run location |
|---|---|---|
| S0 | intake | `S0-intake/` |
| S1a | s1-discovery | `S1a-ba-discovery/` |
| S1b | ba-research | `S1b-ba-brief/` |
| S1.5 | ux-intake | `S1.5-ux-intake/` |
| S2 | tl-design | `S2-tl-design/` |
| S2.5 | plan-review | `S2.5-plan-review/` |
| S3a/3b | contract-design | `S3-contracts/` |
| S4a | backend-implement | `S4a-backend/` |
| S4a-r | backend-review | **`run_dir: null`** (review artifacts live under `S4a-backend/review/`; `artifacts: []` is valid) |
| S4b | frontend-implement | `S4b-frontend/` |
| S4b-r | frontend-review | **`run_dir: null`** |
| S4c | qa-plan | `S4c-qa-test-design/` |
| S5 | qa-validate | `S5-qa-validation/` |
| S6 | release-handoff | `S6-deploy/` (compensation: `handoff-revoke`) |
| S7 | prod-validate | `S7-prod-validation/` |
| T1–T12 | backend-unit-tests · sast-gate · frontend-unit-tests · accessibility-tests · contract-tests · integration-tests · appsec-scan · e2e-tests · perf-load-test · adversarial-pentest · smoke-tests · canary-analysis | `gates/{yaml_id}.json` |

### 3.2 `dag` — edges + canonical linearization

`edges[]` come verbatim from the YAML `depends_on` graph. `topo_order` is the
**`dashboard-data.json` `stages[]` order, validated as a topological sort** of those
edges: the generator asserts every predecessor appears earlier and **fails closed** if
the curated order ever stops being a valid linearization. This is the replay order —
run artifacts are deliberately timestamp-free (uuid5/sha256 determinism), so clocks can
never be the ordering source (ADR-002).

### 3.3 `roster[]` — owner → agent normalization

Owner strings in the data are stringy; the pack pins the normalization **once**:

| Owner string(s) (verbatim from dashboard-data.json) | Sim agent | Dept |
|---|---|---|
| `Delivery Ops` | Delivery Ops | Delivery |
| `BA lead` (lowercase l) | BA Lead | Analysis |
| `Tech Lead` | Tech Lead | Engineering |
| `dev-squad` | Dev Squad | Build |
| `qa-squad` | QA Lead | Quality |
| `security` | Governance | Risk |
| `Release Manager` | Release Mgr | Releases |
| `On-call / Rel Mgr`, `On-call / Release Mgr` (both spellings) | On-Call (primary; Release Mgr co-actor) | Support |
| — (unbound, ambient) | Tia | Open-Plan |
| — (unbound; announces run start/end in feed) | Mia | Reception |

### 3.4 `rooms[]` — stage → room + sim-state mapping

Gate-type policy (ADR-004): `auto`→WORK · `async`→WORK + handoff feed line ·
`sync`→MEET · `gate`/`human`→MEET in CONF · `auto+exc`→WORK + exception feed line on FAIL.

| Stage | Agent | Room | Sim state | Rationale |
|---|---|---|---|---|
| S0 Intake | Delivery Ops | RECEP | WORK | intake arrives at reception |
| S1a BA Discovery | BA Lead | PO1 | WORK | BA office |
| S1b BA Brief | BA Lead | PO1 | WORK | + handoff feed line (async) |
| S1.5 UX Intake | Tech Lead | HUD1 | WORK | UX huddle |
| S2 TL Design | Tech Lead | PO2 | MEET | TL office, sync gate |
| S2.5 Plan-Review gate | Tech Lead | CONF | MEET | formal gate = conference |
| S3a/3b Contracts | Dev Squad | OPEN | WORK | open-plan build floor |
| S4a Backend Impl | Dev Squad | OPEN | WORK | |
| S4a-r Backend Review | Dev Squad | HUD2 | WORK | review huddle (async) |
| T1 Unit · Backend | Dev Squad | SRVIT | WORK | CI runs on machines |
| T2 SAST gate | Dev Squad | SRVIT | WORK | |
| S4b Frontend Impl | Dev Squad | OPEN | WORK | |
| S4b-r Frontend Review | Dev Squad | HUD2 | WORK | |
| T3 Unit · Frontend | Dev Squad | SRVIT | WORK | |
| T4 Accessibility · WCAG AA | Dev Squad | SRVIT | WORK | auto+exc |
| T5 Contract · Pact | Dev Squad | SRVIT | WORK | |
| T6 Integration | QA Lead | SVR2 | WORK | big server room = staging env; auto+exc |
| T7 AppSec · DAST/SCA | Dev Squad | SVR2 | WORK | |
| S4c QA Test Design | QA Lead | PO3 | MEET | QA office, sync |
| S5 QA Validation | QA Lead | PO3 | MEET | |
| T8 End-to-end | QA Lead | SVR2 | WORK | auto+exc |
| T9 Performance / Load | QA Lead | SVR2 | WORK | |
| T10 Adversarial pentest | Governance | CONF | MEET | human gate = conference ceremony |
| S6 Deploy | Release Mgr | SVR2 | MEET | deploy from server room, sync |
| T11 Smoke / sanity | On-Call | SRVIT | WORK | |
| T12 Canary analysis | On-Call | SRVIT | WORK | auto+exc |
| S7 Prod Validation | On-Call (+Release Mgr) | SYNC | MEET | closing standup ceremony |

Bound rooms: 11 of 18 (RECEP, PO1, PO2, PO3, CONF, OPEN, HUD1, HUD2, SRVIT, SVR2, SYNC).
Amenity rooms stay unbound (idle/coffee between stages): CAFE, LOUNGE, WC, PRINT, FP1–FP3.

### 3.5 `replay.timeline[]` — ReplayStep

One step per stage in `topo_order`:

```
{ seq, stage_id, agent, room, sim_state,
  feed_lines[],            // templated from REAL artifact fields: audit_id suffix, verdict, output_type
  verdict|null, artifacts[] }
```

Review stages without a run dir get `artifacts: []` but still appear (the DAG includes
them). Deferred stages (S0, S3a/3b, S5, S7) replay with a `deferred` feed marker — the
sim must keep the honest built-vs-deferred distinction visible, not paper over it.

### 3.6 `gates.board[12]` + `gates.rollup`

Per gate: `{ gate_id (T1–T12), stage_id, yaml_id, verdict, rag }`. Mapping mirrors the
Delivery Review Console: PASS→G, pass-with-exception/AMBER→A, FAIL→R. `rollup` =
worst-of across the board. The PLANNED `gate-board` panel renders this inside the
remounted Sidebar (ADR-005).

## 4. Component map (honest built vs planned)

| Component | Context | Status | Notes |
|---|---|---|---|
| `dashboard-data.json` | pipeline-data-plane | **BUILT** | 27 flat stage records; canonical stage order |
| `workflows/delivery-pipeline.yaml` | pipeline-data-plane | **BUILT** | depends_on DAG, failure policies, SAGA compensation |
| `workflows/schemas/` (30) | pipeline-data-plane | **BUILT** | boundary schemas; pack generator revalidates against them |
| `tmp/runs/shoppilot/` (+ `gates/`) | pipeline-data-plane | **BUILT** | deterministic run artifacts; replay source |
| squad-delivery dashboard (standalone.html) | pipeline-data-plane | **BUILT** | sibling consumer of dashboard-data.json |
| delivery-review console (per-run HTML) | pipeline-data-plane | **BUILT** | sibling consumer of the run folder; gate-board semantics donor |
| sim core (`map.jsx` · `sim.jsx` · `App.jsx` etc.) | office-sim | **BUILT** | untouched by this design |
| `Sidebar`/`Metrics`/`Roster`/`Feed` components | office-sim | **BUILT, unmounted** | exist in App.jsx as dead code; remount is PLANNED (Enhanced) |
| `build_pipeline_pack.py` | binding-adapter | **PLANNED** | proposed home `workflows-ui/tools/`; deterministic, stdlib-only, fail-closed |
| `pipeline-pack.json` | binding-adapter | **PLANNED** | proposed home `workflows-ui/public/` (Vite serves statically); THE contract |
| `pipeline-adapter` module | office-sim | **PLANNED** | loads + validates the pack; translates to sim-native shapes |
| `replay-controller` module | office-sim | **PLANNED** | the one orchestrator; drives agent states + pushFeed per tick |
| `gate-board` panel | office-sim | **PLANNED** | T1–T12 worst-of R/A/G; hosted by remounted Sidebar |

## 5. Topology

Build-time (sync, the generator pulls):

- `build_pipeline_pack.py` → `dashboard-data.json` (stage records + tests + skillmap)
- `build_pipeline_pack.py` → `delivery-pipeline.yaml` (depends_on DAG + failure_policy)
- `build_pipeline_pack.py` → `tmp/runs/shoppilot/` (artifacts + gate verdicts)
- `build_pipeline_pack.py` → `workflows/schemas/` (revalidate artifacts, fail-closed)
- `build_pipeline_pack.py` → emits `pipeline-pack.json` (byte-deterministic)

Runtime (the sim consumes):

- `pipeline-adapter` → `pipeline-pack.json` (load + validate; **the only seam**)
- `replay-controller` → `pipeline-adapter` (timeline · roster · room map) — sync
- `replay-controller` → sim core (drive agent states + `pushFeed` per tick) — async
- `gate-board` → `pipeline-adapter` (T1–T12 verdicts → worst-of R/A/G) — sync
- remounted `Sidebar/Feed` hosts `gate-board` and renders the feed

Existing (unchanged, shown for context): squad dashboard ↔ `dashboard-data.json`
(roundtrip skill); delivery-review console ← run folder.

One L2 tab carries both phases; edges are disambiguated by label prefixes
`build:` / `runtime:` / `existing:` (ADR-006).

## 6. ADRs

### ADR-001 — Build-time pipeline pack over runtime fetch or a live server
**Decision:** A deterministic Python generator merges the three backend sources into one
`pipeline-pack.json` at build time; the UI never parses YAML, schemas, or run folders.
**Alternatives:** (a) runtime fetch of raw sources — rejected: couples the sim to YAML
parsing and backend file layouts, adds a browser YAML dependency; (b) live server —
rejected: no engine exists, and a server contradicts the static/offline house posture.
**Consequences:** source-format changes are absorbed by the generator; the pack must be
regenerated when sources change (acceptable: sources only change by deliberate edit).

### ADR-002 — Replay from artifacts, not an engine; DAG-order timeline
**Decision:** Replay order = the dashboard's curated stage order validated as a
topological sort of `depends_on`. The `replay-controller` is the design's only
orchestrator (signal 3, temporal control).
**Alternatives:** timestamp ordering — impossible by design (artifacts are
timestamp-free for byte-determinism); re-deriving a fresh topo sort — rejected: would
shadow the curated, human-reviewed dashboard order with a second source of truth.
**Consequences:** compensation (`release-handoff`→`handoff-revoke`) stays a data-plane
fact rendered in the feed, never replay logic.

### ADR-003 — Single-contract seam
**Decision:** `workflows-ui` consumes exactly one artifact: `pipeline-pack.json`.
**Alternatives:** multiple narrow imports per source — rejected: N seams = N coupling
points; violates the black-box decoupling preference.
**Consequences:** the pack schema is the compatibility surface; version it
(`pack_version`) and validate on load (fail-visible in the feed, not silently).

### ADR-004 — Stage→room & gate-type→sim-state mapping policy
**Decision:** Static tables (§3.3, §3.4) shipped inside the pack; gate semantics map
`auto`→WORK, `async`→WORK + handoff line, `sync`→MEET, `gate`/`human`→MEET in CONF,
`auto+exc`→WORK + exception line on FAIL.
**Alternatives:** heuristic room assignment at runtime — rejected: non-deterministic and
unreviewable.
**Consequences:** new stages or rooms require a deliberate table edit in the generator —
which is the point.

### ADR-005 — Remount Sidebar/Feed as the Quality-Gate Board host
**Decision:** Reuse the intentionally-unmounted `Sidebar`/`Feed` components (status:
Enhanced) as the host chrome for the gate board and real-event feed.
**Alternatives:** new panel chrome — rejected: duplicate styling, and the dead code was
kept precisely for this.
**Consequences:** the unmounted components stop being dead code; CLAUDE.md's "mount
`<Sidebar>` to restore" note becomes the implementation hook.

### ADR-006 — One L2 diagram for two phases
**Decision:** Build-time and runtime edges share the single L2 tab, disambiguated by
`build:`/`runtime:`/`existing:` label prefixes (sync solid = data pull; async dashed =
tick/event push).
**Alternatives:** two diagrams — rejected: two artifacts drift; one source of truth.
**Consequences:** L2 is denser; the prefixes carry the phase semantics.

## 7. Open questions (for the implementation session)

1. Pack consumption mechanism: static `import` (bundled at build) vs
   `fetch('/pipeline-pack.json')` (swap pack without rebuild). Leaning fetch-from-public.
2. Do `Metrics`/`Roster` remount along with `Sidebar`/`Feed`, or gate-board only?
3. Replay pacing: one timeline step per N sim ticks (coupled to the 320ms/speed loop) vs
   its own clock. Leaning N-ticks (one clock, pausable with Space for free).
4. Flourish: Mia announces run start/end in the feed (recommended, cheap, on-theme).

## 8. References

- `workflows/skills/designing-tech-lead-handoff/SKILL.md` — the design scaffold followed here
- `reference/plan/diagrams/workflows-ui-binding-architecture.spec.json` — diagram source (edit this, regenerate)
- `dashboard-data.json` · `workflows/delivery-pipeline.yaml` · `tmp/runs/shoppilot/` — the three backend sources
- `.claude/skills/rendering-delivery-review-console/` — gate roll-up semantics donor
- Root `CLAUDE.md` §workflows-ui — sim architecture + conventions (module chain, tile-space, mutable `world` ref)
