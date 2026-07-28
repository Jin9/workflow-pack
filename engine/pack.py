"""Live pipeline-pack export — the single seam the workflows-ui sim consumes.

Same philosophy as the designed build-time pipeline-pack.json (ADR-003): the
UI reads ONE artifact; the adapter on the UI side owns all name mapping. A
live pack is just a pack whose timeline grows and which carries run status +
pending gates. `band` is the stable semantic key the sim maps to rooms.
"""
from __future__ import annotations

from typing import Dict

PACK_VERSION = "live-1"

STAGE_BAND: Dict[str, str] = {
    "intake": "intake",
    "s1-discovery": "ba", "ba-breakdown": "ba", "ba-research": "ba",
    "ux-intake": "ux",
    "tl-design": "design", "plan-review": "design",
    "contract-design": "contracts",
    "backend-implement": "dev-be", "backend-review": "dev-be",
    "frontend-implement": "dev-fe", "frontend-review": "dev-fe",
    "qa-plan": "qa", "qa-validate": "qa",
    "release-handoff": "deploy", "prod-validate": "prod",
}

_RAG = {  # worst-of roll-up: verdicts map to G/A/R without normalizing the vocab
    "PASS": "G", "pass": "G", "promote": "G", "approve": "G",
    "conditional": "A", "hold": "A",
    "FAIL": "R", "fail": "R", "ERROR": "R", "rollback": "R",
}


def band_for(stage_id: str) -> str:
    return STAGE_BAND.get(stage_id, "tests")


def build_pack(orch) -> dict:
    """orch: engine.orchestrator.Orchestrator (duck-typed for tests)."""
    stages = []
    board = []
    rollup = "G"
    order = {"G": 0, "A": 1, "R": 2}
    for sid in orch.dag.topo_order:
        rec = orch.stage[sid]
        spec = orch.workflow.stage_by_id[sid]
        gate = orch.gates.get(sid)
        stages.append({
            "id": sid,
            "band": band_for(sid),
            "type": spec.type,
            "skill": spec.skill_name,
            "state": rec["state"],
            "attempts": rec["attempts"],
            "caveat": rec["caveat"],
            "artifact": rec["artifact"],
            "queue": rec["queue"],
            "gate": gate.as_record() if gate else None,
        })
        if band_for(sid) == "tests":
            verdict = None
            if rec["artifact"]:
                try:
                    verdict = orch.store.read_artifact(sid).get("verdict")
                except Exception:
                    verdict = None
            rag = _RAG.get(str(verdict), "pending" if rec["state"] != "succeeded" else "A")
            board.append({"stage_id": sid, "verdict": verdict, "rag": rag})
            if rag in order and order[rag] > order.get(rollup, 0):
                rollup = rag

    return {
        "pack_version": PACK_VERSION,
        "pack_seq": orch.pack_seq,
        "run": {
            "run_id": orch.run_id,
            "state": orch.run_state,
            "mode": orch.mode,
            "request_type": orch.request_type,
            "terminal_reason": orch.terminal_reason,
            "workflow": f"{orch.workflow.name}@{orch.workflow.version}",
        },
        "stages": stages,
        "dag": {
            "topo_order": list(orch.dag.topo_order),
            "edges": [[p, sid] for sid, parents in orch.dag.parents.items() for p in parents],
        },
        "gates": {
            "pending": [g.as_record() for g in orch.pending_gates()],
            "board": board,
            "rollup": rollup,
        },
        "timeline": orch.events[-120:],
    }
