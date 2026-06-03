---
name: generate-ux-pack
description: >
  Produce a v1.1 UX-design intake pack from a UX team's drop (bundled prototype HTML,
  Frontend Spec markdown, BA brief directory). Emits a structured `ux-design-{idem8}/`
  tree with tokens.json (W3C design tokens + WCAG contrast), route-map.md,
  component-inventory.md, microcopy.json (bilingual TH/EN with tipping-off scan),
  screen-states.md, form-validation.md (Thai-locale rules + banking-grade carve-outs),
  responsive-spec.md, accessibility-spec.md (WCAG AA), flows/, and per-epic screens/.

  Use when a UX team submits a prototype + brand spec for TL handoff. Use when
  Stage 2 TL Design requires a tokens.json + route-map contract. Use when an
  existing UX pack needs a maturity audit (re-run produces same artifact tree
  with refreshed findings).

  Do NOT use for code generation (use implement-frontend-feature). Do NOT use for
  BA elicitation (use ba-elicit-from-raw). Do NOT use to extract Thai strings from
  bundled HTML — emit `TBD-extract-from-prototype` for the UX team to fill.
compatibility: [claude-code, codex, opencode]
metadata:
  version: 0.1.0
  stage_type: analyze
  input_schema: schemas/input.json
  output_schema: schemas/output.json
  banking_grade: {idempotent: true, reversible: n/a, audit_level: enhanced}
  expected_duration_p95_seconds: 180
  max_retries_recommended: 2
---

# Generate UX Pack

## Purpose

Convert a UX team's drop into a structured v1.1 UX-design intake pack consumed by the downstream TL-design and frontend-implementation steps. Banking-grade discipline: bilingual handling, WCAG contrast computed (not asserted), tipping-off vocabulary scan on every emitted English string, no invented PII, BA story cross-references verified before emission, honest TBDs over fabricated completeness.

## Inputs

Per `schemas/input.json`:

- `frontend_spec_path` — Frontend Spec markdown (authoritative content source)
- `prototype_html_path` — bundled prototype HTML (structural reference only; do not extract text)
- `ba_brief_dir` — BA brief output directory with `output.json` + `epics/` (authoritative source for stories)
- `idempotency_key` — UUID v4 for run identity
- Optional: `figma_url`, `ux_team_contact`, `workload_tier` (T1|T2|T3, default T2)

## Procedure

1. **Pre-flight** — validate inputs exist, parse BA brief, generate `idem8` (first 8 chars of UUID v4) for output directory, refuse on missing required fields.

2. **Load sources** — read frontend spec sections (brand, routes, components, business logic, recommended stack); list BA epics + stories from `ba_brief_dir`; treat HTML as opaque (structural reference only).

3. **Emit core contract files** — write the 9 required artifacts at `ux-design-{idem8}/` per `references/per-file-rules.md`: README.md, tokens.json, route-map.md, component-inventory.md, microcopy.json, screen-states.md, form-validation.md, responsive-spec.md, accessibility-spec.md.

4. **Compute WCAG contrasts** — for every brand/text/background combination in tokens.json, compute contrast ratio with the WCAG formula; emit `wcagAA` / `wcagAAA` booleans + `usage_note`. Failures surface as P1 findings.

5. **Generate flows/** — 4 required flows (customer-onboarding, customer-checkout, customer-order-tracking, payment-failure-recovery) with Mermaid sequence diagrams and per-screen narrative. Add others if BA brief has additional customer journeys.

6. **Generate screens/** — one folder per customer-facing BA epic (skip admin/governance epics). Per epic: `EPIC.md` + `stories/STORY-N-{slug}.md` per BA story. Cross-references back to route-map.md, microcopy.json, component-inventory.md, screen-states.md.

7. **Run maturity audit** — count artifacts present (target 9/9), TBD count in microcopy.json, WCAG failures, BA stories without UX coverage, UX routes without BA stories. Compute `maturity_level` (0|1|2|3) per v1.1 §4 audit triage.

8. **Emit output.json** — discriminated `output_type`: `ux_pack | blocked_ux_pack | partial_ux_pack | failure_shape`. Include `pack_dir`, paths to all artifacts, `maturity_level`, P1/P2 findings, `audit_id`. Write to disk + return summary in chat.

## Quality rules (load-bearing — see `references/per-file-rules.md` §Quality rules)

- **No invented PII.** Example email/phone/name values must look obviously fake.
- **Bilingual handling.** Default `en` if obvious; mark `th` as `TBD-extract-from-prototype` unless verbatim in spec.
- **Tipping-off discipline.** Forbidden vocabulary scan on every emitted English string (financial-domain: flagged, suspicious, AML, sanctions, PEP, EDD, SAR, adverse media, fraud-flagged, watchlist).
- **WCAG honesty.** Compute contrasts with the actual formula; don't claim AA pass without the math.
- **BA cross-reference accuracy.** Every BA story ID referenced must exist in the BA brief.
- **TBD discipline.** When data is missing, emit `TBD-<what>-<who-fills>`. Never silently invent.
- **Cross-reference integrity.** Every microcopy key, every component, every route referenced elsewhere must exist in its respective inventory file.

## Output

Filesystem: `ux-design-{idem8}/` directory tree per `references/per-file-rules.md`.
JSON: `output.json` matching `schemas/output.json` — paths to all emitted artifacts, maturity verdict, findings, audit trace.

## References

Progressive disclosure — load only what each step needs:

- `references/generate-prompt.md` — original v1.1 generator prompt (full body, verbatim)
- `references/per-file-rules.md` — extracted per-file authoring rules + quality rules + output discipline

Not skill references (external to this skill; informational only, never loaded
at runtime): a canonical Maturity-Level-2 example output exists in the project
under the `ux-intake-v1.1` design directory. Frontmatter schema validation is a
build/CI concern handled outside the skill.
