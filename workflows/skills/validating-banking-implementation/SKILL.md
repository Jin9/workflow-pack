---
name: validating-banking-implementation
version: 0.2.1
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
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: detailed, pii_handling: redact, tier_default: T1, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
expected_duration_p95_seconds: 1800
max_retries_recommended: 0
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

`schemas/input.json` is **ENFORCED** — the engine validates the ASSEMBLED payload
against it before this stage runs (fail-closed, exactly like output validation);
it documents the POST-adapter payload assembled at stage `adversarial-pentest`. Required: `totals` and `verdict` picked from `qa-validate`
(**the upstream QA verdict — `PASS|FAIL|ERROR`, distinct from this stage's
lowercase advisory `pass|conditional|fail`**) and the engine-injected
`idempotency_key`. Optional: `adversarial_pentest_context` from the workflow
input — the authorized target (`target_ref`, `target_kind:
ci-sandbox|uat-sandbox`, **required `authorization_ref`** — the signed
authorization for this adversarial run; no live pentest without it), plus
optional `threat_personas` (items: `{persona_id, objective, auth_context}`),
`runner_profile_ref`, `tier`. Live mode without a context is `needs-input`;
replay needs none. Optional engine-injected: `upstream_artifacts`,
`loop_back_feedback`.

**Example (validates against schemas/input.json):**

```json
{
  "totals": {"planned": 24, "executed": 24, "passed": 24, "failed": 0, "blocked": 0},
  "verdict": "PASS",
  "adversarial_pentest_context": {"target_ref": "uat-shoppilot", "target_kind": "uat-sandbox", "authorization_ref": "AUTH-PENTEST-2026-07-12-001"},
  "idempotency_key": "req-2026-07-12-shoppilot-001"
}
```

## Procedure

1. **Attach to the authorized target** (`references/adversarial-pentest.md`):
   confirm `authorization_ref` covers this run, then attach to the ALREADY-STAGED
   sandbox target named by `target_ref` — this skill never deploys anything and
   never attacks outside the authorized sandbox. Personas come from the context
   or, when absent, the default roster in the reference (stable `persona_id`s).
   Entry: an authorized target + roster. Exit: a target ready for probing.
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
   `execution` provenance (`runner` = a real adversarial run with evidence_ref +
   report_sha256; `replay` = byte-verbatim reference corpus — no pentest ran) and
   `audit_id`. Stop — findings route to a fixer; the named human's decision is
   recorded engine-side at the gate.

## Output contract

Validate against `schemas/output.json`. Required: `verdict`
(pass|conditional|fail — **advisory**), `persona_findings[]` (each with a
non-empty `persona` carrying the stable `persona_id`, `severity`, `scenario`,
and `evidence`; a `conditional` or `fail` verdict REQUIRES at least one finding —
empty evidence can never support a non-pass), `execution` (provenance), and
`audit_id`. The verdict is advisory input to the human gate, not the decision.

`audit_id` (live): `UUIDv5(HOUSE_NS, "adversarial-pentest:{idempotency_key}")`,
`HOUSE_NS = uuid5(NAMESPACE_URL, "https://squad-delivery/audit")` — producer-
stamped, independent of the optional context, distinct from the engine's
per-attempt id. The human L3 gate verdict is recorded **engine-side**
(events.jsonl / HITL records), not under this artifact id.

**Example (validates against schemas/output.json):**

```json
{
  "verdict": "pass",
  "persona_findings": [],
  "execution": {"mode": "replay", "target_source": "reference-corpus"},
  "audit_id": "4ca20e80-8ebd-58bd-a8ff-67f433ed5986"
}
```

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| VB-01 | live mode: no context / no authorization_ref / target unreachable | `needs-input` (no fabricated pentest) | human supplies the authorized context |
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
uphold a `fail`. The skill never auto-approves. The human decision and the named
reviewer are recorded **engine-side** (the gate's HITL record + `events.jsonl`) —
NOT inside this artifact, whose `audit_id` identifies the pentest evidence only.

## References

| Need | Reference |
|------|-----------|
| Threat-persona roster, OWASP + chaos scenarios, evidence discipline, advisory verdict, human gate | `references/adversarial-pentest.md` |
