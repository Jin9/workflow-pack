# Phase I2 — Frame-4 Cap-Exception Protocol (ba-elicit-from-raw v1.3.0 → v1.3.1)

> **Auditor mandate**: record the rationale and acceptance verdict for v1.3.1 — the cap-exception protocol that resolves the FM-17 ↔ Frame-4 soft-cap incoherence observed during v6 elicitation. Warning-grade in v1.3.1 (assertion F-8 `should-pass`); promotion to must-pass scheduled for v1.3.2.

---

## 1. Why this refactor

v1.2.2 shipped FM-17 (Frame 4 sub-topic coverage enforcement). v1.3.0 lifted the rule data to `references/frame-rule-data.json`. **v6 elicitation under v1.3.0** then produced the first real-world signal that FM-17 mandatory coverage is incoherent with Frame 4's soft cap of 10 declared at [references/hidden-requirements-frames.md:122](../../references/hidden-requirements-frames.md#L122):

- Naked ShopPilot input → 5 active triggers (pii_collection / jurisdiction_thailand / payment_processing / audit_logging / consumer_facing)
- 5 triggers × ~4–6 required sub-topics each = **22 required findings** per FM-17
- Cap of 10 (soft, BA-judgment-only) was deliberately overshot by the sub-agent
- v6 reasoning trace explicitly noted: *"Frame 4 cap 10 was overshot to 22 deliberately because the 5 active triggers each pull required sub-topics"*

The cap was originally a "rank by blast radius" tool to keep Frame 4 from drowning briefs in low-impact regulatory questions. FM-17 changes the calculus: when the cap is breached *because mandatory coverage requires it*, the overshoot is a feature, not a defect — but the protocol to declare it as such did not exist.

`frame_4_cap_exception` was named in the [v1.3.0 audit doc](phase-i1-frame-rule-data-lift-v1.3.md) as a v1.3.x carry-forward; this cycle implements it.

---

## 2. Design decisions

