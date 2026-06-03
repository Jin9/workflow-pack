---
name: implement-backend-feature
description: >
  Generate production-grade Go backend code for one microservice feature from an
  approved design document. Use when implementing a Go HTTP handler from a design
  spec. Use when generating a CQRS command or query handler from an approved spec.
  Use when implementing a Kafka consumer or producer with idempotency requirements
  for a banking-grade service. Do NOT use for frontend or UI code. Do NOT use for
  infrastructure, Terraform, or Kubernetes manifests. Do NOT use for greenfield
  architecture decisions (defer to design-backend-feature). Do NOT use for fixing
  existing production bugs (use generate-backend-fix).
compatibility: [claude-code, codex, opencode]
metadata:
  version: 1.0.0
  stage_type: generate
  input_schema: schemas/input.json
  output_schema: schemas/output.json
  banking_grade: {idempotent: true, reversible: soft, audit_level: detailed}
  expected_duration_p95_seconds: 180
  max_retries_recommended: 2
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
  consumer/producer from an approved design document.
- Use when: a code-generation step selects this skill for a Go microservice
  target package.
- Use when: a design specifies idempotency, audit, and compensation requirements
  and the next stage is code emission.
- Do NOT use when: frontend / UI code is the target.
- Do NOT use when: infrastructure (Terraform, K8s, CI/CD) is the target.
- Do NOT use when: the task is greenfield architecture — defer to `design-backend-feature`.
- Do NOT use when: the task is repairing a known production bug — defer to `generate-backend-fix`.

## Input

Input MUST validate against `schemas/input.json`. Required fields:

| Field | Type | Notes |
|-------|------|-------|
| `design_document` | string (markdown) | Approved design. Must declare invariant, contract, data owner, error cases, idempotency strategy. |
| `target_package` | string | Existing Go package path (e.g., `internal/loan/disbursement`). |
| `idempotency_key` | string (UUID v4) | Same key → same output bytes. |

Optional: `convention_overrides` (object), `test_coverage_target` (default `0.80`).

Reject the input with a `loop_back` signal if any required field is missing,
malformed, or if the design contains unresolved ambiguities (see Failure Modes).

## Procedure

Run all 7 steps in order. Do not skip steps for "small" features.

1. **Pre-flight — design completeness.** Verify the design declares: L1
   invariant, L2 contract + data owner, L3 transaction scope + idempotency
   strategy + observability, L4 file/package sketch. If any are missing or
   marked as "TBD", emit `uncertainty_flags` and signal `loop_back`.
2. **Pre-flight — target package exists.** Read `target_package`. If it does
   not exist, signal `loop_back` to design. If it exists, inspect conventions:
   error wrapping style, logger interface, context plumbing, repository shape,
   table-driven test style. Conventions discovered locally outrank
   `template-defaults.md`.
3. **Inspect — repo-first.** Read at least 2 sibling handlers / consumers /
   commands in the same package. Mirror their boundary, naming, and import
   layout. If conventions conflict with the design, emit an `uncertainty_flag`
   and prefer the repo's conventions (additive change discipline).
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
   (default 0.80). Failing to reach coverage signals `loop_back` (the feature
   is over-scoped for one Generate pass).
6. **Self-review.** Apply every YES/NO item in `references/self-review-checklist.md`.
   Any NO halts emission and routes to `loop_back` or `human-queue` per the
   Failure Modes table.
7. **Emit.** Produce a payload conforming to `schemas/output.json`. Include
   every audit event type the code will emit, every compensating action defined
   for an irreversible path, the idempotency strategy in plain text, and the
   uncertainty flags raised during steps 1–6.

## Output Contract

Output MUST validate against `schemas/output.json`. Structured fields:

| Field | Type | Purpose |
|-------|------|---------|
| `files_generated` | array of `{path, content_hash, lines_added}` | Files written. `content_hash` = sha256 of file bytes. |
| `tests_generated` | array of `{path, content_hash, coverage_pct}` | Companion tests. Each entry MUST achieve `>= test_coverage_target`. |
| `idempotency_strategy` | string | Plain-text description of the dedup mechanism. For naturally idempotent paths (GET, pure analyze) state so. |
| `compensating_actions` | array of `{trigger, action_skill_ref, timeout_seconds}` | Empty if no irreversible external effect. Required for any `commit` / `notify`-equivalent path. |
| `audit_events_emitted` | array of event-type strings | Every state-changing path must contribute at least one entry. |
| `uncertainty_flags` | array of `{kind, location, note}` | Ambiguities surfaced during steps 1–6. Non-empty signals a downstream `loop_back` (revision request). |
| `decision_metadata` | object `{complexity, pattern_choices, repo_conventions_followed}` | For audit. `complexity` in `low|medium|high`. |

## Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Design has unresolved ambiguities | Step 1: any `TBD`, missing L1/L2/L3/L4 | `loop_back` to the design author with `uncertainty_flags` populated |
| Target package missing or unreadable | Step 2: filesystem / permission error | `loop_back` to design (package boundary undecided) |
| Repo conventions conflict with design | Step 3: discovered pattern contradicts design intent | Prefer repo, emit `uncertainty_flag`, continue |
| Test coverage `< test_coverage_target` | Step 5: coverage report | `loop_back` to design (feature is over-scoped for one Generate) |
| Self-review checklist has any NO | Step 6 | First NO that is data/auth/idempotency: `human-queue`; otherwise `loop_back` |
| Output fails `schemas/output.json` validation | Step 7: schema check | `retry` once with full self-review re-run; second failure: `human-queue` |
| Generation produced unreviewed external HTTP, secret access, or destructive command | Self-review item | `human-queue` immediately, no retry |

## Anti-Patterns

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
| Why this skill exists, what was extracted from the source, what was added | `RATIONALE.md` (human audit only — do not load into LLM context) |
