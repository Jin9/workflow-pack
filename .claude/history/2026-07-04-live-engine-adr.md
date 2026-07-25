# 2026-07-04 — ADR: local live runtime engine (supersedes the static-only posture, runtime scope only)

**Decision (user, 2026-07-04):** build a local Python runtime engine (`engine/`) that actually
executes `workflows/delivery-pipeline.yaml` — agent stages via a hybrid runner (headless
`claude -p` for JSON-only stages, claude-agent-sdk for code-gen stages, replay + script
executors otherwise), fail-closed dual-schema JSON handoffs at every boundary, human gates
surfaced to a web console, and the workflows-ui HELL FACTORY sim driven as the live run
visualization. This **supersedes ADR-001 of `reference/plan/workflows-ui-binding.md`
("live server — rejected") for the runtime phase only.**

**What changes**
- New root `engine/` tree (FastAPI at localhost:8000; `runs/<run-id>/` gitignored outputs
  mirroring the ShopPilot layout so `validate.py` patterns and the review console work unchanged).
- The gate table is externalized to machine-readable `engine/config/gates.yaml`
  (27/27 stages; validated by `gates.schema.json`; the s1-discovery `human_review` block is
  mirrored and kept in sync).
- `delivery-pipeline-input.json` gains an optional, advisory `request_type`
  (`new-product|fix|enhance`); back-compat, no skip-profiles yet.
- workflows-ui consumes live data through the same single `pipeline-pack.json` seam (ADR-003
  unchanged) via a polled `LivePackSource`; a control overlay (request form, gate inbox) posts
  to the engine API.

**What stays**
- Shipped HTML artifacts (dashboard, run consoles, viewers) remain **offline** — no CDN /
  `https://` loads; workflows-ui's Google-Fonts links were vendored to @fontsource this same day.
- Generators stay **byte-deterministic** (no `now()`/randomness); skill versions stay exact-pinned.
- Human gates are never relaxed: sync-named gates (S6 release-handoff) structurally cannot be
  auto-approved by the engine; S6/S7 stay human-queued until named approvers + short-lived OIDC
  deploy credentials exist (README Part A blockers #1–2).
- Static replay still works with zero server (`python3 -m engine replay`).

**Shipped alongside this ADR (P0):** the 5-site `from_stage.ba-research` singular→plural drift
fix; explicit `contract-design` failure_policy; 7 skills' nested `metadata:` frontmatter
flattened (patch-bumped: eliciting-banking-brief 1.6.1, designing-tech-lead-handoff 0.2.2,
generate-ux-pack 0.1.1, implement-backend/frontend-feature · planning-banking-tests ·
review-frontend-code 1.0.1) with YAML pins + dashboard bundle re-synced.
