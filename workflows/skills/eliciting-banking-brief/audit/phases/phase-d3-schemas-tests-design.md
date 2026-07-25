# Phase D3 — Schemas + Test Cases Design (`ba-elicit-from-raw`)

> **Role**: Schemas + Test Cases Designer, BA Skill Factory
> **Mission**: Design the JSON schemas (input/output) and test-case + assertion specification that E1 will implement. This document is the contract — E1 translates it into real JSON Schema files, fixture inputs, and assertion files.
> **Inputs**: phase-d1 (SKILL.md design), phase-c1 (30 patterns), phase-c2 (26 anti-patterns), phase-c3 (18 edge cases + 13 failure modes), `epic-and-stories.template.md`, `references/ba-best-practices.md`, three pilot raw inputs + one hold-out.
> **Audience**: E1 implementers; R6/test reviewers.

---

## 0. Design Orientation

Three-layer contract:

1. **Input** — minimal surface; only `raw_content` + `idempotency_key` required. Other fields are optional hints.
2. **Output** — JSON form of `epic-and-stories.template.md` plus governance extensions (governance_gaps, processing_metadata, failure_state).
3. **Failure** — when brief cannot be produced safely (FM-01/02/05/06/11/12/13), output replaces brief with `failure_state` preserving audit envelope.

Schema-shape drivers (phase-c1, phase-d1):

- **Per-epic tier** (C19) — `epics[]` array supports heterogeneous tiers (003).
- **Banking-grade force-fill** (C18 + FM-11) — 7 mandatory rows × non-null `status` × ≥10-char `justification`.
- **Surface, don't repair** (C2 §9.5) — ambiguities in `open_questions[]`; P1 OQ blocks `status: ready-for-tl`.

Highest-leverage rule (C14, AP-5.1): **Legal-absent + regulatory = P1 governance gap** — enforced via `governance_gaps[]` + `blocks_tl_handoff`.

---

## Part 1 — Input Schema Design (`schemas/input.json`)

### 1.1 Goals

- Minimal required surface; rich optional surface for harness control.
- Strict `additionalProperties: false` — unknown keys are configuration drift, refused.
- Validation that fails fast (length + enum + UUID format).
- Allow downstream tier override but never silent under-strict (matches AP-1.3: skill always re-infers tier from content).

### 1.2 Field-by-field rationale

| Field | Req? | Type | Constraints | Rationale (source) |
|---|---|---|---|---|
| `raw_content` | yes | string | minLen 200; maxLen 200000 | C1 needs body; FM-01 < 5.0 likely under 200; maxLen guards EC-04 token budget. |
| `source_type` | opt | enum | jira/slack/email/meeting-notes/doc/mixed/unknown | C1 detects if absent; `mixed` for forwards; `unknown` forces detection. |
| `idempotency_key` | yes | string | UUID v4 regex | Skill `idempotent: true` (phase-d1); same key + content → same output. |
| `tier_hint` | opt | enum | T1/T2/T3 | AP-1.3 guard — skill re-infers, emits `inferred > manual` if mismatched. |
| `domain_glossary_ref` | opt | path | maxLen 256 | C5 — supplementary; skill emits own glossary. |
| `project_context_ref` | opt | path | maxLen 256 | Optional project-context.md hint. |
| `ground_truth_strip_mode` | opt | enum | auto/force/skip (default auto) | EC-17/FM-12; `skip` only in `training` mode. |
| `audit_mode` | opt | enum | standard/enhanced/strict/training (default enhanced) | phase-d1 §1.1 `audit_level: enhanced` for T2; `strict` for T1; `training` enables `skip`. |
| `requested_at` | opt | RFC-3339 | — | C4 relative-date anchor. |

