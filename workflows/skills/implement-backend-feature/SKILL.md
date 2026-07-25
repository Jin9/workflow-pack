---
name: implement-backend-feature
version: 2.0.0
description: Generate production-grade Go backend code for one microservice feature from an approved design document. Use when implementing a Go HTTP handler from a design spec. Use when generating a CQRS command or query handler from an approved spec. Use when implementing a Kafka consumer or producer with idempotency requirements for a banking-grade service. Do NOT use for frontend or UI code. Do NOT use for infrastructure, Terraform, or Kubernetes manifests. Do NOT use for greenfield architecture decisions (defer to designing-tech-lead-handoff). Do NOT use for unplanned hotfix diagnosis (a human-triggered concern; pipeline-approved fix implementations may use this skill).
stage_type: generate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: detailed, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_generation, file_write]
expected_duration_p95_seconds: 180
max_retries_recommended: 2
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Implement Backend Feature

## Purpose

Take a single approved backend design and emit production-grade Go code plus
companion tests for one code-generation pass. Owns code synthesis
only — analysis, design, review, and validation live in sibling atomic skills.
Banking-grade discipline is non-negotiable on every output: idempotency keys on
side-effects, classified errors, propagated context, observability at every
failure mode, audit events on every state change.

## When to use this skill

- Use when: implementing a Go HTTP handler, CQRS command/query handler, or Kafka
  consumer/producer from the approved architecture handoff (tl-design's
  api_contracts + component_map, elaborated through the locked repo-generator
  scaffold).
- Use when: a code-generation step selects this skill for a Go microservice
  target package.
- Use when: a design specifies idempotency, audit, and compensation requirements
  and the next stage is code emission.
- Do NOT use when: frontend / UI code is the target.
- Do NOT use when: infrastructure (Terraform, K8s, CI/CD) is the target.
- Do NOT use when: the task is greenfield architecture — defer to `designing-tech-lead-handoff`.
- Do NOT use when: the task is unplanned hotfix diagnosis (human-triggered; a pipeline-approved fix implementation may use this skill).

## Input contract

ADVISORY — documents the assembled stage input; the engine validates workflow input
and stage OUTPUTS only (engine/validation.py). Validate against `schemas/input.json`.
Required: `api_contracts` + `component_map` (tl-design's ARCHITECTURE-LEVEL
blueprint — this skill elaborates it into production Go through the locked
repo-generator scaffold, whose conventions supply the L4 detail; the contracts'
payload_shape/idempotency_rules/failure_modes supply the behavioral detail),
`idempotency_key` (engine-injected: GENERATION-ATTEMPT identity — same key + same
inputs ⇒ same output bytes; NEVER embedded in generated source: application
runtime idempotency derives from each contract's `idempotency_rules`). Optional
engine-injected: `upstream_artifacts`, `loop_back_feedback` (backend-review
findings the regeneration MUST apply). Genuine ambiguity the scaffold + contracts
cannot resolve is an execution failure (needs-input), not silent invention. A
future detailed-design handoff (`backend_implementation_handoff`) is a ledgered
design follow-up, not part of this contract.

**Example (validates against schemas/input.json):**
```json
{
  "api_contracts": { "template_version": "1.0", "contracts": [] },
  "component_map": { "template_version": "1.0", "components": [] },
  "idempotency_key": "d4b8c2a0-7e31-4f95-8a6d-2c9e1b0f3a47"
}
```

## Procedure

Run all 7 steps in order. Do not skip steps for "small" features.

1. **Pre-flight — design completeness.** Verify the design declares: L1
   invariant, L2 contract + data owner, L3 transaction scope + idempotency
   strategy + observability, L4 file/package sketch. If any are missing or
   marked as "TBD" and the scaffold conventions cannot supply it, terminate as
   an execution failure (retry → human-queue). This stage has NO loop_back route;
   `loop_back_feedback` arrives only FROM backend review.
2. **Pre-flight — scaffold target.** Resolve the target service tree from the
   repo-generator scaffold (component_map names the services). Inspect conventions:
   error wrapping style, logger interface, context plumbing, repository shape,
   table-driven test style. Conventions discovered locally outrank
   `references/go-conventions.md` defaults.
3. **Inspect — repo-first.** Read at least 2 sibling handlers / consumers /
   commands in the same package. Mirror their boundary, naming, and import
   layout. If conventions conflict with the design, emit a `convention_conflict`
   uncertainty flag (advisory) and prefer the repo's conventions (additive
   change discipline).
4. **Generate — code.** Emit files in the smallest safe shape. Every emitted
   file MUST satisfy the rules in `references/implementation-rules.md` and the
   Go conventions in `references/go-conventions.md`. Specifically:
   - Idempotency: every external side-effect path takes a key from `idempotency_key`,
     deduplicates against the dedup mechanism named in the design document (e.g., a
     dedicated dedup/idempotency-key store such as a Postgres `idempotency_keys`
     table when the design does not specify one), and returns the prior result on
     replay.
   - Errors: preserve cause via `fmt.Errorf("...: %w", err)`. Classify as
     `client | server | dependency`. No panics in request paths.
   - Context: every exported function takes `ctx context.Context` first. No
     `context.Background()` inside request paths.
   - Observability: log + metric + trace span at every declared failure mode.
     Span name = `package.Function`. Metric label cardinality is bounded.
   - Security: validate every input at the boundary. Use repo-approved
     auth/crypto helpers — never hand-roll. No secrets in code, fixtures, or test
     data. No SQL string interpolation.
   - Audit: every state-changing path emits an audit event whose type is listed
     in `audit_events_emitted` output field. Event payload includes actor,
     action, target, timestamp, and decision metadata.
