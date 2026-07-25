# RATIONALE — review-backend-code

> **Audience**: humans reviewing the skill before merge / promotion.
> **Not loaded into LLM context.**
>
> **Source skills consulted** (mono-skills, all multi-mode):
> - `treasury/crafting-backend-code/` (mode `review`)
> - `treasury/validating-banking-implementation/`
> - `treasury/reviewing-software-security/`
> - `treasury/implement-backend-feature/` (the upstream Generate stage whose
>   output this skill verifies — co-evolved, not extracted from)

## 1. Why this skill exists

`COGNITIVE_OS.md` Section 6 wires a `review-code` stage between `implement-code`
and `validate-build` in the Dev workflow, with failure policy `loop_back` to
`design-handler` (max 2 loops). Without an atomic review skill, the Generate
stage has nowhere to be checked — the next stage is `validate-build` (a
compile/test runner), which catches syntax and test failures but not
banking-grade discipline.

The closest sources are all mono-skills:

- `crafting-backend-code` has a `review` mode but mixed in with five other
  modes (`design`, `optimize`, `fix`, `analyze`, `plan`) and produces
  free-form markdown, not a machine-routable verdict.
- `validating-banking-implementation` is the right *posture* (adversarial, Approve/Reject)
  but its scope spans full OWASP + concurrency + chaos planning — too
  heavy for the workflow's per-feature Review stage.
- `reviewing-software-security` is exhaustive security review across
  infra, gateways, K8s — comprehensive but out of scope for the per-feature
  Review (it belongs in its own workflow).

This skill is the *workflow-internal verifier*: same rules the Generate
stage applies, run adversarially from the opposite end.

## 2. What was extracted from the sources

| Source | Target | Notes |
|--------|--------|-------|
| `crafting-backend-code/SKILL.md` mode `review` checklist (severity, evidence, fix per finding) | `SKILL.md` Procedure + `schemas/output.json` finding shape | Re-cast as a machine-readable JSON contract |
| `crafting-backend-code/references/decision-rules.md` (11 rules) | `references/review-rubric.md` § Base rule questions (B1–B11) | Re-cast each rule as an adversarial scan question. Same 11 rules. |
| `implement-backend-feature/references/implementation-rules.md` v2 augmentations (A1–A7) | `references/review-rubric.md` § v2 augmentation questions (A1–A7) | Re-cast each augmentation as an adversarial scan question. Same 7 augmentations. |
| `implement-backend-feature/references/self-review-checklist.md` sections A–J | `references/review-checklist.md` sections A–J | Lifted the structure 1:1 so generate-side and review-side cover identical ground. Wording shifted from first-person ("Did I...?") to third-person ("Cite the line...") |
| `validating-banking-implementation/SKILL.md` auto-reject criteria (P1 vulns, missing transaction, unverifiable code) | `references/severity-guide.md` § P1 categories + verdict matrix | The auto-reject list became the P1 category list. |
| `validating-banking-implementation/SKILL.md` validation gate items | `SKILL.md` Failure Modes + audit_metadata `rules_evaluated` field | The gate's "every category walked" check became a numeric floor in the audit metadata. |
| `reviewing-software-security/SKILL.md` severity-and-confidence discipline | `references/severity-guide.md` § Confidence + the hard rule against fabrication | The confidence rules and "never publish at Low without [needs verification]" rule transferred verbatim. Standards-identifier shapes (CWE/ASVS/OWASP/NIST/CIS/SLSA) preserved. |
| `reviewing-software-security/SKILL.md` Finding Format philosophy | `schemas/output.json` finding object | Compressed from 16-field template to 8 required fields; standards_ref optional. |

## 3. What was added (v2-specific augmentations)

