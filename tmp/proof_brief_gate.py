"""Adversarial proof for the new ba-research gate (G1).

A passing unit test proves record_verdict() behaves; it does NOT prove a real run
parks. This drives the whole 28-stage replay against a corpus whose BA brief
declares state: needs-work (schema-valid, with the failure_state its own skill
schema demands), signs every gate it can, and checks the run stops there.

Run: engine/.venv/bin/python tmp/proof_brief_gate.py
"""
from __future__ import annotations

import asyncio
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.binding import RuntimeBinding
from engine.executors.replay import ReplayExecutor
from engine.gates import GateBook
from engine.loader import load_workflow
from engine.orchestrator import Orchestrator
from engine.runstore import SHOPPILOT, RunStore, artifact_relpath
from engine.tests.helpers import AMIGOS

WF_INPUT = {"raw_request": "ShopPilot replay", "requester": "proof",
            "idempotency_key": "00000000-0000-4000-8000-0000000000cc"}


def hook(gate):
    """Approve everything possible — the point is that the gate refuses anyway."""
    verdict = gate.spec.proceed_when or (
        "approve" if "approve" in gate.spec.verdicts else gate.spec.verdicts[0])
    if gate.spec.quorum:
        for role in gate.outstanding_roles:
            return (verdict, AMIGOS[role], f"proof {role} approval", role)
        return None
    return (verdict, "Khun Pim", "proof operator approval")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="brief-gate-proof-"))
    corpus = tmp / "corpus"
    shutil.copytree(SHOPPILOT, corpus)

    brief_path = corpus / artifact_relpath("ba-research")
    brief = json.loads(brief_path.read_text())
    assert brief["state"] == "ready-for-tl", brief["state"]
    brief["state"] = "needs-work"
    brief["failure_state"] = {
        "failure_code": "open_rule_blocks_story",
        "reason": "RULE-014 retention period is unresolved; three stories depend on it.",
        "blocking_items": ["RULE-014"],
        "suggested_next_action": "Legal confirms the PDPA retention period, then re-elaborate.",
    }
    brief_path.write_text(json.dumps(brief, indent=2) + "\n")

    wf = load_workflow()
    store = RunStore("brief-gate-proof", base=tmp / "runs")
    orch = Orchestrator(wf, GateBook.load(wf), RuntimeBinding.load(),
                        run_id="brief-gate-proof", workflow_input=WF_INPUT,
                        mode="replay", store=store, approve_hook=hook)
    orch._executors["replay"] = ReplayExecutor(corpus=corpus)
    state = asyncio.run(orch.start())

    events = [json.loads(l) for l in store.events_path.read_text().splitlines() if l.strip()]
    executed = {e.get("stage") for e in events if e.get("kind") == "stage.executed"}
    gate = orch.gates.get("ba-research")

    checks = [
        ("the run did NOT complete", state != "done"),
        ("the ba-research gate exists and is blocked",
         gate is not None and gate.status == "blocked"),
        ("the refusal names the required state",
         gate is not None and "ready-for-tl" in (gate.note or "")),
        ("an approve verdict was actually attempted",
         gate is not None and gate.verdict == "approve"),
        ("the brief did NOT reach tl-design", "tl-design" not in executed),
        ("the brief did NOT reach ux-intake", "ux-intake" not in executed),
        ("the upstream amigos gate still released",
         orch.gates["ba-breakdown"].status == "released"),
    ]

    print(f"run terminal state : {state}")
    print(f"terminal reason    : {orch.terminal_reason}")
    print(f"ba-research gate   : status={gate.status if gate else None} "
          f"verdict={gate.verdict if gate else None}")
    print(f"gate note          : {(gate.note if gate else '')!r}")
    print(f"stages executed    : {len(executed)} (tl-design present: {'tl-design' in executed})")
    print()
    ok = True
    for label, passed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}")
        ok &= bool(passed)
    # ── counterfactual: the SAME brief under the OLD advisory gate ──────────────
    # Proves the defect was real rather than theoretical: restore the pre-change
    # spec (blocking: false, no artifact precondition) and watch it ship.
    from dataclasses import replace
    old_book = GateBook.load(wf)
    old_book.specs["ba-research"] = replace(
        old_book.specs["ba-research"], blocking=False, on_field=None,
        proceed_when=None, release_requires_field_value=None,
        verdicts=("approve", "reject"), on_block=None,
    )
    store2 = RunStore("brief-gate-counterfactual", base=tmp / "runs")
    orch2 = Orchestrator(wf, old_book, RuntimeBinding.load(),
                         run_id="brief-gate-counterfactual", workflow_input=WF_INPUT,
                         mode="replay", store=store2, approve_hook=hook)
    orch2._executors["replay"] = ReplayExecutor(corpus=corpus)
    state2 = asyncio.run(orch2.start())
    events2 = [json.loads(l) for l in store2.events_path.read_text().splitlines() if l.strip()]
    executed2 = {e.get("stage") for e in events2 if e.get("kind") == "stage.executed"}
    shipped = "tl-design" in executed2

    print()
    print("── counterfactual (pre-change advisory gate, same needs-work brief) ──")
    print(f"run terminal state : {state2}")
    print(f"reached tl-design  : {shipped}   (no gate record: "
          f"{orch2.gates.get('ba-research') is None})")
    print(f"  [{'PASS' if shipped else 'FAIL'}] the defect was real: the needs-work brief "
          f"shipped downstream unsigned")
    ok &= bool(shipped)

    print()
    print("PROOF: PASS" if ok else "PROOF: FAIL")
    shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
