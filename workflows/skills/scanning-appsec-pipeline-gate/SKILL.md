---
name: scanning-appsec-pipeline-gate
version: 0.2.1
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
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: detailed, pii_handling: redact, tier_default: T1, tier_adaptable: [T1, T2, T3]}
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

`schemas/input.json` is **ENFORCED** — the engine validates the ASSEMBLED payload
against it before this stage runs (fail-closed, exactly like output validation);
it documents the POST-adapter payload assembled at stage `appsec-scan`. Required: `files_generated` and the engine-injected
`idempotency_key`. **Collision (documented):** `files_generated` is picked from
BOTH implement stages and the engine merges last-writer-wins — the top-level
field is the FRONTEND manifest only. It is a hint, never the enumeration
source: resolve BOTH full artifacts via
`upstream_artifacts["backend-implement"/"frontend-implement"]` and scan the
union. (A per-producer nested shape is reserved for a future contract.)

Optional: `appsec_scan_context` from the workflow input — the runner context
(`target_ref`, `target_kind: ci-sandbox|sit-sandbox`, `build_ref`, `sbom_ref`,
`severity_floor`, nullable `baseline_ref`, scanner profile refs; all
non-secret). Live runner mode without a context — or without a resolvable
SBOM — is `needs-input`: the integrated gate cannot certify zero
known-exploited CVEs without SCA evidence. Replay needs no context. Optional
engine-injected: `upstream_artifacts`, `loop_back_feedback`.

**Example (validates against schemas/input.json):**

```json
{
  "files_generated": [{"path": "src/features/checkout/CheckoutForm.tsx", "content_hash": "9b12f1e6c56c1e00c4f4f4a1a5c9b8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1", "size_bytes": 6212, "lines_added": 188}],
  "appsec_scan_context": {"target_ref": "sit-shoppilot-web", "target_kind": "sit-sandbox", "build_ref": "build-2026-07-12-001", "sbom_ref": "sboms/shoppilot-2026-07-12.spdx.json", "severity_floor": "high"},
  "idempotency_key": "req-2026-07-12-shoppilot-001"
}
```

## Procedure

1. **Resolve the target** (`references/appsec-dast-sca.md`): from
   `appsec_scan_context`, confirm `target_ref` is reachable in the sandbox and
   `sbom_ref` resolves; never attack outside the sandboxed environment. Entry:
   the context + both resolved implement artifacts. Exit: a scannable target.
2. **Run DAST** against the running app from outside, collecting real scanner
   output. Findings come from the scanner, never a model guess; a crashed or
   unreachable scan is `ERROR`, not a silent pass.
3. **Run SCA** over the SBOM at `sbom_ref`: match imported dependencies to known
   CVEs and mark any flagged as **known-exploited** (actively exploited in the
   wild). A failed or skipped SCA can never PASS — PASS requires
   `execution.scanners.sca.status: completed`.
4. **Sweep for secrets** across the build/image. A detected secret is **always a
   hard fail**; redact any matched value as [PII:REDACTED:CLASS=...] before
   recording it.
5. **Gate new vs baseline.** Pre-existing accepted findings do not block; **new**
   findings at or above the context severity floor do — each carries
   `gate_status: blocking`; per-scanner counts land in
   `new_vs_baseline.{dast,sca}` as `{new, accepted, fixed}`.
6. **Apply the gate:** `FAIL` if `secrets` is non-zero OR any known-exploited CVE
   is present OR any new finding is at or above `severity_floor`; `ERROR` if a
   scanner could not run; else `PASS`. Banking default: uncertain → fail.
7. **Emit** the verdict with execution provenance (Output contract): `execution`
   records `runner` (real scans: evidence_ref + report_sha256) vs `replay`
   (byte-verbatim reference corpus — no scanner ran) plus per-scanner
   `scanners.{dast,sca,secrets}.status`. Stop — this is an **automatic machine
   gate**: PASS completes the leaf; FAIL/ERROR retry once and then enter the
   named-human queue for RESOLUTION. AppSec evidence is not release
   authorization.

## Output contract

Validate against `schemas/output.json`. Required: `verdict` (PASS|FAIL|ERROR),
`dast_findings[]` (each with `fingerprint`, `rule_id`, `gate_status`
blocking|advisory, non-secret `target`, `baseline_status`, `evidence_ref`),
`sca_cves[]` (each with `package`, `gate_status`, plus version/fix data),
`secrets` (count), `new_vs_baseline{dast,sca}{new,accepted,fixed}`, `execution`
(with per-scanner statuses), and `audit_id`. Optional: `blocking_reasons[]`,
`errors[]` (required non-empty on ERROR), `secret_findings[]` (fingerprint +
detector + location ONLY — the matched value is never emitted).

Conditionals: PASS ⇒ secrets 0 ∧ all three scanners completed ∧ no blocking
finding; secrets > 0 ⇒ FAIL + secret_findings; ERROR ⇒ non-empty errors.

`audit_id` (live): `UUIDv5(HOUSE_NS, "appsec-scan:{idempotency_key}")`,
`HOUSE_NS = uuid5(NAMESPACE_URL, "https://squad-delivery/audit")` — distinct
from the engine's per-attempt audit id; corpus ids grandfathered.

**Example (validates against schemas/output.json):**

```json
{
  "verdict": "PASS",
  "dast_findings": [],
  "sca_cves": [],
  "secrets": 0,
  "new_vs_baseline": {"dast": {"new": 0, "accepted": 0, "fixed": 0}, "sca": {"new": 0, "accepted": 0, "fixed": 0}},
  "execution": {"mode": "replay", "target_source": "reference-corpus", "scanners": {"dast": {"status": "completed"}, "sca": {"status": "completed"}, "secrets": {"status": "completed"}}},
  "audit_id": "85b67b51-29d2-5edb-b66e-76acb879b8f0"
}
```

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| AP-01 | live runner mode: context/SBOM missing or target unreachable | `needs-input` (no fabricated scan) | human supplies the context |
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
- The gate is an automatic machine gate; a named human resolves FAILURES — do
  not claim per-verdict human sign-off, and never treat PASS as release
  authorization.
- DO NOT echo real PII or secrets; redact as [PII:REDACTED:CLASS=...].
- DO NOT attack any target outside the sandboxed environment.

## References

| Need | Reference |
|------|-----------|
| DAST attack model, SCA known-CVE matching, secrets sweep, new-vs-baseline gating, human layer | `references/appsec-dast-sca.md` |
