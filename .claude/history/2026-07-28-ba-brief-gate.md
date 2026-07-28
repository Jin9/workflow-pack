# 2026-07-28 — The BA brief gets a gate: closing four supervision gaps in the BA leg

A supervision review of the BA leg (the `agentic-workflow-design` lens) over the v2
reshape from earlier the same day (`2026-07-28-ba-leg-v2.md`). The leg's controls were
found to be **structural where they were implemented and prose where they were not** —
and the prose ones read exactly like the implemented ones. That is the same failure mode
the v2 adversarial pass caught twice already: "no verdict clears a P1 gap" was a comment
before it became `release_requires_field_value`.

The v2 signature move is right and is preserved: gating the **shape** (a 207-line
`breakdown.md` agenda) rather than the **flesh** (a 4,918-line brief) is what makes the
three-amigos gate load-bearing instead of ceremonial. The defect was that having moved
the gate earlier, nothing was left at the later boundary.

## What was wrong

**G1 (P1) — the elaborated brief had no gate and no state check.** `ba-research` was
`blocking: false`, so `_open_gate` returned early, emitted `gate.advisory` and marked the
stage succeeded; `ready-for-tl` was enforced **nowhere** in the engine or the YAML (zero
grep hits). A brief emitting `state: needs-work` or `blocked` passed `required_fields`
and flowed into `tl-design` and `ux-intake`. The skill's own schema conditional
(`ready-for-tl ⇒ clean ledgers`) only constrains what a *ready* brief must contain; it
never stopped a non-ready one from shipping. So the leg's deepest artifact — 65
acceptance criteria, 37 edge-case entries, the seven banking-grade rows per story, which
is where PDPA / AMLA interpretation actually happens — reached the Tech Lead with no
human signature at all.

**G2 (P1) — reviewer conditions were silently dropped.** `elaborating-user-stories`
declared `amigos_verdict` as **binding input** ("a condition is elaborated like a rule").
The key appeared nowhere in `engine/` or the pipeline YAML. An amigo signing "agreed, but
split checkout at payment" had that recorded in the audit trail and ignored by the stage
that would act on it.

**G3 (P2) — a documented fail-closed re-check could not fire.** The skill re-checks
`breakdown.blocks_elaboration`; the field was not in `ba-research`'s picks and not
`required` in its input schema, so the check silently no-opped.

**G4 (P2) — the highest-blast-radius call took a one-character approver.** `named` was
`gate in ("sync-named","human") or bool(required_roles)`. `s1-discovery` is `async-peer`
with no roles, so the ≥2-char check was skipped: the `proceed` vs `do-not-build` decision
accepted `approver="x"` while the breakdown gate demanded distinct named humans.

**G5 (P3) — the fail-closed fallback was fail-open past the BA leg.** A missing
`gates.yaml` kept the amigos quorum and s1-discovery but defaulted everything else to
`auto`/non-blocking, silently disarming every sync-named gate the file would have
declared — `tl-design`, the brief's only downstream human, included.

## What changed

| Gap | Change |
|---|---|
| G1 | `gates.yaml` `ba-research` → `blocking: true`, `on_field: state`, `proceed_when: approve`, `release_requires_field_value: ready-for-tl`, verdicts `[approve, needs-work, reject]`, `on_block: ba-brief-review`. **No new engine code** — it reuses the mechanism built and tested for `ba-breakdown`. |
| G2 | `Orchestrator._upstream_quorum_verdict()` threads a **released** quorum gate's record into the next stage's payload as `amigos_verdict`, beside the existing `loop_back_feedback` injection. `conditions` are the reviewers' own signature notes — the only channel an amigo has to qualify an `agreed`. A blocked or looped-back gate is not threaded; those findings already travel as `loop_back_feedback`. |
| G3 | `blocks_elaboration` added to the `ba-breakdown` boundary `required`, to the YAML producer `required_fields` and consumer picks, and to `breakdown.required` in the elaboration input schema. The producer's own skill schema already required it — the boundary was simply weaker than the skill. |
| G4 | `GateSpec.named` gains `or self.blocking`. If a gate is worth parking a run for, it is worth a name on the record. Safe direction only: it tightens s1-discovery, ba-research and tl-design; auto and advisory gates are untouched. |
| G5 | `_fail_closed_fallback`'s default branch is now a blocking `human` gate (`on_block: gates-policy-missing`) instead of `auto`/non-blocking. A missing gates.yaml is a misconfiguration, not a licence to run ungated. |

Also cut, for the same honesty reason that motivated the review: `resolved_open_questions`
was removed from the elaboration input schema — the engine assembles that payload and
never produced the field, so it was another contract line that read as implemented.

## Provenance and pins

`elaborating-user-stories` 1.0.0 → **1.1.0** (its input contract tightened) with the YAML
pin updated; workflow 3.1.0 → **3.2.0**; gates 1.1.0 → **1.2.0** and its pipeline pin.
The corpus keeps `produced_by: elaborating-user-stories 1.0.0` — grandfathered recorded
provenance; nothing validates it against the pin.

Stage count is unchanged at 28. The **dashboard and the drawio needed almost nothing**:
both already depicted S1c as human-gated (`gate: "async"`, a 👤 marker). The mirrors had
been describing a control the engine did not enforce; the engine now matches them. Only
the S1c skill pin, `caps`, `fail` and `tip` were refreshed, through
`roundtripping-dashboard-data-contract`; the drawio is byte-unchanged.

## Verification

69/69 engine tests (62 before + 7 new), both contract lints 0 findings (28 stages / 29
skills), `quick_validate.py` + `check_links.py` ok on the bumped skill, dashboard
`build.py --verify` in sync and byte-deterministic across two builds (only the
`c7f43bda` DATA value changed).

**The gate was proven adversarially, not inferred from a green test**
(`tmp/proof_brief_gate.py`): the full 28-stage replay was driven against a corpus whose
brief declares `state: needs-work` — schema-valid, carrying the `failure_state` its own
skill schema demands — with a hook that signs `approve` on everything it can. Result: the
gate refused (`"refused: artifact state is 'needs-work', release requires 'ready-for-tl'"`),
the run terminated `gate blocked: ba-research` after 4 stages, and `tl-design` and
`ux-intake` never executed. The same script re-runs the identical corpus under the
**pre-change advisory spec** as a counterfactual: the run reaches `done`, ships to
tl-design, and no gate record exists at all — the defect was real, not theoretical.
