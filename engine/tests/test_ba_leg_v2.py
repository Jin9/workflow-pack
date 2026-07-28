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
    return GateInstance(run_id="r", stage_id="ba-breakdown", spec=_spec(),
                        contract_sha256="x", artifact_field_value="ready-for-amigos")


def _brief_spec():
    return GateBook.load(load_workflow()).spec_for("ba-research")


def _brief_gate(state="ready-for-tl"):
    return GateInstance(run_id="r", stage_id="ba-research", spec=_brief_spec(),
                        contract_sha256="x", artifact_field_value=state)


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


@pytest.mark.parametrize("second", ["Khun Pim", "khun pim", "KHUN PIM", "Khun  Pim", " Khun Pim "])
def test_one_human_cannot_cover_two_roles(second):
    """Case and whitespace are not identity. Without normalisation one person
    releases the whole gate by varying their own capitalisation."""
    g = _gate()
    record_verdict(g, "agreed", "Khun Pim", role="ba-lead")
    with pytest.raises(GateApprovalError, match="DISTINCT"):
        record_verdict(g, "agreed", second, role="dev-lead")


def test_no_verdict_releases_a_blocked_breakdown():
    """The documented guarantee that no gate verdict clears a P1 governance gap,
    enforced structurally: the artifact's own state gates the release."""
    s = _spec()
    assert s.release_requires_field_value == "ready-for-amigos"
    g = GateInstance(run_id="r", stage_id="ba-breakdown", spec=s,
                     contract_sha256="x", artifact_field_value="blocked")
    record_verdict(g, "agreed", AMIGOS["ba-lead"], role="ba-lead")
    assert g.status == "blocked"
    assert "release requires" in (g.note or "")
    # and the happy artifact still releases on a full quorum
    ok = GateInstance(run_id="r", stage_id="ba-breakdown", spec=s,
                      contract_sha256="x", artifact_field_value="ready-for-amigos")
    for role in s.required_roles:
        record_verdict(ok, "agreed", AMIGOS[role], role=role)
    assert ok.status == "released"


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


def test_the_quorum_survives_a_missing_gates_yaml():
    """If gates.yaml disappears the fallback must NOT silently downgrade the
    three-amigos gate to something one person can release."""
    from engine.gates import _fail_closed_fallback
    fb = _fail_closed_fallback(load_workflow())["ba-breakdown"]
    assert fb.quorum and fb.blocking and fb.named
    assert fb.required_roles == ("ba-lead", "dev-lead", "qa-lead")
    assert fb.release_requires_field_value == "ready-for-amigos"


def test_the_gate_question_names_what_is_blocking():
    """A reviewer staring at a gate they cannot clear must be told why."""
    s = _spec()
    g = GateInstance(run_id="r", stage_id="ba-breakdown", spec=s,
                     contract_sha256="x", artifact_field_value="blocked")
    assert "BLOCKED" in g.question and "no verdict can clear this" in g.question


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


# ── the gate on the FLESH, not just the shape ────────────────────────────────
# The amigos sign story skeletons with no acceptance criteria. Everything written
# afterwards — 65 AC, the edge-case ledgers, the seven banking-grade rows, which is
# where regulatory interpretation actually happens — used to reach tl-design with no
# human signature and no state check at all: the gate was advisory, so _open_gate
# returned early and `ready-for-tl` was enforced nowhere in the engine.
def test_the_brief_gate_is_blocking_and_named():
    s = _brief_spec()
    assert s.blocking and s.named and not s.quorum
    assert s.proceed_when == "approve"
    assert s.release_requires_field_value == "ready-for-tl"
    assert set(s.verdicts) == {"approve", "needs-work", "reject"}


def test_no_signature_releases_a_needs_work_brief():
    """The BA lead may sign approve; a brief that declares itself unready stays put."""
    for state in ("needs-work", "blocked"):
        g = _brief_gate(state)
        record_verdict(g, "approve", "Khun Pim")
        assert g.status == "blocked", state
        assert "ready-for-tl" in (g.note or "")


def test_a_ready_brief_releases_on_approve_and_blocks_on_reject():
    g = _brief_gate()
    record_verdict(g, "approve", "Khun Pim")
    assert g.status == "released"

    g2 = _brief_gate()
    record_verdict(g2, "reject", "Khun Pim")
    assert g2.status == "blocked"


