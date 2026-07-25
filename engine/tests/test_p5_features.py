"""P5: resume API for human-queued stages, ref-chain hydration, gate-runner parsers."""
import asyncio
import json

import pytest

from engine.executors.script import parse_go_test_json, parse_vitest_report
from engine.loader import load_workflow
from engine.mapping import assemble_input
from engine.model import EngineError
from engine.runstore import SHOPPILOT
from engine.tests.conftest import FakeExecutor, drive_until, make_orch


def run(coro):
    return asyncio.run(coro)


# ── resume API ────────────────────────────────────────────────────────────────
def test_human_queued_stage_resumes_via_typed_resolution(mini_workflow, tmp_path):
    fake = FakeExecutor({"alpha": ["raise", "raise", "raise", "ok"]})  # exhausts retry x2
    orch = make_orch(mini_workflow, tmp_path, fake)

    async def scenario():
        task = await drive_until(orch, lambda o: o.stage["alpha"]["state"] == "human-queued")
        assert orch.run_state == "waiting-human"
        with pytest.raises(EngineError):
            orch.resolve_stage("alpha", "retry", "")  # nameless -> refused
        with pytest.raises(EngineError):
            orch.resolve_stage("beta", "retry", "Ops Lead")  # not queued -> refused
        res = orch.resolve_stage("alpha", "retry", "Ops Lead Somchai", "root cause fixed")
        assert res["state"] == "pending"
        await task

    run(scenario())
    assert orch.run_state == "done"
    assert orch.stage["alpha"]["attempts"] == 4
    assert any(e["kind"] == "stage.human-resolved" and e["resolver"] == "Ops Lead Somchai"
               for e in orch.events)


def test_resolution_abort_is_recorded(mini_workflow, tmp_path):
    fake = FakeExecutor({"alpha": ["raise", "raise", "raise"]})
    orch = make_orch(mini_workflow, tmp_path, fake)

    async def scenario():
        task = await drive_until(orch, lambda o: o.stage["alpha"]["state"] == "human-queued")
        orch.resolve_stage("alpha", "abort", "Ops Lead Somchai")
        await task

    run(scenario())
    assert orch.run_state == "aborted"
    assert "Ops Lead Somchai" in orch.terminal_reason


# ── ref-chain hydration ───────────────────────────────────────────────────────
def test_hydration_inlines_epics_and_stories_from_the_manifest():
    wf = load_workflow()
    tl = wf.stage_by_id["tl-design"]
    index = json.loads((SHOPPILOT / "S1b-ba-brief" / "INDEX.json").read_text())
    ux = json.loads((SHOPPILOT / "S1.5-ux-intake" / "output.json").read_text())
    payload, warnings = assemble_input(
        tl,
        {"raw_request": "r", "requester": "u",
         "idempotency_key": "00000000-0000-4000-8000-000000000042"},
        {"ba-research": index, "ux-intake": ux},
        wf.input_required,
        stage_dirs={"ba-research": SHOPPILOT / "S1b-ba-brief",
                    "ux-intake": SHOPPILOT / "S1.5-ux-intake"},
    )
    # refs became inline Epic objects (the inline-era consumer contract)
    assert payload["epics"] and "problem_statement" in payload["epics"][0]
    assert "stakeholders" in payload["epics"][0]
    # stories hydrated from story_files; the refs stay available too
    assert payload["stories"] and "acceptance_criteria" in payload["stories"][0]
    assert "file" in payload["story_files"][0]
    # the workflow's one idempotency key rides along (TL contract requires it)
    assert payload["idempotency_key"].endswith("42")


def test_hydration_absent_without_stage_dirs():
    wf = load_workflow()
    tl = wf.stage_by_id["tl-design"]
    index = json.loads((SHOPPILOT / "S1b-ba-brief" / "INDEX.json").read_text())
    payload, _ = assemble_input(tl, {}, {"ba-research": index, "ux-intake": {}}, ())
    assert "stories" not in payload  # no dirs -> refs pass through untouched
    assert "file" in payload["epics"][0]


