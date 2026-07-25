---
name: contract-testing-pact
version: 0.2.0
description: Run consumer-driven contract tests with Pact in a sandbox via the CI/test runner, verify the provider against each consumer contract, query the Pact Broker can-i-deploy compatibility check, and emit a PASS, FAIL, or ERROR verdict with honest execution provenance (runner vs replay). Use when asked to run Pact contract tests, verify a provider against its consumer pacts pre-merge, check can-i-deploy before promoting a release, or produce the contract pass/fail gate with evidence. On failure the stage retries once, then parks in the contract-test-failures human queue. Do NOT use to author the API contract (use befe-contract-design). Do NOT use to implement provider or consumer code. Do NOT use to run unit, integration, or e2e levels (use the dedicated execution skills).
stage_type: validate
input_schema: schemas/input.json
output_schema: schemas/output.json
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: detailed, pii_handling: redact, tier_default: T2, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution, sandbox_network_access]
expected_duration_p95_seconds: 360
max_retries_recommended: 1
fallback: human-queue
compatibility: claude-code, codex, opencode
---

# Contract Testing with Pact

## Purpose

Run **consumer-driven contract tests** (CDCT) with Pact and emit the T5 gate with
honest execution provenance. This is the contract-level execution stage: it
verifies the provider against each consumer pact in a sandbox via the CI/test
runner and queries the Pact Broker `can-i-deploy` — a **compatibility result that
feeds the release decision, not release authorization** (T5 is leaf evidence; it
does not order or block release-handoff by itself). It never authors the API
contract and never implements code; an unverified pact is a fail, not a pass.
In replay (no runner bound) the artifact proves the contract, not a runner-backed
verification, and says so via `execution.mode`.

## When to use this skill

- Use when: consumer pacts exist and the provider must be verified against them
  pre-merge, or `can-i-deploy` must be checked before promoting a release.
- Use when: asked to "run Pact contract tests", "verify the provider against its
  pacts", or "check can-i-deploy".
- Do NOT use: to author the API contract (`befe-contract-design`), to implement
  provider or consumer code, or to run unit/integration/e2e levels (the dedicated
  execution skills).

## Input contract

ADVISORY — documents the assembled stage input; the engine validates workflow input
and stage OUTPUTS only (engine/validation.py). Validate against `schemas/input.json`.
Required: `contract_spec` + `fe_state_binding` (structured objects from
contract-design), `files_generated`, `idempotency_key` (engine-injected).
FLAT-MERGE COLLISION: both implementation stages supply `files_generated` and the
engine merges last-writer-wins — **the top-level field is the frontend manifest
only**; load both manifests via `upstream_artifacts["backend-implement"]` and
`upstream_artifacts["frontend-implement"]`. Optional: `contract_test_context`
(workflow-supplied runner context: pact_refs, provider_ref, environment,
broker_profile_ref). In live runner mode with no `contract_test_context`, stop
`needs-input` — broker/environment identity cannot be safely derived from contract
prose or file manifests.

**Example (validates against schemas/input.json):**
```json
{
  "contract_spec": { "summary": "OpenAPI 3.1 per context.", "documents": [] },
  "fe_state_binding": { "summary": "4-state binding.", "states": {} },
  "files_generated": [{ "path": "src/api/types.gen.ts" }],
  "idempotency_key": "3f6c0b2e-7a41-4d9b-9c2a-8e5b1f0a4d22"
}
```

## Output contract

Validate against `schemas/output.json`: `verdict` (PASS|FAIL|ERROR),
`provider_verified`, `pacts[]{consumer,verified}` (runner mode adds per-pact
`pact_ref`/`result_ref`/`content_hash`), `can_i_deploy` (a compatibility result,
not release authorization), `execution{mode: runner|replay}` (runner mode must
carry `provider_ref`, `environment`, `broker_evidence`), optional `errors[]`
(required non-empty for ERROR), and `audit_id` — producer-stamped, deterministic:
UUIDv5(HOUSE_NS, "contract-tests:{idempotency_key}") with HOUSE_NS =
uuid5(NAMESPACE_URL, "https://squad-delivery/audit"). Schema-enforced invariants:
PASS requires provider verified + broker true + every pact verified; FAIL requires
an unverified pact or a false broker result; null results only under ERROR.

**Example (validates against schemas/output.json):**
```json
{
  "verdict": "PASS",
  "provider_verified": true,
  "pacts": [{ "consumer": "web", "verified": true }],
  "can_i_deploy": true,
  "execution": { "mode": "replay" },
  "audit_id": "3e1410c9-be4c-5f6d-9034-e2335714c6a2"
}
```

## Procedure

1. **Resolve the verification set** (`references/pact-cdct.md`): pact refs,
   provider, and environment come from `contract_test_context`; the contract
   documents come from `contract_spec.documents[]`; load BOTH implementation
   manifests via `upstream_artifacts`. Entry: context + contracts. Exit: a
   runnable verification set (or `needs-input` in live mode without context).
2. **Verify the provider** against each consumer pact through the CI/test runner
   in the sandbox — never an LLM-asserted pass. Record per-pact `verified` plus
   runner-mode evidence refs and hashes.
3. **Query can-i-deploy.** Ask the Pact Broker whether the provider can deploy to
   the target environment; record `can_i_deploy` as a compatibility result.
4. **Apply the gate:** `PASS` only when ALL pacts verify AND `can_i_deploy` is
   true; `FAIL` if any pact is unverified, `can_i_deploy` is false, or a result is
   masked/uncertain; `ERROR` (with `errors[]`) if verification or the broker query
   could not run.
5. **Emit** the verdict (Output contract). Stop — per the configured gate: `PASS`
   completes automatically; failures exhaust one retry and park in the
   `contract-test-failures` queue for named-human resolution.

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| PC-01 | live mode without contract_test_context | no verdict | needs-input → human-queue |
| PC-02 | verification or broker query cannot run | `ERROR` + errors[] | retry ×1 → contract-test-failures queue |
| PC-03 | a consumer pact is unverified | `FAIL` + pacts[] | retry ×1 → contract-test-failures queue |
| PC-04 | can-i-deploy is false | `FAIL` + can_i_deploy=false | retry ×1 → contract-test-failures queue |
| PC-05 | masked/uncertain verification result | `FAIL` | retry ×1 → contract-test-failures queue |

## Constraints

- DO NOT author the API contract or implement provider/consumer code — verify only.
- DO NOT emit a pass not backed by runner results; uncertain is a fail (banking).
- DO NOT pass when can-i-deploy is false; within this gate the broker result is
  authoritative — but it is compatibility evidence, never release authorization.
- DO NOT claim runner-backed verification without a bound runner —
  `execution.mode` must say `replay` when replaying corpus evidence; failures
  need a named human in the queue, PASS completes automatically.
- DO NOT run outside the sandbox or reach the network beyond the broker/provider.
- DO NOT echo real PII in pacts or logs; redact as [PII:REDACTED:CLASS=...].

## References

| Need | Reference |
|------|-----------|
| Pact CDCT verification, provider verification, can-i-deploy broker gate, gate policy, human layer | `references/pact-cdct.md` |
