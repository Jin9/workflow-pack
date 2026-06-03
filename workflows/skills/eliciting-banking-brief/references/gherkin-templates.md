# Gherkin Templates

> Gherkin format rules + banking-grade scenario library. Loaded by `SKILL.md` Step 8 (banking-grade auto-emission) and Step 10 (AC composition).

## Purpose & When to Apply

Loaded on every AC composition pass. Every prose AC from raw input → Gherkin `Given/When/Then` with concrete values. For every state-change / notification / customer-facing story, auto-emit the banking-grade scenarios in §6 even when the source did not write them. Reference templates by inserting under each story's `acceptance_criteria` block per `schemas/output.json`.

Sources: C18, C20, C21, C29, C30; AP-4.2, AP-4.3, AP-4.4, AP-7.2, AP-8.1, AP-8.2, AP-8.3, AP-8.4; ba-best-practices §2.

## Format Rules

- **`Given`** = state / preconditions only. NO actions. Must name (a) concrete actor with role, (b) concrete state (`application status = "verification failed"`; `wire status = "additional review"`), (c) concrete input data where relevant (`NRIC re-upload, retry_attempt = 2`).
- **`When`** = ONE trigger action per scenario. Multi-action `When` is forbidden (AP-8.2) — chaining actions hides which step failed and breaks idempotency-replay.
- **`Then`** = observable outcome: UI element change / DB state with concrete field / outbound message with required payload / downstream event emission. Subjective predicates (`is happy`, `is satisfied`, `is improved`) forbidden (AP-8.3).
- **`And`** chains `Given` (additional preconditions) or `Then` (additional outcomes) only. Never chains additional `When` actions.
- One scenario per behavior. Never combine happy + error in one scenario (AP-7.2).

## Concrete-Value Enforcement

Replace vague placeholders with calculated values. Banking-corpus examples:

| Vague | Concrete | Rule |
|---|---|---|
| `Given a valid amount` | `Given amount = 50000` | Use input metadata when available |
| `When customer submits by EOW` | `When customer submits by 2026-05-16` | Resolve relative dates via SKILL.md Step 3 |
| `Then N=3 retries allowed` (anonymous source) | `Then proposed_retry_limit = 3 (anonymous, requires_named_owner: true)` | AP-2.3 anonymous downgrade |
| `Then transfer fee = $Xk` | `Then transfer_fee = TBD (owner: <name>)` | Placeholder requires named owner |
| `When 5 business days have elapsed` | `When 5 business days have elapsed` | Concrete already — keep verbatim |

If a value cannot be resolved concretely, **convert AC to Open Question** (AP-4.2) rather than ship vague AC.

## Mandatory Scenario Types Per Story

Per C29 — every story must carry at minimum:

| Type | Required when | Source |
|---|---|---|
| `happy` | Always — primary success criterion | C29 |
| `error` / `edge_case` | Always — what happens if X fails / loops / escalates / times out / hits rate limit | C29 |
| `banking_grade_*` | Auto-emit per banking-grade row that says `applies` | C18, C29 |

Banking-grade scenario types: `banking_grade_idempotency`, `banking_grade_audit`, `banking_grade_tipping_off`, `banking_grade_reversibility`, `banking_grade_notification`.

## Banking-Grade Scenario Templates

### 6.1 Idempotency Replay (auto-emit on state-change / notification)

```gherkin
Scenario: Idempotency replay produces no duplicate effect
  Given a previous request with idempotency_key = "ik-001" was processed
  And the resulting state is <state_after_first_call>
  When the same request with idempotency_key = "ik-001" is replayed
  Then no duplicate side effect occurs
  And no duplicate audit event is emitted
  And the response returns the original result
```

Tag: `scenario_type: banking_grade_idempotency`. Required when `banking_grade.idempotency.status: applies` (AP-4.3).

### 6.2 Audit Emission (auto-emit on state change)

