# BA leg v2 — deeper analysis, simpler reports, fewer artifacts

**Date:** 2026-07-28 · **Status:** built in staging, awaiting sign-off for the phase-2 wiring pass
**Staging:** `tmp/runs/ba-leg-v2/` (gitignored — promotion to `workflows/skills/` is a separate human step)

## Context

Feedback on the BA steps asked for four things at once: keep the analysis deep, make the
reports simpler, cut what is not needed, and — structurally — break epics and stories down
and **review them with a developer and a tester before writing detail**, group epics by
**business dependency**, and split the skills that do too much.

An audit of the live BA leg (`intake` → `s1-discovery` → `ba-research`) found:

| Problem | Evidence |
|---|---|
| Large unconsumed surface | Downstream reads only `normalized_request` (S0) and `epics` / `story_files` / `governance_gaps` (S1b). `scope_sheet`, `run_plan`, `ba_reasoning_trace`, `ba_compliance_checklist` (10 all-true booleans) and per-story `dor_checklist` (8 all-true booleans) plus `change_log` have **no consumer**. |
| Four surfaces for one brief | `brief.json` (1,373 lines) · `ba-research-viewer.html` (3,284) · `render_markdown_tree.py` (2,191, which produced **no output** in the reference run) · the run-level `delivery-review.html`, which already has BA menus. |
| One skill doing thirteen jobs | `eliciting-banking-brief` — 16,902 lines, 13 procedure steps, 16 references, two renderers, bilingual emission, a viewer template. |
| Depth gaps | Business rules existed only inside acceptance-criteria prose. No domain or state model, no cross-story flow map, edge cases chosen ad hoc under a "≥1 error AC" floor. |
| No tech checkpoint | Detail was elaborated with no developer or tester input; rework surfaced at S2 plan-review. |

**The tension resolves.** Depth lives in the *procedure*; bloat lives in the *emission*.
Stating each fact once with an id and referencing it raises rigour while cutting bytes.

## Target shape

```
S0 intake ─► S1a discovery ─[gate: BA lead · proceed]─► S1b ba-breakdown ─[GATE: THREE-AMIGOS]─► S1c ba-research ─► S1.5 ux-intake ─► S2 tl-design
```

The elaboration node **keeps the stage id `ba-research`**. Five downstream stages reference it
(`workflows/delivery-pipeline.yaml:210,235,255,406,658`), so the boundary contract
`[epics, story_files, governance_gaps, state, audit_id]` is unchanged and the split is
invisible to every consumer. Verified: the new S1c manifest validates against the **live**
`workflows/schemas/ba-brief.json` untouched.

## What was built

### `breaking-down-ba-scope 1.0.0` — the new S1b

Eleven steps: preflight and PII redaction → regulator citations → stakeholders and the
Legal-absence gate → **epic grouping** → **rule catalogue** → **domain model** →
**flow map** → story skeletons → tier inference and the assembly gates → one report.

Governance detection runs *before* the gate deliberately: a P1 gap found during elaboration
has already wasted the session.

Emits a pack of small files under a thin INDEX — `INDEX.json`, one `EPIC-*.json`, one
`STORY-*.json` skeleton each, `RULES.json`, `DOMAIN.json`, one `FLOW-*.json` each, and
`breakdown.md`.

Three new analytical artifacts:

- **`RULES.json`** — every rule stated once with `RULE-DOMAIN-NN`, a `type`
  (calculation / eligibility / threshold / state-transition / constraint / authorization),
  a source reference and an `open` flag. A rule whose value the source leaves vague is
  emitted `open: true` with a linked question, never omitted.
- **`DOMAIN.json`** — entities, lifecycle states and guarded transitions, and `key_fields`
  with a forced `pii_class`. This **absorbs the old standalone PII inventory**: personal data
  is declared where the field is defined, once, instead of re-listed per story.
- **`FLOW-*.json`** — one primary actor, a trigger, numbered steps citing entities, rules and
  stories, decision points that must each cite the rule that decides them, and at least two
  outcomes. A flow with only a success outcome has not been analysed for failure.

**Story skeletons carry no acceptance criteria and no banking-grade rows.** Writing them
before the gate agrees the shape is the rework this stage exists to prevent.

### The epic decoupling rule

A candidate is an epic only if all three hold, recorded in the epic's `decoupling` block:

1. **Independently valuable** — a business audience gets value from it alone.
2. **Own success metric** — a `success_criteria` row that is not another epic's metric.
3. **No mandatory business dependency on a sibling** — if A cannot deliver value without B
   shipping first *for business reasons*, A and B are one epic.

Test 3's qualifier is load-bearing: **business** dependency merges; **technical sequencing**
and **release preference** do not — those live in story `dependencies.depends_on`.
`sibling_dependencies` is schema-capped at zero entries, so an unmerged pair cannot validate.

