# RATIONALE — implement-backend-feature

> **Audience**: humans reviewing the skill before merge / promotion.
> **Not loaded into LLM context.** Skills are loaded as `SKILL.md` +
> `references/`; this file lives at the skill root specifically because the
> Tier-2 loader does not pull it.
>
> **Source skill** (mono-skill, 6 modes):
> `treasury/crafting-backend-code/` — read for the design lineage of this skill.

## 1. Why this skill exists

The source skill `crafting-backend-code` is a high-quality mono-skill with six
modes: `design`, `optimize`, `fix`, `analyze`, `review`, `plan`. None of those
modes produces production code for a *new* feature from an approved design.
The closest mode is `fix`, but it explicitly targets *existing* bugs with
minimal patches — wrong shape for greenfield feature implementation.

`COGNITIVE_OS.md` (Section 6) requires one atomic skill per stage. The Dev
workflow needs a `Generate` stage that turns design → code. This skill fills
that gap.

## 2. What was extracted from the source

| Source file | Target in this skill | Notes |
|-------------|----------------------|-------|
| `references/decision-rules.md` (all 11) | `references/implementation-rules.md` — verbatim block | The 11 rules are banking-grade non-negotiables. They stay character-for-character. |
| `references/thinking-model.md` L4 | `SKILL.md` Procedure step 4 (Generate) | L1–L3 are out of scope (they belong in the design stage). L4 is the implementation discipline this skill enforces. |
| `references/template-defaults.md` (Go portions) | `references/go-conventions.md` | Re-organized into Service / Package / Context / Errors / Logging / CQRS / Events / Postgres / HTTP / Tests / Lint sections. Banking flavor added (Section 5–10 below). |
| `references/editing-guardrails.md` | Folded into `SKILL.md` Procedure (Inspect, Scope) and Anti-Patterns; cross-referenced in `implementation-rules.md` augmentations. | Did not create a separate guardrails file — guardrails are most useful in the active workflow, not as deep reference. |
| `SKILL.md` Safety workflow steps 4–7 + Validation gate | `references/self-review-checklist.md` | Reformatted as YES/NO checklist with explicit routing on any NO. |
| `SKILL.md` Operating posture (identity, risk, change policy) | `SKILL.md` Purpose paragraph + Anti-Patterns | Compressed — the atomic skill needs the posture in the body, not as a separate section. |

## 3. What was added (v2-specific augmentations)

| Augmentation | Lives in | Why it's new |
|--------------|----------|--------------|
| A1: canonical audit event shape | `implementation-rules.md` | Source skill said "observability follows failure modes" but did not specify audit event shape. v2 (`COGNITIVE_OS.md` Section 8) requires every stage to emit a structured audit event. |
| A2: idempotency key format (UUID v4) and replay behavior | `implementation-rules.md` | Source said "idempotency required for retries" without naming the key shape or replay semantics. v2 workflow engine passes a UUID v4 per workflow instance. |
| A3: compensating-action discipline | `implementation-rules.md` | Source skill had no compensation concept — it was a design-stage rule. v2 `commit`-type stages require compensation declared at Generate time. |
| A4: error classification at the boundary (`client|server|dependency`) | `implementation-rules.md`, `go-conventions.md` Errors | Source said "errors are operational signals" without a fixed taxonomy. v2 needs a stable class for retry-policy and audit. |
| A5: test fixtures discipline (no network, no secrets, no shared state) | `implementation-rules.md` | Source had test guidance in the `design` mode only. Atomic Generate stage must enforce it directly. |
| A6: convention discovery overrides templates | `implementation-rules.md`, `go-conventions.md` preamble | Source mentioned "repo first" once. Made explicit: discovery wins, emit `uncertainty_flag`. |
| A7: no silent dependency additions | `implementation-rules.md`, SKILL.md Anti-Patterns | Source's editing-guardrails warned against dependency churn but did not block. v2 escalates to `uncertainty_flag` because dependency addition is a design decision, not a Generate decision. |
| Stage-aware Failure Modes table (`loop_back` / `human-queue` / `retry`) | `SKILL.md` Failure Modes | Source was workflow-agnostic. v2 wires every failure to a workflow policy. |
| Output Contract with 7 structured fields + JSON Schema | `SKILL.md` Output Contract, `schemas/output.json` | Source returned free-form markdown. Atomic skill emits machine-validatable JSON. |
| Self-review NO-routing table | `references/self-review-checklist.md` bottom | Source's validation gate was a soft "re-check" — v2 needs deterministic routing. |

