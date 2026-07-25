# CLAUDE.md change-log — index

Workspace-local reference. The dated `Latest …`/`Prior …` change-log notes that used to
accumulate at the top of `CLAUDE.md` are now **one file per entry** under [`history/`](history/),
kept **verbatim** for honest history. They record *past* state, not live instructions. This
index is the thin catalog; read an individual file when you need that entry.

**Live guidance lives in `CLAUDE.md`** — when something changes, edit the current-state prose
there (don't append a dated note). Neither this index nor `history/` is auto-loaded into the
session context, so they don't count against the `CLAUDE.md` size limit. (The full history is
also recoverable via `git log`/`git show` on `CLAUDE.md`.)

**To add an entry:** create `history/YYYY-MM-DD-<slug>.md` (a `#` title + the verbatim note),
then add one bullet at the top of the matching list below. Append-only — never rename an
existing file (keeps links + git history stable).

---

## Dated change-log (newest first)

- [2026-07-12 — Fleet-wide skill I/O contract reshape (31/31)](history/2026-07-12-skill-io-reshape.md) — every skill's input/output contract rewritten to the real post-adapter payload (Codex-advised, Claude-adjudicated: 263 findings, 6 rejected); contract-drift lint 68→0 and now BLOCKING; execution provenance + audit_id fleet-wide; S0 schemas authored and un-exempted; real bugs fixed (silently-lost backend review verdict, severity_floor suppression, destroy-the-input paths)
- [2026-07-04 — Engine P0–P6 shipped: the pipeline RUNS (evidence log)](history/2026-07-04-engine-shipped.md) — replay 27/27 + live runs (BA leg, design leg, SDK code-gen, scripted go test/vitest gates, live SAGA revoke); adversarial loop exercised live to its designed hard-fail; 38/38 pytest
- [2026-07-04 — ADR: local live runtime engine (posture departure)](history/2026-07-04-live-engine-adr.md) — `engine/` runtime + localhost API allowed; shipped HTML stays offline; gates externalized to `engine/config/gates.yaml`; drift fix + 7 frontmatters flattened + fonts vendored
- [2026-06-10 — spec_to_drawio.py 0.2.1: multi-service context bands](history/2026-06-10-spec-to-drawio-multi-service-fix.md) — L2 service stacking + channel fold + dense-bundle labels; ShopPilot drawio proven byte-identical; pins synced (YAML · dashboard · test case)
- [2026-06-10 — workflows-ui ⇄ pipeline binding design (design-only)](history/2026-06-10-workflows-ui-binding-design.md) — `reference/plan/workflows-ui-binding.md` + generated L1–L4 `.drawio`; pipeline-pack single-seam adapter; no sim code changed
- [2026-06-07 — Root cleanup: retired the stage-flow `.drawio` (later reverted)](history/2026-06-07-root-cleanup-drawio.md) — removed `delivery-pipeline-flow.drawio`; later reverted (it's back)
- [2026-06-07 — Full S0→S7 simulated run + Delivery Review Console v1.1.0](history/2026-06-07-s0-s7-sim-console-v1.1.md) — 27-node contract-faithful sim (`03b9000`); console all-stages, gate roll-up GREEN
- [2026-06-07 — S2 skill narrowed to the system-design blueprint (0.2.0)](history/2026-06-07-s2-skill-narrowed.md) — `designing-tech-lead-handoff` scoped down; contract-safe
- [2026-06-06 — Human-review output-contract design + the Delivery Review Console](history/2026-06-06-delivery-review-console.md) — new `rendering-delivery-review-console` skill; Quality-Gate Board; 3 boundary schemas closed
- [2026-06-06 — Spec-review reports refreshed + `templates-review/` deleted](history/2026-06-06-spec-review-refresh.md) — 104 specs, tuned green; authoritative state 28 skills / 27 stages / OI-002 closed
- [2026-06-06 — Offline draw.io stage-flow diagram](history/2026-06-06-drawio-stage-flow.md) — `delivery-pipeline-flow.drawio` added; 8 SDLC bands, 27 nodes, colour-graded by gate
- [2026-06-04 — S1→S2.5 ShopPilot demo run + contract debug-viewer skill; repo on GitHub](history/2026-06-04-shoppilot-demo-debug-viewer.md) — first live run committed; `rendering-contract-debug-viewer` added
- [2026-06-04 — Skill-version pinning + boundary-schema closure + spec-validator gate](history/2026-06-04-skill-pinning-spec-gate.md) — exact pins; `additionalProperties:false`; opt-in `spec-review/` gate
- [2026-06-02 — YAML consolidated to one + S1 run-folder split](history/2026-06-02-yaml-consolidated-run-split.md) — `squad-delivery.yaml` deleted; run folder → S1a/S1b
- [2026-06-02 — Dashboard S1 split into two cards](history/2026-06-02-dashboard-s1-two-cards.md) — S1a · BA Discovery → gate → S1b · BA Brief (visual/data-model only)
- [2026-06-02 — Skill consolidation (skill-packs split by use → workflows/skills/)](history/2026-06-02-skill-consolidation.md) — 14 used skills kept; ~100 unused deleted *(later 28)*
- [2026-06-02 — Root trim + archive relocation + full S0–S7 demo](history/2026-06-02-root-trim-archive-relocation.md) — `.archive/` → sibling `../archive/`; `design-diagram/` removed
- [2026-06-01 — Subproject CLAUDE.md files retired (context note)](history/2026-06-01-subproject-claudemd-retired.md) — `business-analyse/` archived, `design-diagram/` removed; root CLAUDE.md authoritative

## Historical asides

- [2026-06-01 — Top-level design-doc consolidation](history/2026-06-01-design-doc-consolidation.md) — design docs folded into `README.md`; overview rebuilt as the dashboard
- [2026-06-03 — Dashboard scripted-rebuild provenance](history/2026-06-03-dashboard-rebuild-provenance.md) — one-time re-encode; render module (`c022aabb…`) still manual
- [2026-06-06 — `templates-review/` deletion](history/2026-06-06-templates-review-deletion.md) — review copy of the archived templates tree, git-restorable
- [2026-06-02 — Skill-pack reduction](history/2026-06-02-skill-pack-reduction.md) — 113-skill `treasury/*` copy reduced; unused deleted, gone from this workspace
