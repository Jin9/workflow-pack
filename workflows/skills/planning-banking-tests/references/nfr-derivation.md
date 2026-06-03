# NFR Derivation Rules

> Reference for `planning-banking-tests` v1.0.0. Loaded by **SKILL.md Step 6** on every run.

## 1. Purpose

This document defines the deterministic rules by which the skill derives non-functional requirement (NFR) tests from the BA brief. Inputs are:

- `epics[].success_criteria[]` — explicit measurable targets.
- `processing_metadata.hidden_requirements_sweep` — Frame 1 (Scale), Frame 4 (Regulatory), Frame 6 (Failure) and adjacent frames.
- `pii_inventory[]` — drives security NFR coverage.
- `epics[].tier_signals[]` and `stories[].acceptance_criteria[]` — drive accessibility and reliability coverage.

The output is `nfr_tests[]` in the canonical `output.json`. The derivation rules are deterministic: identical BA input ⟹ identical `nfr_tests[]` membership and ordering. Targets that depend on unresolved Open Questions are emitted as `TBD pending OQ-N` — never as a guessed default (AP-Q9).

## 2. NFR categories

The `nfr_type` enum in the output schema:

| nfr_type | Concern domain |
|---|---|
| `performance` | End-to-end response time under stated load. |
| `latency` | Single-hop or per-call timing budget. |
| `throughput` | Sustained requests-per-second or transactions-per-second. |
| `scalability` | Behaviour as load grows (horizontal, vertical, peak). |
| `availability` | Uptime / SLO target over a window. |
| `reliability` | Mean time between failures, error budget. |
| `resilience` | Recovery from named failure modes. |
| `security` | Authz, authn, confidentiality, integrity. |
| `accessibility` | WCAG conformance, assistive-technology compatibility. |
| `observability` | Log, metric, trace, audit coverage. |
| `data-integrity` | Idempotency, exactly-once, consistency. |

## 3. Per-category derivation rules

### 3.1 Performance / latency / throughput

**Source**: `epics[].success_criteria[]` where the `metric` field matches the regex `(p50|p95|p99|latency|response[_-]?time|rps|tps|throughput)` (case-insensitive).

**Rule**: For each matching success criterion, emit one `nfr_tests[]` entry per percentile and per load profile (steady, peak, soak).

**ID pattern**: `NFR-{epic_id}-perf-{seq:03d}` (e.g. `NFR-EPIC-CART-CHECKOUT-2-perf-001`).

**Target field**: copy the `metric` and `target` verbatim from the BA success criterion. If the BA names a load profile, copy it; otherwise default to `steady` and emit a `coverage_gap` of severity P2 with `gap_type: load_profile_unstated`.

**Story linkage**: link to every story in the epic whose `acceptance_criteria.then` surface implies the timing claim (typically all customer-facing stories in the epic).

### 3.2 Scalability

**Source**: `processing_metadata.hidden_requirements_sweep.frame_1` (Scale findings) plus any `epics[].tier_signals[]` containing the substrings `peak`, `concurrent`, `flash-sale`, or `seasonal`.

**Rule**: Emit one `nfr_tests[]` entry per identified scale dimension (concurrent users, requests per second at peak, write fan-out).

**ID pattern**: `NFR-{epic_id}-scale-{seq:03d}`.

**Target field**: from the Frame 1 finding. Where Frame 1 surfaces a capacity question without a numeric answer, emit `target: "TBD pending OQ-{id}"` and populate `blocking_oqs[]` with the OQ id.

### 3.3 Security

**Source**: every entry in `pii_inventory[]` plus every Frame 4 (Regulatory) finding in `processing_metadata.hidden_requirements_sweep`.

**Rule**: For each `pii_inventory[i]`, emit two security NFR tests:

- One authorization test: verify that only the documented principals (per `pii_inventory[i].treatment` plus the access matrix derived from BA section 5.x) can read the field on each named surface.
- One access-audit test: verify that every read by an admin or system principal produces an audit-log record matching `pii_inventory[i].access_audit`.

For `password` (always-masked, blocked-for-admins on the holdout) and `session_token` (regulatory, never-echoed), the access-audit test asserts **absence** of the value in audit payloads — never presence.

**ID pattern**: `NFR-{epic_id}-sec-{seq:03d}` where `{epic_id}` is the epic that owns the surface under test (typically IDENTITY or GOVERNANCE-OBS).

**Story linkage**: link to every story that introduces a surface reading or writing the PII field.

Frame 4 findings emit one `NFR-{epic_id}-sec-{seq:03d}` per finding, with `target` carrying the regulatory citation reference. Cross-link to `compliance_tests[]` via `related_compliance_test_ids[]`.