### 1.3 JSON Schema (draft-07) — design

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://ba-skill-factory/schemas/ba-elicit-from-raw/input.json",
  "title": "ba-elicit-from-raw input contract",
  "type": "object",
  "additionalProperties": false,
  "required": ["raw_content", "idempotency_key"],
  "properties": {
    "raw_content": {
      "type": "string",
      "minLength": 200,
      "maxLength": 200000,
      "description": "Raw text body — Jira / Slack / meeting / email / doc / mixed. Skill detects source_type if not provided."
    },
    "source_type": {
      "type": "string",
      "enum": ["jira", "slack", "email", "meeting-notes", "doc", "mixed", "unknown"],
      "description": "Optional hint — skill detects from markers if absent (C1)."
    },
    "idempotency_key": {
      "type": "string",
      "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
      "description": "UUID v4. Same key + same raw_content → same output (skill is idempotent)."
    },
    "tier_hint": {
      "type": "string",
      "enum": ["T1", "T2", "T3"],
      "description": "Optional. Skill re-infers tier from content (C19); emits inferred > manual flag if mismatched (AP-1.3)."
    },
    "domain_glossary_ref": {
      "type": "string",
      "maxLength": 256
    },
    "project_context_ref": {
      "type": "string",
      "maxLength": 256
    },
    "ground_truth_strip_mode": {
      "type": "string",
      "enum": ["auto", "force", "skip"],
      "default": "auto"
    },
    "audit_mode": {
      "type": "string",
      "enum": ["standard", "enhanced", "strict", "training"],
      "default": "enhanced"
    },
    "requested_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "allOf": [
    {
      "description": "Production safety: skip-strip requires training mode.",
      "if": {
        "properties": { "ground_truth_strip_mode": { "const": "skip" } },
        "required": ["ground_truth_strip_mode"]
      },
      "then": {
        "properties": { "audit_mode": { "const": "training" } },
        "required": ["audit_mode"]
      }
    }
  ]
}
```

### 1.4 Example input matching schema

```json
{
  "raw_content": "[LOAN-2847] Add document re-upload feature ... (≥ 200 chars production string)",
  "source_type": "jira",
  "idempotency_key": "550e8400-e29b-41d4-a716-446655440000",
  "tier_hint": "T2", "audit_mode": "enhanced", "requested_at": "2026-05-12T09:00:00Z"
}
```

---

## Part 2 — Output Schema Design (`schemas/output.json`)

### 2.1 Top-level shape

Envelope object, three shapes by `output_type`:

- `brief` — happy path; full content.
- `blocked_partial_brief` — P1 unresolved (FM-02/05/06); `frontmatter.status: "blocked"`, `governance_gaps` non-empty, `blocks_tl_handoff: true`.
- failure modes — `needs_clarification` (FM-01), `preprocessing_failure` (FM-12), `pii_echo_blocked` (FM-13), `schema_validation_failure` (FM-11), `meta_response` (EC-09). `failure_state` block describes refusal; `stories` absent.

Enforced via `oneOf` keyed by `output_type`.

### 2.2 Required top-level keys (brief case)

```text
{ output_type, blocks_tl_handoff: bool, frontmatter, scope_kind,
  initiative? (multi-epic), epic? (single), epics? (multi — mutex with epic),
  stories: [Story], open_questions: [OQ], assumptions_made, glossary,
  governance_gaps, ba_compliance_checklist, ba_reasoning_trace, processing_metadata,
  failure_state? (failure shapes only) }
```

### 2.3 Frontmatter sub-schema (mirrors template.md frontmatter)

| Field | Type / Constraint |
|---|---|
| `id` | string, pattern `^EPIC-[A-Z0-9-]+$` |
| `workload_tier` | enum T1/T2/T3 |
| `created_at` | RFC-3339 |
| `created_by` | string (e.g. `ba-elicit-from-raw@1.0.0`) |
| `source_ref` | string path |
| `source_type` | enum (mirrors input) |
| `idempotency_key` | UUID v4 (echoes input) |
| `ba_confidence` | enum high/medium/low/refused |
| `status` | enum draft/reviewed/ready-for-tl/blocked/locked |
| `upstream_refs` | `{ triage_id?, source_artifacts: [] }` |
| `downstream_will_be_consumed_by` | `{ stage, role }` |

**Constraint**: `status: ready-for-tl` ⟹ zero P1 open_questions AND zero `blocks_tl_handoff: true` governance_gaps. Enforced via `allOf / if-then` (§2.7 rule 1).

### 2.4 Epic sub-schema

| Field | Type / Constraint | Source |
|---|---|---|
| `title` | string, minLen 8, maxLen 120 (verb-noun) | template |
| `problem_statement` | string, minLen 80 | template |
| `why_now` | string, minLen 20 | template |
| `hypothesis` | string, optional | template |
| `success_criteria` | ≥1 of `{metric, baseline, target, measurement_method}` — all non-empty | template; quality heuristic |
| `scope` | `{in: [], out_explicit: [], out_deferred: []}` with in.length ≥ 1 | template + C11 |
| `stakeholders` | ≥2 of `{role, name, function, type, decision_authority, affected, authority_mode, attribution_confidence}` | C12-C17 |
| `legal_status` | enum present/scheduled/mentioned_only/absent — always emitted | C14, FM-05, AP-5.1 |
| `inferred_tier` | enum T1/T2/T3 — per epic | C19, B5 §6 |
| `tier_signals` | ≥1 of `{signal, weight, evidence_quote}` | phase-d1 §1.1 |

### 2.5 Story sub-schema (most complex — full detail)

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["id","title","format","card","context","acceptance_criteria","banking_grade_concerns","priority","sizing","dependencies","dor_checklist"],
  "properties": {
    "id": { "type": "string", "pattern": "^EPIC-[A-Z0-9-]+-\\d+$" },
    "title": { "type": "string", "minLength": 8, "maxLength": 120 },
    "format": { "type": "string", "enum": ["job_story", "classic_user_story"] },
    "card": {
      "oneOf": [
        { "type": "object", "additionalProperties": false,
          "required": ["when","i_want_to","so_i_can"],
          "properties": { "when":{"type":"string","minLength":8}, "i_want_to":{"type":"string","minLength":8}, "so_i_can":{"type":"string","minLength":8} } },
        { "type": "object", "additionalProperties": false,
          "required": ["as_a","i_want","so_that"],
          "properties": { "as_a":{"type":"string","minLength":3}, "i_want":{"type":"string","minLength":8}, "so_that":{"type":"string","minLength":8} } }
      ]
    },
    "context": { "type": "string", "minLength": 30 },
    "acceptance_criteria": {
      "type": "array", "minItems": 3,
      "items": {
        "type": "object", "additionalProperties": false,
        "required": ["scenario_name","scenario_type","given","when","then"],
        "properties": {
          "scenario_name": { "type": "string", "minLength": 8 },
          "scenario_type": { "type": "string", "enum": ["happy","error","banking_grade_audit","banking_grade_idempotency","banking_grade_tipping_off","banking_grade_reversibility","banking_grade_notification","edge_case"] },
          "given": { "type": "array", "minItems": 1, "items": { "type":"string", "minLength":8 } },
          "when": { "type": "string", "minLength": 8, "description": "Single action; multi-action forbidden (AP-8.2)." },
          "then": { "type": "array", "minItems": 1, "items": { "type":"string", "minLength":8 } },
          "tags": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "banking_grade_concerns": {
      "type": "object", "additionalProperties": false,
      "required": ["pii_fields","audit_events","idempotency","reversibility","authn_authz","regulatory","tipping_off"],
      "properties": {
        "pii_fields":   { "$ref": "#/definitions/BankingGradeRow" },
        "audit_events": { "$ref": "#/definitions/BankingGradeRow" },
        "idempotency":  { "$ref": "#/definitions/BankingGradeRow" },
        "reversibility":{ "$ref": "#/definitions/BankingGradeRow" },
        "authn_authz":  { "$ref": "#/definitions/BankingGradeRow" },
        "regulatory":   { "$ref": "#/definitions/BankingGradeRow" },
        "tipping_off":  { "$ref": "#/definitions/BankingGradeRow" }
      }
    },
    "priority": { "type": "string", "enum": ["Must","Should","Could","Won't"] },
    "sizing": {
      "type": "object", "additionalProperties": false,
      "required": ["story_points","complexity"],
      "properties": {
        "story_points": { "oneOf": [ {"type":"integer","enum":[1,2,3,5,8,13]}, {"type":"string","const":"TBD_by_TL"} ] },
        "complexity": { "type": "string", "enum": ["trivial","low","medium","high","unknown"] },
        "split_required": { "type": "boolean", "default": false }
      }
    },
    "dependencies": {
      "type": "object", "additionalProperties": false,
      "required": ["depends_on","blocks"],
      "properties": {
        "depends_on": { "type": "array", "items": { "type": "string" } },
        "blocks":     { "type": "array", "items": { "type": "string" } }
      }
    },
    "dor_checklist": {
      "type": "object", "additionalProperties": false,
      "required": ["format_clear","happy_path_present","error_path_present","banking_grade_evaluated","priority_set","dependencies_identified","sizing_done","no_blocking_ambiguities"],
      "properties": {
        "format_clear":{"type":"boolean"}, "happy_path_present":{"type":"boolean"}, "error_path_present":{"type":"boolean"},
        "banking_grade_evaluated":{"type":"boolean"}, "priority_set":{"type":"boolean"}, "dependencies_identified":{"type":"boolean"},
        "sizing_done":{"type":"boolean"}, "no_blocking_ambiguities":{"type":"boolean"}
      }
    }
  },
  "definitions": {
    "BankingGradeRow": {
      "type": "object", "additionalProperties": false,
      "required": ["status","justification"],
      "properties": {
        "status": { "type": "string", "enum": ["applies","not_applicable","unknown_p2"] },
        "justification": { "type": "string", "minLength": 10, "description": "Non-empty even when status=not_applicable (AP-4.1 disable-path)." },
        "fields_or_events": { "type": "array", "items": { "type": "string" } },
        "treatment": { "type": "string" },
        "compensating_action": { "type": "string" }
      }
    }
  }
}
```

