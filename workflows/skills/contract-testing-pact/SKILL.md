---
name: contract-testing-pact
version: 0.1.0
description: >
  Run consumer-driven contract tests with Pact in a sandbox via the CI/test runner,
  verify the provider against each consumer contract, query the Pact Broker
  can-i-deploy gate, and emit a runner-backed PASS, FAIL, or ERROR verdict that feeds
  a human verification layer. Use when asked to run Pact contract tests, verify a
  provider against its consumer pacts pre-merge, check can-i-deploy before promoting
  a release, or produce the contract pass/fail gate with evidence. Routes failures to
  a fixer rather than fixing them. Do NOT use to author the API contract (use
  befe-contract-design). Do NOT use to implement provider or consumer code. Do NOT
  use to run unit, integration, or e2e levels (use the dedicated execution skills).
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: n/a, audit_level: detailed, pii_handling: none, tier_default: T2, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
expected_duration_p95_seconds: 360
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Contract Testing with Pact

## Purpose

Run **consumer-driven contract tests** (CDCT) with Pact and emit a runner-backed
sign-off gate. This is the contract-level execution stage: it verifies the provider
against each consumer pact in a sandbox via the CI/test runner, queries the Pact
Broker `can-i-deploy` — the final gate that confirms every consumer contract is
verified before a deploy — and hands the verdict to a human verification layer. It
never authors the API contract and never implements code; an unverified pact is a
fail, not a pass.

## When to use this skill

- Use when: consumer pacts exist and the provider must be verified against them
  pre-merge, or `can-i-deploy` must be checked before promoting a release.
- Use when: asked to "run Pact contract tests", "verify the provider against its
  pacts", or "check can-i-deploy".
- Do NOT use: to author the API contract (`befe-contract-design`), to implement
  provider or consumer code, or to run unit/integration/e2e levels (the dedicated
  execution skills).

## Input contract

Validate against `schemas/input.json`. Required: `pacts` (the consumer contracts),
`provider_ref` (the provider to verify), `environment` (the deploy environment for
the can-i-deploy query), `idempotency_key`. Optional: `tier`. Stop with
`needs-input` if there are no pacts, no provider, or no environment.

## Procedure

1. **Resolve pacts and provider** (`references/pact-cdct.md`): load `pacts` and
   `provider_ref`. Entry: consumer contracts + a provider + an environment. Exit:
   a runnable verification set.
2. **Verify the provider** against each consumer pact through the CI/test runner
   in the sandbox — never an LLM-asserted pass. Record per-pact `verified`.
3. **Query can-i-deploy.** Ask the Pact Broker whether `provider_ref` can deploy
   to `environment`; this is the final gate confirming all consumer contracts are
   verified. Record `can_i_deploy`.
4. **Apply the gate:** `PASS` only when ALL pacts verify AND `can_i_deploy` is
   true; `FAIL` if any pact is unverified, `can_i_deploy` is false, or a result is
   masked/uncertain; `ERROR` if verification or the broker query could not run.
5. **Emit** the verdict (Output contract). Stop — failures route to a fixer; the
   gate feeds a **human verification layer**, never auto-approves.

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR),
`provider_verified` (boolean), `pacts[]{consumer,verified}`, `can_i_deploy`
(boolean), and `audit_id`.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| PC-01 | no pacts / provider / environment | no verdict | needs-input → human-queue |
| PC-02 | verification or broker query cannot run | `ERROR` | human-queue |
| PC-03 | a consumer pact is unverified | `FAIL` + pacts[] | route to progressive-bug-hunter |
| PC-04 | can-i-deploy is false | `FAIL` + can_i_deploy=false | block → human-queue |
| PC-05 | masked/uncertain verification result | `FAIL` | flag for human verification |

## Constraints

- DO NOT author the API contract or implement provider/consumer code — verify only.
- DO NOT emit a pass not backed by runner results; uncertain is a fail (banking).
- DO NOT pass when can-i-deploy is false; the broker gate is authoritative.
- DO NOT auto-approve; the gate feeds a named human verification layer.
- DO NOT run outside the sandbox or reach the network beyond the broker/provider.
- DO NOT echo real PII in pacts or logs; redact as [PII:REDACTED:CLASS=...].

## References

| Need | Reference |
|------|-----------|
| Pact CDCT verification, provider verification, can-i-deploy broker gate, gate policy, human layer | `references/pact-cdct.md` |
