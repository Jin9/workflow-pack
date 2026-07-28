"""Fixtures: a synthetic mini-workflow workspace (loader-compatible) and a
scripted FakeExecutor, so orchestrator semantics are tested without touching
the real 28-stage pipeline or spending any tokens."""
from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict
from pathlib import Path

import pytest

from engine.executors.base import ExecutionResult
from engine.gates import GateBook
from engine.loader import load_workflow
from engine.model import GateSpec, StageExecutionError
from engine.runstore import RunStore

MINI_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["audit_id"],
    "properties": {"audit_id": {"type": "string"}, "verdict": {"type": "string"}},
}

MINI_YAML = """
apiVersion: cognitive-os/v1
kind: Workflow
metadata: {name: mini, version: 0.0.1, owner: tests}
spec:
  input:
    schema_ref: schemas/mini-input.json
    required_fields: [raw_request]
  output:
    schema_ref: schemas/mini-output.json
    required_fields: [audit_id]
  sla: {p95_latency_seconds: 60, max_retries_per_stage: 3, overall_timeout_seconds: 300}
  default_failure_policy:
    {on_failure: retry, max_retries: 1, backoff: exponential,
     after_max_retries: human-queue, human_queue_name: mini-failures}
  compensation: {enabled: true, timeout_seconds: 60}
  stages:
    - id: alpha
      type: analyze
      skill_ref: skills/alpha
      skill_version: "0.0.1"
      input: {from_workflow_input: [raw_request]}
      output: {schema_ref: schemas/mini.json, required_fields: [audit_id]}
      timeout_seconds: 5
      failure_policy:
        {on_failure: retry, max_retries: 2, backoff: exponential,
         after_max_retries: human-queue, human_queue_name: q-alpha}
    - id: beta
      type: review
      skill_ref: skills/beta
      skill_version: "0.0.1"
      depends_on: [alpha]
      input: {from_stage: {alpha: [audit_id]}}
      output: {schema_ref: schemas/mini.json, required_fields: [audit_id]}
      timeout_seconds: 5
      failure_policy:
        {on_failure: loop_back, loop_to_stage: alpha, max_loops: 1,
         after_max_loops: human-queue, human_queue_name: q-beta}
    - id: delta
      type: generate
      skill_ref: skills/delta
      skill_version: "0.0.1"
      depends_on: [alpha]
      output: {schema_ref: schemas/mini.json, required_fields: [audit_id]}
      timeout_seconds: 5
    - id: gamma
      type: validate
      skill_ref: skills/gamma
      skill_version: "0.0.1"
      depends_on: [beta, delta]
      output: {schema_ref: schemas/mini.json, required_fields: [audit_id]}
      timeout_seconds: 5
    - id: release
      type: notify
      skill_ref: skills/release
      skill_version: "0.0.1"
      depends_on: [gamma]
      output: {schema_ref: schemas/mini.json, required_fields: [audit_id]}
      timeout_seconds: 5
      failure_policy: {on_failure: human-queue, max_retries: 0, human_queue_name: q-release}
      compensating_action:
        {type: revoke, skill_ref: skills/revoke, skill_version: "0.0.1", timeout_seconds: 30}
    - id: post
      type: validate
      skill_ref: skills/post
      skill_version: "0.0.1"
      depends_on: [release]
      output: {schema_ref: schemas/mini.json, required_fields: [audit_id]}
      timeout_seconds: 5
"""


@pytest.fixture()
def mini_workflow(tmp_path):
    wf = tmp_path / "workflows"
    (wf / "schemas").mkdir(parents=True)
    for name in ("mini.json", "mini-input.json", "mini-output.json"):
        (wf / "schemas" / name).write_text(json.dumps(MINI_SCHEMA))
    for skill in ("alpha", "beta", "delta", "gamma", "release", "post", "revoke"):
        d = wf / "skills" / skill
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            f"---\nname: {skill}\nversion: 0.0.1\ndescription: test skill\n---\n# {skill}\n"
        )
    yaml_path = wf / "mini.yaml"
    yaml_path.write_text(MINI_YAML)
    return load_workflow(yaml_path)


class FakeExecutor:
    """Scripted per-stage outcomes: 'ok', 'verdict:<value>', 'raise'.
    The last entry repeats for further attempts."""

    def __init__(self, script=None):
        self.script = script or {}
        self.calls = defaultdict(int)
        self.payloads = defaultdict(list)  # sid -> input payload per attempt

    async def execute(self, ctx) -> ExecutionResult:
        sid = ctx.stage.id
        outcomes = self.script.get(sid, ["ok"])
        outcome = outcomes[min(self.calls[sid], len(outcomes) - 1)]
        self.calls[sid] += 1
        self.payloads[sid].append(dict(ctx.input_payload))
        if outcome == "raise":
            raise StageExecutionError(f"{sid}: scripted failure")
        artifact = {"audit_id": ctx.audit_id}
        if outcome.startswith("verdict:"):
            artifact["verdict"] = outcome.split(":", 1)[1]
        ctx.output_path.parent.mkdir(parents=True, exist_ok=True)
        ctx.output_path.write_text(json.dumps(artifact, sort_keys=True))
        return ExecutionResult("artifact_written", detail=outcome,
                               request_digest={"executor": "fake"})


def all_auto_gates(workflow) -> GateBook:
    return GateBook({s.id: GateSpec(stage_id=s.id, gate="auto") for s in workflow.stages})


def make_orch(workflow, tmp_path, fake, gatebook=None, approve_hook=None, run_id="t-run",
              mode="replay"):
    from engine.binding import RuntimeBinding
    from engine.orchestrator import Orchestrator

    return Orchestrator(
        workflow,
        gatebook or all_auto_gates(workflow),
        RuntimeBinding.load(),
        run_id=run_id,
        workflow_input={"raw_request": "test request", "requester": "pytest",
                        "idempotency_key": "00000000-0000-4000-8000-00000000abcd"},
        mode=mode,
        store=RunStore(run_id, base=tmp_path / "runs"),
        approve_hook=approve_hook,
        # the fake serves every executor slot so live-mode paths (e.g. the SAGA
        # compensation's headless flip) stay token-free in tests
        executors={"replay": fake, "headless": fake, "sdk": fake, "script": fake},
    )


async def drive_until(orch, predicate, timeout=8.0):
    """Start the orchestrator and wait for a condition (e.g. parked at a gate)."""
    task = asyncio.create_task(orch.start())
    t0 = time.monotonic()
    while not predicate(orch) and not task.done():
        if time.monotonic() - t0 > timeout:
            task.cancel()
            raise AssertionError("drive_until timed out")
        await asyncio.sleep(0.01)
    return task