**Key story-level invariants enforced by the schema** (with reference to assertions for the dynamic checks):

1. `acceptance_criteria` minItems = 3. Assertion `gherkin-quality.md` further requires 1+ happy, 1+ error, 1+ banking-grade scenario_type.
2. `banking_grade_concerns` has all 7 required keys. Each row has `status` ∈ enum and `justification.minLength: 10` — so an empty row (FM-11) is rejected.
3. `card` is a `oneOf` keyed by `format`; the schema accepts either job-story or classic-user-story shape.
4. `dependencies.depends_on / blocks` always present (even if empty array) — forces explicit declaration.

### 2.6 OQ / Assumptions / Glossary / Governance Gaps sub-schemas

```text
open_questions[]:    { id, severity ∈ {P1,P2,P3}, question (≥12), why_matters (≥20), suggested_resolver,
                       conflict_evidence?: [{speaker, quote, line_ref, authority_mode}], related_story_ids?: [] }
assumptions_made[]:  { assumption, why_made, related_story_ids?: [] }
glossary[]:          { term, canonical_form, surface_form: [], definition, source,
                       pii_sensitivity ∈ {direct,indirect,regulatory,none},
                       regulatory_tie: {regulator, citation_id, status} | null }
governance_gaps[]:   { type ∈ {legal_absent_on_regulatory, tipping_off_violation, pii_inventory_missing,
                                regulatory_citation_unresolved, dual_approval_named_owner_missing,
                                compensating_action_missing, retention_policy_unstated},
                       severity ∈ {P1,P2}, evidence: [], required_action, blocks_tl_handoff: bool }
```

### 2.7 Cross-cutting constraints (allOf rules)

