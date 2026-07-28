"""Input-contract enforcement: the ASSEMBLED payload must match the consumer's
schemas/input.json — fail-closed, exactly like output validation.

Only possible since the 2026-07-12 reshape, when the input schemas started
describing the real post-adapter payload instead of a fictional envelope.
"""
import asyncio
import json
import pytest

from engine.binding import RuntimeBinding
from engine.gates import GateBook
from engine.loader import load_workflow
from engine.model import ValidationFailed
from engine.orchestrator import Orchestrator
from engine.runstore import RunStore

from engine.tests.helpers import quorum_aware_hook
from engine.validation import validate_stage_input

APPROVER = "Input Validation Test Operator"
WF_INPUT = {"raw_request": "ShopPilot replay", "requester": "pytest",
            "idempotency_key": "00000000-0000-4000-8000-0000000000aa"}


def _stage(wf, sid):
    return next(s for s in wf.stages if s.id == sid)


def test_config_default_is_enforce():
    assert RuntimeBinding.load().input_validation == "enforce"


def test_assembled_payload_conforms_for_every_stage(tmp_path):
    """The full replay must produce ZERO input-contract findings — 28/28."""
    wf = load_workflow()
    orch = Orchestrator(
        wf, GateBook.load(wf), RuntimeBinding.load(), run_id="input-e2e",
        workflow_input=WF_INPUT, mode="replay",
        store=RunStore("input-e2e", base=tmp_path / "runs"),
        approve_hook=quorum_aware_hook(APPROVER),
    )
    state = asyncio.run(orch.start())
    assert state == "done"
    # Read the RECORDED events, not an attribute AuditLog does not expose: the
    # previous `hasattr(orch.audit, "events")` guard made this assertion vacuous.
    events = [json.loads(l) for l in
              orch.store.events_path.read_text().splitlines() if l.strip()]
    breaches = [e for e in events if e.get("kind") == "input.validation.failed"]
    assert breaches == [], f"input-contract breaches: {breaches}"
    assert any(e.get("kind") == "stage.executed" and e.get("stage") == "ba-breakdown"
               for e in events), "ba-breakdown did not run"


def test_bad_payload_is_rejected_fail_closed():
    """A payload missing a required input field is a contract breach, not a warning."""
    wf = load_workflow()
    stage = _stage(wf, "backend-review")
    good = {"files_generated": [], "tests_generated": [], "api_contracts": {},
            "idempotency_key": "k"}
    assert validate_stage_input(stage, good) == []
    bad = {k: v for k, v in good.items() if k != "api_contracts"}  # drop a required pick
    findings = validate_stage_input(stage, bad)
    assert findings, "a payload missing a required field must be a finding"
    assert any("api_contracts" in f for f in findings)


def test_unknown_key_is_rejected(tmp_path):
    """Strict inputs: a key the consumer never declared is drift, not a freebie."""
    wf = load_workflow()
    stage = _stage(wf, "sast-gate")
    payload = {"files_generated": [], "idempotency_key": "k", "surprise_field": 1}
    findings = validate_stage_input(stage, payload)
    assert any("surprise_field" in f or "additional" in f.lower() for f in findings)
