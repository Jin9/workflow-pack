# Review Rubric

The canonical scan list applied at step 4 of `SKILL.md`. Each item is the
same banking-grade rule used by `implement-backend-feature` — but re-cast as
an *adversarial question* the reviewer asks of the code. The mapping is
1:1: every rule a Generate stage must follow, the Review stage must verify.

The framing differs deliberately:
- Generate's `self-review-checklist.md`: "Did I do X?" (first-person, self-discipline)
- This file: "Show me where X is. Cite the line." (third-person, adversarial)

When a question's answer is "no" or "not visible in the code," emit a
finding. Severity is assigned at step 7 using `severity-guide.md`.

## Base rule questions (11)

Source for the rules: `treasury/crafting-backend-code/references/decision-rules.md`.

| # | Rule | Adversarial scan question |
|---|------|---------------------------|
| B1 | Pattern first for templates | Has the code copied an example service's package name, deployment shape, or business capability as if it were mandatory? Cite the over-borrowed identifier. |
| B2 | Repo first for existing services | Does the new code mirror the existing package's error wrapping, logger, validator, DI shape, and test style? Cite a sibling file that the code diverges from. |
| B3 | Contracts before code | Does every public function / handler / message exposed by the new code match the contract declared in the design (shape, versioning, error envelope, auth)? Cite the design line and the code line. |
| B4 | One owner per piece of state | Does the new code mutate a table / aggregate / cache key / event stream that another package already owns? Cite the cross-package write. |
| B5 | Transactions are explicit | For every multi-statement write path: is `BEGIN`/`COMMIT` visible? For cross-aggregate work: is outbox / saga / compensation present? Cite the missing boundary. |
| B6 | Idempotency is required for retries | For every command handler / webhook / consumer / outbox dispatcher: where is the dedup key persisted and checked? Cite the missing dedup. |
| B7 | Context propagates | Does every exported function take `ctx context.Context` first and pass it into every repo / HTTP / Kafka call? Cite a function that drops ctx. |
| B8 | Errors are operational signals | Is every returned error wrapped with `%w`? Is every public error response free of SQL fragments, internal IDs, stack traces, env values, PII? Cite the leak. |
| B9 | Observability follows failure modes | For every declared failure mode in the design: is there a counter, a log line, a span? Cite the missing instrumentation. |
| B10 | Security is not a cleanup task | Are authN / authZ / input validation / SSRF guards / parameterized queries / secret handling / PII masking / approved crypto all present at the boundary they belong? Cite the missing control. |
| B11 | Generated and migrated artifacts are special | Has the code edited a generated file (`*.pb.go`, OpenAPI client, committed migration)? Cite the edit. |

## v2 augmentation questions (7)

Source for the augmentations: `implement-backend-feature/references/implementation-rules.md`.

| # | Augmentation | Adversarial scan question |
|---|--------------|---------------------------|
| A1 | Canonical audit event shape | For every state-changing path: is exactly one audit event emitted with `event_type / actor / action / target / timestamp / trace_id / decision_metadata`? Does the event_type appear in `implement_stage_output.audit_events_emitted`? Cite the missing emit or the mismatch. |
| A2 | Application idempotency vs contract | For every external side-effect path: is an application idempotency key read at the boundary in the FORM the api_contracts idempotency_rules declare (never assume UUID-v4; the engine workflow key is NOT an application key)? Is `(key, request_hash, response_payload, status)` persisted? Does a same-key replay return the stored response without re-running the side-effect? Does a same-key + different-request_hash return a 409 / domain-equivalent? Cite the missing piece. |
| A3 | Compensating-action discipline | For every irreversible external side-effect in the code: is the corresponding `compensating_actions[].trigger` declared by Generate and is its referenced action_skill_ref plausible? Cite an irreversible call site that has no declared compensation. |
| A4 | Error classification (`client | server | dependency`) | Does every error returned from a handler carry a class at the type level (not inferred at the edge)? Does the class drive the HTTP status, retry decision, and trace error attribute correctly? Cite the unclassified error. |
| A5 | Test fixtures discipline | Do any test files call `net/http` against a real host, read secrets from environment, mutate shared state between cases, or `t.Skip(...)` without a named unblock condition? Cite the offender. |
| A6 | Convention discovery overrides templates | If the code follows a template default but the target package's existing code uses a different convention (e.g., custom logger vs. `slog`): did Generate emit a `convention_conflict` uncertainty flag? Cite the divergence the flag should have named. |
| A7 | No silent dependency additions | Does the code import a Go module not in `go.mod`? Did Generate emit a `dependency_addition` uncertainty flag? Cite the import. |

## Workflow-contract questions

In addition to the rules, the Review stage verifies the Generate stage's
contract-level claims. These do not map to a base rule — they exist
because the workflow exists.

| # | Contract item | Adversarial scan question |
|---|---------------|---------------------------|
| C1 | Companion tests exist | Is there a test file for every production file in `code_under_review`? Cite the unaccompanied production file. |
| C2 | Per-file coverage claim plausibility | For each `tests_generated[].coverage_pct` claim: does the test file appear to exercise the branches required to reach that number? Cite a coverage claim with an obviously thin test. |
| C3 | `decision_metadata.pattern_choices` consistency | For each pattern choice declared by Generate (e.g., "no audit on read-only path"): is the code consistent with the choice? Cite the inconsistency. |
| C4 | `uncertainty_flags` triage | For each flag Generate raised: is it still unresolved, was it resolved by the code in a way the design accepts, or does it need escalation? Output a triage line per flag. |

## Out-of-scope by design

This skill does NOT cover:

- Full OWASP Top 10 walk per artifact — that is `validating-banking-implementation` or
  `reviewing-software-security` scope. The Review stage spot-checks
  security via B10 + A4 only.
- Chaos test planning — separate stage.
- Performance / load testing — separate stage.
- Architectural / boundary critique — that was the design stage's job.
  The Review stage takes the design as given.

If a reviewer spots an issue outside scope, surface it as an `uncertainty_flag`
of kind `other`, not as a finding.