1. **No P1 OQ when `ready-for-tl`**: `frontmatter.status = "ready-for-tl"` ⟹ no `open_questions[].severity = "P1"` AND no `governance_gaps[].blocks_tl_handoff = true`.
2. **Empty banking-grade row forbidden**: every banking-grade row `justification.minLength ≥ 10` (AP-4.1).
3. **Tier-shape consistency**: `scope_kind = multi-epic` ⇔ `epics[]` + `initiative` present, `epic` absent. Other `scope_kind` values ⇔ `epic` present, `epics` absent.
4. **Failure-state exclusivity**: failure `output_type` values ⟹ `failure_state` required AND `stories` absent or `partial_output_available: true`.
5. **Per-epic tier signals**: in multi-epic mode, each `epics[]` entry has own `inferred_tier` + `tier_signals` (B5 §6 decision 1).

### 2.8 Output skeleton example

```json
{
  "output_type": "brief",
  "blocks_tl_handoff": true,
  "frontmatter": {
    "id": "EPIC-LOAN-2847", "workload_tier": "T2",
    "created_at": "2026-05-12T09:01:14Z", "created_by": "ba-elicit-from-raw@1.0.0",
    "source_ref": "inputs/raw-request-001.md", "source_type": "jira",
    "idempotency_key": "550e8400-e29b-41d4-a716-446655440000",
    "ba_confidence": "medium", "status": "draft",
    "upstream_refs": { "source_artifacts": ["inputs/raw-request-001.md"] },
    "downstream_will_be_consumed_by": { "stage": "2-tl-design", "role": "tl-squad" }
  },
  "scope_kind": "single-epic",
  "epic": {
    "title": "Self-service document re-upload for loan applicants",
    "problem_statement": "...", "why_now": "Q3 campaign launch end-June",
    "success_criteria": [ { "metric": "Wrong-doc reupload tickets", "baseline": "142/week", "target": "≤20/week", "measurement_method": "Zendesk tag report" } ],
    "scope": { "in": ["..."], "out_explicit": ["..."], "out_deferred": ["..."] },
    "stakeholders": [ /* Sarah Lim, Priya, Raj, ... */ ],
    "legal_status": "absent", "inferred_tier": "T2",
    "tier_signals": [ { "signal": "compliance officer + retention rule", "weight": "T1-shadow", "evidence_quote": "Priya — archived not deleted (001:77)" } ]
  },
  "stories": [ /* per §2.5 */ ],
  "open_questions": [
    { "id": "OQ-1", "severity": "P1", "question": "Retention on replaced PII (delete vs archive 7y)?", "why_matters": "Compliance vs AC conflict (001:54 vs 001:77)", "suggested_resolver": "Priya Naidoo" }
  ],
  "governance_gaps": [
    { "type": "legal_absent_on_regulatory", "severity": "P1", "evidence": ["No Legal; PII+retention scope"], "required_action": "Schedule Legal review", "blocks_tl_handoff": true }
  ],
  "assumptions_made": [], "glossary": [],
  "ba_compliance_checklist": { /* 10 booleans */ },
  "ba_reasoning_trace": {
    "why_epic_boundary": "...", "why_story_decomposition": "...",
    "best_practices_applied": ["INVEST","Gherkin","Job stories","MoSCoW"], "deviations": []
  },
  "processing_metadata": {
    "tier_decisions": [], "chunking": null,
    "ground_truth_stripped": { "found": true, "byte_range": [4521,7892], "strip_method": "marker_to_eof" },
    "parsing_mode": "structured", "language_inventory": [{ "script": "Latin", "frequency": "100%" }]
  }
}
```

---

## Part 3 — Test Cases Design (6 cases)

Each case lists: ID, input path, expected key fields (skeleton, not exhaustive), expected ambiguity / OQ count (rough), expected tier, expected failure mode (if any), and the assertions that must pass.

### Test 001 — Jira Lending Happy Path

- **Input**: `inputs/raw-request-001.md`
- **Coverage**: Jira parsing (C1, C2); multi-story split (C9, C25, C26); Legal-absence (C14, AP-5.1, FM-05); retention conflict (C24); replace-vs-archive (AP-2.1, EC-02).
- **Expected**: `output_type: brief`, `blocks_tl_handoff: true` (Legal absent on PII); tier T2 (T1-shadow on retention); `scope_kind: single-epic`; 3-5 stories (re-upload happy / retry-limit-escalation / archive-on-sensitive / audit-emission); 6-8 OQs (replace-vs-archive P1, N=3 anonymous P2, sensitive-doc retention P1, abandoned-app retention P2, EOW P3, urgent-label P3); 1-2 governance_gaps (legal_absent_on_regulatory, pii_inventory_missing); ground-truth block 137-181 stripped.
- **Critical assertions**: all three assertion files pass; `governance_gaps` non-empty; `frontmatter.status != ready-for-tl`.

### Test 002 — Slack Payments Conversational

- **Input**: `inputs/raw-request-002.md`
- **Coverage**: conversational Slack parsing (EC-12); tipping-off (C20, AP-4.4, FM-06); anonymous + pronoun resolution (C16, EC-14); ETA flattening (AP-3.1); emoji-as-signoff (B4 HCP-1).
- **Expected**: `output_type: blocked_partial_brief` (tipping-off P1 must mitigate; Legal mentioned 3× but 0 utterances); tier T2 borderline T1 (sanctions+SAR+tipping-off); `scope_kind: single-epic`; 4-6 stories (customer-facing status / agent-UI status / rejection messaging / state-machine / audit / notification policy); 8-12 OQs (internal-SLA flattening P2, mobile-vs-web P2, Legal sign-off P1, tipping-off forbidden terms P1, emoji-as-signoff P2); 2-3 governance_gaps (tipping_off_violation P1, legal_absent_on_regulatory P1, pii_inventory_missing P2).
- **Critical assertions**: `gherkin-quality.md` strict on G-7 tipping-off scenarios; `banking-grade-fields.md` tipping_off row = `applies` with mitigation; story-split agent-UI vs customer-UI per C28.

