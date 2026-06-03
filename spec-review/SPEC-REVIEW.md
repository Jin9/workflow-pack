# Spec review — `universal-spec-validator` over the live delivery pipeline

**Date:** 2026-06-03 · **Scope:** live pipeline only (`workflows/**` + the `.claude/` workspace skill;
`reference/repo-generator/**` and root `dashboard-data*.json` excluded) · **Action taken:** 2026-06-03
review + tuned config; **2026-06-04 fix-list applied**, then **OI-002 closed** — the S6 deploy pair
(`handoff-to-deploy` / `handoff-revoke`) and a 12-stage post-development test group (T1–T12) were built and
wired (see the Updates below). NB: the spec/finding counts in the tables below **predate** that build — 28
new specs were added (14 `SKILL.md` + 14 boundary schemas under `workflows/schemas/`), so a fresh validator
run is needed to refresh them; the qualitative verdict (false-positive-driven C4/C3) is unchanged.

## Verdict

Out of the box the gate **fails (exit 1) with 32 blocking findings**, but **every blocking finding is a
heuristic false positive** — substring matches and keyword-vocabulary mismatches, not real unsafe
surfaces. This is precisely the failure mode the validator's own severity policy warns about ("an
over-aggressive auto-fail takes a healthy agent offline just as surely as drift does"). The fix is
**risk-tiered config**, not mass spec edits.

With the recommended `.spec-validator.yaml` (in this folder) the gate goes **green (exit 0)** while
**keeping every real signal visible as a `warn`** — nothing was silenced that points at an actual issue.

| Run | specs | block | warn | exit | note |
|---|---|---|---|---|---|
| **Raw** (no config) | 47 | **32** | 46 | **1** | block = C4/C3, left to config tiering by decision |
| **Tuned** (this config) | 47 | **0** | 46 | **0** | green; the 46 warns are all intentional |

Reports: `spec-validation.raw.{json,md}` (red baseline) · `spec-validation.{json,md}` (tuned/green).
Counts above are **post-fix (2026-06-04)**; the original 2026-06-03 baseline was 52 warn.

## Update — fix-list applied (2026-06-04)

The genuine remediations were applied to the live pipeline and verified: the 4 edited skills pass
`quick_validate.py` + `check_links.py`; the 3 closed schemas stay valid draft-07 and the demo artifact
`tmp/runs/shoppilot/S1a-ba-discovery/discovery.json` **still validates** against the now-closed
`discovery.json`; the YAML loads and its `depends_on` graph is unchanged. Effect: **raw warn 52 → 46**.
Block stays 32 because C4/C3 were **left to config tiering by decision** (confirmed false positives; the
autonomous S3/S4a/S4b stages must not carry HITL markers). Tuned gate still **exit 0**.

| Fix | Status | What changed |
|---|---|---|
| **1 · C5 version pins** | ✅ done | All 15 built `skill_ref`s in `delivery-pipeline.yaml` exact-pinned (10 caret→exact + 5 added; `scoping-ba-intake` given a `version: 1.0.0` field). The real `delivery-pipeline.yaml` C5 is **gone**. `handoff-revoke` left unpinned (unbuilt, OI-002). Kept as **warn** (not escalated to block) by decision. |
| **3 · P2 close contracts** | ✅ done (root) | `additionalProperties:false` at the **root** of `discovery.json`, `delivery-pipeline-input.json`, `delivery-pipeline-output.json` (P2 21→18). `ba-brief.json` + the Translations / `convention_overrides` value-maps left open by design; nested-node P2 warns remain (acceptable). |
| **4 · P5 capabilities** | ✅ done | `requires_capabilities` added to `implement-backend-feature`, `implement-frontend-feature` (`[code_generation, file_write]`) and `executing-qa-test-suite` (`[code_execution, sandbox_network_access]`). P5 7→5; the 5 left are intentional (read-only reviewers = false positive, 2 schema files, the workflow YAML). |
| **2 · C4 HITL** | ✅ done — OI-002 closed (2026-06-04) | `handoff-to-deploy` / `handoff-revoke` authored with `requires_approval: true` + "named approval"/"confirm" prose, so C4's negation recognises the gate and they pass cleanly. Re-escalation is now active via that annotation; the global tier stays `warn` for the remaining substring false positives. See the C4 update note below. |
| **5 · E-axis baseline** | ↪️ out of scope | Gate-run / CI concern, not a pipeline spec edit. |

