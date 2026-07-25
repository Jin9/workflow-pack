# HANDOFF — next session starts here

Written 2026-07-13, end of the fleet I/O contract reshape. Everything below is **verified state**, not
plan. Last commit `a147c40`, pushed to `origin/main`. Working tree clean.

---

## 1. Where things stand (60-second verify)

Run this first. If it is all green, the workspace is exactly as this doc describes:

```bash
cd ~/Desktop/project/research/workflow-pack
engine/.venv/bin/python -m pytest engine/tests -q                     # 42 passed
engine/.venv/bin/python tmp/runs/shoppilot/_sim/validate.py | tail -1 # ALL PASS — 0 failure(s)
engine/.venv/bin/python workflows/scripts/check_contract_consistency.py  # 0 findings (BLOCKING mode)
engine/.venv/bin/python workflows/scripts/check_contract_examples.py     # 0 findings (BLOCKING mode)
git status --short                                                    # empty
```

**What is done:**

- **All 31 skills reshaped** (28 pipeline + 3 tooling), 36 commits, every one gate-green before landing.
  273 Codex findings adjudicated (235 ACCEPT · 32 MODIFIED · 6 REJECT) — one verdict per finding in
  `adjudications/<skill>.md`, no silent drops.
- **Contract drift 68 → 0**, and both lints are **BLOCKING by default** now (`--advisory` to report only).
- **Inputs are ENFORCED fail-closed** (2026-07-13): `engine/validation.py validate_stage_input` checks the
  assembled payload against `skills/<s>/schemas/input.json` before each stage runs. Config:
  `engine/config/runtime-binding.yaml` → `input_validation: off | warn | enforce` (default **enforce**).
- Workflow `metadata.version` **3.0.0**. All skill pins lockstep with folder versions.
- End-to-end proven: full 27-stage replay `done` → `validate-run` 27/27 → audit chain OK, **under**
  input enforcement.

**Read these, in this order, if you need the story:** `report.md` (completion report) →
`.claude/history/2026-07-12-skill-io-reshape.md` (durable entry) → `INDEX.md` (the blow-by-blow).

---

## 2. What to do next (ranked; each is self-contained)

These are the surviving items from the engine follow-up ledger. They were **deliberately not** done in
the reshape — each is a real change with its own blast radius.

### #1 — Script-executor artifact enrichment (T1/T3) · highest value

**Why:** T1/T3 are the only gates that run REAL suites live (`go test -race -json`, `vitest`). Their
`script.py` emits only `{verdict, totals, failures[strings], audit_id}`, so several fields the schemas
*could* require had to stay optional (`coverage`, `execution`, `flaky`, structured `failures`). That's the
**LIVE-SAFETY RULE** recorded in `INDEX.md`: never require an output field the live executor does not
emit.

**Do:** enrich the script executor to emit `coverage`, `execution{mode: runner, target_source: current-run,
runner, evidence_ref, report_sha256}`, `flaky[]`, and object-typed `failures`. Then flip those fields from
optional to required in `executing-backend-unit-tests` / `executing-frontend-unit-tests`
(`schemas/output.json` + boundary + YAML `required_fields`), patch the corpus via
`tmp/runs/shoppilot/_sim/simulate.py`, bump both skills + pins.

**Verify:** a live T1/T3 run (they are already bound live in `runtime-binding.yaml` via
`gate-runners.yaml`) must produce artifacts that pass the tightened schemas — then `pytest` + `_sim` +
both lints + a replay.

### #2 — `ba-research` INDEX exemption removal · the last exempt stage

**Why:** `engine/validation.py SKILL_SCHEMA_EXEMPT = {"ba-research"}` is now a set of one. S0 `intake` was
un-exempted in this pass (schemas authored, `_sim` CHECKS flipped, pytest green) — this is the same move,
one stage over.

**Do:** `eliciting-banking-brief` already ships `schemas/manifest.json` (the INDEX shape, authored this
pass). Point the oracle at it (`tmp/runs/shoppilot/_sim/validate.py` CHECKS row for
`S1b-ba-brief/INDEX.json`, currently `None` for the skill slot), confirm the corpus validates, then remove
`"ba-research"` from `SKILL_SCHEMA_EXEMPT` and run pytest + a replay. **Note:** the stage's artifact is the
INDEX manifest, *not* the skill's canonical `output.json` — validate against `manifest.json`, which is
exactly why that schema exists.

### #3 — `audit_id` equality enforcement across the chain

**Why:** every artifact now carries a house-derived `audit_id`
(`UUIDv5(HOUSE_NS, "<stage-id>:{idempotency_key}")`), but nothing checks that a nested/echoed id actually
equals the top-level one (e.g. discovery's `handoff_to_intake.audit_id`, the smoke/prod-SLO `receipt_id`
echo). A mismatch is a broken audit trail that currently validates.

**Do:** an engine-side post-validation check (next to `validate_artifact`), plus a test. Careful: corpus ids
are **grandfathered** (see doctrine below) — enforce equality *within* an artifact, not against the live
formula, or the replay corpus fails.

### #4 — `from_stage` alias syntax

**Why:** `files_generated` is picked from BOTH implement stages into appsec / contract-tests /
integration-tests; the flat merge keeps only the frontend's. Today that's *documented* (each consumer's
Input contract names the winner and resolves both artifacts via `upstream_artifacts`) and whitelisted in the
lint (`COLLISION_WHITELIST`). An alias syntax (`backend-implement: [files_generated as backend_files]`)
would fix it structurally. **Precedent to copy:** `qa-plan`'s review-verdict collision, which was
functionally material, was fixed with `NESTED_HANDOFF` in `engine/mapping.py`.

