# engine/ — the delivery-pipeline runtime

Executes `workflows/delivery-pipeline.yaml` (27 stages) with fail-closed
dual-schema JSON handoffs, externalized human gates, retry / loop_back /
human-queue policies, SAGA compensation, and a hash-chained audit log.
This runtime is the recorded posture departure of
`.claude/history/2026-07-04-live-engine-adr.md` — shipped HTML stays offline,
generators stay deterministic, and **no code path can auto-approve a
sync-named gate** (test-proven).

## Quick start

```bash
python3.13 -m venv engine/.venv
engine/.venv/bin/pip install pyyaml jsonschema fastapi uvicorn pytest httpx claude-agent-sdk

# token-free full-pipeline replay from the ShopPilot corpus
engine/.venv/bin/python -m engine replay --run-id r1 --approve-as "Your Name"
engine/.venv/bin/python -m engine validate-run runs/r1 --strict   # dual-schema oracle
engine/.venv/bin/python -m engine verify-audit runs/r1            # hash chain

# the console backend (serves workflows-ui/dist at / when built)
engine/.venv/bin/python -m engine serve --port 8000

# tests (zero tokens)
engine/.venv/bin/python -m pytest engine/tests -q
```

## How a stage runs

ready-set (DAG) → assemble input (`from_workflow_input`/`from_stage` picks;
the ba-research←s1-discovery handoff nests under `input.discovery` per the
YAML comment) → executor → **dual validation** (skill `schemas/output.json` +
boundary schema + `required_fields`; INDEX/run-plan are boundary-only, exactly
like `_sim/validate.py`) → verdict routing (per-stage vocabularies, unknown →
human, fail closed) → gate (from `engine/config/gates.yaml`).

Executors (`engine/config/runtime-binding.yaml` binds per stage; `mode=replay`
forces replay everywhere):

| kind | what | notes |
|---|---|---|
| `replay` | byte-verbatim copy from `tmp/runs/shoppilot/` | token-free; deterministic |
| `headless` | `claude -p --model X --effort low` subprocess | prompt via stdin carries BOTH schemas + data-fenced input; success = artifact file exists ∧ validates; stdout never parsed; process-group kill on timeout (macOS has no `timeout`) |
| `sdk` | claude-agent-sdk session (same prompt protocol) | code-gen stages (S4a/S4b); needs Python ≥3.10; proven live, default-off for cost |
| `script` | REAL test commands emitting gate JSON (`gate-runners.yaml`) | T1 = `go test -race -json` over the 4 corpus services, T3 = `vitest run --reporter=json`; verdict PASS\|FAIL\|ERROR computed from tool output, no LLM |

Failure: `retry` (backoff) → `human-queue`; `loop_back` resets the target's
downstream cone (ledgered, capped) and threads the reviewer's findings into
the re-run (`input.loop_back_feedback`); `abort` → hard-fail. SAGA: when
release-handoff already succeeded, the COMPENSATING skill (`handoff-revoke`)
executes against its own boundary (`schemas/revoke-receipt.json`, wired via
the YAML's `compensating_action.schema_ref`) — simulated in replay,
live-proven with a schema-valid revoke receipt.

## API (what the HELL FACTORY console consumes)

`POST /api/runs {raw_request, requester, request_type?, idempotency_key?, mode}` ·
`GET /api/runs` · `GET /api/runs/{id}` · `GET /api/runs/{id}/pack` (ETag) ·
`GET /api/runs/{id}/events?after=N` ·
`POST /api/runs/{id}/gates/{stage}/verdict {verdict, approver, note?}`
(422 without a named approver) ·
`POST /api/runs/{id}/stages/{stage}/resolve {action: retry|abort, resolver, note?}`
(typed HITL resolution for HUMAN-QUEUED failures — each grant buys one more
attempt) · `POST /api/runs/{id}/abort`.

Run outputs land in gitignored `runs/<run-id>/` mirroring the ShopPilot layout,
so `rendering-delivery-review-console` and the validation oracle work on live
runs unchanged. `runs/<id>/events.jsonl` is append-only and hash-chained; it
carries digests and names only — never raw_request bodies or artifact content.

## Deliberately not here (yet)

Wiring scripted gates to freshly code-generated output (needs repo-stamping /
worktree so live code-gen lands as a buildable module tree — today T1/T3 test
the reference implementation the replayed manifests describe); request-type
skip-profiles; live ux-intake (needs a real UX drop) and live qa-validate
(GAP-05 execution node — an agent without a harness must not fabricate
evidence); S6/S7 stay human-queued until named approvers + short-lived OIDC
deploy credentials exist (README Part A blockers).
