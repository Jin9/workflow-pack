# Contract field map — what the renderer highlights

The renderer is **generic** (any JSON renders as a collapsible tree) but **contract-aware**: it color-codes
the recurring semantic fields the pipeline contracts share. This table is the source of the classifier in
`scripts/render_contract_viewer.py` (`scalar()` and the `Set`s near the top). Extend both together.

| Field / key pattern | Where it appears | Value vocabulary | Render |
|---|---|---|---|
| `audit_id` (top-level only for the header chip), `idempotency_key`, `*_id`, `id` | every contract | UUID / stable id | monospace chip; the header `audit_id` chip is reserved for top-level `data.audit_id` — a `processing_metadata.audit_id` renders at its own path only |
| `*_path`, `*_file`, `path`, `file`, `*_ref`, `slug` | ux/tl outputs, INDEX | relative path text | monospace chip (inert text, not a link) |
| `output_type` | ux/tl outputs | `ux_pack`/`design`/`brief` → ok · `partial_*`/`blocked_partial_brief` → warn · `blocked_*`/`failure_shape` → err | status badge |
| `verdict` | reviews & gates | `PROCEED`/`pass`/`approve`/`promote` → ok · `REVISE`/`conditional`/`hold`/`loop_back`/`human-queue`/`pass-with-caveats`/`reroute` → warn · `BLOCK`/`FAIL`/`ERROR`/`rollback`/`hard-fail` → err (case-insensitive) | status badge |
| `recommendation` | discovery | `proceed` → ok · `needs-work` → warn · `do-not-build` → err; badged ONLY when the value is a recognized decision enum — nested remediation prose renders as ordinary text | status badge / text |
| `status`, `state`, `spec_status` | most | `ready-for-tl`/`ready-for-implementation`/`accepted`/`resolved`/`pass`/`handed_off`/`revoked` → ok · `draft`/`proposed`/`pending`/`partial` → warn · `blocked`/`fail`/`rejected`/`deprecated` → err | status badge |
| `legal_status`, `citation_status`, `coverage_score` | brief/tl | `present`/`resolved`/`complete` → ok · `partial`/`pending` → warn | status badge |
| `severity` | findings / gaps / OQs | `P1`/`high` → high · `P2`/`medium` → med · `P3`/`low` → low | colored dot + label |
| `priority` | stories | `Must` · `Should` · `Could` · `Won't` (MoSCoW) | priority tag (red/amber/slate/faint) |
| `tier`, `inferred_tier`, `workload_tier`, `tier_default`, `tier_signal`, `tier_hint` | most | `T1` / `T2` / `T3` | tier badge (indigo/blue/teal) |
| `maturity_level`, `confidence` | ux / discovery / review | `0..3` / `low|medium|high` / `0..1` | info badge |
| booleans | `count_check`, checklists | `true` → ok · `false` → err | ok/err badge |

## Array sections the viewer expects to see (rendered as collapsible groups)

`findings[]`, `p1_findings[]`, `p2_findings[]` (each with `severity`, `code`, `claim`/`description`,
`recommendation`), `governance_gaps[]`, `open_questions[]` (with `severity`, `question`, `why_matters`),
`epics[]` / `story_files[]` (INDEX), `components[]` / `contracts[]` / `adrs[]` / `l4_specs[]` (tl-design),
`assumptions[]` / `opportunities[]` / `regulatory_regimes[]` (discovery), `bias_checks[]` (plan-review),
`processing_metadata` (skill name/version, tier, ids — provenance).

## Detected "kind" (header label)

`detectKind()` resolves, in order: `output_type` → `verdict` (plan-review) → `recommendation`
(discovery) → `epics` + `story_files` (ba-brief INDEX) → `$schema` + (`properties`|`$defs`) (JSON Schema)
→ `stage` → `JSON`. Add new artifact shapes here.

## Adding a new field

1. Add the key (or key-pattern) to the relevant `Set`/regex in `scalar()`.
2. If it needs a new color, add a CSS class in `CSS` and a row above.
3. Re-run the smoke test on a real artifact carrying the field; confirm offline-clean + determinism.
