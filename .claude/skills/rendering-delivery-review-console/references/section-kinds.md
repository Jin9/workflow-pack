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
| `scope_sheet` | normalized-request + business-goal prose · in/out scope rows · quantified-NFR table · open-questions table · risk-flag/assumption chips · run-plan tree | S0 `run-plan.json` (scoping-ba-intake) |
| `befe_contracts` | contract_spec / fe_state_binding / client_types / mock_plan / list_conventions prose fields · per-context `be/`+`fe/` file chips (scanned from disk) | S3 `befe-contracts.json` (befe-contract-design) |
| `impl_artifacts` | stat strip (files · test files · avg coverage · bundle Δ / audit-event count) · a11y+security pill row (FE) · idempotency prose (BE) · audit/analytics event chips · files table · compensating-action chips | S4a `backend-artifacts.json` · S4b `frontend-artifacts.json` |
| `code_review` | verdict banner (approve/loop_back/human-queue) · a11y+security verdict pills (FE) · two-column verified/unverified claims · findings table (or clean state) | S4a-r `backend-review.json` · S4b-r `frontend-review.json` |
| `qa_plan` | type/status/plan-id chips · pyramid-allocation stat strip · high-risk-area chips · test-cases table (id/story/type/level/risk/smoke) · go / no-go sign-off chips | S4c `qa-plan.json` (planning-banking-tests) |
| `qa_evidence` | verdict banner · totals stat strip (executed/passed/failed/skipped) · coverage · defects table (or clean state) | S5 `qa-evidence.json` (executing-qa-test-suite) |
| `handoff_receipt` | status banner (irreversible-boundary note) · receipt-id / release-ref / named-approver chips | S6 `handoff-receipt.json` (handoff-to-deploy) |
| `slo_validation` | verdict banner + grade + window · per-SLO table (target/observed/burn/judgement, R/A/G judgement pill) | S7 `smoke-slo.json` (validating-production-slo) |
| `diagram_svg` | the transcoder's inline `<svg>` inserted via **innerHTML** (the ONE trusted-markup field) + a caption + an inert path chip | S2 `diagrams/*.drawio` → `drawio_to_svg.transcode()` |
| `gate_board` | the **Quality-Gate Board** (below) | T-gate `*.json` discovered under the run dir / `gates/` |
| `pending` | a muted "not yet produced" card naming the stage + the expected skill (via `_pending_menu()`) | any S0/S3/S4/S4c/S5/S6/S7 stage whose artifact is **absent** in the run dir |
| `generic` | any other JSON → collapsible tree (ported from `render_contract_viewer.py`) | fallback for an unknown kind |

## Section envelope fields

Every section carries: `id`, `menu` (which menu it belongs to), `title`, `kind`, `source_path` (relative
artifact path, shown as a chip), and `payload` (only the fields the renderer reads). Optional surface
badges shown next to the title: `status`, `verdict`, `tier`, `audit_id` (first 8 chars). `sub_of` is
reserved for nested sub-sections (currently unused; reserved in the contract).

## Quality-Gate Board logic (the highest-value win)

The build script collects the 12 T-gate JSONs with canonical `gates/<file>` authoritative; recursive
filename discovery under the run dir is a legacy fallback used only when the canonical file is absent —
and more than one fallback candidate stops the build with an ambiguity diagnostic (never a silent
first-pick). The filenames: `backend-unit-tests.json`, `frontend-unit-tests.json`, `sast-gate.json`,
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
- **Roll-up with evidence accounting.** The payload carries `expected_count: 12`, `evidence_count`,
  `missing_gates[]`, `evidence_complete`, and `worst_observed`. An unqualified worst-of colour (any `R` ⇒
  **RED**, else any `A` ⇒ **AMBER**, else **GREEN**) is shown ONLY when all 12 gates have readable
  recognized verdicts; partial evidence ⇒ **INCOMPLETE** (with `worst_observed` preserved alongside); no
  evidence at all ⇒ **PENDING**. The board is presentation-only — it proves neither a release-blocking
  barrier nor production readiness.
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
