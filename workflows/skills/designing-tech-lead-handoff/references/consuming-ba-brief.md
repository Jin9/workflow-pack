# Consuming the BA brief (step 1)

The input is the `elaborating-user-stories` output (shapes inlined in
`schemas/input.json`). Map it as follows.

## Gate first

- `output_type` must be `brief`. `blocked_partial_brief` / any failure shape →
  emit `blocked_design` (`BLOCK-BA-NOT-READY`).
- Any `governance_gaps[]` with `blocks_tl_handoff: true` → `blocked_design`
  (`BLOCK-P1-GOVERNANCE`). Do not architect past a P1 governance gap.
- Missing `tokens_path` or `route_map_path` → `blocked_design`
  (`BLOCK-UX-CONTRACT`).

## Field → design mapping

- **`epic` / `epics`+`initiative`** → bounded contexts. One context per epic
  **workstream** (user-value axis), never a tech-layer split. `epic.scope.in`
  scopes the context; `scope.out_explicit` / `out_deferred` are explicit
  non-goals — do not design for them.
- **`epic.success_criteria[]`** → NFR targets that feed the observability spec
  and L4 §14. `metric/baseline/target/measurement_method` are concrete; do not
  invent thresholds the brief did not state — emit an `OQ-*` instead.
- **`stories[]`** → one L4 spec each. `story.card` + the verbatim
  happy-path Gherkin from `acceptance_criteria[]` go into L4 §1.
  `story.dependencies.depends_on/blocks` order the L4 fan-out.
- **`story.banking_grade_concerns`** (7 rows) → every row with
  `status: applies` is binding: `idempotency.applies` → L3 §6.5 idempotency
  anchor + L4 §11 + a `banking_grade_idempotency` consideration;
  `audit_events.applies` → observability audit taxonomy + L4 §15;
  `reversibility.applies` → a compensation carve-out (failure≠rollback);
  `authn_authz.applies` → L4 §12; `regulatory.applies` → L4 §15 + an ADR if it
  forces a design trade-off; `pii_fields.applies` → data-model + observability
  redaction list; `tipping_off.applies` → keep customer-facing copy clean.
- **`governance_gaps[]`** (non-blocking, severity P2) → each becomes either a
  candidate ADR (when it drove a design trade-off) or an `open_questions[]`
  entry naming the resolver.
- **`epic.legal_status` / stakeholders with `status: absent` +
  `engagement_required_for`** → surface as `open_questions[]`; do not silently
  assume sign-off.

## Discipline

When a decision the brief leaves open is genuinely undecidable from the brief
(idempotency-key derivation, lock-order pin, retry tuning), make it a **TL
decision with an ADR** — or, if it cannot be decided at design time, a P1/P2
`open_questions[]` entry. Never fabricate a value silently.
