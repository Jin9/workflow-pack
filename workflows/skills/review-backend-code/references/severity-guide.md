# Severity Guide & Verdict Matrix

Applied at step 7 of `SKILL.md` to classify findings and compute the verdict.
Banking-grade flavored: every routing decision is deterministic, and the
verdict is a function of the findings, not the other way around.

Source: extracted from
`treasury/crafting-backend-code/SKILL.md` (review-mode P1/P2/P3),
`treasury/validating-banking-implementation/SKILL.md` (auto-reject criteria), and
`treasury/reviewing-software-security/SKILL.md` (severity + confidence
discipline). Re-cast as a single matrix the Review stage applies.

## Severity definitions

### `P1` — block

Banking-grade non-negotiables. A `P1` finding ALWAYS routes to
`human-queue` — never `loop_back`, never `approve`. The Generate stage
cannot fix `P1` issues in another iteration without a person looking.

Categories that are inherently `P1`:

- Data correctness — missing transaction boundary on a state-mutating flow,
  cross-aggregate write without outbox / saga, lost update on a
  concurrency-sensitive path.
- Idempotency — missing key on an external side-effect path, dedup store
  not consulted on replay, silent overwrite on same-key conflict.
- AuthN / AuthZ — handler reachable without authentication, ownership
  predicate missing, tenant-scoping absent from a query.
- Secret exposure — credentials / tokens / connection strings in code,
  fixtures, test data, logs, or error messages.
- Injection — unparameterized SQL, command interpolation, deserialization
  of untrusted input, SSRF on a user-controlled URL.
- Audit — state change with no audit event emitted, or with an event_type
  not declared in Generate output.
- Compensation — irreversible external call with no declared compensating
  action and no `human-queue` escalation in the workflow.
- PII handling — PII written to a log line, error response, or test fixture
  without masking.
- Hand-rolled crypto where a repo-approved helper exists.
- Hand-edited generated file or committed migration.

### `P2` — fix before merge

Correctness or discipline issues the next Generate iteration can address.
`P2` routes to `loop_back` (target = `implement`).

Categories typically `P2`:

- Error not wrapped with `%w`; cause lost in the chain.
- Error not classified (`client | server | dependency`); retry-policy will
  be guessed at the edge.
- Context not propagated into a downstream call.
- Missing observability on a declared failure mode (counter / log / span).
- Test missing for a declared failure mode.
- Per-file coverage claim implausible (test obviously thin).
- Pattern choice declared by Generate not consistent with the code.
- Convention divergence not flagged by Generate.

### `P3` — note, don't block

Style, scope, or future-improvement items. `P3` does NOT block `approve`.
The finding is carried forward as a note for the next sprint / refactor.

Categories typically `P3`:

- Code duplication that could be extracted (within reason — banking-grade
  prefers boring over clever).
- Comment / docstring style.
- Test could be table-driven but isn't (when correctness is unaffected).
- Naming inconsistency that doesn't break discovery.
- Adjacent issue spotted outside `code_under_review` (file the reviewer
  noticed in passing).

## Confidence

Borrow the discipline from `reviewing-software-security`:

- **High** — file:line cited, behavior reproducible from the code alone.
- **Medium** — pattern is present but the exploit / failure path requires
  context the reviewer doesn't have (e.g., upstream caller behavior).
- **Low** — suspicion only. The reviewer cannot cite file:line confidently.

**Hard rule** (verbatim from the source): never publish a `P1` / `P2` at
`Low` confidence without an explicit `[needs verification]` tag in the
finding's `evidence` field. Do not fabricate file:line references,
standards identifiers, or CWE numbers — withhold instead.

When confidence is `Low`, drop the severity by one tier (`P1` → `P2`,
`P2` → `P3`) before applying the verdict matrix, unless the design
itself flagged the area as known-fragile.

## Verdict matrix

Applied after every finding has a severity. The verdict is the highest
escalation any finding produces, with one extra check for unsubstantiated
claims.

| Condition | Verdict | `loop_back_target_stage` |
|-----------|---------|--------------------------|
| Any `P1` finding | `human-queue` | null |
| `claims_unverified` non-empty (and no `P1`) | `loop_back` | `implement` |
| Any `P2` finding (and no `P1` / no unverified claims) | `loop_back` | `implement` |
| `uncertainty_flag` of kind `design_ambiguity` raised in step 2 | `loop_back` | `design` (overrides `implement` routing) |
| Only `P3` findings (and no `P1` / no `P2` / no unverified claims / no design ambiguity) | `approve` | null |
| No findings at all | `approve` | null |

Notes:

- `design_ambiguity` always wins routing — fixing it at `implement` is
  treating the symptom. Send it back to `design`.
- `human-queue` from a `P1` is final for this stage. The workflow policy
  decides whether the human can override.
- `approve` with `P3` findings still emits them — the next stage receives
  them as a notes list, not as blockers.

## Standards identifiers

When a finding maps to a published standard, cite it in
`finding.standards_ref`. Withhold (omit the field) rather than guess.

Acceptable identifier shapes:

- `CWE-###`
- `OWASP A0#:2021` or `OWASP API#:2023`
- `ASVS V#.#.#`
- `NIST SSDF PW.#.#` / `PS.#.#`
- `CIS Kubernetes #.#.#` / `CIS MySQL #.#.#`
- `SLSA L#`

If unsure of the exact identifier, omit the field. Do NOT invent.
