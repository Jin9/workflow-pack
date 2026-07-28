"""BA leg v2: the three-amigos quorum gate, its loop-back, and breakdown hydration.

These are the structural guarantees the split depends on — that a quorum cannot be
released by one person, that a non-agreed verdict returns the work instead of
killing the run, and that the breakdown pack arrives hydrated at elaboration.
"""
from __future__ import annotations

import asyncio
import json

import pytest

from engine.tests.helpers import AMIGOS, quorum_aware_hook

from engine.binding import RuntimeBinding
from engine.gates import GateApprovalError, GateBook, GateInstance, record_verdict
from engine.loader import load_workflow
from engine.mapping import assemble_input
from engine.orchestrator import Orchestrator
from engine.runstore import SHOPPILOT, RunStore
from engine.validation import SKILL_SCHEMA_EXEMPT, validate_stage_input

WF_INPUT = {"raw_request": "ShopPilot replay", "requester": "pytest",
            "idempotency_key": "00000000-0000-4000-8000-0000000000bb"}


def _spec():
    return GateBook.load(load_workflow()).spec_for("ba-breakdown")


def _gate():
    return GateInstance(run_id="r", stage_id="ba-breakdown", spec=_spec(), contract_sha256="x")


# ── the gate is a real quorum ────────────────────────────────────────────────
def test_gate_declares_three_distinct_roles():
    s = _spec()
    assert s.quorum and s.named and s.blocking
    assert s.required_roles == ("ba-lead", "dev-lead", "qa-lead")
    assert s.proceed_when == "agreed"
    assert set(s.verdicts) == {"agreed", "split-stories", "descope", "needs-rework"}


def test_two_signatures_do_not_release_the_gate():
    g = _gate()
    record_verdict(g, "agreed", AMIGOS["ba-lead"], role="ba-lead")
    assert g.status == "pending" and g.outstanding_roles == ["dev-lead", "qa-lead"]
    record_verdict(g, "agreed", AMIGOS["dev-lead"], role="dev-lead")
    assert g.status == "pending" and g.outstanding_roles == ["qa-lead"]
    record_verdict(g, "agreed", AMIGOS["qa-lead"], role="qa-lead")
    assert g.status == "released" and g.outstanding_roles == []


def test_one_human_cannot_cover_two_roles():
    g = _gate()
    record_verdict(g, "agreed", "Khun Pim", role="ba-lead")
    with pytest.raises(GateApprovalError, match="DISTINCT"):
        record_verdict(g, "agreed", "Khun Pim", role="dev-lead")


@pytest.mark.parametrize("verdict,approver,role", [
    ("agreed", "", "ba-lead"),            # nameless
    ("agreed", "Khun Pim", None),         # no role on a quorum gate
    ("agreed", "Khun Pim", "product-owner"),  # role not required by this gate
    ("approve", "Khun Pim", "ba-lead"),   # verdict outside the vocabulary
])
def test_malformed_signatures_are_refused(verdict, approver, role):
    with pytest.raises(GateApprovalError):
        record_verdict(_gate(), verdict, approver, role=role)


def test_a_role_may_not_sign_twice():
    g = _gate()
    record_verdict(g, "agreed", AMIGOS["ba-lead"], role="ba-lead")
    with pytest.raises(GateApprovalError, match="already signed"):
        record_verdict(g, "agreed", "Someone Else", role="ba-lead")


def test_dissent_resolves_the_gate_immediately():
    g = _gate()
    record_verdict(g, "agreed", AMIGOS["ba-lead"], role="ba-lead")
    record_verdict(g, "split-stories", AMIGOS["dev-lead"], role="dev-lead")
    assert g.status == "blocked"  # no point collecting the third signature