### Test 003 — Meeting KYC Multi-Epic

- **Input**: `inputs/raw-request-003.md`
- **Coverage**: meeting-notes parsing; multi-epic (C8, EC-10); per-epic tier (C19, B5 §6); tier escalation T2→T1 (AP-1.3); note-taker paraphrase (C16, EC-15, AP-5.3); regulator citation incomplete (C6, EC-18); Legal apologies (EC-16).
- **Expected**: `output_type: blocked_partial_brief`; tier T1-by-content (manual T2) — emit `inferred > manual` flag; `scope_kind: multi-epic` (5-6 epics: EDD redesign / biometric / risk-engine calibration / mobile follow-on / migration / status page); 12-18 stories total; 15-20 OQs (regulator citation P1, Acuant SLA P2, biometric Security review P1, tiered approval owner P2, abandoned-app retention P2, EOW P2, threshold values P2); 3-4 governance_gaps (legal_absent P1, citation_unresolved P1, dual_approval_owner P2, pii_inventory P2-elevated-T1); block 167-221 stripped.
- **Critical assertions**: all three files; `epics[]` array with ≥3 entries each with own `inferred_tier`; `ba_reasoning_trace.why_epic_boundary` populated per epic.

### Test 004 — Hold-out Email Card-Disputes

- **Input**: `inputs/raw-request-holdout.md`
- **Coverage**: email quoted-reply inversion (EC-13); VISA VCR 2026-07 deadline; Diana parental leave handoff to Felix (EC-16); Marcus's prioritization meta-Q (FM-09 scope unclear); attachment "explains everything" missing (EC-06).
- **Expected**: `output_type: brief` (handoff blocked) or `blocked_partial_brief`; tier T2 with T1-shadow on VISA VCR scope; `scope_kind: ambiguous → recommended multi-epic` (Marcus's question forces FM-09 P2 OQ); 6-10 stories (unified case view / packet auto-assembly / comm templates / SLA timer / VCR reason-code mapping / session-timeout); 10-14 OQs (Marcus single-most-valuable P2, Felix-as-cover P1, missing attachment P1, VISA VCR rules P1, card-admin owner P2, treasury reversal P2); 2-3 governance_gaps (legal_absent P1, citation_unresolved P1, pii_inventory P2); `stakeholder_availability` shows Diana 2026-06-01→2026-08-15 with cover Felix.
- **Critical assertions**: `processing_metadata.parsing_inversion_applied: true`; `quoted_replies_deduplicated > 0`; regulatory_deadline resolved to absolute `2026-07-01`; `inbound_handoff_metadata` populated.

### Test 005 — Minimal Input Failure (Synthetic)

- **Input**: `inputs/synthetic-minimal-001.md` (E1 creates: single Jira title + 1-line description, total < 200 chars). Example: `[KYC-9876] Update KYC form. Priority: high.`
- **Coverage**: FM-01 (quality below threshold) + EC-01 (minimal signal).
- **Expected**: `output_type: needs_clarification`; `failure_state: { mode: "FM-01", reason: "linguistic_quality_composite < 5.0", recommended_questions: [...], blocking_items: ["problem statement", "owner identity", "at least 1 constraint"] }`; no `stories`; `frontmatter.ba_confidence: refused`.
- **Critical assertions**: `failure_state.mode == "FM-01"`; no fabricated stories; harness routes input-schema-validation failure (`raw_content` < 200) to FM-01 path, not silent fabrication.

### Test 006 — Ground-Truth Leak (Synthetic; two sub-cases)

- **Input**: `inputs/synthetic-ground-truth-leak-001-clean.md` (006a) and `inputs/synthetic-ground-truth-leak-001-corrupted.md` (006b). E1 creates: a copy of r1's first 50 lines + an `## Intentional Issues for R6 to Catch` block. 006a has clean boundary; 006b has overlapping / multi-block / substring-survival corruption.
- **Coverage**: EC-17 (annotation block present) + FM-12 (strip-success vs strip-failure).
- **Expected 006a**: `output_type: brief`; `processing_metadata.ground_truth_stripped.{found: true, byte_range non-empty, strip_method: "marker_to_eof"}`. No annotation-block substring appears in any story/OQ/glossary.
- **Expected 006b**: `output_type: preprocessing_failure`; `failure_state.mode: "FM-12"`; `failure_state.reason` describes the triggered condition (multi-block / boundary-overlap / substring-survival); `do_not_proceed: true`; no `stories`.
- **Critical assertions**: 006a — no annotation substring in output; strip log present. 006b — refusal path; `partial_output_available: false`.

### Test-case summary table

| Case | Input | Output type | Tier | Scope kind | Stories ~N | P1 OQ | Governance gaps | Failure mode |
|---|---|---|---|---|---|---|---|---|
| 001 | r1 Jira Lending | brief (blocked) | T2 | single-epic | 3-5 | 2-3 | legal_absent, pii_inventory_missing | none |
| 002 | r2 Slack Payments | blocked_partial_brief | T2/T1-borderline | single-epic | 4-6 | 3-4 | tipping_off, legal_absent, pii_inventory_missing | none (mitigations required) |
| 003 | r3 Meeting KYC | blocked_partial_brief | T1 (per epic) | multi-epic | 12-18 | 4-6 | legal_absent, citation_unresolved, dual_approval_owner | none (governance) |
| 004 | hold-out Email Cards | brief or blocked | T2 (T1-shadow) | multi-epic or ambiguous | 6-10 | 3-5 | legal_absent, citation_unresolved | FM-09 if scope unresolved |
| 005 | synthetic minimal | needs_clarification | n/a | n/a | 0 | n/a | n/a | FM-01 |
| 006a | synthetic GT-strip-OK | brief | T2 | single-epic | 1-3 | 1-2 | legal_absent | none (strip clean) |
| 006b | synthetic GT-strip-FAIL | preprocessing_failure | n/a | n/a | 0 | n/a | n/a | FM-12 |

---

## Part 4 — Test Assertions Design (3 assertion files)

Assertions live in `tests/assertions/*.md`. Each file is a checklist E1 implements as a runner — pseudo-code per rule, evaluated against the JSON output. Severity: **must-pass** = test fails on miss; **should-pass** = warning logged but test passes (allows graceful degradation on edge cases).

### 4.1 `invest-compliance.md`

**Purpose**: every `stories[]` entry satisfies INVEST per `references/ba-best-practices.md` §1.

| # | Rule | Severity | Source |
|---|---|---|---|
| I-1 | **Independent**: each `depends_on[]` entry resolves to an in-brief story id OR is in `processing_metadata.external_dependencies`. | must-pass | INVEST §I; AP-7.1 |
| I-2 | **Negotiable**: no tech-layer prescription in `title`/`card` (`API`, `endpoint`, `DB schema`, `frontend component`). Spike stories whitelisted. | must-pass | INVEST §N; AP-7.1 |
| I-3 | **Valuable**: `card.so_i_can` (or `so_that`) length ≥ 12 AND contains a value-word (complete / verify / track / comply / resolve / ...). | must-pass | INVEST §V |
| I-4 | **Estimable**: `sizing.story_points` ∈ Fibonacci [1,2,3,5,8,13] OR `"TBD_by_TL"` (requires `split_required: true`). | must-pass | INVEST §E |
| I-5 | **Small**: `sizing.story_points ≤ 8` OR `sizing.split_required: true`. | must-pass | INVEST §S; AP-7.3 |
| I-6 | **Testable**: `acceptance_criteria.length ≥ 3` AND every AC well-formed (deeper check in `gherkin-quality.md`). | must-pass | INVEST §T |
| I-7 | **DoR completeness**: all 8 `dor_checklist` fields = `true` for Must/Should stories; Could/Won't may have `sizing_done: false`. | must-pass M/S; should-pass C/W | DoR §4 |

**Interpretation**: must-pass failure → case fails. Should-pass → `pass-with-warnings`.

### 4.2 `gherkin-quality.md`

**Purpose**: every AC meets BDD / testability rules per `references/ba-best-practices.md` §2 and C29-C30.

| # | Rule | Severity | Source |
|---|---|---|---|
| G-1 | **Format**: every AC has `scenario_name`, `given[]` (≥1), `when` (string), `then[]` (≥1). | must-pass | Gherkin §; schema |
| G-2 | **Single-action When (AP-8.2)**: `when` has no `\band\b` joining two verb phrases. Regex `\b(and|&)\b\s+\w+(s\|es\|ed\|ing)?\b` followed by second verb. | must-pass | AP-8.2; C30 |
| G-3 | **Concrete values**: each AC has ≥1 concrete value (number, quoted string, proper noun) across given+when+then. | must-pass | AP-8.1, AP-8.3, C30 |
| G-4 | **Observable Then (AP-8.3)**: every `then` matches observable-outcome pattern (state verb / audit event / UI element / payload). Reject `is happy`, `is satisfied`, `is improved`. | must-pass | AP-8.3 |
| G-5 | **No vague Given (AP-8.1)**: no bare `Given the system / a user / the application` — must reference concrete role + state. | must-pass | AP-8.1 |
| G-6 | **Scenario-type coverage (C29)**: per story, multiset has ≥1 `happy`, ≥1 `error`/`edge_case`, ≥1 `banking_grade_*`. | must-pass when any banking-grade row `applies`; should-pass otherwise | C29; AP-8.4 |
| G-7 | **Tipping-off scenario**: when `banking_grade.tipping_off.status == "applies"`, ≥1 AC with `scenario_type: banking_grade_tipping_off` whose `then[]` includes deny-list scan. | conditional must-pass | C20, AP-4.4, FM-06 |
| G-8 | **Idempotency replay**: when `banking_grade.idempotency.status == "applies"`, ≥1 `banking_grade_idempotency` AC: `given` previous identical request + key, `when` replayed, `then` no duplicate effect + no duplicate audit. | conditional must-pass | C18, AP-4.3 |
| G-9 | **Testability**: every `then` references concrete observable AND no soft-language tokens (`happy`, `satisfied`, `fast`, `improved`) within 30 chars of unmeasurable predicate. | must-pass | quality heuristic; AP-8.3, AP-4.2 |

**Interpretation**: G-1..G-5, G-9 foundational. G-6..G-8 conditional. > 5% AC failure rate → case fails; ≤ 5% → pass-with-warnings.

### 4.3 `banking-grade-fields.md`

**Purpose**: enforce C18 force-fill contract — 7 rows × non-null status × non-empty justification × cross-checks to governance_gaps and tier.

| # | Rule | Severity | Source |
|---|---|---|---|
| B-1 | **All 7 rows**: `banking_grade_concerns` has keys `{pii_fields, audit_events, idempotency, reversibility, authn_authz, regulatory, tipping_off}`. | must-pass | C18; FM-11 |
| B-2 | **Status enum**: every row `status ∈ {applies, not_applicable, unknown_p2}`. | must-pass | FM-11 |
| B-3 | **Justification ≥ 10 chars (AP-4.1)**: `not_applicable` rows cite workflow class reason. | must-pass | AP-4.1 |
| B-4 | **Applicable → treatment**: `status == applies` ⟹ at least one of `fields_or_events` (non-empty) or `treatment` (non-empty). | must-pass | C18 |
| B-5 | **Tier inference**: `epic.inferred_tier` (or per-`epics[]` entry) ∈ {T1,T2,T3} AND `tier_signals[]` non-empty. | must-pass | C19 |
| B-6 | **Compensating action**: `reversibility.status == applies` AND treatment contains `irreversible` ⟹ `compensating_action` non-empty. | must-pass state-change stories | C21; AP-4.3 |
| B-7 | **Tipping-off cross-check**: any story with `tipping_off.status == applies` ⟹ tipping-off AC present (cross-ref G-7) AND `governance_gaps` has `tipping_off_violation` OR `processing_metadata.tipping_off_scan_clean: true`. | must-pass | C20, FM-06 |
| B-8 | **Legal-absent + regulatory**: `epic.legal_status != "present"` AND any `regulatory`/`tipping_off`/`pii_fields` row `applies` ⟹ `governance_gaps` has `legal_absent_on_regulatory` with `blocks_tl_handoff: true`. | must-pass | C14, FM-05, AP-5.1 |
| B-9 | **PII force-fill (AP-4.1)**: any `pii_fields.status == applies` ⟹ `fields_or_events` non-empty AND `treatment` non-empty AND `glossary` has ≥1 PII-tagged entry. | must-pass | AP-4.1; C7 |
| B-10 | **Tier escalation (AP-1.3)**: `tier_hint` provided AND `epic.inferred_tier` rank-strictly higher than hint ⟹ `processing_metadata.tier_decisions[]` has `inferred_higher_than_manual: true` AND `frontmatter.status != "ready-for-tl"`. | must-pass | AP-1.3 |

**Interpretation**: B-1..B-3 absolute structural. B-4..B-10 condition-based. Cross-checks (B-7, B-8) are highest-leverage — failures expose silent governance defects.

### 4.4 Common runner semantics

E1's assertion runner (phase-d4 specifies language) produces per-case JSON: `{ case_id, rule_results: [{ assertion_file, rule_id, status, evidence? }], case_status, must_pass_failures, should_pass_warnings }`. Aggregate: `{ total_cases, pass, fail, pass_with_warnings, must_pass_failures_by_rule }`.

---

## Part 5 — Coverage Matrix (Tests × Phase-C Edge Cases / Failure Modes)

| Phase-C3 entry | Covered by case |
|---|---|
| EC-01 minimal | 005 |
| EC-02 conflicting speakers | 001 (replace-vs-archive), 002 (mobile-scope) |
| EC-06 missing citations | 003 (MAS-AML-1A), 004 (VISA VCR rules) |
| EC-10 multi-epic | 003, 004 |
| EC-12 conversational-only | 002 |
| EC-13 email inversion | 004 |
| EC-14 anonymous | 001 (N=3) |
| EC-15 note-taker paraphrase | 003 |
| EC-16 stakeholder on leave | 003 (Legal-Sundar), 004 (Diana parental) |
| EC-17 ground-truth block | 001, 002, 003, 006a, 006b |
| EC-18 incomplete citation | 003, 004 |
| FM-01 quality below threshold | 005 |
| FM-02 P1 info missing | 001, 002, 003 |
| FM-05 Legal absent | 001, 002, 003, 004 (all positive cases) |
| FM-06 tipping-off | 002 primary, 003 secondary |
| FM-07 tier ambiguous | 003 |
| FM-09 scope unclear | 004 |
| FM-11 schema validation | implicit — every test asserts schema-valid output |
| FM-12 GT-strip failed | 006b |
| FM-13 PII echo | implicit — every output verified PII-free post-generation |

Gaps not exercised: EC-03 multi-language, EC-04 very-long token-budget, EC-05 very short, EC-08 PII in input, EC-09 meta-request. Optional follow-on cases 007-011 — not MVP scope.

---

## Part 6 — Implementation Notes for E1

1. **Schema files**: `schemas/input.json` + `schemas/output.json` — JSON Schema draft-07. Use `$ref` to factor out shared sub-schemas (BankingGradeRow, Stakeholder, AcceptanceCriterion, OpenQuestion, GovernanceGap).
2. **Test fixtures**: existing `inputs/raw-request-{001,002,003}.md` and `inputs/raw-request-holdout.md` cover cases 001-004. E1 creates `inputs/synthetic-minimal-001.md`, `inputs/synthetic-ground-truth-leak-001-{clean,corrupted}.md`. No actual PII.
3. **Test directory layout** (mirrors existing tests/):
   ```
   tests/
     cases/{001-jira-lending-happy, 002-slack-payments-conversational, 003-meeting-kyc-multi-epic,
            004-holdout-email-card-disputes, 005-minimal-input-failure,
            006a-ground-truth-leak-clean, 006b-ground-truth-leak-corrupted}/
       input.json
       expected.partial.json
       README.md
     assertions/{invest-compliance, gherkin-quality, banking-grade-fields}.md
   ```
4. **Expected-output strategy**: not byte-equality (skill is LLM-driven). Use `expected.partial.json` listing `MUST_HAVE`, `MUST_HAVE_VALUES`, `MUST_HAVE_COUNTS` (ranges), `MUST_NOT_CONTAIN` (deny-list regex). Story / AC content checked via the three assertion files.
5. **Schema validation order**: input validated against `input.json` BEFORE invocation; output validated against `output.json` AFTER emission. Output-schema fail → FM-11 path. Input-schema fail → orchestrator rejects (not the skill's failure mode).
6. **Conditional rules**: at least one fixture per `output_type` enum value.

---

## Part 7 — Validation Checklist for E1

- [ ] `schemas/input.json` validates §1.4 example.
- [ ] `schemas/input.json` rejects missing `idempotency_key`.
- [ ] `schemas/input.json` rejects `raw_content` < 200 chars.
- [ ] `schemas/input.json` rejects `ground_truth_strip_mode: skip` unless `audit_mode: training`.
- [ ] `schemas/output.json` accepts §2.8 skeleton.
- [ ] `schemas/output.json` rejects empty banking-grade `justification`.
- [ ] `schemas/output.json` rejects `status: ready-for-tl` with any P1 OQ.
- [ ] `schemas/output.json` enforces multi-epic vs single-epic shape consistency.
- [ ] `schemas/output.json` allows failure-state shapes (FM-01, FM-11, FM-12, FM-13, EC-09).
- [ ] All 7 test fixtures (001, 002, 003, 004, 005, 006a, 006b) have `input.json` + `expected.partial.json` + `README.md`.
- [ ] Each assertion file lists rules with severity + pseudo-check.
- [ ] Coverage matrix §5 confirms every priority C3 entry exercised.
- [ ] Test 005 routes input-validation failure to FM-01 (not silent fabrication).
- [ ] Test 006b verifies FM-12 refusal — `do_not_proceed: true`.
- [ ] No fixture contains actual PII values.

---

## Part 8 — Open Design Questions for E1

1. **JSON Schema draft version**: draft-07 (recommended) vs 2020-12. Pick 07 unless 2020-12 toolchain available.
2. **AC `when` multi-action detection**: regex may produce false positives on compound subjects. Regex first; escalate to mini-parser if FP rate > 10%.
3. **`failure_state.recommended_questions` shape**: free-form strings (FM-01) vs structured (FM-12/13). Recommend mixed per failure mode.
4. **EC-08 (PII in input) fixture**: synthetic fake-NRIC pattern matching format (`S1234567A`) — clearly not real; documented synthetic origin. Optional.
5. **Assertion runner language**: Python (richer JSON tooling) vs Bash+jq (lighter). E1 chooses; phase-d4 specifies.

---

## Part 9 — Summary

This design specifies:

- **Strict input schema**: 2 required + 7 optional fields, `additionalProperties: false`, production safety constraint (`skip` requires `training` mode).
- **Strict output schema**: matches `epic-and-stories.template.md` plus governance extensions (governance_gaps, processing_metadata, failure_state). Story sub-schema enforces banking-grade force-fill via 7 required keys × non-null `status` + non-empty `justification` (≥10 chars).
- **7 test fixtures** (cases 001-006b) covering happy / blocked / multi-epic / hold-out / minimal-fail / ground-truth-clean / ground-truth-corrupted.
- **3 assertion files**: `invest-compliance.md` (7 rules), `gherkin-quality.md` (9 rules), `banking-grade-fields.md` (10 rules) = 26 rule-level checks.
- **Coverage matrix** confirms priority C3 entries exercised (FM-01, FM-02, FM-05, FM-06, FM-07, FM-09, FM-11, FM-12 + EC-02, EC-06, EC-10, EC-12, EC-13, EC-14, EC-15, EC-16, EC-17, EC-18).

Schemas implement C18 forcing function + AP-5.1/FM-05 Legal-absence detector structurally — bad data cannot be encoded as valid output. Tests verify dynamic behaviors: tier inference, scope detection, ambiguity surfacing, ground-truth strip safety, refusal paths. Every brief either passes the assertion suite or fails loudly via `failure_state` — no silent fabrication.

---

*End of Phase D3 Schemas + Test Cases Design. E1 translates this into `schemas/input.json`, `schemas/output.json`, `tests/cases/*/`, and `tests/assertions/*.md` per the validation checklist in §7.*
