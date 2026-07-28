import pytest

from engine.mapping import assemble_input
from engine.model import SpecError
from engine.policies import (
    CAVEAT, HUMAN, OK, REWORK, Action, on_failure, route_verdict,
)


def test_assemble_basic_and_nested_discovery(mini_workflow):
    from engine.loader import load_workflow  # real workflow for the nested rule
    wf = load_workflow()
    ba = wf.stage_by_id["ba-breakdown"]
    payload, warnings = assemble_input(
        ba,
        {"raw_request": "r", "requester": "u"},
        {
            "intake": {"normalized_request": "n"},
            "s1-discovery": {"problem_framing": "p", "recommendation": "proceed",
                             "audit_id": "a", "regulatory_regimes": ["BOT"]},
        },
        wf.input_required,
    )
    assert payload["raw_request"] == "r" and payload["normalized_request"] == "n"
    # The YAML-documented nested handoff: s1-discovery fields land under input.discovery
    assert payload["discovery"]["recommendation"] == "proceed"
    assert "handoff_to_intake" not in payload["discovery"]
    assert any("handoff_to_intake" in w for w in warnings)  # optional field absent -> warned


def test_assemble_missing_required_workflow_input_raises(mini_workflow):
    alpha = mini_workflow.stage_by_id["alpha"]
    with pytest.raises(SpecError):
        assemble_input(alpha, {}, {}, ("raw_request",))


def test_verdict_routing_fail_closed():
    assert route_verdict({"verdict": "PASS"}) == OK
    assert route_verdict({"verdict": "conditional"}) == CAVEAT
    assert route_verdict({"verdict": "reject"}) == REWORK
    assert route_verdict({"verdict": "totally-new-word"}) == HUMAN  # unknown -> human
    assert route_verdict({}) == OK  # no verdict field at all


def test_on_failure_retry_then_queue(mini_workflow):
    alpha = mini_workflow.stage_by_id["alpha"]  # retry max 2 -> q-alpha
    assert on_failure(alpha, 1, 0, 0).kind == "retry"
    assert on_failure(alpha, 2, 0, 0).kind == "retry"
    a = on_failure(alpha, 3, 0, 0)
    assert (a.kind, a.queue) == ("human-queue", "q-alpha")


def test_on_failure_loop_cap(mini_workflow):
    beta = mini_workflow.stage_by_id["beta"]  # loop_back to alpha, cap 1 -> q-beta
    a = on_failure(beta, 1, 0, 0)
    assert (a.kind, a.loop_to) == ("loop_back", "alpha")
    a = on_failure(beta, 2, 1, 0)
    assert (a.kind, a.queue) == ("human-queue", "q-beta")
