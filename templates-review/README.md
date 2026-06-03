# Review-document templates — per stage (dual-output)

Every delivery-pipeline stage emits **two** artifacts:

1. **A JSON contract → the next node** — the machine handoff (schema-validated, deterministic, replayable, carries
   `audit_id`). Schemas live in [`../schemas/`](../schemas/). This is the *efficient* path between agent nodes.
2. **A human-readable review document** — rendered from the per-stage template in this folder, for the human review
   / sign-off gate. Markdown by default; **draw.io** (raw XML, house style) for architecture; **OpenAPI/typed** for contracts.

The JSON drives the next node; the templated doc drives the human gate. (Implements the follow-up noted in
`README.md` — "one fill-in template per gate".)

**Human-view → HTML (2026-05-31, per-stage policy).** The human review doc moves to a self-contained **offline HTML viewer**
**where review benefits from visualization** (findings · evidence · metrics · rosters · maturity). **S1 BA Research is the
first (built)** — now a **discovery→brief composite**: `S1a-ba-discovery/` (the discovery review doc — problem-space
framing · 4 product risks · regimes · the `proceed`/`needs-work`/`do-not-build` recommendation gate) → `S1b-ba-brief/`
(the four-layer pack, human-view `ba-research-viewer.html` rendering discovery · brief · epics · stories); the review /
evidence / maturity stages (S1.5 · S2.5 · S4a-r · S4b-r · S4c · S5 · S7) are next. Outputs whose native form *is* the right
human-view stay as-is: **OpenAPI / structured** contracts (API-Path · event · request/response), **code + manifest** for
implementation, **draw.io** house-style for architecture, and **markdown** for operational checklists (run plan · runbook).

**Leaning (2026-05-31).** A Codex GPT-5.5 (effort xHigh) brainstorm — with **Claude as the final decision-maker** —
marked the 3 **autonomous** stages **S3a/3b · S4a · S4b** as **JSON-only**: their readable doc is **advisory** (the
template is kept, not deleted; the JSON contract is unchanged), since their human-inspectable evidence already
surfaces at the adjacent S2 design / S4*-review gates. Rationale + per-stage verdict: [`LEAN_DECISION.md`](LEAN_DECISION.md).

## Stage → schema → template → reuse source

| Stage | Review document | JSON contract (schema) | Template | Reuse source |
|---|---|---|---|---|
| S0 Intake | Run plan | `../schemas/delivery-pipeline-input.json` + run-plan | `S0-run-plan.md` | new |
| S1a BA Discovery | **Discovery review doc** (problem-space) · gate on `recommendation` | `../schemas/discovery.json` | **`S1a-ba-discovery/`** (`discovery.template.json`) | **new** (`researching-ba-problem-space`) |
| S1b BA Brief | **Four-layer pack · unified HTML viewer** | `../schemas/ba-brief.json` (INDEX manifest → `EPIC-*` files → `STORY-*` files) | **`S1b-ba-brief/`** (viewer + INDEX/epic/story templates) | **references** BA story template; mirrors squad-flow `epic.md`/`story.md` |
| S1.5 UX Intake | UX pack maturity report | `../schemas/ux-intake.json` | `S1_5-ux-pack-maturity-report.md` | new |
| S2 TL Design | TL Design doc + ADRs | `../schemas/tl-design.json` | `S2-tl-design-index.md` | **references** the 12 `workflows/skills/designing-tech-lead-handoff/templates/` + the external `drawio` skill |
| S2.5 Plan-Review | Plan-review findings | `plan-review` object (no schema file — design gate) | `S2_5-plan-review-findings.md` | mirrors ref `plan-reviewer-finding.md` |
| S3a/3b Contracts | Typed contract spec · **JSON-only (advisory)** | OpenAPI / typed JSON (the contract itself) | `S3-befe-contract.md` | mirrors ref `api-spec.md`; composes `api-contract-design` + `universal-spec-validator` |
| S4a Backend Impl | Artifacts manifest · **JSON-only (advisory)** | `../schemas/backend-artifacts.json` | `S4a-backend-artifacts.md` | **references** `repo-generator/project-skeleton/` (+ `generate-repos.sh`) |
| S4a-r Backend Review | Backend review report | `../schemas/backend-review.json` | `S4a_r-backend-review-report.md` | mirrors ref `reviewer-finding.md` |
| S4b Frontend Impl | Artifacts manifest · **JSON-only (advisory)** | `../schemas/frontend-artifacts.json` | `S4b-frontend-artifacts.md` | **references** `implement-frontend-feature` structure |
| S4b-r Frontend Review | Frontend review report | `../schemas/frontend-review.json` | `S4b_r-frontend-review-report.md` | mirrors ref `reviewer-finding.md` |
| S4c QA Test Design | Test plan & sign-off | `../schemas/qa-plan.json` | `S4c-test-plan-and-signoff.md` | new |
| S5 QA Validation | QA evidence report | `qa-evidence` object (deferred, GAP-05) | `S5-qa-evidence-report.md` | mirrors ref `qa-report-csv.md` |
| S6 Deploy | Release runbook + KNOWN_ISSUES + sign-off | `../schemas/handoff-receipt.json` | `S6-release-runbook-packet.md` | new |
| S7 Prod Validation | Smoke/SLO + rollback record | smoke/SLO metrics (deferred, OI-003) | `S7-smoke-slo-rollback.md` | new |

"ref" = the **archived** `../archive/agentic-delivery-pipeline/reference/squad-flow-v0.7/docs/templates/` (off-limits without explicit permission); the per-template "mirrors ref" citations below are historical provenance.

## Reference-in-place — do NOT duplicate

These canonical sources are **referenced, never copied** (copying would break their invariants / single-source-of-truth):

- **BA story template** — **archived** `business-analyse/.../drafting-ba-stories/templates/` (sibling `../archive/`; byte-identical invariant; bilingual EN/TH) — reference via the live skill `eliciting-banking-brief` in `workflows/skills/`.
- **Microservice skeleton** — `reference/repo-generator/project-skeleton/` + `generate-repos.sh` (deterministic generator — invoke, don't copy).
- **draw.io house style** — the external **`drawio` skill** (raw draw.io XML, never Mermaid; versioned style-guide). The local `design-diagram/` subproject was removed.
- **TL-handoff sub-templates** — `workflows/skills/designing-tech-lead-handoff/templates/` (12 files; S2 composes them).
- **squad-flow-v0.7 blueprints** — **archived** `../archive/agentic-delivery-pipeline/reference/squad-flow-v0.7/docs/templates/` (off-limits; locked, versioned; templates mirror structure + cite).

## Conventions

- Fill every `<…>` and `TBD-<what>-<who>`; never fabricate values.
- **Never echo real PII** — redact as `<PII:REDACTED:CLASS=…>` (workspace banking rule).
- Every human-review template carries a **sign-off block** (reviewer · verdict · date · `audit_id`).
- `audit_id` threads the JSON contract and the review doc to the same run for the audit trail.
