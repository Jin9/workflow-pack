---
name: running-sast-security-gate
version: 0.2.0
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
banking_grade: {idempotent: true, reversible: not-applicable, audit_level: detailed, pii_handling: redact, tier_default: T1, tier_adaptable: [T1, T2, T3]}
requires_capabilities: [code_execution]
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

`schemas/input.json` is **ENFORCED** — the engine validates the ASSEMBLED payload
against it before this stage runs (fail-closed, exactly like output validation);
it documents the POST-adapter payload assembled at stage `sast-gate`. Required: `files_generated` (the backend-implement manifest — what
there is to scan) and the engine-injected `idempotency_key`. Optional
engine-injected: `upstream_artifacts`, `loop_back_feedback`. Manifest paths
resolve relative to the directory containing
`upstream_artifacts["backend-implement"]`. The gate policy (severity floor,
baseline mode/ref) is emitted in the output `policy` record — it is never a
caller-supplied suppression knob. An unusable manifest produces NO artifact and
follows the stage failure policy (retry once, then the named-human queue) —
there is no needs-input output shape.

**Example (validates against schemas/input.json):**

```json
{
  "files_generated": [{"path": "services/checkout/app/checkout/service.go", "content_hash": "9b12f1e6c56c1e00c4f4f4a1a5c9b8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1", "lines_added": 214}],
  "idempotency_key": "req-2026-07-12-shoppilot-001"
}
```

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
4. **Gate new vs baseline.** Diff scanner findings against the baseline: every
   CURRENT finding is `new` or `existing` (its `baseline_status`); `fixed` counts
   baseline findings absent from this scan (they appear only in
   `new_vs_baseline`, never as current findings). Pre-existing findings do not
   block; **new** findings at or above the policy severity floor do — each gets
   `blocking: true` and a `blocking_reasons[]` entry.
5. **Apply the gate:** `FAIL` if `secrets` is non-zero OR any new finding is at or
   above `severity_floor`; `ERROR` if a scanner could not run; else `PASS`.
   Banking default: a masked or uncertain result is a fail, not a pass.
6. **Emit** the verdict with execution provenance (Output contract): `execution`
   records `runner` (a real scan: scanner name/version + evidence_ref +
   report_sha256) vs `replay` (byte-verbatim reference corpus — **no scanner
   ran**), and `scan_scope.targets_scanned` records coverage. Stop — this is an
   **automatic machine gate**: PASS completes the leaf stage; an execution or
   schema failure retries once and then enters `sast-gate-failures` for a named
   human to RESOLVE. PASS is evidence, not release authorization.

## Output contract

Validate against `schemas/output.json`. Required: `verdict` (PASS|FAIL|ERROR),
`findings[]` (each with stable `fingerprint`, `baseline_status: new|existing`,
`blocking`; summaries redact matched values as `[PII:REDACTED:CLASS=...]`),
`secrets` (count), `new_vs_baseline{new,existing,fixed}`,
`policy{severity_floor,baseline_mode,baseline_ref}` (the machine-auditable gate
policy this decision applied), `blocking_reasons[]` (why the gate blocked; empty
on PASS), `execution`, `scan_scope`, and `audit_id`. Optional: `errors[]`
(required non-empty on ERROR).

Conditionals enforce the matrix: PASS ⇒ zero secrets ∧ no blocking finding ∧ no
blocking reasons; FAIL ⇒ ≥1 blocking reason; secrets > 0 ⇒ FAIL; ERROR ⇒
non-empty errors.

`audit_id` (live): `UUIDv5(HOUSE_NS, "sast-gate:{idempotency_key}")`,
`HOUSE_NS = uuid5(NAMESPACE_URL, "https://squad-delivery/audit")` — distinct
from the engine's per-attempt audit id; reference-corpus ids are grandfathered.

**Example (validates against schemas/output.json):**

```json
{
  "verdict": "PASS",
  "findings": [],
  "secrets": 0,
  "new_vs_baseline": {"new": 0, "existing": 0, "fixed": 2},
  "policy": {"severity_floor": "medium", "baseline_mode": "baseline-aware", "baseline_ref": null},
  "blocking_reasons": [],
  "execution": {"mode": "replay", "target_source": "reference-corpus"},
  "scan_scope": {"targets_scanned": 45},
  "audit_id": "dc6f4fbd-e9a4-526a-b332-7fa4aeac34ee"
}
```

## Failure modes

| Code | Condition | Output | Escalation |
|---|---|---|---|
| SS-01 | manifest unresolvable / unusable | NO artifact (stage failure) | retry once → sast-gate-failures (named human) |
| SS-02 | scanner crashed / output unparseable | `ERROR` | human-queue |
| SS-03 | secret detected | `FAIL` (hard) | route to a fixer (rotate + remove) |
| SS-04 | new finding at or above severity_floor | `FAIL` + findings[] | route to a fixer |
| SS-05 | only pre-existing baseline findings | `PASS` + note | tracked as accepted tech-debt |

## Constraints

- DO NOT fix, edit, or rewrite code — scan, gate, and route only.
- DO NOT emit a pass not backed by scanner output; uncertain → fail (banking).
- DO NOT block on pre-existing baseline findings; block only on NEW findings at
  or above the policy severity floor. A detected secret is always a hard fail
  regardless of baseline.
- The gate is an automatic machine gate; a named human resolves FAILURES — do
  not claim per-verdict human sign-off, and never treat PASS as release
  authorization.
- DO NOT echo real PII or secrets; redact as [PII:REDACTED:CLASS=...].
- DO NOT run outside the sandbox or reach the network beyond fetching the source.

## References

| Need | Reference |
|------|-----------|
| Static scanner integration, in-house vuln classes, secrets hard-fail, new-vs-baseline gating, human layer | `references/sast-gate.md` |