| Augmentation | Lives in | Why it's new |
|--------------|----------|--------------|
| Machine-readable `verdict` enum (`approve | loop_back | human-queue`) | `schemas/output.json`, severity-guide.md verdict matrix | Source skills emitted markdown verdicts. Workflow engine needs an enum. |
| `loop_back_target_stage` (`design | implement | null`) | `schemas/output.json` | Section 8 Review Pattern says "loop back to earlier stage" but did not specify which. This stage decides: `design_ambiguity` → design; everything else → implement. |
| Claims-vs-reality verification (step 6) | `SKILL.md` Procedure, `review-rubric.md` § C1–C4, `review-checklist.md` § K | The unique reason a Review stage exists in v2: verify the upstream stage's claims. None of the source skills did this — they reviewed standalone code, not the *output of a Generate stage*. |
| `claims_verified` / `claims_unverified` arrays | `schemas/output.json` | The Review stage's specific output beyond findings: trust-but-verify trail. |
| `audit_metadata.rules_evaluated` floor (≥ 22) | `schemas/output.json`, harness `RulesEvaluatedFloorAssertion` | Forces the reviewer to walk every rule. The source skills' validation gate said "every category walked" but did not numerically enforce. |
| `severity_floor` input (default `P3`) | `schemas/input.json` | Lets noisy reviews be quieted at the workflow-config layer without changing the skill. |
| `design_ambiguity` overrides `loop_back_target_stage` | severity-guide.md verdict matrix | New rule: fixing a design ambiguity at implement is treating the symptom. Always route to design. |
| Audit-event-on-every-verdict expectation | SKILL.md frontmatter `audit_level: detailed` + Procedure step 7 | Per Section 8 audit event schema, every stage emits an audit event. Review is no exception. |

## 4. What was intentionally dropped (and why)

| Dropped from sources | Reason |
|----------------------|--------|
| `validating-banking-implementation` chaos planning mode | Separate stage in v2 (`chaos-plan-stage` — to be built). |
| `validating-banking-implementation` full OWASP A01–A10 walk per artifact | Too heavy for per-feature review. Spot-checked via B10 + A4 only. The full walk belongs in `reviewing-software-security` as its own workflow. |
| `reviewing-software-security` 11-area taxonomy + 12 worked examples | Out of scope. That skill remains the comprehensive security review; this stage spot-checks against the workflow's own rule set. |
| `reviewing-software-security` STRIDE Depth 2/3 + abuse-case catalog | Same — belongs in the comprehensive review skill. Review stage uses inline (Depth 1) STRIDE only when judging a security finding. |
| `crafting-backend-code` other 5 modes (`design`, `optimize`, `fix`, `analyze`, `plan`) | Each is a separate atomic skill in v2. |
| Mode-selection logic | Workflow engine picks the skill. |

## 5. Deviations from the prompt / standards (flagged)

| Standard / convention | We did | Why |
|-----------------------|--------|-----|
| `tests/README.md` (project default) | `tests/harness-guide.md` | `quick_validate.py` BANNED_DOCS rejects `README.md` at any depth. Same trade-off as `implement-backend-feature`. |
| Nested YAML `banking_grade:` block (per `COGNITIVE_OS.md` Section 7) | Inline YAML `{idempotent: true, reversible: n/a, audit_level: detailed}` | Flat-YAML validator can't parse indented frontmatter. Inline round-trips through any real YAML parser. Same trade-off as `implement-backend-feature`. |
| Success criteria reference to `schemas/skill-v1.schema.json` | Validated against `quick_validate.py` only | No `schemas/skill-v1.schema.json` exists in this repo yet. |

## 6. What still needs human review

- **`audit_metadata.rules_evaluated` floor of 22** is a hard count today
  (11 base + 7 augmentation + 4 contract). If the rule set grows, the floor
  needs to grow with it — or move to a fraction (`>= 1.0`).
- **Claims-vs-reality coverage** depends on the reviewer LLM actually
  searching every claim. The `RulesEvaluatedFloorAssertion` checks the
  count but not the depth. The harness should add a check that every
  `audit_events_emitted` entry from input appears either in `claims_verified`
  or `claims_unverified` — neither dropped.
- **`severity_floor` interaction with `P1` routing**: if a workflow sets
  `severity_floor: P2`, a `P1` is still emitted and still forces
  `human-queue`. Documented in the schema; worth re-checking when the
  workflow engine implements floor handling.
- **Confidence-driven severity drop** (P1 → P2 → P3 when confidence is Low)
  is documented but not enforced by schema. The harness should add an
  assertion.
- **Standards identifier validation**: `standards_ref` is a free string —
  no regex enforces shape. Trade-off chosen because the union regex is
  ugly and the rule "withhold rather than fabricate" is human-judgment.

## 7. Recommended next skills to build

Two candidates, both unblocking the Dev workflow further:

1. **`validate-build-go`** (`stage_type: validate`) — Run `go build`,
   `go test`, `golangci-lint`, `go vet` on the emitted code and emit a
   structured pass/fail with per-tool output. Smallest, most mechanical
   next skill. Build first.
2. **`analyze-backend-spec`** (`stage_type: analyze`) — The upstream
   sibling of `design-backend-feature`. Takes a raw spec and extracts the
   structured requirements that `design-backend-feature` turns into a
   design. Build second; the workflow can survive without it for a while
   if specs come in already analyzed.