def test_a_blocking_gate_refuses_an_unnamed_approver():
    """s1-discovery decides proceed vs do-not-build — the highest-blast-radius call
    in the leg — on an async-peer gate with no required_roles, so the named-approver
    check did not apply and `approver="x"` was accepted."""
    s = GateBook.load(load_workflow()).spec_for("s1-discovery")
    assert s.blocking and s.named
    g = GateInstance(run_id="r", stage_id="s1-discovery", spec=s,
                     contract_sha256="x", artifact_field_value="proceed")
    with pytest.raises(GateApprovalError):
        record_verdict(g, "proceed", "x")
    assert g.status == "pending"  # never mutates on failure


def test_a_missing_gates_yaml_does_not_disarm_the_rest_of_the_pipeline():
    """The fallback kept the amigos quorum but defaulted everything else to
    auto/non-blocking, silently disarming every sync-named gate the file would have
    declared — tl-design, the brief's only downstream human, included."""
    from engine.gates import _fail_closed_fallback
    fb = _fail_closed_fallback(load_workflow())
    assert fb["tl-design"].blocking and fb["tl-design"].named
    assert all(g.blocking for g in fb.values())


# ── the reviewers' conditions actually arrive ────────────────────────────────
def test_amigos_conditions_reach_elaboration(tmp_path, monkeypatch):
    """A reviewer who signs "agreed, but ..." has said something BINDING. The skill
    declared amigos_verdict as binding input; the engine populated it nowhere, so the
    condition was recorded in the audit trail and dropped on the floor."""
    from engine.executors.replay import ReplayExecutor
    CONDITION = "guest checkout stays out of scope for this release"
    seen: dict = {}
    original = ReplayExecutor.execute

    async def spy(self, ctx):
        seen.setdefault(ctx.stage.id, ctx.input_payload)
        return await original(self, ctx)

    monkeypatch.setattr(ReplayExecutor, "execute", spy)

    def hook(gate):
        if gate.spec.quorum:
            for role in gate.outstanding_roles:
                note = CONDITION if role == "ba-lead" else f"test {role} approval"
                return ("agreed", AMIGOS[role], note, role)
            return None
        return quorum_aware_hook("Replay Test Operator")(gate)

    wf = load_workflow()
    orch = Orchestrator(
        wf, GateBook.load(wf), RuntimeBinding.load(), run_id="amigos-conditions",
        workflow_input=WF_INPUT, mode="replay",
        store=RunStore("amigos-conditions", base=tmp_path / "runs"), approve_hook=hook,
    )
    state = asyncio.run(orch.start())
    assert state == "done", orch.terminal_reason

    av = seen["ba-research"]["amigos_verdict"]
    assert av["verdict"] == "agreed"
    assert [a["role"] for a in av["approvers"]] == ["ba-lead", "dev-lead", "qa-lead"]
    assert [a["name"] for a in av["approvers"]] == [
        AMIGOS["ba-lead"], AMIGOS["dev-lead"], AMIGOS["qa-lead"]]
    assert CONDITION in av["conditions"]
    # and it is threaded ONLY from a released quorum gate: tl-design's upstreams
    # (ba-research, ux-intake) are ordinary gates, so it must not appear there.
    assert "amigos_verdict" not in seen["tl-design"]


def test_blocks_elaboration_reaches_the_consumer_that_re_checks_it():
    """The skill re-checks breakdown.blocks_elaboration fail-closed, but it was not in
    ba-research's picks and not required in its input schema, so the check no-opped."""
    wf = load_workflow()
    stage = wf.stage_by_id["ba-research"]
    assert "blocks_elaboration" in stage.input_from_stage["ba-breakdown"]
    index = json.loads((SHOPPILOT / "S1b-breakdown" / "INDEX.json").read_text())
    payload, _ = assemble_input(
        stage, WF_INPUT,
        {"intake": {"normalized_request": "n"}, "ba-breakdown": index},
        wf.input_required,
        stage_dirs={"ba-breakdown": SHOPPILOT / "S1b-breakdown"},
    )
    assert payload["breakdown"]["blocks_elaboration"] is False
    assert validate_stage_input(stage, payload) == []
    # and a payload missing it is now REFUSED rather than silently accepted
    del payload["breakdown"]["blocks_elaboration"]
    assert validate_stage_input(stage, payload) != []
