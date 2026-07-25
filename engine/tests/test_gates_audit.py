import pytest

from engine.audit import AuditLog, verify_chain
from engine.gates import GateApprovalError, GateInstance, record_verdict
from engine.model import GateSpec


def _gate(**over):
    spec = GateSpec(stage_id="release-handoff", gate="sync-named",
                    owner_role="release-manager", blocking=True, mandatory=True,
                    **over)
    return GateInstance(run_id="r", stage_id="release-handoff", spec=spec,
                        contract_sha256="deadbeef")


def test_sync_named_requires_a_named_human():
    with pytest.raises(GateApprovalError):
        record_verdict(_gate(), "approve", "")
    with pytest.raises(GateApprovalError):
        record_verdict(_gate(), "approve", "   ")
    g = record_verdict(_gate(), "approve", "Release Manager Somchai")
    assert g.status == "released" and g.approver == "Release Manager Somchai"


def test_verdict_vocabulary_is_enforced_verbatim():
    with pytest.raises(GateApprovalError):
        record_verdict(_gate(), "LGTM", "Somchai")
    spec = GateSpec(stage_id="adversarial-pentest", gate="human", owner_role="governance",
                    blocking=True, verdicts=("pass", "conditional", "fail"))
    g = GateInstance(run_id="r", stage_id="adversarial-pentest", spec=spec, contract_sha256="x")
    assert record_verdict(g, "conditional", "Gov Officer").status == "released-with-caveat"


def test_on_field_machine_gate_releases_only_on_proceed():
    spec = GateSpec(stage_id="s1-discovery", gate="async-peer", owner_role="ba-lead",
                    blocking=True, on_field="recommendation", proceed_when="proceed",
                    on_block="ba-discovery-review",
                    verdicts=("proceed", "needs-work", "do-not-build"))
    g = GateInstance(run_id="r", stage_id="s1-discovery", spec=spec, contract_sha256="x",
                     artifact_field_value="proceed")
    blocked = GateInstance(run_id="r", stage_id="s1-discovery", spec=spec,
                           contract_sha256="x", artifact_field_value="needs-work")
    assert record_verdict(g, "proceed", "BA Lead").status == "released"
    assert record_verdict(blocked, "needs-work", "BA Lead").status == "blocked"


def test_gate_cannot_be_decided_twice():
    g = record_verdict(_gate(), "approve", "Somchai")
    with pytest.raises(GateApprovalError):
        record_verdict(g, "reject", "Somebody Else")


def test_audit_chain_verifies_and_detects_tamper(tmp_path):
    log = AuditLog(tmp_path / "events.jsonl")
    for i in range(4):
        log.emit("test.event", "run-1", None, index=i)
    assert verify_chain(tmp_path / "events.jsonl") == 4

    lines = (tmp_path / "events.jsonl").read_text().splitlines()
    lines[1] = lines[1].replace('"index": 1', '"index": 99')  # tamper
    (tmp_path / "events.jsonl").write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError):
        verify_chain(tmp_path / "events.jsonl")


def test_no_pii_style_payloads_in_events(tmp_path):
    """Events carry digests + names, never raw request bodies."""
    log = AuditLog(tmp_path / "e.jsonl")
    log.emit("run.created", "run-1", None, input_sha256="ab" * 32)
    text = (tmp_path / "e.jsonl").read_text()
    assert "input_sha256" in text and "raw_request" not in text