### Also open (not from the ledger)

- Terminal workflow artifact assembly · run-snapshot schema digests · compensation trigger threading the
  resolving human · the `backend_implementation_handoff` + tl `frontend_quality_policy` detailed-design
  stages (deferred in adjudication — a topology cascade, needs its own design).
- From the older backlog (still true): live `ux-intake` (needs a real UX drop) · live `qa-validate`
  (GAP-05 execution node — never fabricate evidence) · `request_type` skip-profiles · S6/S7 named approvers
  + short-lived OIDC · async-gate blocking-vs-advisory semantics.

---

## 3. Doctrines this pass established — do not violate them

These are now in the project `CLAUDE.md`, but they are the ones most likely to be argued away by a
confident consult:

1. **Never rewrite recorded provenance.** Corpus `audit_id`s and `processing_metadata.skill_version` are
   grandfathered history. The house `audit_id` formula applies to LIVE derivations only. (Three separate
   Codex consults proposed stamping the formula into the corpus. All three were rejected.) Adding a
   *missing* field through the generator is fine; changing a *recorded* value is falsification.
2. **Never fabricate corpus data.** A value must be honestly derivable from the run's own bytes (real file
   counts/hashes, the run's own receipt id, real `STORY-*` ids) or it does not go in. Synthetic latencies,
   invented p99s, retroactive rubric traces: refused. An unmeasurable row is `insufficient_data` with a
   reason, never a guessed number.
3. **Never weaken a gate to make a run green.** The run-77777777 behaviour is BY DESIGN: a regulatory-scoped
   request carries P1 governance gaps, the red team correctly BLOCKs, and no autonomous path clears it. Do
   not relax the gate, widen the verdict routes, or bump `max_loops`.
4. **LIVE-SAFETY RULE:** never require an output field the live executor does not emit (see item #1 above).
5. **The corpus generator is the source of truth for corpus edits** — patch
   `tmp/runs/shoppilot/_sim/simulate.py` and regenerate; never hand-edit an artifact, or the next
   `simulate.py` run silently reverts it.

---

## 4. Gotchas that cost me time (so they don't cost you)

- **Audit events use `kind`, not `type`.** My first warn-mode probe read `event['type']`, matched nothing,
  and cheerfully reported "0 input-contract breaches across 27 stages". It was a false negative — three
  gates would have hard-failed on the next live run. Instrumentation lies too: verify the instrument.
- **`engine replay` (the bare CLI) parks at the `s1-discovery` named-approver gate — by design.** No code
  path auto-approves a sync-named gate. To drive a full replay non-interactively, construct the
  `Orchestrator` with an `approve_hook` (copy `engine/tests/test_replay_e2e.py::_replay`). `runs/replay-1`
  is a **stale Jul-4 dir**; ignore it (`runs/` is gitignored).
- **Codex quota (ChatGPT account) allows ~6–10 max-effort `gpt-5.6-sol` consults per window**, resetting
  roughly every 4–5 h. `bin/consult.sh` is idempotent (skips anything whose output ends with the
  `FINDINGS-TOTAL:` sentinel), so a re-run of the same `xargs` line retries only what failed.
- **The probe-sentinel trap:** because `consult.sh` skips on the sentinel, a *stale* `codex/_probe.md` makes
  every scheduled quota probe report success without calling the API. Always `rm -f codex/_probe.md` before
  probing.
- **Your global `CLAUDE.md` gotcha is STALE** — it says Codex "only `gpt-5.5` works; rejects
  `gpt-5`/`gpt-5-codex`". This run drove **`gpt-5.6-sol` at max effort** for all 32 consults, successfully.
  That's your file to edit, so I left it alone.

---

## 5. Where the evidence lives

| Path | What |
|---|---|
| `report.md` | The completion report (numbers, structural changes, real bugs, rejections, ledger). |
| `adjudications/<skill>.md` | One verdict per Codex finding + rationale. The audit trail of every decision. |
| `codex/<skill>.md` · `.log` · `manifest.jsonl` | Raw consults, each with a PROVENANCE line (model, effort, sandbox, exit). |
| `gates/<chunk>.log` | The gate-stack evidence for each commit; `e2e-verification.log` + `chunk-input-enforcement.log` are the end-to-end proofs. |
| `house-v2-spec.md` | The target contract standard the fleet now conforms to. |
| `queue/input-stubs/` | Deterministic post-adapter input.json stubs (`bin/gen_input_stub.py`). **Caveat:** the generator marks workflow-input picks as *required* — optional contexts (appsec/perf/pentest) must be hand-relaxed. That bug cost me a hard-failed enforce run. |
| `.claude/history/2026-07-12-skill-io-reshape.md` | The durable history entry (survives this staging folder). |

**The gate stack** (run all of it before any commit that touches a skill, schema, or the YAML):

```bash
python3 ~/.claude/skills/skillify/scripts/quick_validate.py <skill-dir>
python3 ~/.claude/skills/skillify/scripts/check_links.py   <skill-dir>
engine/.venv/bin/python workflows/scripts/check_contract_examples.py
engine/.venv/bin/python workflows/scripts/check_contract_consistency.py
engine/.venv/bin/python -m pytest engine/tests -q
engine/.venv/bin/python tmp/runs/shoppilot/_sim/validate.py
# corpus changed? regenerate first:
engine/.venv/bin/python tmp/runs/shoppilot/_sim/simulate.py
```

Bumping a skill = **folder `version` + the YAML pin, together** (supply-chain reproducibility; the loader
fails closed on a mismatch — that is how you find out).
