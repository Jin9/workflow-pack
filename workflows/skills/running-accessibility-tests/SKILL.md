---
name: running-accessibility-tests
version: 0.1.0
description: >
  Run automated accessibility tests against a built front end during FE review or
  SIT and emit a PASS, FAIL, or ERROR gate for WCAG 2.1 AA — surfacing automated
  violations AND the needs-review items the engine cannot decide, so automation is
  never mistaken for full coverage. Use when asked to run accessibility or a11y
  tests, check a page or component against WCAG 2.1 AA, produce the accessibility
  gate, or scan a built front end with axe-core. Runs in a sandbox via an a11y
  engine and a browser driver and reports only; it never edits the UI. Automated
  engines catch about 57 percent of WCAG issues on average and flag incomplete
  items for manual review, so the skill flags manual checks rather than claiming
  full coverage. Do NOT use to design the UI, tokens, or layout (use
  generate-ux-pack). Do NOT use to fix accessibility issues or write remediation
  code.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: detailed, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
expected_duration_p95_seconds: 300
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Running Accessibility Tests

## Purpose

Scan a built front end for **WCAG 2.1 AA** conformance during FE review / SIT and
emit a PASS / FAIL / ERROR gate backed by an automated a11y engine — while making
the engine's limits explicit. Automated tooling (axe-core) catches only part of
WCAG and returns "incomplete" items that need a human; this skill surfaces those
`needs_review` items and required `manual_checks` rather than passing them
silently or claiming full coverage. It reports only; it never edits the UI.

## When to use this skill

- Use when: a built front end (pages/components) must be scanned against WCAG 2.1
  AA before sign-off, with automated violations plus manual follow-ups surfaced.
- Use when: asked to "run the a11y tests", "check WCAG AA", or "produce the
  accessibility gate with evidence".
- Do NOT use: to design the UI/tokens/layout (`generate-ux-pack`), or to fix
  accessibility issues / write remediation code.

## Input contract

Validate against `schemas/input.json`. Required: `target` (pages/components or the
built FE to scan), `idempotency_key`. Optional: `wcag_level` (default "AA"),
`tier`. Stop with `needs-input` if there is no reachable built front end to scan.

## Procedure

1. **Bind the standard** (`references/wcag-a11y.md`): use `wcag_level` (default
   AA) as the conformance target; do not author criteria. Entry: target + level.
   Exit: a runnable scan spec.
2. **Run the a11y engine** (axe-core) against `target` via a browser driver
   (Playwright). Capture the engine report — violations are read from the engine,
   never asserted by the agent. If the build cannot render, that is an `ERROR`.
3. **Collect automated violations** into `wcag_violations[]` with rule, impact,
   and WCAG reference. These are the machine-decidable failures.
4. **Surface needs-review items.** Map the engine's "incomplete" results into
   `needs_review[]` and the required human steps into `manual_checks` (e.g.
   keyboard-only traversal, focus order, meaningful alt text, contrast on
   images-of-text). Automation covers only part of WCAG; the rest is manual.
5. **Apply the gate:** `ERROR` if the build could not be scanned; `FAIL` on any AA
   automated violation, or when `needs_review` is non-empty and unresolved
   (banking default: unresolved manual items are not a silent pass); else `PASS`
   with manual checks still listed for human follow-up.
6. **Emit** the verdict (Output contract). Stop — a named human resolves the
   manual checks; this skill never auto-approves or claims full WCAG coverage.

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR),
`wcag_violations[]{rule,impact,wcag_ref}`, `needs_review[]{rule,note}`,
`manual_checks` (the required human checks), and `audit_id`.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| AX-01 | no reachable built front end | no verdict | needs-input → human-queue |
| AX-02 | build cannot render / engine cannot run | `ERROR` | human-queue |
| AX-03 | one or more AA automated violations | `FAIL` + wcag_violations[] | route to FE fixer |
| AX-04 | unresolved needs-review / manual items | `FAIL` + needs_review[] | flag for human verification |

## Constraints

- DO NOT claim full WCAG coverage from automation; surface needs-review + manual
  checks explicitly (engines catch ~57% on average).
- DO NOT edit the UI, tokens, or remediation code — report only.
- DO NOT silently pass needs-review items; uncertain → human follow-up (banking).
- DO NOT auto-approve; the gate feeds a named human sign-off.
- DO NOT echo real PII captured in screenshots/DOM; redact as
  [PII:REDACTED:CLASS=...].

## References

| Need | Reference |
|------|-----------|
| WCAG AA binding, axe-core limits, needs-review/manual checks, gate policy, boundary | `references/wcag-a11y.md` |