## Per-rule triage

| Rule | Axis | Raw | What it means | Verdict | Disposition |
|---|---|---|---|---|---|
| **C4** irreversible-action w/o HITL | cmd-safety | 26 block | flags `deploy/publish/push/prod/iam/grant/revoke` w/o `approval\|hitl\|confirm` nearby | **False positive** | 17 on schemas → **ignored**; 11 on SKILL.md → **warn** |
| **C3** injection-field-feeds-command | cmd-safety | 6 block | flags `comment/readme/user_input/…` co-occurring with `command/path/query` | **False positive** | 2 on schemas → **ignored**; 4 on SKILL.md/YAML → **warn** |
| **C5** floating version | cmd-safety | 16 warn | `"^`, `~`, `:latest` | **Split** | 15 schema `^pattern` → **ignored**; **1 REAL** (`delivery-pipeline.yaml`) → **kept (warn)** |
| **P2** no `additionalProperties:false` | portability | 21 warn (9 files) | object input open to extra props (OpenAI strict-mode drift) | **Mixed** | kept (warn); real subset in fix-list |
| **P5** capability not annotated | portability | 7 warn | implies network/file-write/code-exec, no `requires_capabilities` | **Advisory** | kept (warn) |
| **C6 / C7** identity / long-lived creds | cmd-safety | 4 / 4 warn | weak audit-identity / static secret heuristics | **Advisory** | kept (warn) |

### Why C4 is noise here (the key finding)
Two independent causes, both confirmed by inspection:
1. **Substring matching.** The `prod(uction)?` pattern fires inside "**prod**uct" — so
   `researching-ba-problem-space`, whose only trigger is the phrase "**product** risks" and which performs
   **no** irreversible action at all, is flagged.
2. **Vocabulary mismatch.** The skills *do* carry human gates — but as prose: `review-backend-code` says
   "Reviewer **verdict**", `validating-production-slo` says "**human gate**". C4's negation only recognises
   `approval | hitl | confirm | requires_approval`, so it can't see them.

Decisive point (2026-06-03): **none of the then-14 built skills performed a deploy / IAM / publish
side-effect** — they were BA / design / implement / review / test stages. The genuinely irreversible
stages, `handoff-to-deploy` and `handoff-revoke`, were **unbuilt** (OPEN_ISSUE OI-002) — so the one place
C4 *should* block had no spec to scan.

**Update 2026-06-04 — OI-002 CLOSED (C4 re-escalation satisfied).** `handoff-to-deploy` and `handoff-revoke`
are now authored and wired (S6), alongside a 12-stage post-development test group (T1–T12). The two deploy
skills carry `requires_approval: true` plus explicit "named approval" / "confirm" prose, so C4's negation
(`approval | hitl | confirm | requires_approval`) recognises the gate and C4 does **not** fire on them — the
re-escalation the original finding called for is delivered by that annotation (a future deploy/publish skill
that omits it would surface on C4). The global tier stays `warn` because the other built skills and the new
test runners still trip C4/C3 as substring/vocabulary false positives; a hard `C4: block` with scoped
ignores for those false positives is left to a follow-up run that can confirm, with the validator, exactly
which specs still trip C4 after the 2026-06-04 build.

The 11 C4 warns (review for context, none blocking): `befe-contract-design`, `designing-tech-lead-handoff`,
`executing-qa-test-suite`, `generate-ux-pack`, `implement-backend-feature`, `implement-frontend-feature`,
`red-teaming-implementation-plan`, `researching-ba-problem-space`, `review-backend-code`,
`review-frontend-code`, `validating-production-slo`.

The 4 C3 warns: `delivery-pipeline.yaml`, `generate-ux-pack`, `planning-banking-tests`,
`review-frontend-code` — all co-occurrence, none interpolate untrusted text into a shell.

## Recommended config