### 3.4 Accessibility

**Source predicate**: emit accessibility NFR tests when **either** holds:

- `epics[i].tier_signals[]` contains `customer-facing`, OR
- any `stories[i].acceptance_criteria[].when` references a customer-surface verb (`sees`, `clicks`, `taps`, `enters`, `views`, `reads`).

**Rule**: Emit one accessibility test per customer-facing surface in the epic. Target framework: **WCAG 2.1 AA**. Where the BA names a stricter target (e.g. AAA for a specific surface), use the BA value.

**ID pattern**: `NFR-{epic_id}-a11y-{seq:03d}`.

**Coverage shape per surface**: perceivable (alt text, contrast, captions), operable (keyboard nav, focus order, timing), understandable (label clarity, error identification), robust (assistive-tech compatibility). Emit at least one test per WCAG principle per surface.

**Bilingual surfaces**: when `04-glossary.md` carries Thai/English pairs for a surface, emit a paired-language accessibility test (screen-reader pronunciation in both locales).

### 3.5 Reliability / resilience / availability

**Source**: `processing_metadata.hidden_requirements_sweep.frame_6` (Failure findings) plus every `banking_grade_applies[]` row whose `concern` is `reversibility`, `idempotency`, or `durability`.

**Rule**:

- Per Frame 6 failure mode: emit one resilience test verifying recovery behaviour (target: documented RTO/RPO; render as `TBD pending OQ-{id}` if missing).
- Per `reversibility` row: emit one reliability test verifying the reverse operation is exact and audit-logged.
- Per epic with availability targets in `success_criteria[]`: emit one availability test asserting the SLO measurement is reachable from the observability stack.

**ID patterns**: `NFR-{epic_id}-resil-{seq:03d}`, `NFR-{epic_id}-rel-{seq:03d}`, `NFR-{epic_id}-avail-{seq:03d}`.

### 3.6 Observability and data-integrity

**Observability**: derive from BA section references to audit logs, metrics, or traces. Emit one test per named telemetry surface verifying schema, retention, and queryability. ID pattern `NFR-{epic_id}-obs-{seq:03d}`.

**Data-integrity**: derive from `banking_grade_applies[]` rows with `concern: idempotency`. Emit one test per row asserting the idempotency key honours replay and produces identical observable state. ID pattern `NFR-{epic_id}-integ-{seq:03d}`.

## 4. Target unresolved handling

When a derived target depends on an unresolved Open Question:

1. Set `target: "TBD pending OQ-{id}"` exactly. Do not substitute an industry default. Do not back-compute from observed system behaviour.
2. Append the OQ id to `nfr_tests[i].blocking_oqs[]`.
3. Set `nfr_tests[i].status: draft-blocked`.
4. Add a P1 entry to `qa_readiness_checklist[]`: "OQ-{id} resolved by {promisor} before {due_date}".

This mirrors AP-Q9 (no invented thresholds). The holdout's 51 Open Questions drive a substantial fraction of NFR tests into `draft-blocked` until BA returns refined answers.

## 5. Tier-specific NFR coverage

The skill scales NFR coverage with `tier_default` from the BA brief (with `tier_hint` override permitted via input):

| Tier | Performance | Security | Accessibility | Reliability | Observability |
|---|---|---|---|---|---|
| **T1** (banking-grade, hard) | Full: p50/p95/p99 across steady/peak/soak per epic | Full: authz + access-audit per PII field; pen-test alignment | Full: WCAG 2.1 AA across every customer surface | Full: every Frame 6 failure mode + every reversibility row | Full: every named telemetry surface |
| **T2** (standard, holdout) | p95 across steady/peak per epic | Authz + access-audit per PII field | WCAG 2.1 AA across every customer surface | Frame 6 failure modes + reversibility rows | Audit-log surfaces only |
| **T3** (lightweight) | p95 steady only, top epic only | Authz only on direct-PII fields | Smoke a11y (axe-core scan) on top customer surface | Frame 6 happy-path recovery only | Skipped |

The skill writes the applied policy into `processing_metadata.nfr_policy_applied` for audit.

## 6. References

- `tier-aware-test-policy.md` — full tier policy across all coverage dimensions.
- `compliance-test-patterns.md` — security NFR cross-links into `compliance_tests[]`.
- `test-data-design.md` — synthetic data for NFR fixtures (load generation, security probes, a11y screen-reader corpora).
- `anti-patterns.md` — AP-Q9 (invented thresholds) and AP-Q10 (missing OQ linkage).
- Holdout source: `qa-holdout/e-commerce-v5/output-e5f8b9c2/output.json` (`processing_metadata.hidden_requirements_sweep`, `pii_inventory`, `epics[].success_criteria[]`).
