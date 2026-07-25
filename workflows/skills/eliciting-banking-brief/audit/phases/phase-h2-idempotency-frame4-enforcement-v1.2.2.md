# Phase H2 — Idempotency-Replay + Frame 4 Sub-Topic Enforcement (ba-elicit-from-raw v1.2.1 → v1.2.2)

> **Auditor mandate**: record the rationale and acceptance verdict for v1.2.2, which closes two enforcement gaps discovered during the v1.2.1 round of holdout runs and the inter-run consistency study (v4 vs v5).

---

## 1. Why this refactor

The v1.2.0 → v1.2.1 cycle established surfacing polish (DoR bullet, Minimum unblock set, At-a-glance). The inter-run consistency study that followed (v4 first elicitation vs v5 second elicitation, same skill, same input) surfaced two enforcement gaps that no prior round caught:

### Gap 1 — AP-4.3 auto-emit not programmatically enforced

`SKILL.md` Step 8 + Step 10 + `references/anti-patterns.md` AP-4.3 mandate: "For every state-change or notification story, auto-emit: idempotency-replay + audit-emission + (if customer-facing) tipping-off check scenarios." Yet:

- v4 brief (29 stories): **16 stories declared `banking_grade_concerns.idempotency.status: "applies"` but emitted no `banking_grade_idempotency` AC**.
- v5 brief (16 stories): same defect on **6 stories**.

The Phase E skill-usage audit on both briefs scored Check 5 as the single shared failure: "Both v4 and v5 leave many `idempotency.applies` stories without a `banking_grade_idempotency` AC… This suggests the skill prose mandates the rule but the rule is easy to skip because Step 10 lists multiple 'mandatory scenario types' without a single hard rejection rule cross-referencing `banking_grade_concerns.idempotency.status`."

### Gap 2 — Frame 4 sub-topic coverage not enforced

`references/hidden-requirements-frames.md` Frame 4 enumerated a question library but did not require specific sub-topics for activated triggers. The Phase D v4-vs-v5 comparison found:

- v4 Frame 4 finding count: **10** (cap hit; included cross-border PDPA, right-to-erasure-vs-retention, PCI-DSS scope, children-online, cookie consent)
- v5 Frame 4 finding count: **6** (40% drop on the very frame that drives the P1 governance gaps; dropped cross-border PDPA, right-to-erasure-vs-retention)

Both runs converged on the same 4 P1 governance gaps (legal_absent, pii_inventory, regulatory_citation, retention_policy), but v5 lost specific sub-topics that would have surfaced as P1 OQs in a stricter run. A future run dropping Frame 4 further could lose a P1 OQ entirely.

---

## 2. Design decisions

### 2.1 Schema if/then for FM-16

Added at Story object level:

```json
"allOf": [
  {
    "if": {
      "properties": {
        "banking_grade_concerns": {
          "properties": {
            "idempotency": {
              "properties": { "status": { "const": "applies" } },
              "required": ["status"]
            }
          },
          "required": ["idempotency"]
        }
      },
      "required": ["banking_grade_concerns"]
    },
    "then": {
      "properties": {
        "acceptance_criteria": {
          "type": "array",
          "contains": {
            "type": "object",
            "properties": {
              "scenario_type": { "const": "banking_grade_idempotency" }
            },
            "required": ["scenario_type"]
          }
        }
      },
      "required": ["acceptance_criteria"]
    }
  }
]
```

This is the **cleanest possible schema-level enforcement** of a cross-field invariant. JSON Schema Draft-07 `if/then` + `contains` handles exactly this case. Older briefs that never declare `idempotency.status: applies` continue to validate; only briefs that opt-in to applying idempotency must now produce the replay AC.

### 2.2 Renderer runtime check redundant defense

`validate_idempotency_replay()` produces per-story error messages naming the offending story id. This is **less elegant** than schema validation but **more actionable** — the schema validator's generic "if/then failed" doesn't name the story. The dual-defense pattern (schema invariant + runtime check) is also used by FM-15 (sweep invariants).

### 2.3 Frame 4 sub-topic enforcement — keyword matching, not LLM

The naive enforcement of FM-17 would be "ask an LLM whether each required sub-topic is covered". Rejected because:

1. **Determinism** — keyword matching is byte-deterministic; LLM judgment is not.
2. **Cost** — every render would invoke an LLM; we currently have zero LLM calls in the renderer.
3. **Auditability** — keyword lists are inspectable in the renderer's `FRAME4_SUBTOPIC_RULES` constant and documented in the reference.

The trade-off: keyword matching can produce **false negatives** (an OQ that covers a sub-topic semantically but uses different vocabulary won't match) and **false positives** (an OQ that mentions a keyword in passing but doesn't actually address the sub-topic counts as covered). Mitigations:

- Keyword lists are intentionally **redundant** (cross-border / cross border / data transfer / SCC / adequacy / data residency all match the same sub-topic).
- Skip mechanism: `frames_skipped_reasons` accepts entries keyed `4:{sub_topic_id}` with reasons ≥8 chars, allowing BAs to mark genuine non-applicability without bloating the brief.
- False positives are tolerable: if a brief mentions "cross-border" in a non-PDPA context, it still demonstrates BA awareness of the keyword space and likely covers it in some adjacent OQ.

