---
name: validating-banking-implementation
version: 0.1.0
description: >
  Run an adversarial red-team pentest against a banking implementation in a
  sandbox — driving threat personas through OWASP and chaos scenarios to surface
  findings a scanner cannot — and emit an ADVISORY pass, conditional, or fail
  verdict that a named human confirms at a verification gate. Use when asked to
  red-team or pentest the implementation pre-deploy, run adversarial personas
  against the app for UAT, or produce the advisory security verdict for human
  sign-off. The verdict is persona judgment, not a machine threshold; the skill
  routes it to a named reviewer and never auto-approves or fixes anything. Do NOT
  use for automated static source scanning (use running-sast-security-gate) or for
  DAST and dependency CVE scanning (use scanning-appsec-pipeline-gate). Do NOT use
  to fix vulnerabilities.
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: detailed, pii_handling: none, tier_default: T1, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
expected_duration_p95_seconds: 1800
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Validating the Banking Implementation

## Purpose

Run an **adversarial red-team pentest** against a banking implementation pre-deploy
(UAT) and surface the findings a scanner cannot — abuse paths, business-logic
exploits, and resilience gaps — by driving threat personas through OWASP and chaos
scenarios. Unlike the automated SAST/DAST/SCA gates, there is **no machine
threshold here**: the verdict is **persona judgment**, it is **advisory**, and a
**named human confirms it** at a verification gate. The skill explores, evidences,
and recommends; it never auto-approves and never fixes anything.

## When to use this skill

- Use when: an implementation must be adversarially pentested pre-deploy with
  threat personas and OWASP/chaos scenarios, producing an advisory verdict for
  human sign-off.
- Use when: asked to "red-team the implementation", "run the adversarial personas",
  or "produce the pre-deploy security verdict".
- Do NOT use: for automated static source scanning
  (`running-sast-security-gate`), for DAST/SCA scanning
  (`scanning-appsec-pipeline-gate`), or to fix vulnerabilities.

## Input contract

Validate against `schemas/input.json`. Required: `implementation_ref` (the
deployed-to-sandbox implementation under test), `threat_personas` (the adversarial
personas to drive, or null to use the default roster), `idempotency_key`. Optional:
`tier`. Stop with `needs-input` if there is no reachable implementation.

## Procedure

1. **Stage the implementation** (`references/adversarial-pentest.md`): deploy
   `implementation_ref` into a sandbox; never attack outside it. Entry: an
   implementation + persona roster. Exit: a target ready for adversarial probing.
2. **Drive each threat persona** through OWASP and chaos scenarios — broken
   authorization, injection, abuse-of-functionality, dependency/availability chaos
   — recording concrete `evidence` for every finding (a reproduction, not a claim).
3. **Surface what scanners miss.** Focus on business-logic and abuse paths an
   automated scanner cannot reason about; classify each finding by `severity`.
4. **Form an advisory verdict** from persona judgment: `pass` (no exploitable
   path found), `conditional` (findings that need a named decision), or `fail`
   (an exploitable path was demonstrated). Banking default: uncertain → not pass.
5. **Route to a named human reviewer.** The advisory verdict is **not** the gate —
   a named human confirms it (human verification gate). The skill never
   auto-approves; redact any real PII or secret in evidence as
   [PII:REDACTED:CLASS=...].
6. **Emit** the advisory verdict + persona findings (Output contract) with
   `audit_id`. Stop — findings route to a fixer; the human decision is recorded.

## Output contract

Validate against `schemas/output.json`: `verdict` (pass|conditional|fail,
**advisory**), `persona_findings[]{persona,severity,scenario,evidence}`, and
`audit_id`. The verdict is advisory input to the human gate, not the decision.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| VB-01 | no reachable implementation | no verdict | needs-input → human-queue |
| VB-02 | exploitable path demonstrated | `fail` (advisory) + evidence | route to a fixer → human gate |
| VB-03 | findings needing a named decision | `conditional` (advisory) | human verification gate |
| VB-04 | no exploitable path found | `pass` (advisory) | still confirmed by a named human |

## Constraints

- DO NOT fix, patch, or rewrite the implementation — pentest, evidence, and route
  only.
- DO NOT treat the verdict as the gate; it is **advisory**, and a named human
  confirms it. The skill never auto-approves.
- DO NOT return `pass` on uncertainty; uncertain → not pass (banking).
- DO NOT echo real PII or secrets in evidence; redact as [PII:REDACTED:CLASS=...].
- DO NOT attack any target outside the sandboxed environment.

## Human verification gate

This is a **human-judgment gate**, not a machine threshold. The advisory verdict
the personas produce is routed to a **named human reviewer** who records the
authoritative decision: confirm `pass`, accept a `conditional` with conditions, or
uphold a `fail`. The skill never auto-approves; the human decision and the named
reviewer are logged under `audit_id`.

## References

| Need | Reference |
|------|-----------|
| Threat-persona roster, OWASP + chaos scenarios, evidence discipline, advisory verdict, human gate | `references/adversarial-pentest.md` |
