# AppSec gate — DAST attack model, SCA known-CVE matching, secrets sweep

This gate scans **what you ship and run**, not the source you wrote. Three real
scanners run together in CI/SIT against a sandboxed target. It complements the
source-level SAST gate (`running-sast-security-gate`): SAST finds the
vulnerabilities you wrote in-house; this gate finds runtime weaknesses and
known-CVE dependency risk in the built artifact. All verdicts come from real
scanner output, never model guesses.

## DAST — automated external attack of the running app

DAST (dynamic application security testing) is the **automated external attack of
the running app**: it probes the deployed service from outside as an attacker
would, exercising live endpoints to surface exploitable runtime behavior a static
read of the source cannot see. Run it only against the sandboxed `target_env`,
never a real production or third-party host.

- Vault: [[literature/ai-threats/ai-use-in-vulnerability-discovery|AI use in vulnerability discovery]]
- Web: owasp.org · oneuptime.com (DAST in the pipeline)

## SCA — known CVEs in dependencies you imported

SCA (software composition analysis) matches the third-party dependencies in the
SBOM against known-CVE databases: **SCA finds known CVEs in the dependencies you
imported**, the supply-chain risk SAST does not cover. Mark any matched CVE that
is **known-exploited** (actively exploited in the wild) — these are always hard
fails regardless of baseline.

- Vault: [[literature/ai-threats/ai-supply-chain-security|AI supply-chain security]]
- Web: docs.gitlab.com (SCA) · infosecwriteups.com (DevSecOps SAST+SCA gate)

## Secrets sweep — always a hard fail

Sweep the build/image for leaked credentials, tokens, and keys. A detected secret
is a hard fail regardless of baseline; redact any matched value as
`[PII:REDACTED:CLASS=...]` before recording it, and never echo a raw secret into
findings or logs. The fixer rotates and removes it.

- Vault: [[literature/ai-threats/secrets-leakage-ai-workflows|Secrets leakage in AI workflows]]

## New-vs-baseline gating

As with the SAST gate, security policies typically **block on critical / new
findings and allow pre-existing baseline tech-debt**, so a legacy backlog does not
freeze every build. Pre-existing baseline findings do not block; new findings at
or above `severity_floor` do. Secrets and known-exploited CVEs override this — they
fail even if somehow present in a baseline.

## Gate policy (banking default)

- `ERROR` — a scanner could not run or its output was unparseable.
- `FAIL` — `secrets` non-zero (hard), OR any known-exploited CVE, OR any NEW
  finding at or above `severity_floor`, OR masked/uncertain results.
- `PASS` — zero secrets, zero known-exploited CVEs, and zero new findings at or
  above the floor on real scanner evidence; baseline findings noted, not blocking.

## Human verification layer

The verdict **feeds a named human** sign-off; this skill never auto-approves.
Findings route to a fixer — this gate scans and reports, it does not remediate.
Static source scanning belongs to `running-sast-security-gate`; adversarial
red-teaming belongs to `validating-banking-implementation`.

## Sources

- [[literature/ai-threats/ai-supply-chain-security|AI supply-chain security]]
- [[literature/ai-threats/secrets-leakage-ai-workflows|Secrets leakage in AI workflows]]
- [[literature/ai-threats/ai-use-in-vulnerability-discovery|AI use in vulnerability discovery]]
- [[literature/capabilities/code-review-capability|Code Review Capability]]
- Web: owasp.org · oneuptime.com · docs.gitlab.com · infosecwriteups.com
