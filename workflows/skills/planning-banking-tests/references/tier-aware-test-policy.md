# Tier-Aware Test Policy (v1.0)

## Purpose

This reference defines the T1/T2/T3 differential gates applied by the
skill at three steps of the SKILL.md procedure: Step 3 (tier
resolution and mandatory-test-type expansion), Step 11 (sign-off
threshold computation), and Step 12 (final readiness check). The
policy is tier-aware because the banking-grade pipeline accommodates
three tiers via property gating rather than three pipelines; the same
skill emits stricter or looser plans according to the resolved tier.
The policy is grounded in the tier-properties table in
`DELIVERY_WORKFLOW_PLAN.md`, and the per-tier ratio targets are
cross-linked to `pyramid-allocation-rules.md`.

## Tier definitions

The three tiers are the standard kit-wide tiers. Brief definitions:

- **T1** — Banking and regulated workloads. Lending, payments,
  KYC, regulator-facing reporting. Full banking-grade properties
  apply: mandatory auditability, mandatory idempotency, strict
  determinism, mandatory graceful degradation, mandatory
  compensating reversibility.
- **T2** — Production workloads outside the banking-grade regulated
  boundary. Customer-facing SaaS, internal production systems with
  meaningful downside on failure. Mandatory auditability, mandatory
  idempotency, standard determinism, mandatory graceful
  degradation, compensating reversibility where applicable. The
  e-commerce-v5 holdout is T2.
- **T3** — Research, internal, or low-stakes workloads.
  Experimentation, prototypes, internal dashboards. Light
  auditability, recommended idempotency, flexible determinism,
  best-effort degradation, soft revert acceptable.

The tier is resolved at Step 3 of SKILL.md from the BA brief's
`processing_metadata.workload_tier`, with the optional
`tier_hint` input overriding under the rules in the override section
below. The resolved tier is recorded in
`processing_metadata.resolved_tier`.

## Per-tier mandatory test types

The mandatory-test-types table dictates which categories of test
case must appear in the plan, conditional on the brief actually
carrying inputs that would produce such tests. Mandatory means: if
the brief carries the input, the plan must emit the test; absence
of the test when the input is present fails Step 12.

| Mandatory category                  | T1                                          | T2                                          | T3                                           |
|-------------------------------------|---------------------------------------------|---------------------------------------------|----------------------------------------------|
| `banking_grade_audit`               | Every applicable scenario                   | Every applicable scenario                   | Every applicable scenario (rare on T3)       |
| `banking_grade_idempotency`         | Every applicable scenario                   | Every applicable scenario                   | Where applicable                              |
| `banking_grade_authz`               | Every applicable scenario                   | Every applicable scenario                   | Where applicable                              |
| `banking_grade_reversibility`       | Every applicable scenario                   | Every applicable scenario                   | Where applicable                              |
| `compliance_tests` per regulator    | Every regulator in `regulatory_dependencies` | Every regulator in `regulatory_dependencies` | Smoke-level only when applicable              |
| `security_authz` non-banking-grade  | Full coverage                                | Full coverage                                | Critical paths only                            |
| `nfr_performance`                   | Full perf suite (p50, p95, p99, soak)        | p95 + spike                                  | None (no perf gate)                            |
| `nfr_accessibility`                 | Full WCAG AA suite on customer surfaces      | Critical-path WCAG AA on customer surfaces   | None                                            |
| `smoke_subset`                      | Required                                     | Required                                     | Required                                        |
| `critical_path_e2e`                 | Required                                     | Required                                     | Required                                        |

The four banking-grade categories are validated against the
e-commerce-v5 holdout (16 stories, T2). Every banking-grade flag
that fires in the holdout produces a corresponding test case in the
emitted plan.

## Per-tier environment policy

The environment policy governs which environment a test case
references via `test_cases[].environment_ref` and what the
acceptable environment classes are per tier:

- **T1** — Per-PR ephemeral environment is mandatory for
  integration, e2e, and contract tests. Shared staging is forbidden
  for any test that asserts banking-grade behavior. The kit's
  environment spec must include a `per_pr_ephemeral` entry; if it
  does not, Step 3 emits a `tier_environment_gap` blocking the run.
- **T2** — Hybrid is permitted. Per-PR ephemeral is preferred and
  required for banking-grade and compliance tests; shared staging
  is acceptable for non-banking-grade integration and for e2e
  acceptance flows. Contract tests against external providers may
  run against a shared sandbox tenant.
- **T3** — Shared staging is acceptable for all test classes.
  Per-PR ephemeral is recommended for tests touching shared data
  but not required. No environment-class gap blocks a T3 run.