Enablers — authentication, stock reservation, notification, audit logging — are never epics.
They become stories inside the epic they enable, and every folded candidate is recorded in
`merged_from` so the review session does not re-litigate a deliberate merge. A merged epic
over 12 stories splits on a **value axis**, never a technical layer (AP-7.1 still binds).

Applied to ShopPilot: **4 service-shaped epics → 2 business-shaped epics** —
`EPIC-STOREFRONT-PURCHASE` (auth · cart · coupon · checkout · payment · reservation ·
tracking) and `EPIC-BACKOFFICE-OPERATIONS` (stock correction · fulfilment).

### The three-amigos gate (designed; wired in phase 2)

`stage_id: ba-breakdown` · `gate: sync-named` · `blocking: true` · `owner_role: three-amigos` ·
`required_roles: [ba-lead, dev-lead, qa-lead]`. The `required_roles` key is an **additive
`gates.yaml` field**: the engine must require at least one distinct named approver per role,
matching the existing sync-named guarantee that no code path may auto-approve.

Verdicts: `agreed` | `split-stories` | `descope` | `needs-rework`. Only `agreed` releases
elaboration; anything else loops back with findings threaded, cycle cap 2. **No verdict can
clear a P1 governance gap** — a named human does that, as today.

Open questions carry `for: dev | tester | BA | PM | SME | Legal | Compliance | DPO`, and
`breakdown.md` groups the dev and tester questions first. Those questions are the agenda.

### `elaborating-user-stories 1.0.0` — the new S1c

Seven steps against an **agreed** breakdown. It re-checks two preconditions fail-closed
(`breakdown.state == ready-for-amigos`, `blocks_elaboration == false`) even though the engine
gate enforces them.

**The rule-anchored edge-case sweep** replaces the ad-hoc "≥1 error AC". Per referenced rule,
its `type` dictates the derivations — at / below / above a threshold; rounding and zero on a
calculation; in / out / edge on eligibility; the violation attempt on a constraint; the wrong
actor on an authorization — plus replay, race and partial-failure where the story's shape
calls for them. Per referenced entity with states, the **illegal-transition** case. Every
decision lands in `edge_case_ledger`, including what was judged not applicable **and why**;
a justification must be a reason, not a restatement.

Two coverage ledgers make the depth checkable rather than asserted: `rule_coverage` (rules
referenced, rules with a derived scenario, the uncovered remainder, transitions,
illegal-transition cases, still-open rules) and `hidden_requirements_sweep`. `ready-for-tl`
requires both clean — schema-enforced.

Two new failure modes exist because rules became countable: **FM-18** (a referenced rule with
no derived scenario) and **FM-19** (a story referencing a still-open rule).

**The seven forced banking-grade rows are unchanged.** That is the depth that does not get
trimmed. The reports around it got shorter; the forced evaluation did not.

## The cut list

**Deleted skill assets (~5,500 lines):** `scripts/render_markdown_tree.py` (2,191) ·
`templates/ba-research-viewer.template.html` (2,478) · `references/markdown-rendering-spec.md`
(328) · `references/viewer-rendering-spec.md` (62) · `references/bilingual-emission.md` (181) ·
`references/ui-strings.json` (247). The run-level `rendering-delivery-review-console` skill
already owns the human view, and bilingual EN/TH emission was never exercised
(`bilingual_output: ["en"]`; the Thai source document is an **input**, not an output).

**Deleted per-run artifact:** `ba-research-viewer.html` (3,284 lines) · `ba_reasoning_trace` ·
`ba_compliance_checklist` (the schema already enforces every one of its ten booleans) ·
`processing_metadata.{language_inventory, ground_truth_stripped, bilingual_output,
parsing_reason}` · per-story `dor_checklist` → `dor: pass|fail` with `dor_failures[]` only
when failing · per-story `change_log` (git owns history) ·
`frontmatter.downstream_will_be_consumed_by` (the YAML owns the graph) ·
the S0 `scope_sheet.envelope` ceremony · the standalone `pii_inventory` table (absorbed into
`DOMAIN.json` field rows).

**Skill-fleet reduction:** 16,902 lines in one skill → **2,437 lines across two** (SKILL.md,
schemas and new references; the reused references are copied unchanged).

**A real loss fixed:** S0 builds a scope sheet — business goal, in and out of scope,
quantified NFRs, open questions — and the pipeline **throws it away**; `s1-discovery` receives
only `normalized_request` and re-derives scope from raw prose. Both new skills accept an
advisory `scope` input; the YAML pick is added in phase 2.

