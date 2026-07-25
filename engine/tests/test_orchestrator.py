"""Orchestrator semantics on the synthetic mini-workflow — zero tokens."""
import asyncio

import pytest

from engine.gates import GateApprovalError, GateSpec, GateBook
from engine.tests.conftest import FakeExecutor, all_auto_gates, drive_until, make_orch


def run(coro):
    return asyncio.run(coro)


def test_happy_path_all_succeed(mini_workflow, tmp_path):
    fake = FakeExecutor()
    orch = make_orch(mini_workflow, tmp_path, fake)
    assert run(orch.start()) == "done"
    assert all(r["state"] == "succeeded" for r in orch.stage.values())
    assert fake.calls["alpha"] == 1 and fake.calls["post"] == 1


def test_retry_policy_exhausts_then_recovers(mini_workflow, tmp_path):
    fake = FakeExecutor({"alpha": ["raise", "raise", "ok"]})
    orch = make_orch(mini_workflow, tmp_path, fake)
    assert run(orch.start()) == "done"
    assert orch.stage["alpha"]["attempts"] == 3


def test_loop_back_resets_the_downstream_cone(mini_workflow, tmp_path):
    fake = FakeExecutor({"beta": ["verdict:reject", "ok"]})
    orch = make_orch(mini_workflow, tmp_path, fake)
    assert run(orch.start()) == "done"
    assert orch.loop_ledger.get("beta->alpha") == 1
    assert orch.stage["alpha"]["attempts"] == 2  # alpha re-ran after the loop_back
    assert fake.calls["beta"] == 2


def test_loop_cap_parks_in_human_queue_then_abort(mini_workflow, tmp_path):
    fake = FakeExecutor({"beta": ["verdict:reject", "verdict:reject"]})
    orch = make_orch(mini_workflow, tmp_path, fake)

    async def scenario():
        task = await drive_until(
            orch, lambda o: o.stage["beta"]["state"] == "human-queued")
        assert orch.run_state == "waiting-human"
        assert orch.stage["beta"]["queue"] == "q-beta"
        orch.abort("test abort")
        await task

    run(scenario())
    assert orch.run_state == "aborted"


def test_sync_named_gate_blocks_until_named_verdict(mini_workflow, tmp_path):
    gates = dict(all_auto_gates(mini_workflow).specs)
    gates["release"] = GateSpec(stage_id="release", gate="sync-named",
                                owner_role="release-manager", blocking=True, mandatory=True)
    fake = FakeExecutor()
    orch = make_orch(mini_workflow, tmp_path, fake, gatebook=GateBook(gates))

    async def scenario():
        task = await drive_until(orch, lambda o: bool(o.pending_gates()))
        assert orch.stage["release"]["state"] == "waiting-gate"
        assert orch.stage["post"]["state"] == "pending"  # dependent held back
        with pytest.raises(GateApprovalError):
            orch.post_verdict("release", "approve", "")  # nameless -> structurally refused
        with pytest.raises(GateApprovalError):
            orch.post_verdict("release", "LGTM", "Somchai")  # wrong vocabulary
        orch.post_verdict("release", "approve", "Release Manager Somchai", "ok to ship")
        await task

    run(scenario())
    assert orch.run_state == "done"
    gate = orch.gates["release"]
    assert gate.approver == "Release Manager Somchai" and gate.status == "released"


def test_rejected_gate_fails_the_run(mini_workflow, tmp_path):
    gates = dict(all_auto_gates(mini_workflow).specs)
    gates["release"] = GateSpec(stage_id="release", gate="sync-named",
                                owner_role="release-manager", blocking=True)
    orch = make_orch(mini_workflow, tmp_path, FakeExecutor(), gatebook=GateBook(gates))

    async def scenario():
        task = await drive_until(orch, lambda o: bool(o.pending_gates()))
        orch.post_verdict("release", "reject", "Release Manager Somchai", "not ready")
        await task

    run(scenario())
    assert orch.run_state == "failed"
    assert "gate blocked" in orch.terminal_reason


def test_rollback_verdict_triggers_saga_compensation(mini_workflow, tmp_path):
    fake = FakeExecutor({"post": ["verdict:rollback"]})
    orch = make_orch(mini_workflow, tmp_path, fake)
    assert run(orch.start()) == "hard-fail"
    assert orch.stage["release"]["state"] == "compensated"
    assert any(e["kind"] == "compensation.simulated" for e in orch.events)
    assert "compensated" in orch.terminal_reason
