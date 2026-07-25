# SAST gate — in-house vuln classes, secrets hard-fail, new-vs-baseline gating

SAST (static application security testing) analyzes source **without running it**
to find the vulnerabilities the team wrote in-house: an injection in a hand-built
query builder, a missing authorization check (BOLA/IDOR), or a secret committed to
the tree. It is the complement of dependency scanning — SAST finds flaws in *your*
code; SCA (see `scanning-appsec-pipeline-gate`) finds known CVEs in the code you
imported. This gate runs pre-merge in CI on real scanner output, never on model
guesses, because AI-generated code raises exactly the in-house-vuln risk this gate
exists to catch.

## In-house vulnerability classes

- **Injection** — untrusted input flowing into a query, command, or template
  (e.g. SQL injection in a hand-rolled query builder). SAST is well suited to
  catching these data-flow sinks in your own code.
- **Broken object-level authorization (BOLA/IDOR)** — an endpoint that returns or
  mutates a resource without checking the caller owns it. A logic flaw a scanner
  flags by pattern; confirm intent before accepting.
- **Hardcoded secrets** — credentials, tokens, or keys embedded in source.

## Secrets are always a hard fail

A detected secret is a hard fail regardless of baseline — secrets are never
accepted tech-debt. Redact any matched value as `[PII:REDACTED:CLASS=...]` before
recording it; never echo the raw secret into findings, logs, or the receipt. After
the gate fails, the fixer rotates the credential and removes it from history.

- Source note: Secrets leakage in AI workflows (research-vault literature; not tracked in this repo)
- Source note: AI-generated code risk (research-vault literature; not tracked in this repo)

## New-vs-baseline gating

Security policies typically **block on critical / new findings and allow
pre-existing baseline tech-debt** so a large legacy backlog does not freeze every
merge. Diff scanner output against the baseline: pre-existing findings do not
block; **new** findings at or above `severity_floor` (default `high`) do. This is
the standard pipeline pattern — a SAST + SCA security gate in CI that fails the
build on new high/critical issues.

- Web: docs.gitlab.com (SAST) · infosecwriteups.com (DevSecOps SAST+SCA gate)
- Source note: Code Review Capability (research-vault literature; not tracked in this repo)

## Gate policy (banking default)

- `ERROR` — a scanner could not run or its output was unparseable.
- `FAIL` — `secrets` non-zero (hard), OR any NEW finding at or above
  `severity_floor`, OR results are masked/uncertain (uncertain → fail).
- `PASS` — zero secrets and zero new findings at or above the floor on real
  scanner evidence; pre-existing baseline findings are noted, not blocking.

## Human verification layer

The verdict **feeds a named human** sign-off; this skill never auto-approves.
Findings route to a fixer — this gate diagnoses and reports, it does not edit
code. Scanning a running app (DAST) and dependency CVEs (SCA) belong to
`scanning-appsec-pipeline-gate`; adversarial red-teaming belongs to
`validating-banking-implementation`.

## Sources

- AI-generated code risk (research-vault literature; not tracked in this repo)
- Secrets leakage in AI workflows (research-vault literature; not tracked in this repo)
- AI use in vulnerability discovery (research-vault literature; not tracked in this repo)
- Code Review Capability (research-vault literature; not tracked in this repo)
- Web: docs.gitlab.com · infosecwriteups.com · owasp.org