**Report simplification:** `discovery.problem_framing` was one ~2,000-character paragraph and
becomes `{problem, who, why_now}`, each capped at 400 characters. `workflows/schemas/discovery.json`
accepts **both** shapes via `oneOf`, so recorded artifacts carrying the legacy string stay valid —
simplifying a report must never invalidate provenance already on disk. The validator proves both
directions. The BA leg's entire human-facing output is now **two short markdown files**
(`discovery.md`, 42 lines; `breakdown.md`, 209 lines) instead of a 3,284-line HTML viewer plus a
2,191-line renderer.

## Measured result

The staging sample pack regenerates the **same eight stories' worth of ground** the recorded
corpus covered, so the comparison is like-for-like.

| | Corpus S1b | New S1b + S1c |
|---|---|---|
| Stories | 8 | 8 |
| Acceptance criteria | 29 | **65** |
| Business rules | 0 | **32** |
| Domain entities / state transitions | 0 / 0 | **6 / 18** |
| Business flows | 0 | **2** |
| Edge-case ledger rows | 0 | **39** |
| Total artifact lines | 6,250 | **4,923 (21% smaller)** |
| Human report | 3,284-line HTML viewer | 209-line markdown |

More than double the acceptance criteria, plus three analytical artifacts that did not exist,
in 21% fewer lines.

**Correction to the pre-build estimate.** The approved plan predicted the new pack would come
in under 1,600 lines. That was wrong — it did not account for the rules, domain model and flow
files, which are new content rather than reformatted content. The honest measure is the table
above: total artifact **down 21%**, analysis **up substantially**. The validator asserts the
real relation (new < corpus), not the estimate.

## Verification

`engine/.venv/bin/python tmp/runs/ba-leg-v2/validate.py` — **285/285 checks pass**, covering:

1. skillify `quick_validate.py` and `check_links.py` exit 0 on both skills; both SKILL.md ≤ 500 lines.
2. Every schema is valid draft-07; every fenced example in each SKILL.md validates against its own schema.
3. Every sample artifact validates against the schema that owns it.
4. **Backward compatibility** — the S1c manifest validates against the live `workflows/schemas/ba-brief.json`; the S1a artifact validates against `workflows/schemas/discovery.json`, **and so does the recorded corpus discovery** with its legacy string `problem_framing`.
5. Ref-chain integrity and FM-14 counts: every rule, entity, flow and story id resolves; epic story-id sums match; **every catalogued rule is referenced by a story**; every flow decision point cites a resolvable rule; every flow outcome lands in a declared entity state.
6. Depth: every story cites ≥1 catalogued rule in its criteria; **every rule has ≥1 derived scenario**; every stateful entity has an illegal-transition scenario; all seven banking-grade rows present with substantive justifications; the edge-case ledger covers every referenced rule; `intent` and `rule_refs` are unchanged from the agreed skeleton.
7. Cuts: no HTML emitted at all; exactly two markdown reports in the whole leg; every cut field absent; the new pack is smaller than the brief it replaces.
8. Determinism (regeneration is byte-identical), offline (no URL in any file), and provenance (both stages use the house `audit_id` formula and carry distinct ids).

The live pipeline is untouched and both blocking contract lints still report **0 findings**
(`check_contract_consistency.py`, 27 stages; `check_contract_examples.py`, 28 skills).

> Environment note: the workspace lint scripts require Python 3.10+. The system `python3` here
> is 3.9.6 and cannot parse `check_contract_examples.py` (a `str | None` annotation). Run it
> with `engine/.venv/bin/python`. Pre-existing, unrelated to this change.

## Phase 2 — the wiring pass (not executed)

1. `workflows/delivery-pipeline.yaml`: 27 → 28 stages; add `ba-breakdown`; re-point
   `ba-research` at `elaborating-user-stories`; exact-pin both new skills; add the `scope`
   pick from `intake` to S1a and S1b.
2. `engine/config/gates.yaml`: the three-amigos entry plus `required_roles` support in the
   engine's gate enforcement.
3. `engine/mapping.py`: hydration for the breakdown ref-chain (`epics[].file`,
   `story_files[].file`, `flows[].file`, `rules_file`, `domain_file`) nested under
   `breakdown`; `engine/config/runtime-binding.yaml` entry for the new stage.
4. New boundary schema `workflows/schemas/ba-breakdown.json`; update
   `workflows/schemas/discovery.json` for the object-shaped `problem_framing`.
5. Promote `sample-pack/` into `tmp/runs/shoppilot/` and re-pin the S2+ replay corpus. The
   four Go services under `S4a-backend` stay as they are — they map to bounded contexts, not
   epics.
6. Retire `eliciting-banking-brief`; delete the cut assets.
7. `dashboard-data.json` card, `delivery-pipeline-flow.drawio` node, both lints back to
   blocking at zero drift.
