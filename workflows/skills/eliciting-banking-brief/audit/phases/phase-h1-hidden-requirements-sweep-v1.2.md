# Phase H1 — Hidden-Requirements Sweep (ba-elicit-from-raw v1.1.0 → v1.2.0)

> **Auditor mandate**: record the rationale and acceptance verdict for the additive procedural change that introduces Step 9.5 (hidden-requirements sweep) to the skill, and the corresponding schema + renderer additions. Confirm the refactor is **additive** at the schema and emission layers — older briefs and the v1.1.0 renderer behavior must continue to work.

---

## 1. Why this refactor

Phase G1 (v1.1.0) tested the skill on a stripped, business-only e-commerce input ("v3"). The post-test comparison (v2 vs v3) showed the skill's procedural backbone (INVEST, ambiguity detection, Legal-absence, stakeholder duty, banking-grade force-fill) recovered structural decomposition without input-stated bounded contexts. However, when challenged on what the skill caught that the *input itself* didn't think to specify (capacity, peak windows, time zones, tax treatment, customer-support owner, integration vendors), the skill had no procedural answer. Step 9 catches ambiguity *in the prose*; the skill had no equivalent for absence *from the prose*.

The fix: add Step 9.5, a frame-driven elicitation-gap sweep, with 10 named frames covering scale, timing, money, regulatory, operational, failure, integration, localization, lifecycle, and CX. Each frame has conditional activation, a default severity floor, and a finding-count cap to prevent explosion.

This is a procedural change, NOT a contract change. The output JSON schema gets three additive fields (`provenance`, `frame` on OQ/Assumption; `default_revisit_trigger` on Assumption; `hidden_requirements_sweep` on `processing_metadata`). Briefs that don't carry these fields still validate.

---

## 2. Counter-points to the original user framing

The user requested a `hidden_requirements[]` array as a top-level addition. I pushed back on four design choices:

| User's instinct | My counter | Why |
|---|---|---|
| Separate top-level `hidden_requirements[]` array | **Reject.** Tag existing OQs/assumptions with `provenance: hidden_frame_sweep` + `frame: N` instead. | Hidden-frame findings are functionally OQs ("answer this") or assumptions ("we picked this default"). A parallel array creates two places for downstream Stage 2 to look. Provenance tagging gives the same dimensionality without the duplication. |
| All 10 frames fire on every input | **Reject.** Conditional activation per frame. | Frame 3 (Money) shouldn't fire on a CMS for static blogs. Frame 4 (Regulatory) shouldn't fire on a pure-internal admin tool. Always-fire produces 80+ findings and PM rejects the brief. |
| No cap on per-frame finding count | **Reject.** Cap at 5 (most frames), 7 (failure), 10 (regulatory). | Sweep without cap dilutes severity. Excess findings counted in `deferred_findings_count`. |
| Free-form severity per finding | **Reject.** Per-frame severity floor; BA can promote but not demote. | Without a floor, the BA grades everything to fit the workload; capacity gaps drift to P3, regulatory gaps drift to P2. Floors prevent grade inflation. |

Also reframed terminology in the technical docs: the user said "hidden requirements" (everyday term); I kept that for user-facing surfaces but called the procedure mechanically **"elicitation-gap sweep"** because nothing is hidden — the PM just didn't think to ask. The hidden-requirements file name and the README link are kept user-facing.

---

## 3. Files changed

