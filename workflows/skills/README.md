# workflows/skills/

The skills the live delivery pipeline actually uses. Each is referenced from
`../delivery-pipeline.yaml` (the single canonical workflow file) as
`skill_ref: skills/<name>` — resolved **relative to the workflow file's dir**, so
the ref points here.

Consolidated on **2026-06-02** from the former `skill-packs/` staging copy: only
the skills the pipeline references were kept; the ~100 unused skills (and the old
`manifest.json`) were quarantined and then **deleted** — permanently, since this
workspace has no git and the upstream `treasury/` source is not present here.

## Skills (14) — origin and pipeline stage

| Skill | Pipeline stage | Came from (old `skill-packs/` path) |
|---|---|---|
| scoping-ba-intake | S0 intake | `pack-A-ba-pipeline/` |
| researching-ba-problem-space | S1 s1-discovery | `squad-delivery-skills/` |
| eliciting-banking-brief | S1 ba-research | `standalone/` |
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

## Referenced but not yet built (OI-002)

The S6 release stage and its SAGA compensation reference two skills that do not
exist yet, so their `skill_ref`s remain dangling by design:

- `handoff-to-deploy` — S6 release-handoff
- `handoff-revoke` — S6 compensating action

Building these is the planned next task.

## Note on `designing-tech-lead-handoff`

This skill was renamed from `tl-design-from-brief` (2026-05-28). The S2 `skill_ref`
in both workflow files was updated to the current name as part of this
consolidation.
