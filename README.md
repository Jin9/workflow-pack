# Squad Delivery — Design Reference

![status](https://img.shields.io/badge/status-research%20%26%20design-blue)
![pipeline](https://img.shields.io/badge/pipeline-cognitive--os%2Fv1-6f42c1)
![live skills](https://img.shields.io/badge/live%20skills-28-success)
![dashboard](https://img.shields.io/badge/dashboard-offline--first-orange)

> **Visual core-plan:** open **`squad-delivery-dashboard.standalone.html`** — the
> self-contained, offline, interactive overview of the whole pipeline (stages, gates,
> event bus, test matrix, skill coverage, model roster, verdict). This `README.md` is the
> **textual companion** to that dashboard.
>
> **Stage-flow view:** the dashboard above is the canonical visual core-plan for all **27** pipeline nodes
> (stages, the parallel **BE ∥ FE** legs, and the colour-graded human gates). *(Retired 2026-06-07: the
> root `delivery-pipeline-flow.drawio` stand-alone view was removed to keep the root clean — recoverable
> from git history; the editable per-run architecture diagram lives under
> `tmp/runs/shoppilot/S2-tl-design/diagrams/`.)*
>
> **Agent/workspace guide:** `CLAUDE.md` remains the authoritative guide for working in this
> repository (subprojects, conventions, validation). This README is a *design reference* — the
> minimal steps to actually run the pipeline are in **How to run it** just below.
>
> **This file consolidates** the two former top-level design docs — `SQUAD_DELIVERY_WORKFLOW_DESIGN.md`
> (Part A) and `harness-engineer-workflow.md` (Part B) — refreshed to the **2026-06-02** state:
> the live pipeline lives under `workflows/` (the single canonical `workflows/delivery-pipeline.yaml` +
> `workflows/schemas/`); the **S1 BA-research composite is wired live** (**two stages** — `s1-discovery` →
> recommendation gate → `ba-research`);
> and the Rust `squad-engine` is archived, so **pipeline validation is now static** (YAML well-formedness +
> `ajv`/`jsonschema` on the boundary schemas + a `depends_on` graph check), plus an **optional offline
> `universal-spec-validator` gate** (command-safety / portability / capability heuristics; risk-tiered
> config + reports under `spec-review/`).
>
> **Hardened 2026-06-04:** all built `skill_ref`s in `workflows/delivery-pipeline.yaml` are **exact-pinned**
> (no caret ranges) and the three workflow-boundary schemas enforce root `additionalProperties: false`.
>
> **Demo run 2026-06-04:** the **S1 → S2.5** ShopPilot walkthrough is materialized under
> `tmp/runs/shoppilot/` — S1 re-stamped to the pinned skills, and **S1.5 / S2 / S2.5 produced**
> (S2.5 exercised the cap-1 plan-review loop-back: **REVISE → ADR-008 → PROCEED**). A new workspace
> utility, `.claude/skills/rendering-contract-debug-viewer/`, renders any contract JSON into a
> self-contained, offline, dashboard-themed debug viewer (light+dark, contract-aware badges, view-source).
>
> **Added 2026-06-06 — the Delivery Review Console.** `.claude/skills/rendering-delivery-review-console/`
> assembles **one** run-scoped, offline, byte-deterministic `delivery-review.html` per run folder — a single
> standalone document whose **left-nav menus are pipeline stages** (Epics&Stories · UX Brief · Design&ADRs ·
> Plan Review · Quality), **superseding the per-stage viewers** for review. Diagrams embed as offline **inline
> SVG** (a deterministic `.drawio`→`<svg>` transcoder, never a raster export) + a path chip; the 12 T-gates roll
> into a **Quality-Gate Board** (worst-of R/A/G). The design is recorded in
> `reference/plan/output-contract-and-review-design.md`, and the 3 missing boundary schemas
> (`workflows/schemas/{ux-intake,tl-design,plan-review}.json`) plus an additive `human_view` render-policy
> field are now in place. Demo: `tmp/runs/shoppilot/delivery-review.html`.
>
> **As of 2026-06-02** the retired trees — `agentic-delivery-pipeline/` and `business-analyse/` — live in
> the **sibling** `../archive/` directory (named `archive`, no leading dot, **outside** `workflow-pack/`);
> `design-diagram/` was **removed** (its house-style draw.io role is now the external `drawio` skill); and
> `tmp/runs/shoppilot/` holds a **full S0–S7 walkthrough demo** (one folder per stage; S4a/S4b now emit **real
> code** — 4 compiling+tested Go services under `S4a-backend/services/` and a runnable Vite/React SPA under
> `S4b-frontend/app/` — see that run's README, OI-004).
>
> **Refreshed 2026-06-06:** the optional `spec-review/` gate was re-run over the full post-build spec set
> (**104 specs**; tuned **0 block / 68 warn / exit 0**) and the deletable `templates-review/` review copy was
> removed. This README is now synced to the post-build reality reflected below — **28 live skills** (badge),
> the **S6 deploy pair** (`handoff-to-deploy` / `handoff-revoke`) **built + wired** (OI-002 closed), and the
> **12 T1–T12 test runners wired** (GAP-05 closed).
>
> **Added 2026-06-10 — workspace `AGENTS.md` + the `workflows-ui` subproject.** A new root
> `AGENTS.md` hoists workspace-wide agent boundaries (offline HTML, PII redaction, the
> `../archive/` off-limits rule, the skill/pipeline validation gates) and a `workflows-ui`
> subsection. `workflows-ui/` is a standalone Vite + React "HELL FACTORY" agentic-office
> sim (visual-only verification via headless Brave), independent of the delivery pipeline;
> its guidance is consolidated into the root `AGENTS.md` + `CLAUDE.md`.

---

# How to run it — quick start

The pipeline is runnable today: the runtime is **`engine/`** (Python asyncio + FastAPI; full API
surface in `engine/README.md`). **Replay mode is the token-free default** — no API keys, no LLM
calls, no Go/Node toolchain needed — and is the right first run. Live mode is per-stage opt-in
and spends real tokens.

## 0 · One-time setup

You need **Python 3.13**. (**Node ≥ 18** too, but only for the browser console in Option B.)

```bash
python3.13 -m venv engine/.venv
engine/.venv/bin/pip install pyyaml jsonschema fastapi uvicorn pytest httpx claude-agent-sdk

cd workflows-ui && npm install && cd ..        # optional — Option B only
```

Sanity check (token-free, seconds):

```bash
engine/.venv/bin/python -m pytest engine/tests -q      # expect: 38 passed
```

## Option A · Token-free replay — start here

Executes all **27 stages** (S0→S7 + the 12 T-gates) from the canned ShopPilot corpus.
Deterministic, offline, zero tokens:

```bash
engine/.venv/bin/python -m engine replay --run-id demo-1 --approve-as "Your Name"
```

`--approve-as` matters: every blocking gate requires a **named approver** — omit it and the run
(correctly) parks at the first gate. Output lands in `runs/demo-1/` (gitignored). Then prove the
run to yourself:

```bash
engine/.venv/bin/python -m engine validate-run runs/demo-1 --strict   # dual-schema oracle → all green
engine/.venv/bin/python -m engine verify-audit runs/demo-1            # hash-chained audit intact
```

For a human-readable review page, run the `rendering-delivery-review-console` skill over
`runs/demo-1/` — it assembles one offline `delivery-review.html` (stage menus + the
Quality-Gate Board).

## Option B · Drive it from the browser (HELL FACTORY console)

```bash
engine/.venv/bin/python -m engine serve --port 8000    # terminal 1 — engine API
cd workflows-ui && npm run dev                         # terminal 2 — UI on http://localhost:5173
```

Open http://localhost:5173 and press **`C`** for the console overlay: submit a request
(new-product | fix | enhance · **replay** or live), watch the agents walk to the stage rooms as
the run progresses, and clear blocking gates from the **gate inbox** — the API rejects any
verdict without a named approver (HTTP 422). Engine down? The sim keeps running autonomously.

Single-server alternative: `cd workflows-ui && npm run build` once, then `serve` alone hosts the
built UI at http://localhost:8000.

## Option C · Live mode — real LLM stages (opt-in, spends tokens)

`mode=live` reads `engine/config/runtime-binding.yaml`; any stage **not** listed there stays on
replay, so the live surface grows one stage at a time. Live today: S0 (haiku), S1a/S1b, the
design leg, and both code reviews (headless `claude -p`); **T1/T3 execute the real test suites**
(`go test -race`, `vitest`) with no LLM in the loop.

Extra prerequisites for live: the `claude` CLI installed and logged in; for T1/T3, a Go
toolchain on PATH and a one-time `npm install` inside `tmp/runs/shoppilot/S4b-frontend/app/`.

Start it from the console (Option B → pick **live**) or straight from the API:

```bash
curl -X POST http://localhost:8000/api/runs -H 'content-type: application/json' \
  -d '{"raw_request": "…your requirement…", "requester": "Your Name", "mode": "live"}'
```

Two behaviours are **by design** — do not "fix" them: live stages spend real tokens (confirm
scope before binding more stages live), and a regulatory-scoped request will **not** go green
autonomously — the red-team gate BLOCKs governance gaps until a named human clears them (gate
inbox in the console, or `POST /api/runs/{id}/gates/{stage}/verdict`).

---

# Part A — Squad Delivery supervision design (Raw Requirement → Production)

> **What this is.** A *supervision-design artifact*: it records and recommends **how the AI delivery
> squad is supervised** — its stages and owners, where the human approval gates sit, the never-do
> guardrails, the command-safety policy, accountability for AI output, observability, and
> failure/recovery. **It does not run, deploy, or operate the pipeline**, and it never relaxes a gate
> on the agent's behalf. A **named human is the accountable owner of record** for everything the
> squad produces.
>
> **Grounded in:** the single canonical `workflows/delivery-pipeline.yaml` (15-stage; the former
> `squad-delivery.yaml` mirror was consolidated into it on 2026-06-02) · `DELIVERY_WORKFLOW_PLAN.md`
> v2.3 *(archived)* · the squad-flow v0.7 ShopPilot
> dry-run *(archived)*. **Date:** 2026-05-30 · refreshed 2026-06-02 · **Author of record:** *(pending — see sign-off)*

## Goal & autonomy level
**Goal.** Turn a raw banking/product requirement into a production-ready application through a
supervised AI squad, end to end (Intake → BA → Design → Implement → Review → QA → Deploy →
Prod-Validation).

**Autonomy. L3 — assisted-autonomous.** *Human-on-the-loop (HOTL, monitor + exception)* **inside** a
phase where the work is reversible; *Human-in-the-loop (HITL, approve each)* **at every irreversible
boundary**. **Deploy (S6) and Prod-Validation (S7) require synchronous named-human approval regardless
of agent confidence.** Reversible artifact-producing stages run exception-only.

## Pipeline stages  `stage → agent/skill → input → output → human owner`

| # | Stage | Agent / skill (ver) | Input | Output (artifact) | Reversibility | Human owner | Status |
|---|---|---|---|---|---|---|---|
| **S0** | Intake | orchestrator + Iteration-Planner | `raw_request, requester, idempotency_key` | normalized intake + approved run plan | reversible | **Delivery Ops** | ⚠ GAP (OI-003) |
| **S1a** | BA Discovery | `researching-ba-problem-space 1.0.0` | raw_request | `discovery` (framing · 4 product risks · regimes · recommendation) | reversible (gated decision) | **BA lead** | ✅ wired (live) |
| **S1b** | BA Brief | `eliciting-banking-brief 1.5.0` | discovery + raw_request | `epic, stories, governance_gaps, audit_id` | reversible | **BA lead** | ✅ wired (live) |
| **S1.5** | UX Intake | `generate-ux-pack 0.1.0` · dev-squad | epic, stories | `pack_dir, tokens, route_map, maturity, audit_id` | reversible | **Tech Lead** | ✅ wired |
| **S2** | TL Design | `designing-tech-lead-handoff 0.1.0` · dev-squad | epic, stories, gaps, ux | `component_map, api_contracts, audit_id` | reversible (high blast) | **Tech Lead** | ✅ wired |
| **S2.5** | **Plan-Review gate** | Plan-Reviewer (adversarial red-team) | BA + TL outputs | pass / reroute / **HardFail** | gate | **Tech Lead** | ✅ wired |
| **S3a/3b** | Contracts (BE/FE) | dev-squad | api_contracts | typed BE/FE contracts | reversible | **dev-squad** | ⚠ GAP (OI-003) |
| **S4a** | Backend Impl | `implement-backend-feature 1.0.0` | api_contracts, component_map | `go_files, test_files, audit_id` | reversible (sandbox) | **dev-squad** | ✅ wired |
| **S4a-r** | Backend Review | `review-backend-code 1.0.0` | go_files, contracts | `verdict, findings, audit_id` | reversible | **dev-squad** | ✅ wired |
| **S4b** | Frontend Impl | `implement-frontend-feature 1.0.0` | api_contracts, ux pack | `tsx_files, test_files, audit_id` | reversible (sandbox) | **dev-squad** | ✅ wired |
| **S4b-r** | Frontend Review | `review-frontend-code 1.0.0` | tsx_files, contracts | `verdict, findings, audit_id` | reversible | **dev-squad** | ✅ wired |
| **S4c** | QA Test Design | `planning-banking-tests 1.0.0` · qa-squad | epic, stories, review verdicts | `test_roster, signoff_criteria, audit_id` | reversible | **qa-squad** | ✅ wired |
| **S5** | QA Validation (execute) | `executing-qa-test-suite` · qa-squad | test_roster | pass/fail evidence | reversible | **qa-squad** | ✅ wired (T-gates); owner OI-003 open |
| **S6** | **Deploy** | `handoff-to-deploy 0.1.0` → release runner | signoff_criteria | `receipt_id, audit_id` + **live release** | **IRREVERSIBLE / control-plane** | **Release Manager** | ✅ wired (OI-002 closed) |
| **S7** | **Prod Validation** | ops + observability | live release | smoke/SLO verdict + rollback decision | **production-touching** | **On-call / Release Mgr** | ⚠ GAP (OI-003) |

**S1 BA Research is a discovery→brief composite** — shown above (and on the dashboard) as the two
cards **S1a · BA Discovery** and **S1b · BA Brief** — wired as two pipeline nodes in
`workflows/delivery-pipeline.yaml` with a human gate between: `s1-discovery`
(`researching-ba-problem-space 1.0.0` — problem framing · four product risks · regulatory regimes ·
a `proceed`/`needs-work`/`do-not-build` recommendation; **AI drafts, a named human decides**) →
`ba-research` (`eliciting-banking-brief 1.5.0` — the brief + a **3-level ref chain**: `INDEX.json`
manifest → one `EPIC-*` file per epic → one `STORY-*` file per story; nothing inlined). Boundary
schemas: `workflows/schemas/discovery.json`, `workflows/schemas/ba-brief.json`.

**S4 internal fan-out** (deterministic orchestrator): per component →
`Tech-Designer → Dev → {QA-L1 ‖ Reviewer-L1}`; then a single **Layer-2 barrier** →
`QA-L2 ‖ Reviewer-L2`. *(Real run: 8 components, ~38 sub-agent dispatches, terminal `ShipWithCaveats`.)*

## Per-stage I/O & JSON output-contract policy
Every stage hands off a **schema-validated JSON contract** carrying `audit_id`. **12 of 14 stages emit
a pure JSON contract** the downstream agent consumes directly (deterministic, cheaper, replayable). The
**2 implementation stages (S4a/S4b)** are the exception: they emit **code artifacts referenced by a JSON
manifest** (`backend-artifacts.json` / `frontend-artifacts.json`). The **exactly-one-writer** rule holds
for every artifact (verified in the ShopPilot run). Live boundary schemas live in `workflows/schemas/`.
**Boundary-schema closure (2026-06-04):** `delivery-pipeline-input.json`, `delivery-pipeline-output.json`,
and `discovery.json` now enforce root `additionalProperties: false` (OpenAI strict-mode cross-vendor
portability); per-stage sub-schemas and `ba-brief.json` (the manifest layer) stay open by design.

**Lean decision (2026-05-31 — Codex GPT-5.5 xHigh brainstorm, Claude final decision):** the 3 autonomous
stages — **S3a/3b Contracts · S4a Backend Impl · S4b Frontend Impl** (no human gate, machine-only
consumer) — are **JSON-only**: their human-readable template is **advisory** (kept, not deleted). All 11
human-gate stages stay dual-output (the signed doc is audit evidence).

### Human verification checkpoints & review documents
A **named human verifies at every design / review / QA / deploy boundary** — **11 of 14 stages**, each
with a concrete review document.

| Stage | Human owner of record | Gate type | Review document the human signs |
|---|---|---|---|
| S0 Intake | Delivery Ops | light (plan sign-off) | Run plan |
| S1a BA Discovery | BA lead | HITL on the `proceed`/`needs-work`/`do-not-build` recommendation | Discovery review doc (problem-space layer) |
| S1b BA Brief | BA lead | async peer (L2) | Four-layer pack · one unified HTML viewer |
| S1.5 UX Intake | Tech Lead | async peer (L2) | UX pack maturity report |
| **S2 TL Design** | Tech Lead + governance | **sync named (L3)** | TL Design doc + ADRs |
| S2.5 Plan-Review | Tech Lead | HITL on HardFail | Plan-review findings |
| S4a-r Backend Review | dev-squad | async peer (L2) | Backend review report |
| S4b-r Frontend Review | dev-squad | async peer (L2) | Frontend review report |
| **S4c QA Test Design** | qa-squad lead | **sync on conditional-go (L3)** | Test plan & sign-off criteria |
| **S5 QA Validation** | qa-squad lead | **sync (L3)** | QA evidence report |
| **S6 Deploy** | **Release Manager** | **sync named (L3) — mandatory, confidence-independent** | Release runbook + KNOWN_ISSUES + sign-off packet |
| **S7 Prod Validation** | On-call / Release Mgr | **sync (L3)** | Smoke/SLO report + rollback decision record |

Fully autonomous (no human review): **S3a/3b Contracts · S4a Backend Impl · S4b Frontend Impl** —
reversible, schema-validated, sandboxed. The per-stage human-review templates remain in the archived
(sibling) `../archive/agentic-delivery-pipeline/reference/integration/templates/` tree (not yet recreated
under `workflows/`). The S1 human-view is a self-contained offline **HTML viewer** rendering the four-layer
pack (discovery · brief · epics · stories); demoed inside the **full S0–S7 ShopPilot walkthrough** under
`tmp/runs/shoppilot/` (S1 is **two folders** — discovery at `tmp/runs/shoppilot/S1a-ba-discovery/`, the brief/epic/story pack + unified viewer at `tmp/runs/shoppilot/S1b-ba-brief/`).

## Topology — orchestrator-worker (single-agent default; every handoff justified)
A **deterministic, code-not-LLM orchestrator** dispatches and routes by `(diagnosis_tag, severity)`,
manages per-edge cycle caps, owns the worker pool, and is the **only barrier** at Layer-2. The
single-agent default is overridden only where justified:

| Handoff | Justification |
|---|---|
| BA → TL → QA (sequential) | Phase boundary + context handoff; not parallelism. |
| Fan-out (TD/Dev/QA-L1/Rev-L1 × N components) | **Genuine parallelism** — N independent components. |
| QA-L1 **vs** Reviewer-L1 (parallel per component) | **Security-domain separation** — conformance vs quality+security. |
| Plan-Reviewer (S2.5) | **Adversarial separation** — red-team the plan *before* expensive fan-out. |

## Model / tier policy (per `DELIVERY_WORKFLOW_PLAN.md` v2.3, archived)

| Tier | Hallucination tolerance | Default model | Where overridden |
|---|---|---|---|
| **T1 Banking/regulated** | <5%, 7-yr audit | **Claude Opus 4.8** dominant | — |
| **T2 Production** | <15%, balanced | hybrid | **GPT-5.5** for structured contracts (3a), QA test-design (4c), long-log prod-validation (7); Opus for impl/review |
| **T3 Research** | <30%, cost-preferred | **Gemini 3.1 Pro** | GPT-5.5 if web/long-context (>500K tok) |

Each agent runs under a **distinct identity with a pinned model id + version**, behind a vendor-neutral
abstraction with a declared fallback. Models are assigned by capability-to-role and data-class — never a
single "best model". Re-evaluate the roster quarterly (next ~2026-08-31).

## Approval gates  `action → reversibility / blast radius → gate → who`

| Action | Reversibility / blast | Gate | Approver |
|---|---|---|---|
| BA / UX / TL artifacts, Impl, Reviews, QA-design | reversible files | **AUTO** — L0 schema + L1 verify, then **async peer L2** | stage owner |
| **Plan-Review (S2.5)** | cheap to reverse, **high blast on a bad plan** | automated cap (1) + **HITL on HardFail** | Tech Lead |
| **TL Design (T1)** | ripples to N components | **L3 — sync named approval** | Tech Lead + governance |
| Implementation sign-off / conditional-go | release-gating | **L3 — sync** | dev-squad lead |
| **Deploy (S6)** | **irreversible / control-plane / production** | **L3 — SYNC NAMED APPROVAL, mandatory, confidence-independent** | **Release Manager** |
| **Prod Validation (S7)** | production-touching | monitored + **named rollback decision** | On-call / Release Mgr |

**Review levels:** L0 schema/idempotency (auto) · L1 skill-execution verify (auto/hybrid) · L2
peer/cross-squad (async human) · L3 executive/governance (sync named human). Depth scales by tier (T1 deepest).

## Command-safety policy (enforced *outside* the model, at the tool-calling layer)

| Tier | Scope |
|---|---|
| **ALLOW** | reversible & sandboxed: run tests in sandbox, read-only repo access, schema validation |
| **CONFIRM** | irreversible / control-plane: push to main · **deploy** · DB/schema migration · enabling a live external dependency · frontend publish |
| **DENY** | outside allowlist: non-allowlisted MCP/tool · network egress outside the sandbox allowlist · long-lived secrets · writing to prod directly · an **agent editing its own `AGENTS.md` / profile / permission config** |

> **Current state (honest):** the archived pipeline's `.claude/settings.json` allowlisted only
> `Bash(squad-engine run:*)`. There is **no external policy engine** enforcing CONFIRM/DENY tiers yet
> (→ verdict #3). With `squad-engine` archived, the day-to-day surface is **static validation**, not a run.

## Never-do guardrails (harness / policy-engine enforced — not prompt-only)
The agent must **NEVER**:
- Deploy or push to main **without a synchronous named-human approval**.
- Approve its own PR, its own findings, or modify its own permission config / `AGENTS.md` / profile.
- Treat untrusted content (`raw_request`, story text, PR titles, issue bodies, tool descriptions) as
  **instructions** — it is **data**.
- Echo or persist **real PII** (banking-grade rule).
- **Fan out on a failed Plan-Review** (→ HardFail).
- Exceed a **per-edge cycle cap** (must terminate, not loop).
- **Auto-resolve a governance / P1 blocker** (→ human).

## Accountability map
AI output → **distinct agent identity + pinned model version** → **`audit_id` (UUID)** stamped on every
stage output → **named human owner of record** (the per-stage owner above). The squad **recommends**;
humans **decide, commit, and deploy**. Prefer **signed provenance** over anthropomorphic AI
co-authorship; reasoning traces are **context, not evidence**.

## Observability
- **One correlation id** — `audit_id` (UUID) — threads every stage output and handoff.
- Log **both halves of the loop**: the **model request** (prompt + model id/version + reasoning effort)
  **and** the **tool effect** (what was actually written/run), under that single id.
- Audit store must be **append-only / hash-chained (tamper-evident)** with model version recorded.

> **Current state (honest):** no `agent.trace.v1` schema and no tool-effect logging at a gateway yet (→ GAP-14).

## Handoff contract (versioned typed payload; exactly one writer per artifact)
Per-stage JSON schemas (`discovery`, `ba-brief`, `ux-intake`, `tl-design`, `backend-artifacts`,
`backend-review`, `frontend-artifacts`, `frontend-review`, `qa-plan`, `handoff-receipt`). Every payload
carries the six contract fields: **task/intent** (`skill_ref` + `stage_type`) · **state** (artifact
paths) · **confidence** (`verdict`/`findings`) · **provenance/trace id** (`audit_id`) · **schemaVersion**
(`metadata.version`). **Sole-writer rule:** exactly one owner mutates a given artifact. Pipeline-boundary
input requires `raw_request, requester, idempotency_key`; output requires
`epic_brief, backend_artifacts, frontend_artifacts, qa_plan, audit_id`.

## Failure & recovery (state machine with explicit failure paths)
- **Transient** → `retry` (max 2, exponential backoff). **Fundamental** → `loop_back` (review ↔ impl,
  `max_loops` = 2). **Exhaustion** → named **human-queue (DLQ)**. `tl-design` / `handoff-notify` →
  **no retry → human-queue** (irreversible-adjacent).
- **Per-edge cycle caps:** Plan-stage→BA/TL = **1** (else HardFail) · Dev↔Tech-Designer = **2** ·
  Reviewer-L1↔Dev = **2** · Reviewer-L2↔TL = **1** · QA-L2→TL/BA = **1**.

**Terminal states:** **Done** 🟢 (all clean) · **ShipWithCaveats** 🟡 (per-edge cap hit, no *required*
component with unresolved **high** — the ShopPilot dry-run outcome) · **Failed** 🔴 (cap hit **and** a
*required* component has unresolved **high**) · **HardFail** 🔴 (Plan-Reviewer cap exceeded — do **not**
fan out on a bad plan).

Recovery infra: idempotency via `idempotency_key`; compensation enabled (600s) with `handoff-revoke`
compensating action (**built + wired 2026-06-06 — OI-002 closed**). HITL escalation is the final recovery tier. *(No
replay/checkpoint/idempotency-recovery runtime today → GAP-15; the Rust `squad-engine` that provided this
is archived.)*

## Event-driven choreography model
Each stage **subscribes to** input artifacts (events) and, on completion, **emits** a past-tense event
carrying its JSON contract. The correlation/partition key is **`run_id`** (= `audit_id`): all events for
one run hash to one partition → **per-`run_id` FIFO ordering**. Delivery is **at-least-once + idempotent
consumer = effectively-once** (not exactly-once, which is a myth). "Persist output **and** emit event" is
made atomic by the **transactional outbox**. Pipeline entry is a **Command** (`CreateDeliveryRun`, can be
rejected); every stage output is an **Event** (past-tense fact). **Hybrid orchestration/choreography:** the
deterministic orchestrator drives the **critical path**; cross-cutting reactions (audit log, notifications,
metrics, artifact archival) are **choreographed** off the same events.

**Event catalog (topic · producer · subscribers):** `raw_request`→S0,S1a · `ba.discovery`→S1b · `ba.brief`→S1.5,S2,S2.5,S4c ·
`ux.pack`→S2,S4b · `tl.design`→S2.5,S3,S4a,S4b,S4a-r,S4b-r · `be/fe.artifacts`→reviews ·
`be/fe.review`→S4c · `qa.plan`→`qa.evidence`→`deploy.receipt`→`prod.validated`. **Deploy is a saga with a
pivot:** pre-pivot steps compensate (`handoff-revoke`); past the pivot only a forward-only reversal is
legitimate.

### Shared-input reuse & parallel-collapse waves
- **`tl.design` → 6 consumers** (S2.5, S3a/3b, S4a, S4b, S4a-r, S4b-r) — headline fan-out: after
  `plan.reviewed` passes, **backend (S4a) ∥ frontend (S4b) ∥ contracts (S3)** run concurrently (× N components).
- **`ba.brief` → 4 consumers** (S1.5, S2, S2.5, S4c) · **`ux.pack` → 2** · **`raw_request` → 2**.
- **Joins / barriers:** S4c waits for `be.review` ∥ `fe.review`; the single Layer-2 barrier waits for
  QA-L2 ∥ Reviewer-L2 before a terminal state.

## Real-world SDLC mapping (SIT/UAT/PRD · progressive delivery · four-eyes)

| Squad stages | SDLC phase | Environment / mechanism | Gate / governance |
|---|---|---|---|
| S0–S3 Intake→Contracts | Requirements & Design | pre-code; DDD command/event, bounded contexts | async peer + TL sync ★ |
| S4a/S4b Impl | Development | immutable artifact + unit tests, sandboxed | AUTO |
| S4a-r/S4b-r Review | Pre-merge CI | unit/integration/**contract (Pact)** + schema-registry FULL | async peer (maker ≠ checker) |
| S4c/S5 QA | **SIT → UAT** | contract tests; feature-flag pilot | sync ★ on conditional-go |
| S6 Deploy | Release | **canary / blue-green + AnalysisTemplate**; OpenFeature kill-switch | **sync named ★★** — four-eyes / maker-checker |
| S7 Prod Validation | Operate | **SLO multi-window burn-rate** (14.4×/1h · 6×/6h · 3×/24h); DORA; rollback | sync ★ rollback decision |

**Banking governance overlay:** human-verify gates implement **maker-checker / four-eyes /
segregation-of-duties**; the event log is an immutable, append-only, signable **audit trail** — a
legally-defensible record of who approved what, when.

## Test & quality gates — coverage matrix
**Finding (updated 2026-06-06):** the squad **designs** tests well (S4c `planning-banking-tests` emits a
unit/integration/contract/E2E/smoke roster + NFR derivation) **and now executes them in-pipeline** — the 12
runners below are **wired as the T1–T12 test gates** in `workflows/delivery-pipeline.yaml` (**GAP-05 closed**).

**Measurement method.** A **runner skill + auto-gate tier is defined for every test type** — see the archived
`QUALITY_GATE_MEASUREMENT.md`. The method **measures each result against
an explicit threshold, auto-passes on green, and escalates only exceptions** (FAIL · Marginal · flaky · new
high-severity · `can_i_deploy=false`) to a human — collapsing per-test review into a single **aggregate
sign-off at S5 / S4c** (HITL stays at the irreversible S6/S7 boundaries). **The runners are now wired into
`workflows/delivery-pipeline.yaml` as T1–T12 (GAP-05 — test-runner wiring — closed 2026-06-06).**

| Test type | Level | Runner skill | Gate | Status |
|---|---|---|---|---|
| Unit — Backend / Frontend | unit | `executing-backend-unit-tests` / `executing-frontend-unit-tests` | auto | wired (T1–T12) |
| Integration | integration | `executing-integration-tests` | auto+exc | wired (T1–T12) |
| Contract (Pact / CDCT) | contract | `contract-testing-pact` | auto | wired (T1–T12) |
| End-to-end (E2E) | e2e | `authoring-e2e-test-suite` | auto+exc | wired (T1–T12) |
| Security — SAST / code | security | `running-sast-security-gate` | auto | wired (T1–T12) |
| Security — DAST / SCA / secrets | security | `scanning-appsec-pipeline-gate` | auto | wired (T1–T12) |
| Security — adversarial / pentest | security | `validating-banking-implementation` (persona) | human | wired (T1–T12) · human review-only |
| Performance / Load | performance | `running-performance-load-test` | auto | wired (T1–T12) |
| Accessibility (WCAG 2.1 AA) | a11y | `running-accessibility-tests` | auto+exc | wired (T1–T12) · OI-004 open |
| Smoke / sanity | smoke | `running-smoke-tests` | auto | wired (T1–T12) |
| Canary analysis | progressive | `analyzing-canary-rollout` | auto+exc | wired (T1–T12) |
| SLO validation (prod) | slo | `validating-production-slo` | auto+exc | wired (T1–T12) |

## Verdict: **CONDITIONAL — DESIGN READY** for human sign-off once these GAPS close
1. **Deploy (S6) & Prod-Validation (S7)** get a **named approver** + stage owners (**OI-003**, still open).
   The `handoff-to-deploy` / `handoff-revoke` skills (**OI-002**) are now **built + wired** (closed 2026-06-06).
2. **Deploy credentials → short-lived OIDC tokens** (no long-lived secrets) before the deploy gate is enabled.
3. **External allow/confirm/deny policy engine** stood up.
4. **`agent.trace.v1`** tamper-evident, both-halves audit (**GAP-14**) + **typed HITL approval records** (**GAP-13**).
5. **Test-execution layer:** wire **S5 QA-execution (GAP-05)** for unit/integration/contract; add **E2E**
   (Playwright), **security DAST/SCA** (Semgrep/Trivy/Trufflehog), **performance/load** (k6), **a11y**
   (axe — closes OI-004), and **canary analysis** (Argo AnalysisTemplate).

### Runtime status vs these gaps (2026-07-04 — the pipeline now RUNS: `engine/`, ADR in `.claude/history/`)
A local Python runtime executes this design (replay default; per-stage live opt-in). Against the five gaps:
**#3 partially closed** — command safety is enforced outside the model via per-stage tool allowlists /
permission modes (`engine/config/command-policy.yaml`); a full standalone policy engine remains open.
**#4 functionally covered** — hash-chained both-halves `events.jsonl` + typed named-approver
gate/resolution records (the `agent.trace.v1` name is not used). **#5 partially closed** — T1/T3 run the
REAL suites via `engine/config/gate-runners.yaml` (`go test -race`, vitest); QA-execution (GAP-05),
E2E/DAST/perf/a11y/canary runners remain open. **#1 and #2 stay open** (named approvers + OIDC are org
decisions) — the engine keeps S6/S7 permanently human-queued behind sync-named gates until they exist,
and the S6 SAGA (`handoff-revoke`) is live-proven with a schema-valid revoke receipt.

## Skill coverage (per SDLC step)
Produced by the **`squad-skill-gap` workflow** (53 agents): each of 26 steps mapped to
the former `skill-packs/manifest.json`, confirmed against the ResearchVault, web-grounded where the vault was thin.
All 18 gap-fill skills were built (draft); coverage was **26/26 ✓**. **As of 2026-06-02 the skill
catalog was consolidated by actual use:** the 14 skills the live pipeline references now live in
`workflows/skills/` (see `workflows/skills/README.md`); the ~100 unused skills (incl. the 13 unused
gap-fill skills and the old `manifest.json`) were quarantined and then **deleted** — permanently, since
this workspace has no git and the upstream `treasury/` is not present here. Two skills are **promoted + wired live**:
`researching-ba-problem-space 1.0.0` (S1 `s1-discovery`) and `eliciting-banking-brief 1.5.0` (S1
`ba-research`). Wiring the remaining draft runners into `workflows/delivery-pipeline.yaml` is a separate step.

## Human approval gate (sign-off)
**Stop.** A human owns and signs off this supervision design and remains the **accountable owner of record**
for everything the squad produces. This artifact drafts and recommends only.

- Design author of record: __________________________  Date: __________
- Release Manager (owns S6/S7 gate): _______________  Date: __________
- Governance / risk sign-off (T1): _________________  Date: __________

---

# Part B — Harness Engineer · Agent Scaffold Workflow

## The role and scope
A **harness engineer** owns the *agent harness/scaffold* — the supervisory infrastructure that lets
autonomous agents run safely and accountably: the pipeline stages, the human approval gates, the handoff
contracts, the boundaries, the sandbox, and the run loop. There is no single "harness engineer" skill; the
role is assembled from **8 in-scope skills** drawn from two folders — `design-time-orchestrators/`
(architect the supervision) and `pack-G-agent-scaffold/` (build and run the scaffold). This scopes to the
**agent harness/scaffold** sense of "harness" — not the *test harness* (skill validation) sense, and not
the broader BA/build/QA delivery packs.

## Curated in-scope skills

| # | Skill | Folder | Phase | Role in the harness | Key output | Gate |
|---|-------|--------|-------|---------------------|------------|------|
| 1 | `agentic-workflow-design` | design-time-orchestrators | Design | Supervision design: stages·owners·gates·guardrails·command-safety·observability·failure-recovery | Agentic Workflow Design artifact + verdict | Human sign-off (DESIGN READY) |
| 2 | `multi-agent-handoff-architect` | design-time-orchestrators | Design | Handoff contracts: topology, binary single-writer ownership, 6-field JSON Schema | handoff doc · topology record · `handoff-contract.schema.json` | Schema self-check must PASS |
| 3 | `composing-agent-pipelines` | design-time-orchestrators | Design | Reference phase shape: Plan·Gather·Analyze·Review·Validate·Decide·Compact | versioned phase artifacts under `.agent-pipelines/` | Plan + Decide hard approval gates |
| 4 | `agent-context-initializer` | pack-G-agent-scaffold | Build | The control surface: `AGENTS.md` (boundaries, squad-roles) | `AGENTS.md` + curation checklist | Human curation of checklist |
| 5 | `authoring-scaffold-profile` | pack-G-agent-scaffold | Build | Profile: STAGES·GATED_STAGES·per-stage AGENT/MODEL/PROMPT_PREFIX | `profiles/NAME.sh` | LiteLLM/runner validation; no silent overwrite |
| 6 | `drafting-stage-prompt` | pack-G-agent-scaffold | Build | Curated stage prompts (why-it-works, metric, failure mode) | `prompts/library/STAGE/TOPIC.md` | No overwrite without confirm |
| 7 | `configuring-sandbox-allowlist` | pack-G-agent-scaffold | Build | Egress allowlist for the sandboxed implement runner | `docker/sandbox-proxy/filter` | Default-deny; refuses wildcards/IPs; rebuild + egress-test |
| 8 | `orchestrating-agent-scaffold` | pack-G-agent-scaffold | Run | Operate the run: profile/cap/sandbox, `just workflow`, monitor `state.json` | live run through research→…→test | Never auto-approves; honors AGENTS.md; 🔒 implement gate |

**Adjuncts (standalone — not part of the 8):**
- `authoring-workflow-postmortem` — closes the loop, feeding profile/prompt/allowlist edits back into Build.
- `reviewing-implement-gate` — decides *whether* to approve the 🔒 implement gate at run-time.

## Workflow diagram

```
HARNESS ENGINEER — Agent Scaffold Workflow
8 in-scope skills · 3 phases · postmortem feedback loop

INPUT: a goal/initiative + the agents, tools, credentials, data, and the
       reversible-vs-irreversible actions in play
   |
   v
+======================= PHASE 1 · DESIGN-TIME =======================+
|  Architect the supervision before any scaffold exists              |
|  (design-time-orchestrators)                                       |
|    agentic-workflow-design   => Agentic Workflow Design            |
|        |                        [verdict: DESIGN READY / GAPS]     |
|        v                                                           |
|    multi-agent-handoff-architect => handoff doc · topology ·       |
|        |                            handoff-contract.schema.json   |
|        v                                                           |
|    composing-agent-pipelines  => versioned phase artifacts         |
+========|===========================================================+
         |  design approved (human sign-off)
         v
+======================= PHASE 2 · BUILD-TIME ========================+
|  Instantiate the scaffold from the approved design (pack-G —       |
|  independent skills, can run in parallel)                          |
|    agent-context-initializer  => AGENTS.md + curation checklist    |
|    authoring-scaffold-profile => profiles/NAME.sh (STAGES·GATED·   |
|                                  MODEL · sets *_PROMPT_PREFIX)      |
|    configuring-sandbox-allowlist => docker/sandbox-proxy/filter    |
|    drafting-stage-prompt      => prompts/library/STAGE/TOPIC.md    |
+========|===========================================================+
         |  scaffold ready (AGENTS.md · profile · prompts · allowlist)
         v
+======================= PHASE 3 · RUN-TIME ==========================+
|  Operate the scaffold — never edits state, honors AGENTS.md gates  |
|    orchestrating-agent-scaffold                                    |
|      research --> plan --> critique --> [LOCK] implement -->       |
|                                  review --> test                   |
|                          human approval gate                       |
|                          (reviewing-implement-gate)               |
+========|===========================================================+
         |  run complete
         v
   authoring-workflow-postmortem  (standalone adjunct)
   what to change next run --> feedback: profile/prompt/allowlist edits
                           --> back to PHASE 2
```

## Notes
**Why these 8 (and what's excluded).** The scope is "design and run the agent scaffold," so it pulls the
three `design-time-orchestrators/` skills (supervision, handoffs, pipeline shape) and all five
`pack-G-agent-scaffold/` skills (AGENTS.md, profile, prompts, sandbox, orchestrator). Deliberately
excluded: the delivery packs that *use* a harness rather than build one (BA pipeline, banking brief,
OpenClaw squad, TL design & build) — and the *test-harness* validation tooling, a different sense of "harness."

**The feedback loop.** Each Phase-2 build skill anticipates change after a postmortem or a workflow
win/loss. `authoring-workflow-postmortem` captures those findings and routes them back into Build — making
the harness iterative, not one-shot.

**Human gates are the spine.** Three non-negotiable checkpoints define the harness: (1) **DESIGN READY**
sign-off ends Phase 1; (2) **AGENTS.md** boundaries (always-allowed / requires-approval / prohibited)
govern Phase 2–3; (3) the **🔒 implement gate** in Phase 3 is never auto-approved —
`orchestrating-agent-scaffold` refuses to `just approve` on the user's behalf, and
`reviewing-implement-gate` informs the human's approve/reject decision.
