# 2026-06-10 — workflows-ui ⇄ pipeline binding design (design-only)

Designed the merge of the delivery-pipeline backend into the `workflows-ui` HELL FACTORY
sim, using the `designing-tech-lead-handoff` scaffold (contracts → components → topology →
ADRs → diagram). **No implementation** — nothing under `workflows-ui/src/` changed.

- **`reference/plan/workflows-ui-binding.md`** — the binding blueprint: 3 bounded contexts
  (pipeline-data-plane · binding-adapter · office-sim), layer-presence table (no Gateway;
  one Orchestrator = the PLANNED replay-controller, signal 3 temporal), THE integration
  contract **`pipeline-pack.json`** (triple-key join dashboard-id ↔ YAML-id ↔ run-dir/gate-file,
  DAG topo-order replay — artifacts are timestamp-free by design, owner→agent roster
  normalization incl. the three On-call spellings, 27-stage→room mapping, gates board
  worst-of R/A/G), honest BUILT-vs-PLANNED component map, ADR-001…006.
- **`reference/plan/diagrams/workflows-ui-binding-architecture.spec.json`** +
  generated **`…-architecture.drawio`** (5 tabs L1–L4 + Legend) via the skill's
  `spec_to_drawio.py` — determinism gate (double-build `cmp`) and offline gate both green.
- Chosen architecture: **build-time pipeline pack adapter** — a deterministic generator
  (PLANNED `workflows-ui/tools/build_pipeline_pack.py`) merges
  `{dashboard-data.json + delivery-pipeline.yaml + tmp/runs/shoppilot/}` into one
  UI-consumable `pipeline-pack.json` (PLANNED `workflows-ui/public/`); the sim consumes
  only that single seam. Rejected: runtime fetch of raw sources; live server (no engine).
- CLAUDE.md: fixed the stale "untracked" claim (workflows-ui is git-tracked since
  `4a96020`) and pointed the workflows-ui prose at the binding design.
