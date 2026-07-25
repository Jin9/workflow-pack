# Implementation Rules

Authoritative rules applied during step 4 (Generate) and re-checked at step 6
(Self-review) of `SKILL.md`. The 11 base rules are preserved verbatim from
the pre-consolidation source pack (provenance: workflows/skills/README.md) — they are
banking-grade non-negotiables and do NOT change between stages.

The v2 augmentations are added below the base set. They make the rules
workflow-aware: every Generate stage emits audit events, takes an idempotency
key, and declares compensation for irreversible paths.

## Base Rules (verbatim from source)

- **Pattern first for templates**: extract reusable backend service patterns from examples without copying example package names, deployment shape, or business capabilities as mandatory rules.
- **Repo first for existing services**: match the existing architecture, naming, errors, logging, validation, dependency injection, tests, and package layout before importing a preferred pattern.
- **Contracts before code**: for APIs and messages, decide request/response shape, versioning, compatibility, errors, and authorization before implementation.
- **One owner per piece of state**: do not let multiple services or packages mutate the same table, aggregate, cache key, or event stream without a clear ownership rule.
- **Transactions are explicit**: name what is atomic, what is eventually consistent, and what compensation or retry handles partial failure.
- **Idempotency is required for retries**: commands, webhook handlers, queue consumers, and outbox dispatchers must tolerate duplicate delivery where duplicates are plausible.
- **Context propagates**: carry cancellation, deadlines, trace IDs, auth claims, and request metadata through service, repository, and client calls according to repo conventions.
- **Errors are operational signals**: preserve cause, classify client vs server vs dependency errors, avoid panics in request/worker paths, and avoid leaking secrets or internals in public responses.
- **Observability follows failure modes**: add logs, metrics, traces, and readiness checks where they help operators detect and diagnose real failures.
- **Security is not a cleanup task**: check authN/authZ, input validation, SSRF/deserialization risks, secret handling, SQL injection, PII logging, and crypto usage before shipping backend changes.
- **Generated and migrated artifacts are special**: do not hand-edit generated files or committed migration outputs unless the discovered workflow requires it; regenerate or add migrations using target tooling.

## v2 Augmentations (Generate stage specific)

### A1. Audit event emission

Every state-changing path emits exactly one canonical audit event per state
transition. The event shape:

```json
{
  "event_type": "domain.entity.action.outcome",
  "actor": {"id": "...", "type": "user|service|system"},
  "action": "create|update|delete|approve|reject|...",
  "target": {"id": "...", "type": "entity_type", "version": "..."},
  "timestamp": "RFC3339",
  "trace_id": "...",
  "decision_metadata": {...}
}
```

`event_type` MUST appear in the skill's `audit_events_emitted` output field.
Read-only paths (GET, pure analyze) emit no audit event.

### A2. Idempotency key format

`idempotency_key` is a UUID v4 passed in from the workflow. The Generated code
MUST:

- Accept the key at the boundary (HTTP header `Idempotency-Key`, message
  header `idempotency_key`, or function parameter).
- Persist `(key, request_hash, response_payload, status, created_at)` in the
  repo's `idempotency_keys` table (or the named equivalent from the design).
- On replay with the same key: return the stored response without re-running
  the side-effect.
- On replay with a different `request_hash` for the same key: return a
  `409 Conflict` (HTTP) or domain-equivalent error. Never silently overwrite.
- Naturally idempotent paths (GET, pure analyze) skip persistence but state
  this in the `idempotency_strategy` output field.

### A3. Compensating action discipline

Every external irreversible side-effect (publish to topic, call partner API,
write to ledger, send notification) MUST declare a compensating action in the
`compensating_actions` output array:

```json
{
  "trigger": "publish_disbursement_event",
  "action_kind": "skill",
  "action_ref": "handoff-revoke",
  "timeout_seconds": 60
}
```

If a compensating action is impossible (e.g., "send SMS"), state so explicitly
in `decision_metadata.pattern_choices` and escalate to `human-queue` policy in
the workflow rather than silently shipping unreversible code.

### A4. Failure classification at the boundary

Every error returned from a handler MUST carry a class that maps to:

| Class | HTTP | Retry-safe? | Audit? |
|-------|------|-------------|--------|
| `client` | 4xx | No (caller fault) | Yes — log + metric, no trace error |
| `server` | 5xx | Yes (transient) | Yes — log + metric + trace error |
| `dependency` | 502/503/504 | Yes (with backoff) | Yes — log + metric + trace error + circuit-breaker trip |

The class is part of the error type, not inferred at the edge.

### A5. Test fixtures are inputs, not magic

Tests use deterministic fixtures from `testdata/`. Tests MUST NOT:

- Call external networks (`net/http` against real hosts).
- Read secrets from the environment.
- Mutate shared state between cases.
- Skip without a `t.Skip(reason)` that names the unblock condition.

### A6. Convention discovery overrides templates

When `references/go-conventions.md` and the repo's actual code disagree, the
repo wins. Emit an `uncertainty_flag` of kind `convention_conflict` documenting
the divergence so reflection can update the template later.

### A7. No silent introduction of dependencies

If the Generate step would require a Go module not already in `go.mod`, halt
and emit `uncertainty_flag` of kind `dependency_addition`. Adding a dependency
is a design decision; the Generate stage does not make design decisions.

## Decision matrix (quick lookup)

| Situation | Action |
|-----------|--------|
| Design ambiguous | Step 1: `loop_back` with `uncertainty_flags` |
| Target package missing | Step 2: `loop_back` |
| Repo convention conflicts with design | Step 3: prefer repo, emit `uncertainty_flag`, continue |
| External side-effect without compensation possible | Step 4: escalate `human-queue`, do not emit |
| Test coverage below target | Step 5: `loop_back` (over-scoped) |
| Self-review finds NO on data/auth/idempotency | Step 6: `human-queue` |
| Output fails schema validation | Step 7: `retry` once, then `human-queue` |
