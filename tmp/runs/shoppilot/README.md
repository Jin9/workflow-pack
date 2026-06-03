# ShopPilot MVP — pipeline run folder

> **Run:** `REQ-shoppilot-mvp` · single-merchant B2C storefront + back office (Thai market).
> **Pipeline:** the S0–S7 squad-delivery flow defined in [`squad-delivery-dashboard.standalone.html`](../../../squad-delivery-dashboard.standalone.html)
> (workspace root — the authoritative overview). This folder is the **project structure** for the run: one folder per
> stage, each the home for that stage's two artifacts — a schema-validated **JSON contract → next node** and a
> **human-review document**. One trace id (`audit_id`) threads every stage.

## Stage map

`gate` legend: `auto` machine pass/fail · `async` human confirms after the fact · `sync` named human approval before proceeding · `gate` adversarial review gate.
`status`: ✅ done · ⬜ pending · ⏸ deferred (gap tracked in the overview's OPEN_ISSUES — OI-002/OI-003/GAP-05).

| Stage | Name | Owner | Skill (`skill_ref`) | Consumes → Emits | Output contract | Gate | Human-view | Status |
|---|---|---|---|---|---|---|---|---|
| **S0** | Intake | Delivery Ops | `orchestrator + Iteration-Planner` | `raw_request` → `intake.normalized` | pipeline-input + run-plan | auto | markdown | ⏸ |
| **S1a** | BA Discovery | BA lead | `researching-ba-problem-space ^1.0.0` | `raw_request` → `ba.discovery` | `discovery.json` (recommendation gate) | async | md (discovery review doc) | ✅ |
| **S1b** | BA Brief | BA lead | `eliciting-banking-brief ^1.5.0` | `ba.discovery` → `ba.brief` | `ba-brief.json` (INDEX → EPIC-* → STORY-*) | async | HTML viewer + ref-chain JSON | ✅ |
| **S1.5** | UX Intake | Tech Lead | `generate-ux-pack ^0.1.0` | `ba.brief` → `ux.pack` | `ux-intake.json` (+ pack) | async | md (HTML viewer planned) | ⬜ |
| **S2** | TL Design | Tech Lead | `tl-design-from-brief ^0.1.0` | `ba.brief · ux.pack` → `tl.design` | `tl-design.json` (+ ADRs) | **sync (L3)** | **draw.io + markdown** | ⬜ *(structure drafted)* |
| **S2.5** | Plan-Review gate | Tech Lead | `Plan-Reviewer` (adversarial red-team) | `ba.brief · tl.design` → `plan.reviewed` | `plan-review.json` | gate | md (HTML viewer planned) | ⬜ |
| **S3a/3b** | Contracts (BE/FE) | dev-squad | `dev-squad` | `tl.design` → `contracts.published` | OpenAPI / typed JSON | auto | OpenAPI (JSON-only) | ⏸ |
| **S4a** | Backend Impl | dev-squad | `implement-backend-feature ^1.0.0` | `tl.design` → `be.artifacts` | `backend-artifacts.json` + Go code | auto | code + manifest (JSON-only) | ⬜ |
| **S4a-r** | Backend Review | dev-squad | `review-backend-code ^1.0.0` | `be.artifacts · tl.design` → `be.review` | `backend-review.json` | async | md (HTML viewer planned) | ⬜ |
| **S4b** | Frontend Impl | dev-squad | `implement-frontend-feature ^1.0.0` | `tl.design · ux.pack` → `fe.artifacts` | `frontend-artifacts.json` + TSX code | auto | code + manifest (JSON-only) | ⬜ |
| **S4b-r** | Frontend Review | dev-squad | `review-frontend-code ^1.0.0` | `fe.artifacts · tl.design` → `fe.review` | `frontend-review.json` | async | md (HTML viewer planned) | ⬜ |
| **S4c** | QA Test Design | qa-squad | `planning-banking-tests ^1.0.0` | `ba.brief · be.review · fe.review` → `qa.plan` | `qa-plan.json` | **sync** | md (HTML viewer planned) | ⬜ |
| **S5** | QA Validation | qa-squad | `qa-squad (execute)` | `qa.plan` → `qa.evidence` | qa-evidence (pass/fail) | **sync** | md + CSV (HTML viewer planned) | ⏸ |
| **S6** | Deploy | Release Manager | `handoff-to-deploy ^0.1.0 → release` | `qa.evidence` → `deploy.receipt` | `handoff-receipt.json` | **sync (irreversible)** | release runbook packet | ⏸ |
| **S7** | Prod Validation | On-call / Release Mgr | `ops + observability` | `deploy.receipt` → `prod.validated` | smoke/SLO metrics + rollback record | **sync** | md (HTML viewer planned) | ⏸ |

> Stage IDs `S3a/3b`, `S4a`, `S4b` are **JSON-only** autonomous stages (the human-view doc is advisory). Half-stages
> `S1.5` and `S2.5` and the `-r` review stages run inside the design/dev legs. The canonical per-stage human-view
> templates referenced by the overview now live (archived) under
> `.archive/agentic-delivery-pipeline/reference/integration/templates/`.

## What's here now

- **`S0-intake/`** — holds the **`raw_request`**: the raw business-only spec
  [`ecommerce_mvp_business_only.v3.md`](S0-intake/ecommerce_mvp_business_only.v3.md) **and** the gap-closed happy-path
  input [`ecommerce_mvp_business_only.gap-closed.md`](S0-intake/ecommerce_mvp_business_only.gap-closed.md) (all open
  questions + governance gaps closed; see [`gap-closure-ledger.md`](S0-intake/gap-closure-ledger.md)). Stage skill itself is ⏸ deferred (OI-003).
- **`S1a-ba-discovery/`** — ✅ the discovery layer: `discovery.json` (problem framing · the four product
  risks · regulatory regimes · `recommendation`) + `discovery-input.json`. The `proceed`/`needs-work`/`do-not-build`
  recommendation gate — only `proceed` releases S1b.
- **`S1b-ba-brief/`** — ✅ the brief + epic/story pack: `INDEX.json` (manifest) → `EPIC-*/EPIC-*.json` →
  `EPIC-*/STORY-*.json`, plus `brief.json` and the unified offline `ba-research-viewer.html` (all four layers;
  `discovery_file` → `../S1a-ba-discovery/`). 4 epics / 8 stories: **AUTH · CHECKOUT · ORDER · INVENTORY**.
- **`S2-tl-design/`** — ⬜ the **project-structure design** drafted ahead of the rest:
  [`project-structure.md`](S2-tl-design/project-structure.md) (the polyrepo Go + React layout),
  [`architecture-overview.md`](S2-tl-design/architecture-overview.md) (bounded contexts · component map · events · NFRs),
  and `diagrams/` (draw.io HLD + ERD, house style). This is **design intent, not code** — the actual Go/TSX is emitted later at S4a/S4b.
- **`S0`, `S1.5`, `S2.5`, `S3`, `S4*`, `S4c`, `S5`, `S6`, `S7`** — ⬜/⏸ empty homes awaiting their stage output (each carries a `README.md` describing its contract).

## Topology decided for this run

**Polyrepo · Go microservices (backend) + React/TS (frontend).** One Go service per bounded context, each stamped
from the [`repo-generator`](../../../repo-generator/) skeleton; a single React/TS app for storefront + admin. Full
trees and rationale in [`S2-tl-design/project-structure.md`](S2-tl-design/project-structure.md).

## Conventions (workspace rules that apply here)

- No real PII anywhere — redact as `<PII:REDACTED:CLASS=…>` (the S1 pack already follows this; persona names are synthetic).
- S2 diagrams are **raw draw.io XML in the house style — never Mermaid** (see `design-diagram/CLAUDE.md`).
- Offline-only: no `https://`, `src=`, or CDN references in any HTML artifact.
