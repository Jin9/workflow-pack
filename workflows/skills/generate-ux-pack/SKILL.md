---
name: generate-ux-pack
version: 0.2.0
description: Produce a v1.1 UX-design intake pack from a UX team's drop (bundled prototype HTML, Frontend Spec markdown, BA brief directory). Emits a structured `ux-design-{idem8}/` tree with tokens.json (W3C design tokens + WCAG contrast), route-map.md, component-inventory.md, microcopy.json (bilingual TH/EN with tipping-off scan), screen-states.md, form-validation.md (Thai-locale rules + banking-grade carve-outs), responsive-spec.md, accessibility-spec.md (WCAG AA), flows/, and per-epic screens/. Use when a UX team submits a prototype + brand spec for TL handoff. Use when Stage 2 TL Design requires a tokens.json + route-map contract. Use when an existing UX pack needs a maturity audit (re-run produces same artifact tree with refreshed findings). Do NOT use for code generation (use implement-frontend-feature). Do NOT use for BA elicitation (use elaborating-user-stories). Do NOT use to extract Thai strings from bundled HTML — emit `TBD-extract-from-prototype` for the UX team to fill.
stage_type: analyze
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: enhanced, pii_handling: redact, tier_default: T2, tier_adaptable: [T1, T2, T3]}
expected_duration_p95_seconds: 180
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Generate UX Pack

## Purpose

Convert a UX team's drop into a structured v1.1 UX-design intake pack consumed by the downstream TL-design and frontend-implementation steps. Banking-grade discipline: bilingual handling, WCAG contrast computed (not asserted), tipping-off vocabulary scan on every emitted English string, no invented PII, BA story cross-references verified before emission, honest TBDs over fabricated completeness.

## When to use this skill

- Use when: a UX team submits a prototype + brand spec for TL handoff, or the
  pipeline's ux-intake stage runs on a BA brief (BA-derived fallback pack,
  maturity capped at 2 until a real UX drop lands).
- Use when: an existing UX pack needs a maturity audit (a re-run with the same
  idempotency key validates/updates the SAME pack with refreshed findings).
- Do NOT use: for code generation (`implement-frontend-feature`), for BA
  elicitation (`elaborating-user-stories`), or to extract Thai strings from
  bundled HTML (emit `TBD-extract-from-prototype`).

## Input contract

ADVISORY — documents the assembled stage input; the engine validates workflow input
and stage OUTPUTS only (engine/validation.py). Validate against `schemas/input.json`.
Required: `requester` (workflow input), `epics` + `stories` (engine-hydrated from
the ba-brief ref-chain; `story_files` refs retained), `idempotency_key`
(engine-injected — its first 8 chars form the pack dir suffix; NEVER generate a
fresh UUID). Optional engine-injected: `upstream_artifacts`, `loop_back_feedback`.
Standalone direct invocation (frontend_spec_path / prototype_html_path /
ba_brief_dir) is a separate mode documented in `references/generate-prompt.md`.
Stop `blocked_ux_pack` if there are no stories or epics to derive coverage from.

**Example (validates against schemas/input.json):**
```json
{
  "requester": "Khun Anan (Product Owner)",
  "epics": [{ "id": "EPIC-CHECKOUT", "title": "Checkout" }],
  "story_files": [{ "epic": "EPIC-CHECKOUT", "file": "EPIC-CHECKOUT/STORY-CHECKOUT-01.json" }],
  "stories": [{ "id": "STORY-CHECKOUT-01", "epic_id": "EPIC-CHECKOUT", "title": "Customer pays" }],
  "idempotency_key": "c3f8a1d2-4b6e-4f09-9a7c-1e2d3b4a5c6d"
}
```

## Output contract

Validate against `schemas/output.json` (discriminated by `output_type`):
`ux_pack` = boundary-successful pack — maturity 2 (`ready-for-audit`) or 3
(`ready-for-implementation`, zero P1 findings), all nine core files, required
`status`/`p1_findings`/`p2_findings` + both coverage-gap arrays; every path is
**pack-relative POSIX** (`ux-design-{idem8}/...` — no absolute paths, no
traversal; consumers resolve via `dirname(upstream_artifacts["ux-intake"])`).
`partial_ux_pack` (maturity 0/1 or missing artifacts), `blocked_ux_pack`, and
`failure_shape` intentionally fail the stage boundary and route retry →
`ux-intake-pending`. `audit_id` is producer-stamped, deterministic:
UUIDv5(HOUSE_NS, "ux-intake:{idempotency_key}") with HOUSE_NS =
uuid5(NAMESPACE_URL, "https://squad-delivery/audit").

