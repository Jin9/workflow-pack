---
name: roundtripping-dashboard-data-contract
version: 1.1.0
description: >
  Edit the squad-delivery dashboard's data model through a validated JSON contract instead of
  hand-editing its gzip+base64 bundle. Use when the user asks to "change a dashboard stage, gate,
  owner, or tier", "update the dashboard skill map or tests", "add a stage to the dashboard",
  "regenerate the squad-delivery dashboard bundle", or "extract the dashboard data to JSON". The
  skill extracts the DATA module into dashboard-data.json, validates edits against a JSON Schema
  plus cross-reference and offline rules, and splices a deterministically re-gzipped module back
  into the standalone HTML, leaving the render module and fonts byte-identical. Do NOT use to
  change the dashboard's visual rendering, layout, or CSS (that is the render module), to author
  pipeline stage skills under workflows/skills, or to edit the workflow YAMLs or boundary schemas.
input_schema: schemas/dashboard-data.schema.json
output_schema: schemas/dashboard-data.schema.json
compatibility: claude-code; requires python3 (with jsonschema) and node
---

# Roundtripping the dashboard data contract

## Purpose

Make the squad-delivery dashboard's data model safely editable: lift it out of the
gzip+base64 bundle into one authoritative `dashboard-data.json`, edit and validate that, then
deterministically regenerate the bundle from it.

## When to use this skill

- Use when: the user wants to change dashboard **data** — a stage's fields, gate, owner, model,
  tier; the `events`/`templates` lookup tables; `json_only`; `tests`; or the `skillmap`.
- Use when: the user asks to regenerate the bundle from the contract, or to extract the contract
  from the bundle.
- Do NOT use when: the change is to the dashboard's **rendering/layout/CSS** (that lives in the
  render module `c022aabb`, out of scope), or the user wants to edit pipeline skills, workflow
  YAMLs, or boundary schemas.

The bundle format, the DATA module's structure, and the load-time merge are documented in
`references/bundle-format.md`. Read it before a non-trivial edit.

## Input contract

This is a tooling skill: `schemas/dashboard-data.schema.json` governs **both directions** —
build input (the edited contract) and extract output (the lifted contract). There is **no
boundary schema, YAML pin, adapter payload, engine-injected key, or audit_id**; the HTML output
has byte-level invariants (below), not a JSON schema.

- **build/check/verify:** requires `dashboard-data.json` (strict UTF-8 JSON: duplicate object
  keys and `NaN`/`Infinity` are rejected with a clean nonzero exit and no writes) and the bundle
  HTML. `events` and `templates` keys must **equal** the `stages[].id` set — exactly one entry
  per stage in each; `json_only` entries are unique stage ids (duplicates would silently dedupe
  through the JS `Set` and break the lossless round-trip).
- **extract:** requires the bundle HTML. **Trust contract:** extraction EXECUTES the DATA module
  with node (`vm.runInContext` is not a security boundary) — only the known, workspace-owned
  dashboard bundle is acceptable input; an external or untrusted bundle is a STOP condition. The
  evaluation is bounded (120 s); a non-terminating module fails cleanly.
- **Prerequisites:** python3 with `jsonschema`; node on PATH. Working directory = the repository
  root (default paths resolve there); scripts are invoked via `$SKILL_DIR` (the directory
  containing this `SKILL.md`).
- **Sensitivity precondition:** the contract data must already be redacted and secret-free.
  `build` embeds every value into the bundle and `extract` reproduces every value in JSON — both
  outputs inherit the source's sensitivity and **neither script sanitizes PII or secrets**.
  Suspected sensitive content ⇒ stop and request a redacted input.
- **Stop conditions:** `--out`/`--data` resolving to the bundle itself (exit 2 — the write would
  destroy it); an existing non-default `--out` without `--force`; non-strict JSON; untrusted
  bundle; node unavailable.

## Output contract

- `dashboard-data.json` — the authoritative contract (workspace root), schema-valid.
- `squad-delivery-dashboard.standalone.html` — regenerated bundle where **only** the `c7f43bda`
  entry's `data` value changes; the render module and all 15 fonts stay byte-identical. All
  writes are atomic (temp sibling + replace): a nonzero exit leaves existing files unchanged.
- Modes: `extract.py` (bundle → JSON) · `build.py --check` (validate only) · `build.py --verify`
  (read-only: validate AND assert the bundle matches the contract — the drift check) ·
  `build.py` (JSON → bundle splice).
- **"Validation passed" proves ONLY** the dashboard schema, internal key rules, and offline-token
  rules. It does **not** prove workflow-stage parity, that referenced skills/versions/paths
  exist, or production readiness. When stage/test/skillmap entries changed, run the read-only
  comparison of step 6 and hand off the diagram refresh.

## Procedure