# ── upstream artifact paths ride in every payload ─────────────────────────────
def test_payload_carries_upstream_artifact_relpaths(mini_workflow, tmp_path):
    fake = FakeExecutor()
    orch = make_orch(mini_workflow, tmp_path, fake)
    assert run(orch.start()) == "done"
    beta_payload = fake.payloads["beta"][0]
    # beta consumes alpha; both live in gates/ under the mini layout
    assert beta_payload["upstream_artifacts"] == {"alpha": "alpha.json"}
    assert "upstream_artifacts" not in fake.payloads["alpha"][0]  # no producers


# ── loop_back feedback threading ──────────────────────────────────────────────
def test_loop_back_threads_reviewer_findings_into_the_rerun(mini_workflow, tmp_path):
    fake = FakeExecutor({"beta": ["verdict:reject", "ok"]})
    orch = make_orch(mini_workflow, tmp_path, fake)
    assert run(orch.start()) == "done"
    assert fake.calls["alpha"] == 2
    first, second = fake.payloads["alpha"]
    assert "loop_back_feedback" not in first
    fb = second["loop_back_feedback"]
    assert fb["from_stage"] == "beta" and fb["verdict"] == "reject" and fb["loop_count"] == 1


def test_plan_review_vocabulary_routes():
    from engine.policies import CAVEAT, FAIL, REWORK, route_verdict
    assert route_verdict({"verdict": "BLOCK"}) == REWORK  # feeds loop_back, per the YAML design
    assert route_verdict({"verdict": "reroute"}) == REWORK
    assert route_verdict({"verdict": "hard-fail"}) == FAIL
    assert route_verdict({"verdict": "pass-with-caveats"}) == CAVEAT


# ── SAGA compensation runs the COMPENSATING skill (P6) ────────────────────────
def test_live_compensation_runs_the_compensating_skill(mini_workflow, tmp_path):
    fake = FakeExecutor({"post": ["verdict:rollback"]})
    orch = make_orch(mini_workflow, tmp_path, fake, mode="live")
    assert run(orch.start()) == "hard-fail"

    comp_payloads = fake.payloads["release::compensation"]
    assert len(comp_payloads) == 1  # the synthetic comp stage ran, NOT the deploy skill again
    assert "post verdict" in comp_payloads[0]["reason"]
    assert comp_payloads[0]["original_receipt"]["audit_id"]  # the receipt to revoke rides along
    assert (orch.store.stage_dir("release") / "revoke-receipt.json").is_file()
    assert any(e["kind"] == "compensation.executed" for e in orch.events)


def test_loader_resolves_the_compensation_boundary_schema():
    from engine.loader import load_workflow
    comp = load_workflow().stage_by_id["release-handoff"].compensating_action
    assert comp.skill_dir.name == "handoff-revoke"
    assert comp.output_schema_path is not None
    assert comp.output_schema_path.name == "revoke-receipt.json"  # the once-orphan schema, wired


# ── gate-runner parsers ───────────────────────────────────────────────────────
def test_parse_go_test_json_counts_and_failures():
    lines = "\n".join([
        json.dumps({"Action": "run", "Test": "TestA", "Package": "p"}),
        json.dumps({"Action": "pass", "Test": "TestA", "Package": "p"}),
        json.dumps({"Action": "fail", "Test": "TestB", "Package": "p"}),
        json.dumps({"Action": "skip", "Test": "TestC", "Package": "p"}),
        json.dumps({"Action": "pass", "Package": "p"}),  # package event, not a test
        "not json at all",
    ])
    totals, failures = parse_go_test_json(lines)
    assert totals == {"executed": 3, "passed": 1, "failed": 1, "skipped": 1}
    assert failures == ["p::TestB"]


def test_parse_vitest_report_counts_and_failures():
    report = {
        "numTotalTests": 5, "numPassedTests": 3, "numFailedTests": 1,
        "numPendingTests": 1, "numTodoTests": 0,
        "testResults": [{"assertionResults": [
            {"status": "passed", "fullName": "a"},
            {"status": "failed", "fullName": "checkout > rejects bad card"},
        ]}],
    }
    totals, failures = parse_vitest_report(report)
    assert totals == {"executed": 5, "passed": 3, "failed": 1, "skipped": 1}
    assert failures == ["checkout > rejects bad card"]