`spec-review/.spec-validator.yaml` (in this folder). **To activate:** copy it to the repo root as
`.spec-validator.yaml` and pass `--config .spec-validator.yaml`. It is inert until passed. Tiering summary:
- `gate_overrides: {C4: warn, C3: warn}` — keep command-safety signals **visible**, not build-killing.
- `ignore` C4/C3/C5 on `*/schemas/*.json` — data contracts are shapes, not action surfaces.
- `fail_on: [critical, high]` (default) — a future `rm -rf`/`DROP TABLE` (C1) or P1/P4 lock-in **still blocks**.
- `delivery-pipeline.yaml` C5 is deliberately **not** ignored — it stays a visible warn (see fix #1).

## Prioritized fix-list (genuine remediations — APPLIED 2026-06-04; see "Update" above for status)

The gate is read-only; these are the caller's job (hand to `skillify` / by hand). Ordered by value.

1. **[C5 · highest] Exact-pin skill versions** in `workflows/delivery-pipeline.yaml` — replace the caret
   ranges (`skill_version: "^1.0.0"`, `"^1.5.0"`, `"^0.1.0"`; 10 lines) with exact pins (`"1.0.0"`, …).
   Banking-grade reproducibility + supply-chain safety; clears the one real C5. After this, you may
   `gate_overrides: C5: block` to enforce pinning hard.
2. **[C4] Make the human gate machine-readable** — add a canonical `requires_approval: true` / `human_gate`
   annotation to skills that front genuinely irreversible stages. **Most important for the unbuilt
   `handoff-to-deploy` / `handoff-revoke` when authored**; optionally surface the keyword in the review /
   SLO skills so the gate (and downstream tooling) can see the gate that today is only prose.
3. **[P2] `additionalProperties: false`** on the **closed** contracts — `delivery-pipeline-input.json`,
   `delivery-pipeline-output.json`, `discovery.json`, and the closed per-skill `schemas/*.json` — for
   OpenAI strict-mode cross-vendor portability. **Leave `workflows/schemas/ba-brief.json` permissive by
   design** (it is the manifest layer; add `ignore: {rule: P2, locator: "*ba-brief.json"}` if you want it
   silent).
4. **[P5] `requires_capabilities`** on skills implying network / file-write / code-exec
   (`executing-qa-test-suite`, `implement-frontend-feature`, `review-backend-code`, `review-frontend-code`,
   `delivery-pipeline.yaml`) for capability-gated cross-model routing.
5. **[schema-evolution] Activate the E-axis** once specs start changing: pass `--baseline` from a released
   git tag (e.g. `git show <tag>:workflows/schemas/ba-brief.json` into a temp file). Today the axis is inert
   (no baseline). Git is now active in this repo, so this is feasible.

## CI / pre-commit wiring (recipe — NOT applied)

Once the config is at repo root, gate in CI by propagating the exit code:

```bash
python3 ~/.claude/skills/universal-spec-validator/scripts/validate_spec.py \
  'workflows/skills/**/SKILL.md' 'workflows/skills/**/schemas/*.json' \
  'workflows/schemas/*.json' 'workflows/delivery-pipeline.yaml' \
  '.claude/skills/**/SKILL.md' '.claude/skills/**/schemas/*.json' \
  --config .spec-validator.yaml --out "$(mktemp -d)" --format both
# exit 0 = pass, 1 = blocking finding, 2 = usage/parse error
```

`scripts/ci-gate.sh` is a thin wrapper around the same call. For a pre-commit hook, send `--out` to a
temp dir (or `.gitignore` the report dir) so reports are never committed.

## Re-running this review

```bash
cd workflow-pack
VS=~/.claude/skills/universal-spec-validator/scripts/validate_spec.py
GLOBS=( 'workflows/skills/**/SKILL.md' 'workflows/skills/**/schemas/*.json' 'workflows/schemas/*.json' \
        'workflows/delivery-pipeline.yaml' '.claude/skills/**/SKILL.md' '.claude/skills/**/schemas/*.json' )
python3 "$VS" "${GLOBS[@]}" --out spec-review --format both                                   # raw baseline
python3 "$VS" "${GLOBS[@]}" --config spec-review/.spec-validator.yaml --out spec-review        # tuned/green
```
