# Section kinds — kind → renderer → source

The console is **data-driven** over `window.PACK.sections[]`. Each section names a `kind`; the render module
dispatches on it. Every **unknown** kind falls through to `generic` (a collapsible tree). This table maps
each kind to its renderer behavior and its source artifact. The badge vocabulary (verdict / severity / tier
/ priority / status colors) is **shared with** the donor renderer — see
`../../rendering-contract-debug-viewer/references/contract-field-map.md` for the full field-to-color table
(not duplicated here); this file documents only the per-kind layout and the gate-board logic.

## Kind table

| `kind` | Renderer behavior | Source artifact |
|---|---|---|
| `discovery` | recommendation banner (badge) · problem framing prose · numbered opportunities · assumptions = four-product-risk cards (risk_type tag + confidence meter + de-risk) · regulatory regimes list ("not in play" rows muted) | S1a `discovery.json` |
| `brief` | title + summary card · status/scope/tier/blocks pills · layer-count stat strip · regulatory chips · PII-inventory mono chips | S1b `brief.json` (`initiative`, `frontmatter`, counts) |
| `epics` | count-check pill row · open-questions table · governance-gaps table (or "none") · **epic accordion** → click a story → **slide-in reader** (user-story card, Gherkin acceptance criteria, banking-grade concerns, dependencies/sizing, Definition of Ready). Behavior reused verbatim from the BA-research viewer. | S1b `INDEX.json` + `EPIC-*/EPIC-*.json` + `EPIC-*/STORY-*.json` |
| `ux_pack` | maturity_level + status badges · `*_path` refs as inert mono chips · p1_findings + p2_findings tables (severity badges) · **two-way coverage matrix** (`ba_stories_without_ux_coverage` ⟷ `ux_routes_without_ba_story`) as two red-flagged lists side by side (an empty side reads green "fully covered") | S1.5 `output.json` |
| `design` | collapsible groups for component_map · event_catalog · adrs · l4_specs · coverage_gaps · architecture_smells · open_questions (ported tree renderer) | S2 `output.json` |
| `api_contracts` | **endpoint table**, one row per contract: contract_name (mono) · semantics badge (async → amber) · request keys · response keys · failure_modes (red chips) | S2 `output.json` `api_contracts.contracts[]` |
| `plan_review` | verdict banner (badge) + confidence · steelman prose · findings table (severity dots) · numbered bias-checks | S2.5 `plan-review.json` |
| `diagram_svg` | the transcoder's inline `<svg>` inserted via **innerHTML** (the ONE trusted-markup field) + a caption + an inert path chip | S2 `diagrams/*.drawio` → `drawio_to_svg.transcode()` |
| `gate_board` | the **Quality-Gate Board** (below) | T-gate `*.json` discovered under the run dir / `gates/` |
| `pending` | a muted "not yet produced" card naming the stage + the expected skill | stub stages (README-only): S0, S3, S4, S5, S6, S7 |
| `generic` | any other JSON → collapsible tree (ported from `render_contract_viewer.py`) | fallback for an unknown kind |

## Section envelope fields

Every section carries: `id`, `menu` (which menu it belongs to), `title`, `kind`, `source_path` (relative
artifact path, shown as a chip), and `payload` (only the fields the renderer reads). Optional surface
badges shown next to the title: `status`, `verdict`, `tier`, `audit_id` (first 8 chars). `sub_of` is
reserved for nested sub-sections (currently unused; reserved in the contract).

## Quality-Gate Board logic (the highest-value win)

The build script collects the 12 T-gate JSONs by filename anywhere under the run dir (and a top-level
`gates/` dir): `backend-unit-tests.json`, `frontend-unit-tests.json`, `sast-gate.json`,
`accessibility-tests.json`, `contract-tests.json`, `integration-tests.json`, `appsec-scan.json`,
`e2e-tests.json`, `perf-load-test.json`, `adversarial-pentest.json`, `smoke-tests.json`,
`canary-analysis.json`.

- **Empty state.** If none are found (e.g. the ShopPilot run), the board renders an honest
  "pending — no gate evidence yet" card and the menu is marked `present:false`.
- **Per-gate verdict mapping (do NOT hardcode PASS/FAIL).** Each gate carries a `verdict_map` that encodes
  its own vocabulary:
  - **T10** adversarial-pentest: `pass | conditional | fail` → `G | A | R`
  - **T12** canary-analysis: `promote | hold | rollback` → `G | A | R`
  - **all others**: `PASS | FAIL | ERROR` → `G | R | R`
  - A verdict not in the map (or a gate with no evidence file) → `P` (pending); an evidence file present but
    with an unrecognized verdict defaults to `R` (fail-safe).
- **Worst-of roll-up** over gates that **have** evidence: any `R` ⇒ **RED**, else any `A` ⇒ **AMBER**, else
  **GREEN**. No evidence at all ⇒ **PENDING**.
- **Render.** A grid of cells (id badge · name · status dot · headline · level + verdict). Clicking a cell
  opens its **baked full gate JSON** in the slide-in reader (the View-source / tree pattern).

The synthetic fixture `tmp/runs/_fixtures/gateboard-demo/` (clearly marked synthetic, no real PII) proves
the mapping: `sast-gate` FAIL → RED, `adversarial-pentest` conditional → AMBER (T10), `canary-analysis`
rollback → RED (T12), the rest green/promote/pass → roll-up **RED**.

## Adding a new kind

1. Add a `RENDER.<kind>` function in `templates/delivery-review.template.html` and a `build_<...>_menu`
   (or section) in `scripts/build_review_console.py`.
2. Reuse the shared badge classes (`statusKind()`, `sevTag()`, `tierBadge()`, `prioTag()`) so colors match
   the donor vocabulary; add a CSS class only if a genuinely new visual is needed.
3. Re-run the build on a real run; confirm offline-clean + determinism (build twice, diff).