```gherkin
Scenario: State change emits audit event with required payload
  Given <actor> is authenticated as <role>
  And <entity> is in state <before_state>
  When <action> is performed
  Then <entity> transitions to state <after_state>
  And an audit event is emitted with payload:
    | field      | value                         |
    | event      | <event_name>                  |
    | actor      | <actor_id>                    |
    | ts         | <ISO-8601 timestamp>          |
    | before     | <before_state>                |
    | after      | <after_state>                 |
    | reason     | <human-readable reason>       |
    | idem_key   | <idempotency_key>             |
```

Tag: `scenario_type: banking_grade_audit`. Required payload schema is C18 field 2. Required when `banking_grade.audit_events.status: applies`.

### 6.3 Tipping-Off-Safe Rejection (auto-emit on customer-facing comm change)

```gherkin
Scenario: Customer notification uses non-tipping-off phrasing
  Given a wire transfer is rejected for <internal_reason>
  And <internal_reason> ∈ {sanctions_match, SAR_filed, PEP_review, adverse_media_hit}
  When the customer is notified of the rejection
  Then the message uses the standard non-tipping phrase from
    references/non-tipping-vocabulary.md
  And the message does NOT contain any of:
    "sanctions", "AML", "flagged", "suspicious activity",
    "regulated", "SAR", "PEP", "adverse media", "EDD",
    "compliance hold", "fraud review"
  And legal_signoff_required: true is recorded in audit
```

Tag: `scenario_type: banking_grade_tipping_off`. **Forbidden-terms inset** (do not omit): `sanctions / AML / flagged / suspicious / regulated / SAR / PEP / adverse media / EDD / compliance hold / fraud review`. Required when `banking_grade.tipping_off.status: applies` (AP-4.4, FM-06). See `references/non-tipping-vocabulary.md` for approved replacements.

### 6.4 Authorization Boundary (auto-emit on multi-actor stories)

```gherkin
Scenario: Action requires authorized role
  Given <actor> is authenticated
  And <actor>.role NOT IN <allowed_roles_for_action>
  When <actor> attempts <action>
  Then the request is rejected with HTTP 403 (or domain equivalent)
  And no state transition occurs
  And an authz_denied audit event is emitted with:
    | field    | value                |
    | actor    | <actor_id>           |
    | role     | <actor.role>         |
    | attempted| <action>             |
    | required | <allowed_roles>      |
```

Tag: `scenario_type: banking_grade_authz`. Hooks role-matrix from C18 field 5. Required when story has multiple actors with different access scopes.

## Anti-Patterns in Gherkin

| AP | Detection | Rewrite |
|---|---|---|
| AP-8.1 — Vague `Given` | `Given the system / a user / the application` without state | `Given <role> with <state> and <input>` |
| AP-8.2 — Multi-action `When` | `\b(and\|&)\b` joining two verb phrases in `When` | Split into two scenarios with different `Given` setups |
| AP-8.3 — Non-observable `Then` | `is happy`, `is satisfied`, `handles correctly`, `is improved`, `is compliant`, `is fast` | Replace with state change / payload field / audit event / UI element |
| AP-7.2 — Merged happy+error | Single scenario contains `Then user sees success` AND `Then user sees error if X` | Split into one happy scenario + one error scenario |

## Testability Self-Check

Ask after each AC: **"Can a tester write an automated test from this scenario without asking questions?"**

- YES → keep AC.
- NO → rewrite per concrete-value enforcement (§4); if no measurable predicate exists, convert to Open Question (AP-4.2).

Linguistic-quality composite < 5.0 across the brief → refuse handoff (FM-01).

## Cross-References

- `invest-checklist.md` §3.6 (T-letter interlocks with banking-grade scenarios)
- `anti-patterns.md` §8 (AP-8.1 / 8.2 / 8.3 / 8.4)
- `ambiguity-patterns.md` §3 (modal / vague rewrites for AC concrete-value)
- `non-tipping-vocabulary.md` (§6.3 forbidden terms and approved replacements)
- `ba-best-practices.md` §2 (Gherkin format authority)
