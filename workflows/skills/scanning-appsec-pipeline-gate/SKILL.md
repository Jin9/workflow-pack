---
name: scanning-appsec-pipeline-gate
version: 0.1.0
description: >
  Scan the built and running application plus its third-party dependencies in a
  sandbox — DAST attacking the running app from outside, SCA flagging known CVEs
  in imported dependencies, and a secrets sweep — then emit a PASS, FAIL, or ERROR
  CI/SIT gate from real scanner output with new-vs-baseline gating. Use when asked
  to DAST-scan a running app, run an SCA dependency CVE scan, sweep the build for
  secrets, or produce the integrated AppSec pipeline gate with evidence. Findings
  come from real scanners, not model guesses; a detected secret is always a hard
  fail; it routes findings to a fixer and never remediates. Do NOT use to
  statically scan developer-authored source (use running-sast-security-gate). Do
  NOT use to run an adversarial red-team pentest (use
  validating-banking-implementation). Do NOT use to remediate vulnerabilities.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: detailed, pii_handling: none, tier_default: T1, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
expected_duration_p95_seconds: 600
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Scanning the AppSec Pipeline Gate

## Purpose

Scan the **built and running app and its dependencies** and emit a results-backed
security gate for CI/SIT. Three real scanners run together: **DAST** attacks the
running app from outside to find exploitable runtime behavior, **SCA** flags known
CVEs in the third-party dependencies you imported, and a **secrets sweep** catches
leaked credentials in the build. This complements the source-level SAST gate: SAST
finds the vulnerabilities you wrote, this gate finds runtime weaknesses and
known-CVE dependency risk in what you ship. It reads from real scanner output,
gates new findings against a baseline, routes to a fixer, and never remediates.

## When to use this skill

- Use when: a built/running app and its dependency manifest must be scanned in
  CI/SIT for runtime findings, known CVEs, and secrets, producing a pass/fail gate
  with evidence.
- Use when: asked to "run DAST + SCA", "scan the running app and dependencies", or
  "produce the AppSec pipeline gate".
- Do NOT use: to SAST-scan source (`running-sast-security-gate`), to run an
  adversarial pentest (`validating-banking-implementation`), or to remediate.

## Input contract

Validate against `schemas/input.json`. Required: `target_env` (running app URL or
handle to attack), `sbom` (dependency manifest for SCA, or null), `baseline`
(prior accepted findings, or null), `idempotency_key`. Optional: `severity_floor`
(default `high`), `tier`. Stop with `needs-input` if the target is unreachable.

## Procedure

1. **Resolve the target** (`references/appsec-dast-sca.md`): confirm `target_env`
   is reachable in the sandbox; never attack outside the sandboxed environment.
   Entry: a running app + optional SBOM. Exit: a scannable target.
2. **Run DAST** against the running app from outside, collecting real scanner
   output. Findings come from the scanner, never a model guess; a crashed or
   unreachable scan is `ERROR`, not a silent pass.
3. **Run SCA** over `sbom`: match imported dependencies to known CVEs and mark any
   flagged as **known-exploited** (actively exploited in the wild).
4. **Sweep for secrets** across the build/image. A detected secret is **always a
   hard fail**; redact any matched value as [PII:REDACTED:CLASS=...] before
   recording it.
5. **Gate new vs baseline.** Pre-existing baseline findings do not block; **new**
   findings at or above `severity_floor` do.
6. **Apply the gate:** `FAIL` if `secrets` is non-zero OR any known-exploited CVE
   is present OR any new finding is at or above `severity_floor`; `ERROR` if a
   scanner could not run; else `PASS`. Banking default: uncertain → fail.
7. **Emit** the verdict (Output contract). Stop — findings route to a fixer; the
   gate feeds a **human verification layer**, never auto-approves.

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR),
`dast_findings[]{severity,summary}`, `sca_cves[]{id,severity,known_exploited}`,
`secrets` (integer count), and `audit_id`.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| AP-01 | target unreachable | no verdict | needs-input → human-queue |
| AP-02 | scanner crashed / output unparseable | `ERROR` | human-queue |
| AP-03 | secret detected | `FAIL` (hard) | route to a fixer (rotate + remove) |
| AP-04 | known-exploited CVE in a dependency | `FAIL` + sca_cves[] | route to a fixer (upgrade/pin) |
| AP-05 | new finding at or above severity_floor | `FAIL` + dast_findings[] | route to a fixer |
| AP-06 | only pre-existing baseline findings | `PASS` + note | tracked as accepted tech-debt |

## Constraints

- DO NOT remediate, patch, or rewrite the app or its dependencies — scan, gate,
  and route only.
- DO NOT emit a pass not backed by scanner output; uncertain → fail (banking).
- DO NOT block on pre-existing baseline findings; block only on NEW findings at or
  above `severity_floor`. A detected secret and any known-exploited CVE are always
  hard fails.
- DO NOT auto-approve; the gate feeds a named human verification layer.
- DO NOT echo real PII or secrets; redact as [PII:REDACTED:CLASS=...].
- DO NOT attack any target outside the sandboxed environment.

## References

| Need | Reference |
|------|-----------|
| DAST attack model, SCA known-CVE matching, secrets sweep, new-vs-baseline gating, human layer | `references/appsec-dast-sca.md` |