## 4. What was intentionally dropped (and why)

| Dropped from source | Reason |
|---------------------|--------|
| 5 of 6 modes (`design`, `optimize`, `fix`, `analyze`, `review`, `plan`) | One stage = one skill. Each of these is a separate atomic skill in the v2 architecture (`design-backend-feature`, `optimize-backend-perf`, `generate-backend-fix`, `analyze-backend-codebase`, `review-backend-code`, `plan-backend-migration`). |
| Mode-selection workflow + per-mode checklists | Workflow engine picks the skill — no in-skill mode dispatch. |
| L1, L2, L3 thinking-model content | L1–L3 belong in the design stage's skill. This skill receives an approved design that has already passed L1–L3. |
| "Operating posture" as a top-level section | Folded into Purpose paragraph + Anti-Patterns. Atomic skill body must be lean (`progressive-disclosure.md`). |
| Long output-format table per mode | Replaced by a single Output Contract + JSON Schema, which is the only output shape this stage produces. |
| `troubleshooting` section | Banking-grade Failure Modes table covers the same ground in a workflow-aware way. |

## 5. Deviations from the prompt (flagged)

| Prompt said | We did | Why |
|-------------|--------|-----|
| `tests/README.md` | `tests/harness-guide.md` | `scripts/quick_validate.py` has `README.md` in `BANNED_DOCS` and refuses to validate any skill folder containing `README.md` at any depth. The prompt also requires the skill to pass `quick_validate`. The name was changed to satisfy the validator; content is identical to what `README.md` would have held. |
| Nested `banking_grade:` block in frontmatter (per `COGNITIVE_OS.md` Section 7) | Inline YAML `banking_grade: {idempotent: true, reversible: soft, audit_level: detailed}` | `scripts/quick_validate.py` is a flat-YAML parser — it errors on indented frontmatter lines (`unexpected indented frontmatter line`). Inline YAML round-trips through any real YAML parser identically while passing the flat validator. Should be reviewed when a v2-aware validator lands. |
| `Success Criteria` step 2: validate against `schemas/skill-v1.schema.json` | Validated against `scripts/quick_validate.py` only | No `schemas/skill-v1.schema.json` exists in this repo yet. Recommend that file be authored as part of the Phase 1 deliverables in `COGNITIVE_OS.md` Section 10. |
| `Success Criteria` step 8: write `RATIONALE.md` | Done — this file. | — |

## 6. What still needs human review

- **Failure-policy values** are recommendations, not contracts. The workflow
  engine spec in `COGNITIVE_OS.md` Section 8 may tighten them (e.g.,
  `max_retries_recommended: 2` may need to drop to 1 once Generate cost
  becomes measurable).
- **`idempotency_keys` table shape** is referenced but not specified. A
  separate stage in the substrate-services squad should own the schema.
- **`compensating_actions[].action_skill_ref`** assumes a sibling
  compensation-skill convention that does not exist yet. First Generate
  stage that needs compensation will force the convention to be made
  concrete.
- **Coverage measurement** is per-file in the spec but the harness in
  `COGNITIVE_OS.md` Section 9 is sketched only. The `TestCoveragePerFileAssertion`
  named in `tests/harness-guide.md` is not yet implemented.

## 7. Recommended next skill to build

`review-backend-code` — the Review-stage skill that consumes this stage's
output. Without it, the workflow's `loop_back` policy on review failure has
nowhere to loop back *from*. Build before any Validate / Commit stage.