# ── hydration ────────────────────────────────────────────────────────────────
def test_breakdown_arrives_hydrated_and_valid_at_elaboration():
    wf = load_workflow()
    stage = wf.stage_by_id["ba-research"]
    index = json.loads((SHOPPILOT / "S1b-breakdown" / "INDEX.json").read_text())
    payload, warnings = assemble_input(
        stage, WF_INPUT,
        {"intake": {"normalized_request": "n"}, "ba-breakdown": index},
        wf.input_required,
        stage_dirs={"ba-breakdown": SHOPPILOT / "S1b-breakdown"},
    )
    assert not [w for w in warnings if "hydration" in w]
    b = payload["breakdown"]
    # the *_file refs become the objects the consumer contract names
    assert {"epics", "stories", "flows", "rules", "domain"} <= set(b)
    assert all(isinstance(e, dict) and "decoupling" in e for e in b["epics"])
    assert all("card" in s and "acceptance_criteria" not in s for s in b["stories"])
    assert b["rules"]["rules"] and b["domain"]["entities"]
    assert validate_stage_input(stage, payload) == []


def test_hydration_refuses_a_ref_that_escapes_the_run_directory():
    from engine.mapping import _load_ref
    warnings: list = []
    out = _load_ref(SHOPPILOT / "S1b-breakdown",
                    {"id": "EVIL", "file": "../../../../etc/passwd"}, warnings, "epic")
    assert out == {"id": "EVIL", "file": "../../../../etc/passwd"}  # returned unchanged
    assert any("escapes the run directory" in w for w in warnings)


# ── no stage is exempt from dual-schema validation any more ──────────────────
def test_no_stage_is_skill_schema_exempt():
    assert SKILL_SCHEMA_EXEMPT == set()


# ── the loop-back that did not exist before ──────────────────────────────────
def test_non_agreed_verdict_loops_back_instead_of_failing_the_run(tmp_path):
    """A `split-stories` verdict is an ORDINARY review outcome. Before this change
    it set GATE_BLOCKED and the run terminated as failed."""
    wf = load_workflow()
    run_id = "amigos-loop"
    dissent = {"n": 0}

    def hook(gate):
        if gate.spec.quorum:
            # first visit: the dev lead asks for a split; afterwards everyone agrees
            if dissent["n"] == 0 and gate.outstanding_roles == list(gate.spec.required_roles):
                dissent["n"] += 1
                return ("split-stories", AMIGOS["ba-lead"],
                        "epic 1 is two epics; split at the value axis", "ba-lead")
            for role in gate.outstanding_roles:
                return ("agreed", AMIGOS[role], f"test {role} approval", role)
            return None
        return quorum_aware_hook("Replay Test Operator")(gate)

    orch = Orchestrator(
        wf, GateBook.load(wf), RuntimeBinding.load(), run_id=run_id,
        workflow_input=WF_INPUT, mode="replay",
        store=RunStore(run_id, base=tmp_path / "runs"), approve_hook=hook,
    )
    state = asyncio.run(orch.start())

    events = [json.loads(l) for l in orch.store.events_path.read_text().splitlines() if l.strip()]
    loops = [e for e in events if e.get("kind") == "gate.loop-back"]
    assert loops, "a non-agreed verdict must loop back, not fail the run"
    assert loops[0]["loop_to"] == "ba-breakdown" and loops[0]["verdict"] == "split-stories"
    # the reviewers' OWN WORDS travel with the loop-back, recorded in the HITL trail
    # (loop_feedback itself is popped once the re-run consumes it)
    assert any("value axis" in f for f in loops[0]["findings"])
    assert AMIGOS["ba-lead"] in loops[0]["reviewers"]
    # the re-run really happened, and nothing failed on the way
    assert sum(1 for e in events
               if e.get("kind") == "stage.executed" and e.get("stage") == "ba-breakdown") == 2
    assert not [e for e in events if e.get("kind") == "input.validation.failed"]
    # and the run still completes once the amigos agree
    assert state == "done", orch.terminal_reason
    assert orch.gates["ba-breakdown"].status == "released"
