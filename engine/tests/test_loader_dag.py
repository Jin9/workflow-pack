"""Real-workflow loader + DAG + gate-table facts (fail-closed at load)."""
from engine.dag import Dag
from engine.gates import GateBook
from engine.loader import load_workflow


def test_loads_27_stages_with_resolved_refs():
    wf = load_workflow()
    assert len(wf.stages) == 27
    assert wf.name == "delivery-pipeline"
    for s in wf.stages:
        assert (s.skill_dir / "SKILL.md").is_file()
        assert s.output_schema_path.is_file()


def test_contract_design_policy_is_explicit():
    wf = load_workflow()
    cd = wf.stage_by_id["contract-design"]
    assert cd.failure_policy.on_failure == "retry"
    assert cd.failure_policy.human_queue_name == "contract-design-pending"


def test_s1_composite_human_review():
    wf = load_workflow()
    hr = wf.stage_by_id["s1-discovery"].human_review
    assert hr is not None
    assert (hr.on_field, hr.proceed_when) == ("recommendation", "proceed")
    assert "s1-discovery" in wf.stage_by_id["ba-research"].depends_on


def test_release_handoff_carries_compensation():
    wf = load_workflow()
    comp = wf.stage_by_id["release-handoff"].compensating_action
    assert comp is not None and comp.skill_ref == "skills/handoff-revoke"


def test_dag_parallel_legs_and_cones():
    wf = load_workflow()
    dag = Dag(wf)
    assert len(dag.topo_order) == 27
    be_cone = dag.downstream_cone("backend-implement")
    assert "backend-review" in be_cone and "backend-unit-tests" in be_cone
    assert "qa-plan" in be_cone  # legs rejoin at qa-plan
    assert "frontend-implement" not in be_cone and "frontend-review" not in be_cone
    fe_cone = dag.downstream_cone("frontend-implement")
    assert "backend-implement" not in fe_cone


def test_gatebook_covers_all_stages_and_mirrors_yaml():
    wf = load_workflow()
    gb = GateBook.load(wf)
    assert set(gb.specs) == set(wf.stage_by_id)
    rh = gb.spec_for("release-handoff")
    assert rh.gate == "sync-named" and rh.mandatory and rh.confidence_independent and rh.blocking
    s1 = gb.spec_for("s1-discovery")
    assert s1.blocking and s1.proceed_when == "proceed"
    assert "do-not-build" in s1.verdicts
