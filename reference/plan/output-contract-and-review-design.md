# Output-Contract & Human-Review Design

> **What this is.** The supervision design for how the delivery pipeline *presents* each stage's work to a human
> reviewer — the **dual-output** scheme (a machine contract + a human-review surface) and the single **Delivery
> Review Console** that supersedes per-stage viewers. Companion to [`agentic-workflow.md`](./agentic-workflow.md),
> [`handoff-contracts.md`](./handoff-contracts.md), and [`governance-and-gates.md`](./governance-and-gates.md).
> This artifact **recommends and records**; it never runs, operates, or relaxes a gate. The console is **review
> tooling**, not pipeline operation — deploy-class actions still require a sync named human approval.

---

## 1. Problem & principle

Every stage emits a **dual output**: (a) a **schema-validated JSON contract** for the next node (the machine
handoff) and (b) a **human-review document**. Today only **S1b** (`ba-research-viewer.html`) and **S2.5**
(`plan-review.viewer.html`) have rendered viewers; every other stage is raw JSON a reviewer cannot easily read,
so the human gates downstream are reviewed against unrendered contracts.

| Principle | Rule |
|-----------|------|
| **Render only the not-readable** | Code, OpenAPI, markdown, and draw.io keep their **strong native form** — they are not re-rendered. Only stage outputs that are *unreadable as stored JSON* get a viewer. |
| **Presentation is re-derivable** | The human-review layer is a **re-derivable presentation surface**. On any conflict the **JSON contract is authoritative** (the same status `viewer-rendering-spec` assigns to `ba-research-viewer.html`). Deleting a viewer loses nothing the contract cannot regenerate. |
| **Machine layer stays sharded** | The contract keeps **one file per item under a thin INDEX, referenced by path, never concatenated** (context-window fit + mid-tier-model friendly). |
| **Offline always** | Every rendered surface is offline — no `https://`, `src=`, CDN, `@import`; web citations are bare host text. |

---

## 2. The single Delivery Review Console (the decision)

**Decision:** one **run-scoped** offline `delivery-review.html` whose left-nav menus are pipeline *concerns* (not a
viewer per stage). It supersedes the per-stage viewers for review; `rendering-contract-debug-viewer` is retained
for one-off **single-file debug** inspection. Each menu shows the stage's **gate badge + named owner** (§6).

| Menu | Source stage(s) | Sub-nav |
|------|-----------------|---------|
| **Overview** | run header + gate ledger | status · gates · counts |
| **menu1 · Epics & Stories** | S1a discovery + S1b brief | Discovery · Brief · each Epic → Story |
| **menu2 · UX Brief** | S1.5 | maturity · route map · components · microcopy · coverage matrix |
| **menu3 · Design & ADRs** | S2 | component map · api contracts (table) · event catalog · ADRs · L4 specs · diagram SVGs |
| **menu4 · Plan Review** | S2.5 | verdict · findings · bias checks |
| **menu5 · Contracts** | S3 | BE · FE endpoint tables |
| **menu6 · Impl & Reviews** | S4a/S4b + S4a-r/S4b-r | impl manifest · review findings |
| **menu7 · Quality** | T1–T12 + S5 | Quality-Gate Board (R/A/G) |
| **menu8 · Release & Prod** | S6 + S7 | receipt · SLO |
| **Provenance** | every stage | audit_ids · skill versions |

---

## 3. Per-artifact remediation matrix (the core table)

One row per node. **Disposition legend:** `FOLD` = rendered section inside the console · `DEDICATED` = its own
contract viewer · `NATIVE-md` / `NATIVE-OpenAPI` = native form is already the right human-view · `SPLIT-drawio` /
`SPLIT-ER-pack` = standalone artifact, referenced + inline-SVG preview · `leaf-gate-summary` = rolled into the
Quality-Gate Board.