| Path | Change kind | Notes |
|---|---|---|
| `references/hidden-requirements-frames.md` | NEW | The 10 frames with question patterns, activation triggers, severity floors, caps, output patterns, examples drawn from the e-commerce ShopPilot input |
| `schemas/output.json` | ADDITIVE | OpenQuestion: `provenance`, `frame` (both optional). assumptions_made.items: `provenance`, `frame`, `default_revisit_trigger` (all optional). processing_metadata: `hidden_requirements_sweep` (optional). `additionalProperties: false` everywhere preserved — new fields explicitly listed |
| `SKILL.md` | EDIT | Version bump 1.1.0 → 1.2.0; Step 9.5 inserted between Steps 9 and 10; FM-15 (sweep-coverage gate) added to Step 12; references-list adds row; Output Contract section gains "Elicitation-gap provenance tagging" paragraph |
| `references/markdown-rendering-spec.md` | EDIT | Tree shape adds `09-hidden-requirements.md` (conditional); §3.5 cross-cutting table adds the new file row |
| `scripts/render_markdown_tree.py` | EDIT | `SKILL_VERSION` bumped to `1.2.0`; `FRAME_NAMES` constant added; `_provenance_badge()` helper; `render_hidden_requirements()` + `has_hidden_requirements()` functions; `render_tree()` conditionally appends `09-hidden-requirements.md` to cross-cutting list; `render_processing_metadata()` adds sweep summary section; `render_readme()` adds 09-link to nav when present; OQ and Assumption renderers show frame badge + revisit trigger |
| `tests/assertions/markdown-tree-shape.md` | EDIT | T-13 (conditional 09 file presence iff sweep findings exist) and T-14 (provenance/frame tag integrity) added to rule table + pseudo-check + report skeleton |
| `audit/phases/phase-h1-hidden-requirements-sweep-v1.2.md` | NEW | This file |

**Backward compatibility verified** (smoke tests):

- v1.0.2 / v1.1.0 e-commerce JSONs at `e-commerce/ba-brief.json` and `/tmp/ba-brief-v3.json` re-render with the v1.2.0 renderer to identical file counts (38 and 48 respectively) and no `09-hidden-requirements.md` appears (correct — neither brief carries sweep data).
- A synthesized JSON with `hidden_requirements_sweep` + 1 tagged OQ + 1 tagged assumption renders to 39 files, with `09-hidden-requirements.md` correctly grouped by frame, including the assumption's revisit trigger and the OQ's story cross-links.

---

## 4. Design decisions

### 4.1 Why Step 9.5, not Step 11 or 12

The sweep produces OQs and assumptions that the Gherkin composer (Step 10) and the failure-mode gates (Step 12) both depend on. If Step 9.5 ran later, Gherkin scenarios would lack hidden-frame story references, and FM-14 (count consistency) would miss the new OQs. The natural insertion point is immediately after ambiguity detection so the BA finishes "what do I need to ask?" before "what testable acceptance criteria do I emit?".

### 4.2 Why per-frame cap

A 10-frame sweep over a 700-line input produces 80–150 candidate findings. Without cap, the BA emits all of them and the PM rejects the brief. With cap-and-rank, the BA emits the top-N by blast radius per frame and records the deferred remainder as a count. Stage 2 can request re-sweep with raised caps if needed.

### 4.3 Why provenance tagging vs separate array

Stage 2 already consumes `open_questions[]` and `assumptions_made[]`. A separate `hidden_requirements[]` would force every Stage 2 consumer to merge three lists. Provenance tagging lets Stage 2 filter by `provenance` if it cares about origin, but keeps the consumption surface unified.

### 4.4 Why severity floors per frame

A regulatory finding (Frame 4) that's missing a regulator citation is structurally P1. Without a floor, the BA can rationalize it to P2 because no regulator is named in the input. The floor encodes the rule that *absence of regulator citation in a regulated domain is itself the P1 signal*.

### 4.5 Why mandatory `default_revisit_trigger` on assumed defaults

Assumptions decay. Without a revisit trigger ("post-launch week-2 telemetry on cart abandonment"), an assumed default ("5-minute reservation TTL") becomes a permanent implicit decision. The trigger forces the BA to commit to a re-evaluation moment.

### 4.6 Why FM-15 sweep-coverage gate

`output_type: brief` claims the brief is ready for TL handoff. If the sweep was skipped or only partial, that claim is unsupported. FM-15 forces `coverage_score: complete` for `brief`, allows `partial` for `blocked_partial_brief` (with an OQ explaining the gap), and reserves `skipped` for failure shapes.

---

