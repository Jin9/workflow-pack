# workflows/skills/

The skills the live delivery pipeline actually uses. Each is referenced from
`../delivery-pipeline.yaml` (the single canonical workflow file) as
`skill_ref: skills/<name>` — resolved **relative to the workflow file's dir**, so
the ref points here.

Consolidated on **2026-06-02** from the former `skill-packs/` staging copy: only
the skills the pipeline references were kept; the ~100 unused skills (and the old
`manifest.json`) were quarantined and then **deleted** — permanently, since this
workspace has no git and the upstream `treasury/` source is not present here.

## Skills (28) — origin and pipeline stage

| Skill | Pipeline stage | Came from (old `skill-packs/` path) |
|---|---|---|
| scoping-ba-intake | S0 intake | `pack-A-ba-pipeline/` |
| researching-ba-problem-space | S1 s1-discovery | `squad-delivery-skills/` |
| breaking-down-ba-scope | S1b ba-breakdown | authored 2026-07-28 (split of eliciting-banking-brief) |
| elaborating-user-stories | S1c ba-research | authored 2026-07-28 (split of eliciting-banking-brief) |
| generate-ux-pack | S1.5 ux-intake | `pack-F-tl-design-build/` |
| designing-tech-lead-handoff | S2 tl-design | `pack-F-tl-design-build/` |
| red-teaming-implementation-plan | S2.5 plan-review | `squad-delivery-skills/` |
| befe-contract-design | S3 contract-design | `squad-delivery-skills/` |
| implement-backend-feature | S4a backend-implement | `pack-F-tl-design-build/` |
| review-backend-code | S4a-r backend-review | `pack-F-tl-design-build/` |
| implement-frontend-feature | S4b frontend-implement | `pack-F-tl-design-build/` |
| review-frontend-code | S4b-r frontend-review | `pack-F-tl-design-build/` |
| planning-banking-tests | S4c qa-plan | `pack-F-tl-design-build/` |
| executing-qa-test-suite | S5 qa-validate | `squad-delivery-skills/` |
| validating-production-slo | S7 prod-validate | `squad-delivery-skills/` |
| handoff-to-deploy | S6 release-handoff | authored here 2026-06-04 (OI-002) |
| handoff-revoke | S6 SAGA compensation | authored here 2026-06-04 (OI-002) |
| executing-backend-unit-tests | T1 backend-unit-tests | authored here 2026-06-04 (dashboard `tests[]`) |
| running-sast-security-gate | T2 sast-gate | authored here 2026-06-04 (dashboard `tests[]`) |
| executing-frontend-unit-tests | T3 frontend-unit-tests | authored here 2026-06-04 (dashboard `tests[]`) |
| running-accessibility-tests | T4 accessibility-tests | authored here 2026-06-04 (dashboard `tests[]`) |
| contract-testing-pact | T5 contract-tests | authored here 2026-06-04 (dashboard `tests[]`) |
| executing-integration-tests | T6 integration-tests | authored here 2026-06-04 (dashboard `tests[]`) |
| scanning-appsec-pipeline-gate | T7 appsec-scan | authored here 2026-06-04 (dashboard `tests[]`) |
| authoring-e2e-test-suite | T8 e2e-tests | authored here 2026-06-04 (dashboard `tests[]`) |
| running-performance-load-test | T9 perf-load-test | authored here 2026-06-04 (dashboard `tests[]`) |
| validating-banking-implementation | T10 adversarial-pentest | authored here 2026-06-04 (dashboard `tests[]`) |
| running-smoke-tests | T11 smoke-tests | authored here 2026-06-04 (dashboard `tests[]`) |
| analyzing-canary-rollout | T12 canary-analysis | authored here 2026-06-04 (dashboard `tests[]`) |

## OI-002 — S6 deploy pair (BUILT 2026-06-04)

The S6 release stage and its SAGA compensation are now built and wired — the
`skill_ref`s no longer dangle: `handoff-to-deploy` (release-handoff) and
`handoff-revoke` (compensating action). Both are exact-pinned in
`../delivery-pipeline.yaml` and carry a machine-readable human gate
(`requires_approval: true`) for the irreversible control-plane boundary; their
workflow-level boundary schemas are `../schemas/handoff-receipt.json` and
`../schemas/revoke-receipt.json`.

## Post-development test gates (T1–T12, added 2026-06-04)

Twelve verification skills were authored from the dashboard `tests[]` roster
(grounded in the ResearchVault + web search) and wired as **leaf** gates off their
natural SDLC anchors, each with a `../schemas/<stage>.json` boundary: unit (BE/FE),
SAST, accessibility (WCAG 2.1 AA), contract (Pact/CDCT), integration, AppSec
(DAST/SCA), e2e, performance/load, adversarial-pentest (human gate), smoke, and
canary. They expand the pipeline from 14 to 26 stages and re-introduce the
test-execution layer that the 2026-06-02 consolidation had simplified out.

## Note on `designing-tech-lead-handoff`

This skill was renamed from `tl-design-from-brief` (2026-05-28). The S2 `skill_ref`
in both workflow files was updated to the current name as part of this
consolidation.