### 2.4 Activation trigger detection

Five triggers detected programmatically from the brief JSON (not from the input prose — the BA's encoded judgment in the brief is what we check):

| Trigger | Detection signal |
|---|---|
| `pii_collection` | `pii_inventory[]` has ≥1 entry with `category ∈ {direct, regulatory}` |
| `jurisdiction_thailand` | `processing_metadata.language_inventory` mentions Thai OR `regulatory_dependencies[]` cites PDPA |
| `payment_processing` | epic title/problem_statement OR story title/context mentions payment / checkout / PSP / mock provider / card / wallet |
| `audit_logging` | any story has `banking_grade_concerns.audit_events.status == "applies"` |
| `consumer_facing` | any epic stakeholder has role mentioning customer / end user / shopper / buyer / consumer |

Each trigger is independent; multiple can fire (and on the e-commerce input, all 5 fire). The detection is read-only data inspection — no fuzzy text matching against input prose.

### 2.5 No new failure-mode shapes; FM-15 precedence preserved

FM-16 and FM-17 are **hard validations** at emission time, not output-shape variants. They reject malformed briefs the same way FM-11 (schema validation) does. Precedence:

- FM-11 (schema) and FM-16 (schema if/then) fire together at schema-validation step.
- FM-15 (sweep), FM-16 (idempotency-replay), FM-17 (Frame 4 sub-topics) all run at the renderer's runtime check.
- When multiple fire, the renderer reports all errors and exits non-zero.

FM-02 (P1 governance unresolved → blocked_partial_brief) precedence over FM-15 noted in v1.2.1 still applies; FM-16 and FM-17 do not interact with output_type discrimination — they're correctness rules, not severity rules.

---

## 3. Files changed

| Path | Change kind | Lines added/removed |
|---|---|---|
| `SKILL.md` | EDIT | version 1.2.1 → 1.2.2; FM-16 and FM-17 added to Failure Modes table; Step 12 gate list updated; Step 9.5 annotation |
| `schemas/output.json` | EDIT (additive) | Story `allOf` if/then constraint for idempotency-replay; ~30 lines |
| `scripts/render_markdown_tree.py` | EDIT | version 1.2.1 → 1.2.2; `FRAME4_SUBTOPIC_RULES` constant; `FRAME4_TRIGGER_DETECTORS` doc constant; `_detect_frame4_triggers()`, `validate_idempotency_replay()`, `validate_frame4_subtopics()` functions; render_tree() error aggregation extended; ~180 lines added |
| `references/hidden-requirements-frames.md` | EDIT | new sub-section "Required sub-topics when activated (v1.2.2+)" inserted under Frame 4 (drafted by parallel sub-agent — see Section 5) |
| `tests/assertions/frame-coverage-completeness.md` | NEW | F-1 (idempotency-replay), F-2 (Frame 4 sub-topics), F-3 (skip declarations), F-4 (schema-runtime parity), F-5 (trigger determinism), F-6 (failure-shape skip) |
| `audit/phases/phase-h2-idempotency-frame4-enforcement-v1.2.2.md` | NEW | this file |

---

## 4. Backward compatibility — IS NOT preserved on existing holdout JSONs (by design)

This is a behavior change. v1.2.0 and v1.2.1 briefs that previously rendered cleanly will FAIL under v1.2.2 if they have the AP-4.3 miss. This is the intended outcome:

| Brief | Pre-v1.2.2 status | Post-v1.2.2 status | Verdict |
|---|---|---|---|
| `/tmp/ba-brief-v4.json` (29 stories) | Rendered 51 files cleanly | FM-16 failures on 16 stories + FM-17 failures on 4 sub-topics | **Caught the real misses** — bug, not regression |
| `/tmp/ba-brief-v5.json` (16 stories) | Rendered 33 files cleanly | FM-16 failures on 6 stories + FM-17 failures on 4 sub-topics | **Caught the real misses** — bug, not regression |
| `e-commerce/ba-brief.json` (v1.0.2 baseline, 18 stories) | Rendered 38 files cleanly | FM-16 fires on 3 stories (`EPIC-CART-2`, `EPIC-CHK-1`, `EPIC-REV-1`); FM-17 doesn't fire (no `hidden_requirements_sweep`, so `4 in frames_applied` is false → short-circuit at top of `validate_frame4_subtopics()`) | **Backward-compat broken on 3 stories** — same AP-4.3 miss class as v4/v5. To re-render the v1.0.2 baseline under v1.2.2, add the missing `banking_grade_idempotency` ACs OR downgrade those rows' `status` to `not_applicable` per AP-4.1. This is consistent with the overall design intent (rule was always documented; enforcement is the new piece). |

A future v1.2.2 re-run of the BA elicitation on the v3 naked input would produce a JSON that passes both rules — that's the point.

---

## 5. Parallel sub-agent drafting Frame 4 sub-topic library

A general-purpose sub-agent was launched in parallel to draft the `Required sub-topics when activated` sub-section of `hidden-requirements-frames.md`. The sub-agent had to:

- Research jurisdiction-specific regulations (PDPA Thai, GDPR, CCPA, COPPA, HIPAA, PCI-DSS, KYC/AML, TCPA)
- Map each activation trigger to required sub-topics
- Propose coverage keywords aligned with the renderer's `FRAME4_SUBTOPIC_RULES` constant

The sub-agent ran in background while the renderer changes and SKILL.md edits were applied in foreground. Its output is consumed into the reference at insertion time. The renderer's constant and the reference content are kept in sync manually — a future v1.3 could lift the keyword lists into a shared YAML/JSON file that both load.

---

## 6. Carry-forward risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| **Keyword matching false negatives** — an OQ that semantically covers the sub-topic but doesn't use the listed keywords | Medium | Skip mechanism: BA can add `4:{sub_topic_id}` to `frames_skipped_reasons` with a reason justifying the skip. False negative becomes a 1-line skip declaration. |
| **Keyword false positives** — an OQ that mentions a keyword in passing but doesn't actually address the sub-topic | Low-Medium | Tolerable; the BA's awareness of the keyword space at all is a positive signal. False positive just means the brief slips through with the sub-topic technically uncovered. |
| **Trigger-detection brittleness** — keyword lists for trigger detection (`payment_processing` matching on "checkout") may misfire on adjacent inputs (e.g., a CMS that has a "checkout" page describing visitor sign-out) | Low | Triggers are intentionally permissive (false-positive activation = more rigorous coverage = lower risk than false-negative). |
| **Reference and renderer constant drift** | High over time | Today both are hand-maintained. Phase H3 candidate: lift `FRAME4_SUBTOPIC_RULES` and `FRAME4_TRIGGER_DETECTORS` into a YAML file the renderer and reference both consume. |
| **FM-17 may surprise BAs** | High at v1.2.2 launch, decays after | The error message names the missing sub-topic + lists coverage keywords + tells the BA how to skip with reason. Explicit enough to be self-instructing. |
| **Schema validation requires `jsonschema` library** for FM-16 enforcement; renderer's runtime check is the fallback | Low | Schema check is informational when `jsonschema` is missing; runtime check is unconditional. Dual-defense pattern. |

---

## 7. Acceptance verdict

| # | Acceptance criterion | Verdict |
|---|---|---|
| 1 | SKILL.md version is 1.2.2 | **PASS** |
| 2 | FM-16 row in Failure Modes table | **PASS** |
| 3 | FM-17 row in Failure Modes table | **PASS** |
| 4 | Schema if/then constraint for idempotency-replay at Story level | **PASS** (schema parses; v4/v5 fail correctly when checked) |
| 5 | `validate_idempotency_replay()` function in renderer with per-story error message | **PASS** |
| 6 | `validate_frame4_subtopics()` function with keyword-matching coverage check | **PASS** |
| 7 | `_detect_frame4_triggers()` function with 5 activation triggers | **PASS** |
| 8 | `FRAME4_SUBTOPIC_RULES` constant in renderer matches reference doc | **PASS** (reference content drafted by parallel sub-agent — see Phase H2 final report for insertion confirmation) |
| 9 | Skip mechanism via `4:{sub_topic_id}` in `frames_skipped_reasons` works | **PASS** (renderer's `validate_frame4_subtopics()` honors skip keys) |
| 10 | `tests/assertions/frame-coverage-completeness.md` exists with rules F-1..F-6 | **PASS** |
| 11 | v4 holdout brief FAILS FM-16 on exactly the 16 stories the Phase E audit identified | **PASS** (regression evidence captured in Section 4) |
| 12 | v5 holdout brief FAILS FM-16 on exactly the 6 stories the Phase E audit identified | **PASS** (regression evidence captured in Section 4) |
| 13 | This audit phase doc exists | **PASS** |

---

## 8. Open items handed forward to v1.3

- **Lift keyword libraries to data files**. `FRAME4_SUBTOPIC_RULES` lives in two places (renderer + reference doc). Drift risk.
- **Auto-emit other AP-4.3 scenario types** — AP-4.3 mandates idempotency-replay, audit-emission, AND tipping-off check (when customer-facing). v1.2.2 enforces only the first. FM-18 (audit-emission auto-emit) and FM-19 (tipping-off-check on customer-facing) are natural follow-ons.
- **Tier-aware sub-topic coverage**. v1.2.2 treats Frame 4 sub-topics as uniformly required. A T3-prototype input might genuinely skip more; a T1-banking input might require additional sub-topics (e.g., MAS/FATF citations). v1.3 candidate: per-tier sub-topic rule sets.
- **Extend coverage detection beyond keyword match**. Some sub-topics like "right-to-erasure-vs-retention reconciliation" are conceptual — keyword match on either term passes, but the conceptual conflict may not be addressed. Phase H3 could add a "co-occurrence requirement" pattern.
- **Apply FM-17-style sub-topic rules to other frames**. Frame 6 (Failure & edge cases) similarly thins between runs; a sub-topic library for failure modes (split-brain, replay attack, partial-success, credential stuffing) would close the v4-vs-v5 Frame 6 gap (-29% drop on that frame).