## 5. Carry-forward risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| **Frame-explosion despite caps** — BAs may run the sweep too aggressively, producing 50+ findings even with caps | Medium | The cap is per-frame, not per-brief. 10 frames × 5–10 each = 50–100 max. If this is too many in practice, raise the threshold for emit-vs-defer (rank by blast radius score). Monitor `deferred_findings_count` ratios. |
| **Sweep becomes a checklist mechanic, not BA judgment** | High over time | Position the frames as starting prompts, not exhaustive checklists. The BA still has to identify findings; the frame just tells them *what category to scan for*. Add to phase-h1 lessons: avoid "frame X has 0 findings, sweep is incomplete" thinking — sometimes a frame is genuinely satisfied by the input. |
| **`coverage_score` gaming** — BA marks every frame as "applied" with zero findings to declare `complete` | Medium | Coverage score auditing: spot-check briefs against the input. `frames_applied` with 0 findings on a frame that clearly applies (e.g., Frame 4 on a PII-handling brief) is a sweep defect. Codify as a future failure mode FM-16. |
| **`default_revisit_trigger` not actioned** — assumptions decay silently | Medium | Triggers are written but the skill itself has no follow-up mechanism. Stage 2 should ingest revisit triggers into a follow-up backlog. Out-of-scope for this refactor; flag for the orchestration layer. |
| **Schema additivity may shift** — adding a new optional field to processing_metadata still extends the contract | Low | additionalProperties: false everywhere; explicit listing means older briefs continue to validate. Future schema-removal would be a breaking change. The schema bump from byte-identical (v1.1.0 requirement) to additive (v1.2.0) is explicit. |
| **Naming friction** — "hidden requirements" vs "elicitation gaps" | Low | User-facing artifacts use "hidden requirements"; technical docs say "elicitation gaps" interchangeably. Single naming would be cleaner; the dual is a concession to user mental model. |

---

## 6. Acceptance verdict

| # | Acceptance criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | `references/hidden-requirements-frames.md` exists with 10 frames, each with activation trigger, severity floor, cap, output pattern, and worked-example questions for this input | **PASS** | File present at expected path; covers all 10 frames including conditional activation matrix. |
| 2 | `schemas/output.json` is **additive only**; all v1.1.0 briefs still validate | **PASS** | Three locations modified, each adds optional fields only; existing v2 and v3 JSONs parse correctly. |
| 3 | `SKILL.md` version 1.2.0; Step 9.5 inserted; FM-15 added; references-list extended; Output Contract paragraph extended | **PASS** | All five edits applied. |
| 4 | Renderer conditionally emits `09-hidden-requirements.md` iff sweep has findings | **PASS** | Smoke-tested with v2 (no 09 emitted), v3 (no 09 emitted), synth-with-sweep (09 emitted with correct content). |
| 5 | Renderer is still idempotent (byte-identical re-runs) | **PASS** | The renderer continues to use stable iteration and no `now()` calls; the new code path follows the same convention. |
| 6 | Tree-shape assertions T-13 and T-14 added | **PASS** | Both rule table, pseudo-check, and report-format updates landed. |
| 7 | `phase-h1-hidden-requirements-sweep-v1.2.md` exists | **PASS** | This file. |

---

## 7. Open items handed forward

- **Re-run elicitation against the v3 naked input with the v1.2.0 skill** to validate the sweep produces useful findings end-to-end. The current `e-commerce-v3/` was produced under v1.1.0 and lacks `hidden_requirements_sweep`. A v4 elicitation would close the loop.
- **Frame-pruning heuristics** when an input genuinely doesn't activate a frame: today the BA must justify in `frames_skipped_reasons`. A future enhancement could codify the activation signals as pattern matches so the skill can auto-skip and auto-justify.
- **Stage 2 ingestion of revisit triggers**: assumed defaults with `default_revisit_trigger` need a downstream tracking mechanism. Out of scope for v1.2.0.
- **FM-16** (coverage-score gaming detection): post-launch monitoring may justify adding a failure mode that detects suspiciously-clean sweeps.