| Node | JSON contract | Readable today? | Human-view disposition | Mechanism |
|------|---------------|-----------------|------------------------|-----------|
| **S0** Intake | run-plan | partial | **NATIVE-md** | run-plan markdown |
| **S1a** Discovery | `discovery.json` | no | **FOLD** discovery | console menu1 → Discovery |
| **S1b** Brief | `ba-brief.json` (INDEX→EPIC→STORY) | viewer exists | **FOLD** epics/stories *(reference impl)* | console menu1; `ba-research-viewer.html` is the proven render |
| **S1.5** UX Intake | `ux-intake.json` (+ pack) | no | **DEDICATED** ux-pack | manifest path-refs + p1/p2 findings + **two-way coverage matrix** (`ba_stories_without_ux_coverage` ⟷ `ux_routes_without_ba_story`) |
| **S2** TL Design | `tl-design.json` (+ ADRs) | no | **DEDICATED** design + **SPLIT-drawio** + **SPLIT-ER-pack** | `api_contracts` → **NATIVE-OpenAPI** endpoint table; ADRs/L4 NATIVE-md; diagrams inline-SVG |
| **S2.5** Plan Review | `plan-review.json` | viewer exists | **DEDICATED** *(reference impl)* | verdict · findings · bias checks; `plan-review.viewer.html` is the proven render |
| **S3** Contracts (BE/FE) | befe-contracts | n/a (deferred) | **NATIVE-OpenAPI** | BE/FE endpoint tables |
| **S4a** Backend Impl | `backend-artifacts.json` + Go | code | **NATIVE-md** code manifest | manifest table, path-refs to code |
| **S4b** Frontend Impl | `frontend-artifacts.json` + TSX | code | **NATIVE-md** code manifest | manifest table, path-refs to code |
| **S4a-r** Backend Review | `backend-review.json` | no | **DEDICATED** review-findings | severity-graded findings table |
| **S4b-r** Frontend Review | `frontend-review.json` | no | **DEDICATED** review-findings | severity-graded findings table |
| **S4c** QA Test Design | `qa-plan.json` | no | **NATIVE-md** | roster + sign-off criteria checklist |
| **S5** QA Validation | qa-evidence | n/a (deferred) | **DEDICATED** *(later)* | pass/fail evidence viewer when execution node lands |
| **S6** Deploy | `handoff-receipt.json` | yes | **NATIVE-md** runbook + receipt | runbook + KNOWN_ISSUES + receipt |
| **S7** Prod Validation | smoke-slo | n/a (deferred) | **leaf-gate-summary** | SLO row on the board |
| **T1–T12** test/security gates | per-gate `*.json` verdict | yes | **leaf-gate-summary** | all roll into the **Quality-Gate Board** (R/A/G) |

**Verdict-vocabulary note (do not normalise away).** Three vocabularies coexist and the board must render each
literally: **T10** `pass | conditional | fail` · **T12** `promote | hold | rollback` · all other T-gates
`PASS | FAIL | ERROR`. A `human_view.verdict_map` (§5) carries the per-contract mapping so the board colours
correctly without flattening the semantics.

---

## 4. Diagram & ER split policy

- **Diagrams stay standalone.** Architecture diagrams remain offline **raw-XML `.drawio`** in the house style
  (**never Mermaid** — the external `drawio` skill). They are referenced, not inlined as source.
- **Console preview = inline SVG, not raster.** The console embeds an **offline inline-`<svg>` preview** produced by
  a deterministic **`.drawio`→`<svg>` transcoder**. A raster/PNG export is rejected — it breaks the offline rule and
  byte-determinism. The console also shows a **relative-path chip** to the editable `.drawio`.
- **ER model = a future "pack of ER".** One file **per microservice** under a thin `INDEX.json`, each service a
  **triad**: visual `.drawio` + narrative `.md` + `.sql`. **Source of truth = the SQL DDL** → `er_from_sql` → ERD
  (the diagram and narrative are derived, never authoritative).