5. **Generate — tests.** Table-driven Go tests covering the happy path plus
   every declared failure mode. Test coverage MUST be `>= test_coverage_target`
   (default 0.80). Failing to reach coverage is an execution failure → retry → human-queue (the
   feature is over-scoped for one Generate pass).
6. **Self-review.** Apply every YES/NO item in `references/self-review-checklist.md`.
   Any NO halts emission and routes to `loop_back` or `human-queue` per the
   Failure Modes table.
7. **Emit.** Produce a payload conforming to `schemas/output.json`. Include
   every audit event type the code will emit, every compensating action defined
   for an irreversible path, the idempotency strategy in plain text, and the
   uncertainty flags raised during steps 1–6.

## Output contract

Validate against `schemas/output.json`: `files_generated[]{path, content_hash,
lines_added}` + `tests_generated[]{path, content_hash, coverage_pct}` (flat
manifests; producer-relative POSIX paths, no absolute paths or `..`),
`implementation_units[]{component_name, contract_names, files, tests}`
(required traceability: every path also appears in the flat manifests; `.go`
vs `_test.go` schema-enforced), `idempotency_strategy` (plain text) + optional
structured `runtime_idempotency[]` (from each contract's idempotency_rules —
never the workflow key), `compensating_actions[]{trigger, action_kind:
skill|code, action_ref, timeout_seconds}` (skill actions = bare kebab-case
names, e.g. `handoff-revoke`; code actions = producer-relative paths),
`audit_events_emitted[]`, `uncertainty_flags[]` (SUCCESS artifacts carry only
advisory kinds — convention_conflict, scope_overrun, other; blocking ambiguity
terminates execution instead), `decision_metadata`, and `audit_id` —
producer-stamped, deterministic: UUIDv5(HOUSE_NS,
"backend-implement:{idempotency_key}") for live derivations (corpus ids are
sim-convention, grandfathered).

**Example (validates against schemas/output.json):**
```json
{
  "audit_id": "84def0d2-df9b-5d04-a02d-ffd9662336b2",
  "files_generated": [{ "path": "services/auth/app/handlers/login.go", "content_hash": "sha256:ab12ab12ab12ab12ab12ab12ab12ab12ab12ab12ab12ab12ab12ab12ab12ab12", "lines_added": 120 }],
  "tests_generated": [{ "path": "services/auth/app/handlers/login_test.go", "content_hash": "sha256:cd34cd34cd34cd34cd34cd34cd34cd34cd34cd34cd34cd34cd34cd34cd34cd34", "coverage_pct": 0.96 }],
  "implementation_units": [{ "component_name": "auth", "contract_names": ["auth.login"], "files": ["services/auth/app/handlers/login.go"], "tests": ["services/auth/app/handlers/login_test.go"] }],
  "idempotency_strategy": "login issues a new session pair; refresh dedupes on token family.",
  "compensating_actions": [],
  "audit_events_emitted": ["auth.login.succeeded"],
  "uncertainty_flags": [],
  "decision_metadata": { "complexity": "medium", "pattern_choices": [], "repo_conventions_followed": [] }
}
```

## Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Design has unresolved ambiguities | Step 1: detail the scaffold + contracts cannot supply | execution failure → retry ×2 → backend-implement-failures queue |
| Scaffold target unresolvable | Step 2: component_map names no known service | execution failure → retry ×2 → backend-implement-failures queue |
| Repo conventions conflict with design | Step 3: discovered pattern contradicts design intent | Prefer repo, emit advisory `convention_conflict`, continue |
| Test coverage `< test_coverage_target` | Step 5: coverage report | execution failure → retry ×2 → backend-implement-failures queue |
| Self-review checklist has any NO | Step 6 | First NO that is data/auth/idempotency: `human-queue`; otherwise execution failure → retry |
| Output fails `schemas/output.json` validation | Step 7: schema check | `retry` once with full self-review re-run; second failure: `human-queue` |
| Generation produced unreviewed external HTTP, secret access, or destructive command | Self-review item | `human-queue` immediately, no retry |

## Constraints

- DO NOT introduce dependencies (modules, libraries, services) not named in the design.
- DO NOT emit code for an external side-effect path without an idempotency key on that path.
- DO NOT emit code without companion tests in the same payload.
- DO NOT swallow errors with `_ = err`, `recover()` outside an explicit safety boundary, or by returning `nil` on a non-recoverable failure.
- DO NOT hardcode secrets, tokens, connection strings, or PII — not in code, fixtures, or test data.
- DO NOT modify generated artifacts (protobuf, OpenAPI clients) or committed migration outputs by hand; regenerate or add a new migration.
- DO NOT widen public contracts (API, message schema, persisted shape) beyond what the design declares.
- DO NOT skip self-review steps 4–7 for "obviously small" features — banking-grade applies on every Generate.

## References

| Need | File |
|------|------|
| The 11 banking-grade decision rules + v2 audit/idempotency/compensation augmentations | `references/implementation-rules.md` |
| Go conventions (errors, context, tests, lint) for emitted code | `references/go-conventions.md` |
| YES/NO checklist applied at step 6 before emit | `references/self-review-checklist.md` |
| Why this skill exists (provenance, human audit only — do not load into LLM context) | `RATIONALE.md` |
