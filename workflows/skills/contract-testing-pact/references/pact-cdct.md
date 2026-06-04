# Pact CDCT — provider verification, can-i-deploy broker gate, gate policy

Grounded in the ResearchVault: agentic CI/CD relies on consumer-driven contract
tests to keep services compatible across independent deploys. Pact records each
consumer's expectations, the provider is verified against them, and the Pact
Broker's `can-i-deploy` is the final gate. The runner and the broker are the
source of truth; the agent reports real results, never a self-claimed pass.

## Provider verification

Load `pacts` (consumer contracts) and `provider_ref`. Replay each consumer's
expected interactions against the provider through the CI/test runner in the
sandbox. Record per-pact `verified`. `provider_verified` is true only when every
consumer pact verifies.

## can-i-deploy: the final broker gate

`can-i-deploy` is the Pact Broker query that confirms ALL consumer contracts are
verified for a given application version before it is promoted to an environment.
It is the authoritative pre-deploy gate: even if a local verification looks green,
a false `can_i_deploy` blocks the gate. Query the broker for `provider_ref` and
`environment`; record the boolean result.

- Web: docs.pact.io (can-i-deploy and provider verification)

## Gate policy (banking default)

- `ERROR` — verification or the broker query could not run.
- `FAIL` — any consumer pact is unverified, `can_i_deploy` is false, OR a result
  is masked/uncertain (uncertain is a fail in regulated contexts).
- `PASS` — ALL pacts verify AND `can_i_deploy` is true, on real runner/broker
  evidence.

## Human verification layer

The verdict feeds a named human sign-off; this skill never auto-approves. Failures
route to `progressive-bug-hunter` for diagnosis — the executor does not fix code,
and it never authors the contract (`befe-contract-design` owns that).

## Sources

- [[literature/agent-orchestration/agentic-cicd|Agentic CI/CD]]
- [[literature/agent-orchestration/autonomous-qa-agents|Autonomous QA agents]]
- Web: docs.pact.io (can-i-deploy, provider verification) · oneuptime.com
