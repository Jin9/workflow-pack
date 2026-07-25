# Handoff Contracts

> The typed artifact each stage emits and the next consumes. Every contract is wrapped in the **shared envelope**
> (below), so any stage or human reviewer can trust what it receives. **Exactly one owner mutates state per stage** —
> downstream stages read the upstream contract, they never edit it. See [`agentic-workflow.md`](./agentic-workflow.md)
> for the flow overview.

## Shared envelope (every handoff)

| Field | Type | Meaning |
|-------|------|---------|
| `task_id` | string | the requirement id — the single trace id across all stages |
| `stage` | enum `S1..S5` | which stage produced this contract |
| `intent` | string | what this stage was asked to produce |
| `state` | string | the stage verdict / output type (see each contract) |
| `confidence` | enum `high \| medium \| low` | agent self-rating; `low` forces async human review |
| `provenance` | object | `{ raw_ref, upstream_contract_ref }` — back-pointers for audit |
| `produced_by` | string | distinct agent identity (e.g. `story-agent`) |
| `owner` | string | named human owner of record for this stage |
| `schemaVersion` | string | contract version, for drift detection |
| `created_at` | RFC-3339 | timestamp |

---

## S1 — Scope Sheet  (`intake-agent`)

| Field | Type | Notes |
|-------|------|-------|
| `business_goal` | string (1 sentence) | restated in one line |
| `in_scope[]` | string[] | explicit |
| `out_of_scope[]` | string[] | explicit — prevents scope creep |
| `nfrs[]` | object[] | `{ kind: volume\|latency\|growth\|cost\|security\|privacy, target }` — quantified, not vibes |
| `open_questions[]` | object[] | `{ id, question, for: BA\|PM\|SME }` — ambiguity becomes a question, never a silent assumption |
| `assumptions[]` | string[] | made explicit |
| `risk_flags[]` | enum[] | `unclear \| likely-to-change \| legacy-coupled` |
| `state` | enum | `ready-for-stories \| needs-clarification` |

**Gate G1:** BA/PM confirms `in_scope`/`out_of_scope` and answers blocking open questions before S2.

---

## S2 — Story Set  (`story-agent`)

Shape follows `references/user-story-template.md` (EN; `-th` for Thai parallel).

| Field | Type | Notes |
|-------|------|-------|
| `epic` | object | `{ title, summary }` |
| `stories[]` | object[] | see story object below |
| `state` | enum | `drafted \| needs-scope-rework` |

**Story object**

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `ST-01` |
| `title` | string | `[TYPE] imperative title` |
| `narrative` | object | `{ as_a, i_want, so_that }` |
| `business_rules[]` | string[] | rules the system must enforce; decision-matrix rows where applicable |
| `acceptance_criteria[]` | object[] | `{ given, when, then }` — testable, concrete values |
| `out_of_scope[]` | string[] | per story; names owning team if elsewhere |
| `open_questions[]` | string[] | unresolved, carried forward (not invented answers) |

**Gate G2:** async BA review for INVEST-ness and testable acceptance criteria.

---

## S3 — Governance Check  (`governance-agent`)

Lightweight surface-don't-repair sweep. Flags only; never fixes.

| Field | Type | Notes |
|-------|------|-------|
| `pii_flags[]` | object[] | `{ field, pii_class, where_seen }` — what personal data the stories touch |
| `compliance_flags[]` | object[] | `{ topic, concern, regulator?, named_owner? }` (e.g. retention, consent, customer-facing copy) |
| `blockers[]` | object[] | `{ id, type, description, resolve_owner }` — must be cleared by a human before handoff |
| `verdict` | enum | `clear \| blocked` |
| `state` | enum | mirrors `verdict` |

**Gate G3:** if `blocked`, a **named human (Legal / DPO / Compliance / SME / PM)** resolves each blocker; the
affected upstream stage re-runs. The agent never marks a blocker resolved itself (DENY).

---

## S4 — Feasibility Note  (`feasibility-agent`)

Consumes Story Set + Governance Check **+ the raw requirement** (so the TL sees the original ask, not only the distillation).

| Field | Type | Notes |
|-------|------|-------|
| `options[]` | object[] (≥2) | `{ name, pros[], cons[] }` |
| `dependencies[]` | string[] | systems, vendors, data feeds, prerequisite work |
| `risks[]` | object[] | `{ risk, mitigation }` |
| `spikes[]` | object[] | `{ question, time_box }` — time-boxed unknowns |
| `verdict` | enum | `buildable \| not-now \| phased` |
| `state` | enum | mirrors `verdict` |

**Gate G4:** TL gives the feasibility verdict (sync named).

---

## S5 — TL Handoff Bundle  (composition)

Not a new artifact — the **assembled set** the TL receives and signs for. This is the contract that makes the TL the
accountable owner of record.

| Field | Type | Notes |
|-------|------|-------|
| `task_id` | string | same trace id throughout |
| `raw_requirement` | ref | **the original ask** (provenance — travels all the way here) |
| `scope_sheet` | S1 contract | |
| `story_set` | S2 contract | |
| `governance_check` | S3 contract | must be `verdict: clear` |
| `feasibility_note` | S4 contract | `verdict: buildable` or `phased` |
| `open_items[]` | object[] | any deferred questions, explicitly PM/Sponsor-accepted |
| `state` | enum | `ready-for-tl` (only when no blocker is open) |
| `accepted_by` | string | TL name + date — the sign-off |

**Gate G5:** TL accepts (sync named approval). On acceptance the TL is the owner of record for everything downstream.

---

## Invariants

1. `state: ready-for-tl` ⟹ `governance_check.verdict == clear` **and** no open blocker.
2. The `task_id` is identical across S1–S5 (the one trace id).
3. `raw_requirement` is present in the S5 bundle — the handoff is never "BA contract only".
4. Every contract carries the shared envelope; `schemaVersion` lets a consumer reject a drifted contract.
5. Exactly one stage owner mutates a given contract; downstream stages are read-only on it.
