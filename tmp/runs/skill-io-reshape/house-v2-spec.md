# House Contract v2 — target standard for all 31 skills

Status: DRAFT pending fleet-consult adjudication. Source of truth for the skill-io-reshape pass.
Applies to: 28 pipeline skills (`workflows/skills/`) + 3 tooling skills (`.claude/skills/`).

## 1. Frontmatter (exact key order; flat — never nested `metadata:`)

```yaml
name:                     # kebab-case == folder name
version:                  # semver; slot 2 ALWAYS (pin-checked key, engine loader reads it)
description:              # what + literal "Use when ..." triggers + "Do NOT use ..." negatives; no < >
stage_type:
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade:            # always all 6 keys
  idempotent: true|false
  reversible: reversible|compensable|irreversible|not-applicable
  audit_level: basic|detailed|enhanced
  pii_handling: none|redact|forbid
  tier_default:
  tier_adaptable:
requires_approval:        # OPTIONAL — only handoff-to-deploy / handoff-revoke
requires_capabilities:    # OPTIONAL — keep where present
expected_duration_p95_seconds:
max_retries_recommended:
fallback:
recommended_temperature:  # OPTIONAL sanctioned extension (BA cluster)
tier_review_levels:       # OPTIONAL sanctioned extension (BA cluster)
compatibility: claude-code, codex, opencode   # scalar string, ALWAYS last
```

- `reversible` vocab mapping from v1: `true`→`reversible` · `soft`→`compensable` · `false`→`irreversible` · `n/a`→`not-applicable`.
- `pii_handling` vocab mapping from v1: `minimal`→`redact` (matches the workspace redaction rule); `none`/`redact`/`forbid` unchanged.
- Frontmatter VALUE changes (enum remaps, list→scalar) bump MINOR, not patch — frontmatter is engine-inert metadata but still a machine-readable surface (fleet adjudication F9).
- DELETE `status:` keys (stale process metadata; process state lives in YAML/dashboard).
- Tooling skills (`.claude/skills/`): flatten `metadata:` → top-level `version`; pipeline-only keys (stage_type, banking_grade, duration, retries, fallback) are NOT required for tooling skills; keep their frontmatter minimal but flat.

## 2. Body skeleton (exact headings, this order)

```
# <Title>
## Purpose
## When to use this skill
## Input contract
## Output contract
## Procedure
## Failure modes
## Constraints
## References        (optional)
```

- "Anti-Patterns" content merges into `## Constraints`.
- Field TABLES for I/O are banned. Each contract section = (a) `Validate against schemas/{input,output}.json.` sentence; (b) one prose paragraph: Required fields / Optional fields / stop-condition; (c) ONE compact fenced JSON example, ≤20 lines, required fields + `audit_id` only, placeholder values, no PII, under the lead-in `**Example (validates against schemas/output.json):**` (or input.json).
- Example sync is enforced by `workflows/scripts/check_contract_examples.py` (extracts the first fenced JSON block under each contract heading, validates against the referenced schema).
- `## Input contract` and every `schemas/input.json` carry the marker: `ENFORCED — the engine validates this ASSEMBLED stage input BEFORE the stage runs (engine/validation.py validate_stage_input; fail-closed).` **(2026-07-13: the markers said ADVISORY during the reshape; once the schemas described reality, the engine was wired to enforce them — `engine/config/runtime-binding.yaml input_validation: enforce`.)**
- SKILL.md ≤500 lines; depth goes to `references/`. Cross-skill references use bare skill names; dead refs to nonexistent skills are removed or re-pointed.

## 3. audit_id policy

- SEMANTICS (fleet adjudication F3): the artifact's `audit_id` is a **producer-stamped, deterministic provenance id** — derivation documented in each skill's Output contract, independent of optional inputs. It is DISTINCT from the engine's per-attempt execution audit id (events.jsonl); engine-side equality enforcement is a ledgered follow-up.
- EVERY pipeline skill's output carries required top-level `audit_id` (hash-chained audit house rule).
- The 6 holdouts adopt it: implement-backend-feature, implement-frontend-feature, review-backend-code, review-frontend-code, planning-banking-tests, eliciting-banking-brief.
- Promoted into YAML `required_fields` + boundary `required` for those stages.
- eliciting-banking-brief: audit_id derivation MUST be deterministic and independent of the optional `discovery` input (preserves byte-identical-when-absent regulatory property; documented in its Output contract).