**Example (validates against schemas/output.json):**
```json
{
  "output_type": "blocked_ux_pack",
  "blockers": [
    { "code": "BLOCK-NO-BA-BRIEF", "description": "No epics or stories supplied." }
  ],
  "audit_id": "e5b9d740-2a18-4c63-b0f1-7d6c2a3e9f55"
}
```

## Procedure

1. **Pre-flight** — validate inputs exist, parse the hydrated epics/stories,
   derive `idem8` = first 8 chars of the injected `idempotency_key` (retries
   reuse the same pack directory), refuse on missing required fields.

2. **Load sources** — in pipeline mode, derive brand/routes/components from the
   hydrated stories (BA-derived fallback; maturity cap 2); in standalone mode,
   read the frontend spec sections and treat prototype HTML as opaque
   (structural reference only).

3. **Emit core contract files** — write the 9 required artifacts at `ux-design-{idem8}/` per `references/per-file-rules.md`: README.md, tokens.json, route-map.md, component-inventory.md, microcopy.json, screen-states.md, form-validation.md, responsive-spec.md, accessibility-spec.md.

4. **Compute WCAG contrasts** — for every brand/text/background combination in tokens.json, compute contrast ratio with the WCAG formula; emit `wcagAA` / `wcagAAA` booleans + `usage_note`. Failures surface as P1 findings.

5. **Generate flows/** — 4 required flows (customer-onboarding, customer-checkout, customer-order-tracking, payment-failure-recovery) with Mermaid sequence diagrams and per-screen narrative. Add others if BA brief has additional customer journeys.

6. **Generate screens/** — one folder per customer-facing BA epic (skip admin/governance epics). Per epic: `EPIC.md` + `stories/STORY-N-{slug}.md` per BA story. Cross-references back to route-map.md, microcopy.json, component-inventory.md, screen-states.md.

7. **Run maturity audit** — count artifacts present (target 9/9), TBD count in microcopy.json, WCAG failures, BA stories without UX coverage, UX routes without BA stories. Compute `maturity_level` (0|1|2|3) per v1.1 §4 audit triage.

8. **Emit output.json** — discriminated `output_type`: `ux_pack | blocked_ux_pack | partial_ux_pack | failure_shape`. Include `pack_dir`, paths to all artifacts, `maturity_level`, P1/P2 findings, `audit_id`. Write to disk + return summary in chat.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| UX-01 | no epics/stories to derive coverage from | `blocked_ux_pack` | retry ×1 → ux-intake-pending queue |
| UX-02 | some core artifacts cannot be derived | `partial_ux_pack` (maturity 0/1) | retry ×1 → ux-intake-pending queue |
| UX-03 | runtime error while emitting the pack | `failure_shape` | retry ×1 → ux-intake-pending queue |
| UX-04 | WCAG contrast failure / Thai copy TBD at maturity 3 | `ux_pack` capped at maturity 2 + P1 findings | human UX review |

## Constraints

- **No invented PII.** Example email/phone/name values must look obviously fake;
  redact real values as [PII:REDACTED:CLASS=...].
- **Bilingual handling.** Default `en` if obvious; mark `th` as `TBD-extract-from-prototype` unless verbatim in spec.
- **Tipping-off discipline.** Forbidden vocabulary scan on every emitted English string (financial-domain: flagged, suspicious, AML, sanctions, PEP, EDD, SAR, adverse media, fraud-flagged, watchlist).
- **WCAG honesty.** Compute contrasts with the actual formula; don't claim AA pass without the math.
- **BA cross-reference accuracy.** Every BA story ID referenced must exist in the hydrated stories — copied exactly (e.g. `STORY-CHECKOUT-01`), never paraphrased.
- **TBD discipline.** When data is missing, emit `TBD-<what>-<who-fills>`. Never silently invent.
- **Cross-reference integrity.** Every microcopy key, component, and route referenced elsewhere must exist in its respective inventory file.
- **Idempotent identity.** The pack dir and all identity derive from the injected `idempotency_key`; a retry updates the same pack — never a new directory.

## References

Progressive disclosure — load only what each step needs:

- `references/generate-prompt.md` — original v1.1 generator prompt (full body, verbatim)
- `references/per-file-rules.md` — extracted per-file authoring rules + quality rules + output discipline

Not skill references (external to this skill; informational only, never loaded
at runtime): a canonical Maturity-Level-2 example output exists in the project
under the `ux-intake-v1.1` design directory. Frontmatter schema validation is a
build/CI concern handled outside the skill.
