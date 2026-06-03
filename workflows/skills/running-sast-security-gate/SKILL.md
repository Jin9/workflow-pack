---
name: running-sast-security-gate
version: 0.1.0
description: >
  Run a static application security test (SAST) over developer-authored source in
  a sandbox, detecting insecure logic written in-house — injection, BOLA/IDOR
  authorization flaws, and hardcoded secrets — then emit a PASS, FAIL, or ERROR
  pre-merge gate from real scanner output with new-vs-baseline gating. Use when
  asked to SAST-scan changed source before merge, statically scan a repo for
  in-house vulnerabilities, or produce the pre-merge security gate with evidence.
  Findings come from real scanners, not model guesses; a detected secret is always
  a hard fail; it routes findings to a fixer and never fixes code. Do NOT use to
  scan a running app for DAST or dependency CVEs (use scanning-appsec-pipeline-gate).
  Do NOT use to run an adversarial red-team pentest (use
  validating-banking-implementation). Do NOT use to write or fix code.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: detailed, pii_handling: none, tier_default: T1, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
expected_duration_p95_seconds: 300
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Running the SAST Security Gate

## Purpose

Statically scan **developer-authored source** before merge and emit a
results-backed security gate. SAST finds the vulnerabilities your team wrote — an
injection in a hand-built query, a missing authorization check (BOLA/IDOR), a
secret committed to the tree — by analyzing code without running it. This is the
**pre-merge** gate in CI: it reads from real static scanners, gates new findings
against a baseline, and hands the verdict to a human verification layer. It never
fixes code and never scans a running app.

## When to use this skill

- Use when: changed source (or a repo) must be statically scanned for in-house
  vulnerabilities before merge, producing a pass/fail gate with evidence.
- Use when: asked to "run SAST", "static-scan the diff", or "produce the pre-merge
  security gate".
- Do NOT use: to scan a running app for DAST or dependency CVEs
  (`scanning-appsec-pipeline-gate`), to run an adversarial pentest
  (`validating-banking-implementation`), or to fix code.

## Input contract

Validate against `schemas/input.json`. Required: `source_ref` (repo or changed
files to scan), `baseline` (prior accepted findings, or null on first run),
`idempotency_key`. Optional: `severity_floor` (default `high`), `tier`. Stop with
`needs-input` if there is no resolvable source to scan.

## Procedure

1. **Resolve and stage** (`references/sast-gate.md`): check out `source_ref` into
   a sandbox; never reach the network beyond fetching the source. Entry: a source
   ref. Exit: a scannable working tree.
2. **Run real static scanners** for the in-house classes — injection, BOLA/IDOR
   authorization flaws, hardcoded secrets — and collect their structured output.
   Findings come from the scanners, never from a model guess; an unparseable or
   crashed scan is `ERROR`, not a silent pass.
3. **Count secrets.** A detected secret is **always a hard fail** regardless of
   baseline — secrets are never tech-debt. Redact any matched value as
   [PII:REDACTED:CLASS=...] before recording it.
4. **Gate new vs baseline.** Diff scanner findings against `baseline`: classify
   each as `new` or `fixed`. Pre-existing baseline findings do not block; **new**
   findings at or above `severity_floor` do.
5. **Apply the gate:** `FAIL` if `secrets` is non-zero OR any new finding is at or
   above `severity_floor`; `ERROR` if a scanner could not run; else `PASS`.
   Banking default: a masked or uncertain result is a fail, not a pass.
6. **Emit** the verdict (Output contract). Stop — findings route to a fixer; the
   gate feeds a **human verification layer**, never auto-approves.

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR),
`findings[]{severity,rule,file,summary}`, `secrets` (integer count),
`new_vs_baseline{new,fixed}`, and `audit_id`.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| SS-01 | no resolvable source | no verdict | needs-input → human-queue |
| SS-02 | scanner crashed / output unparseable | `ERROR` | human-queue |
| SS-03 | secret detected | `FAIL` (hard) | route to a fixer (rotate + remove) |
| SS-04 | new finding at or above severity_floor | `FAIL` + findings[] | route to a fixer |
| SS-05 | only pre-existing baseline findings | `PASS` + note | tracked as accepted tech-debt |

## Constraints

- DO NOT fix, edit, or rewrite code — scan, gate, and route only.
- DO NOT emit a pass not backed by scanner output; uncertain → fail (banking).
- DO NOT block on pre-existing baseline findings; block only on NEW findings at or
  above `severity_floor`. A detected secret is always a hard fail regardless of
  baseline.
- DO NOT auto-approve; the gate feeds a named human verification layer.
- DO NOT echo real PII or secrets; redact as [PII:REDACTED:CLASS=...].
- DO NOT run outside the sandbox or reach the network beyond fetching the source.

## References

| Need | Reference |
|------|-----------|
| Static scanner integration, in-house vuln classes, secrets hard-fail, new-vs-baseline gating, human layer | `references/sast-gate.md` |