## 4. Schema conventions

- Draft-07 everywhere (`$schema: http://json-schema.org/draft-07/schema#`). Convert generate-ux-pack's input+output (only 2020-12 files).
- `$id`: skill schemas `https://squad-delivery/skills/<name>/schemas/{input,output}.json`; boundary keeps `https://squad-delivery/schemas/<artifact>.json`.
- Strictness (amended per fleet adjudication F4 — 18/30 boundaries were strict, contradicting the doctrine): skill schemas strict (`additionalProperties: false`); the 14 strict STAGE boundaries (12 T-gates + discovery + plan-review) flip to `additionalProperties: true`. KEEP strict: handoff-receipt + revoke-receipt (deploy-class receipts, deliberate fail-closed rigidity) and the 2 pipeline bookends. Corollary: "additive output field = safe" holds only AFTER the flip. Boundary `required` stays the exact mirror of YAML `required_fields`.
- delivery-pipeline-output.json honestly declares the 10 promised workflow artifacts (properties + required == spec.output.required_fields); terminal assembly at runtime stays a ledgered follow-up (F5).
- Compensation joins the oracle (F8): deterministic revoke-receipt fixture in the corpus + `_sim` CHECKS entry + lint coverage of `compensating_action`.
- Boundary `description`s rewritten to current truth (many cite stale YAML required_fields).
- The engine hydration transform (mapping.py `_hydrate_ba_research`: epic/story refs inlined; `stories` added alongside `story_files`) is documented in: planning-banking-tests `schemas/input.json` properties, `workflows/schemas/ba-brief.json` description, eliciting-banking-brief Output contract.

## 5. Input contracts describe the POST-ADAPTER payload (fleet adjudication F2)

`schemas/input.json` documents what the skill actually receives after engine assembly: the
picked fields PLUS `discovery` nesting (ba-research), hydrated inline `epics`/`stories`
alongside `story_files` refs (ba-research consumers), and the engine-injected keys:
`idempotency_key` (every payload), `upstream_artifacts` (map producer-stage-id → relative
artifact path; whenever the stage has from_stage inputs — orchestrator.py:201), and the
conditional `loop_back_feedback` (only on re-runs after a reviewer loop_back). Injected keys
are optional properties with an `engine-injected` description prefix.
audit_id derivation formula (house): `UUIDv5(HOUSE_NS, "<stage-id>:<idempotency_key>")`
with `HOUSE_NS = uuid5(NAMESPACE_URL, "https://squad-delivery/audit")` — deterministic,
independent of optional inputs, matches the corpus's UUID style. FLAT-MERGE HAZARD (F1): same-named picks from two producers collide
last-writer-wins — affected consumers (qa-plan `verdict`; contract-tests/integration-tests/
appsec-scan `files_generated`) must document the collision; disambiguation via NESTED_HANDOFF
entries is a late-pass chunk gated on pytest, else ledgered follow-up.

## 5b. Consumer-required rule

If a consumer stage picks a producer field via `from_stage`, that field MUST be in the producer's `required` (skill schema + boundary + YAML `required_fields`) or explicitly whitelisted as optional-with-default in the consumer's Input contract. Known fix: qa-plan promotes `test_cases`, `signoff_criteria` to required.

Enforced statically by `workflows/scripts/check_contract_consistency.py`:
- every YAML `from_stage` pick ∈ producer required_fields (or whitelist) ∧ ∈ consumer input.json properties
- boundary `required` == YAML `required_fields` per stage.

## 6. Version bump policy (this pass)

ONE bump per skill, sized by its most severe change: doc-only → patch · additive schema → minor · breaking (new required / rename / tightening) → major if ≥1.0.0, minor if 0.x.
Lockstep checklist: frontmatter `version` → YAML `skill_version` pin (28 pins incl. compensation) → if output shape changed: boundary required+description + YAML required_fields → corpus patch in the SAME commit → full gate stack green → commit.
Never rename stage ids or artifact filenames (gates.yaml, runtime-binding.yaml, dashboard-data.json, `_sim` CHECKS key on them).
