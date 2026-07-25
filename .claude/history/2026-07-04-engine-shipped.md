# 2026-07-04 — Engine P0–P6 shipped: the pipeline runs (evidence log)

Same-day follow-through on the live-engine ADR (see `2026-07-04-live-engine-adr.md`). All phases of
the approved plan landed and were verified by script, not self-report:

- **P0** — YAML contract drift fixed (singular `epic/stories` ×5 sites; phantom `required_fields` +
  mappings at 8 stages/14 sites); explicit `contract-design` policy; `request_type` added;
  `engine/config/gates.yaml` externalized all 27 gates; 7 nested-`metadata:` frontmatters flattened
  (pins + dashboard bundle re-synced, round-trip lossless); fonts vendored; `.gitignore` runs/.
- **P1/P2** — `engine/` runtime: fail-closed loader, asyncio DAG orchestrator (emergent BE∥FE legs),
  dual-schema validation mirroring `_sim/validate.py`, verdict routing (unknown → human),
  hash-chained audit, gates with named-approver-only releases (sync-named cannot auto-approve,
  test-proven), FastAPI + live pipeline-pack. Replay: 27/27 oracle, byte-deterministic.
- **P3** — live slice S0→S1b (haiku/opus headless; dual-schema prompt fix after the first honest
  fail-closed park) + surprise live proof of both S4a/S4b as parallel claude-agent-sdk sessions;
  run-33333333 → done 27/27.
- **P4** — workflows-ui `src/console/`: the sim is the console (adapter seam per ADR-003, director
  choreography, gate inbox, request form); screenshot-verified; engine-offline degrades to the
  autonomous sim.
- **P5** — scripted T-gates run the REAL suites (T1 `go test -race`: 223/223 — the sim had claimed
  96; T3 vitest 18/18); ref-chain hydration; resume API for human-queued failures; loop-back
  feedback threading; `upstream_artifacts` relpaths; design leg live. Acceptance run-77777777:
  live red team **BLOCK → loop_back with findings → revised TL design → BLOCK again → cycle cap →
  hard-fail** ("no fan-out on a bad plan") — the adversarial semantics live, end-to-end. Root
  insight: the live brief carries P1 governance gaps (Legal-absent on regulatory scope), and
  auto-resolving them is on the never-do list ⇒ a fully-autonomous green run through the design
  leg is impossible **by design** for regulatory-scoped requests.
- **P6** — SAGA compensation fixed to execute the COMPENSATING skill (it previously reused the
  stage spec — a live revoke would have re-run the deploy handoff); `revoke-receipt.json` (the
  one orphan schema) wired as the comp boundary via a YAML `schema_ref`; **live-proven**: a real
  headless `handoff-revoke` produced a schema-valid revoke receipt referencing the original
  deploy receipt. S6/S7 stay human-queued pending named approvers + OIDC (README Part A #1–2).

38/38 pytest, token-free. Open backlog: scripted gates against freshly generated code
(repo-stamping/worktrees), live ux-intake/qa-validate, skip-profiles, async-gate semantics.
