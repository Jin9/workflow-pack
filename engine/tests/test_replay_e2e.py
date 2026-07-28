"""P1/P2 acceptance: full 28-stage replay — dual validation, gates, determinism."""
import asyncio
import hashlib
import json

from engine.audit import verify_chain
from engine.binding import RuntimeBinding
from engine.gates import GateBook
from engine.loader import load_workflow
from engine.orchestrator import Orchestrator
from engine.pack import build_pack
from engine.runstore import RunStore, artifact_relpath

from engine.tests.helpers import quorum_aware_hook
from engine.validation import validate_artifact

APPROVER = "Replay Test Operator"


def _replay(tmp_path, run_id):
    wf = load_workflow()
    orch = Orchestrator(
        wf, GateBook.load(wf), RuntimeBinding.load(),
        run_id=run_id,
        workflow_input={"raw_request": "ShopPilot replay", "requester": "pytest",
                        "idempotency_key": "00000000-0000-4000-8000-0000000000aa"},
        mode="replay",
        store=RunStore(run_id, base=tmp_path / "runs"),
        approve_hook=quorum_aware_hook(APPROVER),
    )
    state = asyncio.run(orch.start())
    return orch, state


def _artifact_hashes(orch):
    out = {}
    for s in orch.workflow.stages:
        p = orch.store.artifact_path(s.id)
        out[artifact_relpath(s.id)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_full_replay_28_of_28(tmp_path):
    orch, state = _replay(tmp_path, "e2e-a")
    assert state in ("done", "ship-with-caveats"), orch.terminal_reason

    # every artifact passes the same dual validation as the ShopPilot oracle
    for stage in orch.workflow.stages:
        validate_artifact(stage, orch.store.artifact_path(stage.id))

    # every blocking gate was released by the named operator (typed HITL records)
    blocking = [sid for sid, g in orch.gatebook.specs.items() if g.blocking]
    assert len(blocking) >= 6
    for sid in blocking:
        gate = orch.gates[sid]
        assert gate.status in ("released", "released-with-caveat")
        if gate.spec.quorum:
            # A quorum gate is released by DISTINCT named humans, one per role —
            # never by the single replay operator.
            assert sorted(gate.signed_roles) == sorted(gate.spec.required_roles)
            names = [a["approver"] for a in gate.approvals]
            assert len(set(names)) == len(names) and APPROVER not in names
        else:
            assert gate.approver == APPROVER

    # audit chain verifies end-to-end
    assert verify_chain(orch.store.events_path) == orch.audit._seq

    # workflow output contract written
    out = json.loads((orch.store.dir / "output.json").read_text())
    assert out["ba_brief"]["artifact"] == "S1c-brief/INDEX.json"

    # the pack exports cleanly with a GREEN-ish board
    pack = build_pack(orch)
    assert len(pack["stages"]) == 28
    assert pack["gates"]["rollup"] in ("G", "A")


def test_replay_is_byte_deterministic(tmp_path):
    orch_a, state_a = _replay(tmp_path, "det-same")
    hashes_a = _artifact_hashes(orch_a)
    orch_b, state_b = _replay(tmp_path / "b", "det-same")  # same run id, fresh dir
    assert state_a == state_b
    assert hashes_a == _artifact_hashes(orch_b)

    # deterministic audit ids in replay mode: identical run ids -> identical event
    # CONTENT; parallel-leg completion order may differ, so compare as multisets.
    ev_a = [json.loads(l) for l in orch_a.store.events_path.read_text().splitlines()]
    ev_b = [json.loads(l) for l in orch_b.store.events_path.read_text().splitlines()]
    key = lambda e: (e["kind"], e.get("stage") or "", e.get("audit_id") or "")
    assert sorted(map(key, ev_a)) == sorted(map(key, ev_b))