1. **Locate the artifacts.** The bundle is `squad-delivery-dashboard.standalone.html` and the
   contract is `dashboard-data.json`, both at the workspace root. The schema ships in this skill
   at `schemas/dashboard-data.schema.json`. Run from the repository root.
2. **Bootstrap or refresh the contract** (only if `dashboard-data.json` is missing or the bundle
   is the newer truth): `python3 "$SKILL_DIR/scripts/extract.py"`. This decodes the DATA module,
   evaluates it with `emit_data.js` (bounded), strips the merge-derived keys, and atomically
   writes `dashboard-data.json` (7 top-level keys: `tier, stages, events, templates, json_only,
   tests, skillmap`). To compare without touching the contract, extract to a separate candidate
   path: `--out <candidate> [--force]`.
3. **Edit `dashboard-data.json`.** Keep stages **raw** — never add `consumes/emits/sdlc/template/
   fmt/jsonOnly` to a stage; edit `events`/`templates`/`json_only` instead. One `events` and one
   `templates` entry per stage, exactly. Use bare host text for any citation (no live URLs).
4. **Validate:** `python3 "$SKILL_DIR/scripts/build.py" --check`. Fails on schema violations,
   duplicate stage ids, `events`/`templates` keys not **equal** to the stage-id set (both
   missing and unknown entries are reported), non-unique or unknown `json_only` entries, or any
   forbidden URL token. Fix and re-run until it passes.
5. **Regenerate the bundle:** `python3 "$SKILL_DIR/scripts/build.py"`. Validates again, renders
   the DATA module (7 consts + the 3 verbatim merge statements), re-gzips with `mtime=0`, and
   atomically splices only the `c7f43bda` entry.
6. **Cross-check the repo (read-only) when stages/tests/skillmap changed:** compare the edited
   entries against `workflows/delivery-pipeline.yaml` and `workflows/skills/` (stage ids, skill
   names, pinned versions) and surface any divergence to the user — schema validity is not
   repo synchronization. If stage structure changed, hand off a `delivery-pipeline-flow.drawio`
   refresh (or state explicitly that the diagram is now stale). Never read the sibling archive.
7. **Verify** (see the checklist) before declaring done.

## Constraints

- DO NOT hand-edit the base64 in the bundle, or touch the render module (`c022aabb`) or font
  entries.
- DO NOT add merge-derived keys to a stage in the contract; they are regenerated by `MERGE_JS`.
- DO NOT introduce live URLs (`https://`, `http://`, `src=`, `@import`, `url(`) into any contract
  string — the dashboard must stay offline. (`http://www.w3.org/...` XML namespaces in the
  untouched template wrapper are fine.)
- DO NOT use a re-extract over the edited contract as a "drift check" — that overwrite destroys
  the edits; the drift check is `build.py --verify` (read-only) or an extract to a candidate path.
- MUST ALWAYS run `build.py --check` and fix all findings before writing the bundle.
- MUST ALWAYS keep the build deterministic: gzip with `mtime=0`; no timestamps or randomness.

## Examples

### Example 1: Change a stage owner

**User says**: "Change the S2 stage owner on the dashboard to 'Platform TL'."

1. Edit the `stages[]` entry with `"id": "S2"`, set `"owner": "Platform TL"`.
2. `python3 "$SKILL_DIR/scripts/build.py" --check` then `python3 "$SKILL_DIR/scripts/build.py"`.
3. `python3 "$SKILL_DIR/scripts/build.py" --verify` — in sync.

**Result**: Bundle regenerated with the new owner; render module and fonts unchanged.

### Example 2: Add an event for a new stage

**User says**: "Wire the new S8 stage's event flow into the dashboard."

1. Add the raw stage to `stages[]` AND a matching `events["S8"]` entry (`consumes`, `emits`,
   `sdlc`) AND `templates["S8"]` — the checker enforces one entry per stage in both tables.
2. `python3 "$SKILL_DIR/scripts/build.py" --check` then `python3 "$SKILL_DIR/scripts/build.py"`.
3. Step 6 cross-check: does S8 exist in `workflows/delivery-pipeline.yaml`? If the pipeline has
   no S8, surface that divergence; if stage structure changed, flag the drawio refresh.

**Result**: At load the merge folds `events["S8"]` into the S8 stage; the dashboard renders it.

## Validation checklist

Before finalizing:
- [ ] `build.py --check` passes (schema + cross-reference + offline gates).
- [ ] `node --check` on the decoded DATA module passes.
- [ ] `build.py --verify` reports in-sync (read-only drift check — never re-extract over edits).
- [ ] Only the `c7f43bda` manifest entry changed; the render entry and 15 fonts are byte-identical.
- [ ] A second `build.py` reproduces the byte-identical bundle (determinism).
- [ ] Changed stage/test/skillmap entries cross-checked against the workflow YAML + skills
      (read-only); drawio refresh handed off or staleness stated.

## References

- For the bundle format, DATA module layout, and the load-time merge: see
  `references/bundle-format.md`.