8-question decision matrix recorded during planning:

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | Schema or prose-only? | **Schema** (additive `cap_exceptions` field on `processing_metadata.hidden_requirements_sweep`) | The reason for overshoot is an audit signal worth preserving. `deferred_findings_count` already records the inverse (dropped under cap); the symmetric "kept above cap because FM-17 required it" needs its own field. |
| 2 | Field shape | Per-frame object keyed by string ("1".."10"): `cap_exceptions: {"4": {"cap": 10, "observed_count": 22, "reason": "..."}}` | Generalizes to Frame 6 (cap=7) when backlog #4 adds a Frame 6 sub-topic library. Per-frame keying mirrors the existing `findings_per_frame` and `frames_skipped_reasons` shapes. |
| 3 | Cap-of-10 — keep, raise, remove? | **Keep**, with two-tier semantics: mandatory FM-17 sub-topics uncapped; discretionary question-library findings still ranked-by-blast-radius up to 10 | Preserves the discretionary-tier ranking signal; FM-17 takes precedence on mandatory. |
| 4 | Enforcement strength | **Warning-grade in v1.3.1** (test assertion F-8 `should-pass`); promotion to `must-pass` scheduled for v1.3.2 | The v1.2.0→v1.2.1→v1.2.2 arc was polish-then-enforce. Repeating that two-step here means one real-world cycle to observe before hard-failing. Avoids the scope-creep risk of straight-to-hard-fail. |
| 5 | Renderer validator | New `validate_cap_exceptions(data) -> List[str]` returning warnings (not errors). Surfaced via the renderer's existing return dict on a new `warnings` key + printed to stderr in CLI main(). | Mirrors `validate_frame4_subtopics()` and `validate_idempotency_replay()` shapes, but distinct severity channel (warnings, not hard errors). |
| 6 | Version stamp | **v1.3.1** (patch) | Additive schema; warn-only enforcement; no behavior change on briefs that respect the cap or already declare exceptions. |
| 7 | Retroactive v6 fix | **Do NOT** retro-edit `/tmp/ba-brief-v6.json` | Holdouts are inter-run reliability data points; retro-edits poison the signal. v6 stays as the canonical "pre-cap-exception" artifact; the warning observed on its re-render is V3 verification. |
| 8 | FM-numbering | **Do NOT** assign an FM-N number in v1.3.1 | FM-18 and FM-19 are reserved for the v1.4.0 audit-emission and tipping-off-check rules (backlog #3). The cap-exception rule lives as test assertion F-8 only until v1.3.2 promotion. |

### 2.1 Counter-points considered

- **Drop the cap entirely**: rejected. The cap still has value for discretionary Frame 4 findings (those NOT pulled by FM-17 trigger sub-topics). Removing it would lose the "rank by blast radius" discipline for hypothetical Frame 4 expansions beyond mandatory.
- **Auto-suppress the warning when `findings_per_frame[4] == sum(active_trigger_sub_topics)`**: rejected. The BA's choice to overshoot deliberately *is* a load-bearing audit signal — making it implicit hides the decision from downstream reviewers.
- **Move `cap_exceptions` to a top-level brief field** instead of inside `hidden_requirements_sweep`: rejected. The exception is semantically about the sweep, not the brief; nesting keeps the related fields colocated.

---

## 3. Diff scope

| File | Status | Change |
|---|---|---|
| `schemas/output.json` | modified | Additive `cap_exceptions` property under `processing_metadata.hidden_requirements_sweep`: object keyed by `"1"`..`"10"`, each value `{cap, observed_count, reason (minLength 8)}`. `additionalProperties: false` on inner objects. |
| `scripts/render_markdown_tree.py` | modified | `SKILL_VERSION` `1.3.0` → `1.3.1`; module docstring gains v1.3.1 paragraph; new `FRAME_CAPS = {1: 5, ..., 4: 10, 6: 7, ...}` constant after `_FRAME4_KNOWN_TRIGGERS`; new `validate_cap_exceptions(data) -> List[str]` after `validate_frame4_subtopics()`; wired into `render_tree()` alongside existing validators; `_finalize()` gains a `cap_warnings` parameter (and an optional default for back-compat); CLI `main()` prints warnings to stderr. |
| `tests/assertions/frame-coverage-completeness.md` | modified | Title gains `(refined v1.3.1)`; F-8 row added to rule table (severity `should-pass`); per-rule pseudo-check for F-8; report sample includes F-8; cross-references list `validate_cap_exceptions()` and `FRAME_CAPS`. |
| `references/hidden-requirements-frames.md` | modified | Frame 4 Cap line (line 122) gains the v1.3.1 protocol note; Frame 6 Cap line (line 279) gains a parallel note pointing to the same protocol for the forthcoming backlog #4. |
| `SKILL.md` | modified | Frontmatter `version: 1.3.0` → `1.3.1`; Step 9.5 prose gains a "Cap exception (v1.3.1+)" clause. No new References entry — the protocol uses existing files. |

No call sites of `FRAME4_SUBTOPIC_RULES` change; no behavior change on briefs that respect the cap or that declare exceptions correctly.

---

## 4. Acceptance verdict

Verification matrix — all 5 checks executed before this audit doc was finalized:

| Check | Procedure | Expected | Result |
|---|---|---|---|
| V1 | `python3 scripts/check_frame_rule_data_drift.py` + grep `SKILL_VERSION` | F-7 still PASS; SKILL_VERSION = "1.3.1" | ✅ PASS |
| V2 | Render `/tmp/ba-brief-v122-clean.json` under simulated v1.3.0 baseline + actual v1.3.1; diff trees | Only `created_by:` stamps differ across 3 files (00-BRIEF.md, 09-hidden-requirements.md, README.md); 19 diff lines total | ✅ PASS (19 lines) |
| V3 | Render `/tmp/ba-brief-v6.json` (findings_per_frame[4]=22, no cap_exceptions) | Renderer emits **F-8 warning on stderr** ("Frame 4 findings_per_frame=22 exceeds soft cap 10; declare cap_exceptions['4'] = …"); render still emits 33 files; exit 0 | ✅ PASS |
| V4 | Render `/tmp/ba-brief-v6-with-exception.json` (synthesized: v6 plus `cap_exceptions: {"4": {cap: 10, observed_count: 22, reason: "FM-17 mandatory…"}}`) | **Zero warnings** on stderr; render emits 33 files; exit 0 | ✅ PASS |
| V5 | Grep F-8 row in `tests/assertions/frame-coverage-completeness.md` | Severity column = `should-pass` (warning-grade), not `must-pass` | ✅ PASS |

V3 produced the warning verbatim:
> `warning: F-8 (warning): Frame 4 findings_per_frame=22 exceeds soft cap 10; declare processing_metadata.hidden_requirements_sweep.cap_exceptions["4"] = {"cap": 10, "observed_count": 22, "reason": "<>=8-char reason>"}. Most common driver: FM-17 mandatory sub-topic coverage.`

### 4.1 Bug caught during verification

V2's first execution surfaced a `NameError: name 'cap_warnings' is not defined` in `_finalize()`. Root cause: `_finalize()` is a helper called from `render_tree()`; the new `cap_warnings` local variable in `render_tree()` was not in `_finalize()`'s scope. Fix: thread `cap_warnings` through `_finalize()` as an optional parameter with default `None` (back-compat). Both `_finalize()` call sites (success-shape line 1909, failure-shape line 1866) updated to forward the warnings. V2 re-run produced 19-line clean diff.

---

## 5. Out-of-scope (carry-forward to later cycles)

- **Promotion of F-8 to `must-pass`** — **v1.3.2**. After one or two real-world inputs (e.g., the planned v7 elicitation under v1.3.1) have been observed, the soft-pass becomes a hard fail. The renderer's `validate_cap_exceptions()` already returns a structured list; the v1.3.2 change is one line ("warnings" → "errors" in the `render_tree()` short-circuit).
- **CI hook for F-7 drift check + markdown-table regen from JSON** — v1.3.2 (backlog #8 + #8a). Same patch cycle as the F-8 promotion; both cleanup-class.
- **v1.3-pending Frame 4 triggers** (children / health_medical / financial_lending / telecom_sms_marketing) — **v1.3.3** (backlog #2). Now safe because v1.3.1 declares the cap overshoot. A 9-trigger comprehensive input could push Frame 4 to ~42 findings; `cap_exceptions["4"]` handles it.
- **FM-18 + FM-19** (audit-emission + tipping-off-check auto-emits, mirror of FM-16) — v1.4.0 (backlog #3).
- **Frame 6 sub-topic library** — v1.4.1 (backlog #4). Will reuse this cycle's `cap_exceptions` protocol for the parallel cap-of-7 case.
- **Tier-aware sub-topic coverage** — v1.5.0 (backlog #5).
- **Retroactive v6 fix** — never. v6 stays as-is for inter-run reliability integrity.

---

## 6. Risk register carried forward

| Risk | Mitigation in v1.3.1 | Residual |
|---|---|---|
| BA emits cap_exceptions with wrong `cap` or `observed_count` (e.g., mismatches `findings_per_frame[4]`) | `validate_cap_exceptions()` cross-checks both fields against the source-of-truth and warns on mismatch | Caught at render time as a warning. Solid. |
| Cap promoted to must-pass in v1.3.2 before BA workflow learns the protocol | Two-step polish-then-enforce gives one v1.3.1 cycle to observe before hard fail | If v7 elicitation produces a warning AND the BA doesn't fix it before v1.3.2 ships, v1.3.2's first run will hard-fail. Mitigation: bundle the F-8 promotion with a one-shot fix to v7's JSON before promotion. |
| F-8 doesn't fire on briefs that omit `processing_metadata` entirely (failure shapes) | `validate_cap_exceptions()` early-returns when sweep is absent | Intentional — failure shapes have no sweep, so F-8 is N/A. Same pattern as FM-15. |
| Other frames develop mandatory coverage (Frame 6 in v1.4.1) and hit their caps | `FRAME_CAPS` already declares caps for all 10 frames; protocol generalizes by frame_int → frame_str key | Solid: F-8 and `cap_exceptions` are frame-agnostic by design. |

---

## 7. Carry-forward to Phase I3 (v1.3.2)

Next cycle is **v1.3.2**: promote F-8 to must-pass + wire F-7 into CI/pre-commit (backlog #8) + draft markdown-table regen script (backlog #8a). These are mechanical cleanup items. v1.3.3 (backlog #2 — v1.3-pending Frame 4 triggers) follows once the cap-exception protocol has at least one v1.3.1-stamped real-world run on record.

The v7 elicitation under v1.3.1 (planned same session as v1.3.1 ship) will be the first real-world test: a fresh sub-agent run on the same naked input as v4/v5/v6, with the cap-exception protocol available from the start. Expected outcome: 4th data point in the inter-run reliability series; Frame 4 findings ≈ 22 again (FM-17 floor); `cap_exceptions["4"]` declared inline; zero F-8 warnings.