## Per-tier sign-off thresholds

Sign-off thresholds are evaluated at SKILL.md Step 11 and the
output is emitted in `signoff_criteria`. A plan whose computed
thresholds disagree with the tier defaults below is permitted only
if `signoff_criteria.override_reason` is populated and an approver
identifier is recorded.

- **T1 sign-off (strict)**.
  - 100% pass on every `banking_grade_*` test and every
    `compliance_tests` test.
  - Zero P0 defects open.
  - Zero P1 defects open.
  - Performance: p99 SLO met across the full perf suite.
  - Accessibility: zero WCAG AA violations on customer surfaces.
  - No conditional-go path: failing any threshold is a hard block.
- **T2 sign-off (standard)**.
  - 100% pass on every `banking_grade_*` test and every
    `compliance_tests` test.
  - Zero P0 defects open.
  - Conditional-go is acceptable with one documented exception per
    open P1 defect, signed off by the named approver.
  - Performance: p95 SLO met; p99 is a soft target.
  - Accessibility: critical-path WCAG AA met; remaining issues
    recorded as gaps with severity.
- **T3 sign-off (lenient)**.
  - Smoke subset passes.
  - Critical-path e2e passes.
  - No performance gate.
  - No accessibility gate.
  - P1 and lower defects logged but non-blocking.

The sign-off thresholds are emitted as machine-readable predicates
in `signoff_criteria.predicates[]` so that a downstream stage (Stage
5 QA execution, Stage 6 deploy) can mechanically check them without
re-parsing prose.

## Multi-epic tier heterogeneity

A single BA brief may carry multiple epics with different
`workload_tier` values. The skill preserves per-epic tier without
collapsing to a single workload-wide tier. Specifically:

1. The brief's top-level `processing_metadata.workload_tier` sets
   the default tier inherited by epics that do not declare their
   own tier.
2. An epic's `epics[].workload_tier`, when present, overrides the
   workload-wide default for that epic and all of its stories.
3. A story's `stories[].workload_tier`, when present, overrides
   the epic-level tier for that story alone.
4. The per-test policies above (mandatory test types, environment,
   sign-off thresholds) are applied at the resolved tier for each
   test case's parent story, never at the workload-wide tier.
5. The plan-level `signoff_criteria` block emits per-tier
   thresholds in `signoff_criteria.per_tier[]`, one block per
   distinct tier appearing among the resolved per-story tiers.

Collapsing per-epic tier to a single workload-wide tier is
**AP-Q3** and is rejected at validation. The e-commerce-v5
holdout is uniformly T2 across all five epics, but the schema
supports heterogeneity and the renderer must respect it.

## Tier override via `tier_hint`

The skill accepts an optional `tier_hint` input field for cases
where the brief's resolved tier is wrong or stale. The override
rules are asymmetric:

- A **stricter** hint than the brief's resolved tier (e.g., brief
  resolved to T2, hint is T1) is accepted silently. The resolved
  tier becomes the hint value, and the plan is emitted at the
  stricter policy. The override is recorded in
  `processing_metadata.tier_override` with the prior value, the
  hint value, and the reason `stricter_silent_accept`.
- A **looser** hint than the brief's resolved tier (e.g., brief
  resolved to T1, hint is T2) is accepted but emits a
  `tier_downgrade_warning` in `processing_metadata.warnings[]`.
  The warning carries the prior tier, the hint tier, and a
  request for explicit reviewer acknowledgment before the plan
  may be consumed by downstream stages. Downstream stages must
  refuse the plan until the warning is acknowledged.
- A hint **equal** to the resolved tier is a no-op and is not
  recorded.

The asymmetry reflects the banking-grade principle that adding
rigor is safe but removing rigor requires informed consent.

## References

- Per-tier pyramid ratio targets and the rationale for their
  differences are defined in `pyramid-allocation-rules.md`. This
  document references those targets but does not duplicate the
  ratio table. The mandatory-test-types table here and the ratio
  table there are designed to be jointly satisfiable: a plan
  emitted at T1 with all banking-grade tests at integration level
  naturally lands near the 40/40/5/15 split, and the SKILL.md
  tests assert that joint satisfiability holds.
- Scenario-type to test-type mapping is in
  `scenario-type-mapping.md`. The mandatory-test-types table
  above is expressed in test-type terms; the mapping converts
  scenario types in the brief into the test types referenced here.
- Anti-patterns AP-Q3 (tier collapse) and the related family are
  enumerated in `anti-patterns.md`.