- **Deferred this turn.** The per-service ER split is **recorded as the target state**, not built now.

---

## 5. The `human_view` render-policy field

An **additive, back-compatible** hint on each output contract — absent ⟹ default (the generic collapsible tree).

```jsonc
"human_view": {
  "kind": "ux-pack",                 // artifact family
  "render": "viewer",                // viewer | native | fold | split | gate-summary
  "source": "ux-intake.json",        // contract / pack path this surface derives from
  "renderer": "ux-pack-viewer",      // optional: which renderer/transcoder
  "verdict_map": { "promote": "G", "hold": "A", "rollback": "R" }  // optional, for gate verdicts
}
```

- **Runtime source of truth** = the per-stage **output schema** (the field lives there).
- **Registry mirror** = `dashboard-data.json` carries the same `human_view` per node so the console and the
  dashboard agree on dispositions.
- **Schema state:** the 3 previously-missing boundary schemas — **`ux-intake.json`, `tl-design.json`,
  `plan-review.json`** — are now **created under `workflows/schemas/`**, and the optional `human_view` field was
  added to **`discovery.json` + `ba-brief.json` + the 12 T-gate schemas**.

---

## 6. Review gates & owners

Pulled verbatim from `workflows/delivery-pipeline.yaml` + `dashboard-data.json`. The console ties each menu to this
row — every menu shows the stage's **gate badge + named owner**.

| Stage | Human gate | Gate type | Owner |
|-------|-----------|-----------|-------|
| S0 Intake | auto plan sign-off | AUTO *(deferred)* | Delivery Ops |
| S1a Discovery | recommendation gate (`proceed` releases brief) | async-peer (L2) | BA lead |
| S1b Brief | intake (runs after S1a clears) | async-peer (L2) | BA lead |
| S1.5 UX Intake | UX pack accept | async-peer (L2) | Tech Lead |
| **S2 TL Design** | design accept (ripples to N components) | **sync NAMED (L3)** | **Tech Lead** + governance |
| S2.5 Plan Review | HITL on HardFail | red-team gate (HITL) | Tech Lead |
| S4a-r / S4b-r Reviews | confirm verdict (never self-approve) | async-peer (L2) | dev-squad |
| **S4c QA Test Design** | conditional-go | **sync conditional-go (L3)** | **QA-squad lead** |
| S5 QA Validation | sign-off on evidence | sync (L3) *(deferred)* | QA-squad lead |
| T1–T9, T11–T12 | machine-threshold gates | auto / auto+exc | dev-squad / qa-squad |
| T10 Adversarial pentest | named human confirms persona verdict | **human (L3)** | security |
| **S6 Deploy** | mandatory release approval | **sync NAMED (L3) — IRREVERSIBLE** | **Release Manager** |
| S7 Prod Validation | named rollback decision | sync (L3) *(deferred)* | On-call / Release Mgr |

**Tie-in:** the **Quality-Gate Board** (menu7) is the leaf-gate roll-up; the **Overview** gate ledger lists every
L3 sync-named gate so a reviewer sees, in one place, which boundaries still require a human signature.

---

## 7. Verdict

**DESIGN READY for human sign-off** once two conditions hold: (1) the 3 boundary schemas
(`ux-intake.json` · `tl-design.json` · `plan-review.json`) land with the `human_view` field, and (2) the console
renders the ShopPilot run **offline-clean and byte-deterministic** (no network references; the `.drawio`→`<svg>`
transcode reproducible bit-for-bit on re-run).

The **JSON contract stays authoritative** on any conflict; the console is a re-derivable presentation surface. The
console is **review tooling, never pipeline operation** — it recommends and records, it does not run, deploy, or
relax a gate, and **deploy-class actions still require a sync named human approval** (S6, Release Manager).

> **Human sign-off:** ______________________ (Tech Lead)  ·  ______________________ (Delivery Ops)  ·  date __________
