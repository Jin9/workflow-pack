"""The scheduling loop: ready stages -> executor tasks -> policies/gates -> terminal state.

Single-process pure asyncio. All state mutation happens in this loop (no
locks); the backend/frontend legs parallelize because the ready set contains
both once their shared parents succeed. Human gates park the run in
waiting-human until a verdict arrives (API/CLI); an asyncio.Event wakes the
loop. Every attempt logs both halves to the hash-chained audit log.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

from engine import WORKSPACE
from engine.audit import AuditLog, make_audit_id, sha256_file, sha256_hex
from engine.binding import RuntimeBinding
from engine.dag import Dag
from engine.executors import REGISTRY
from engine.executors.base import StageContext
from engine.gates import GateApprovalError, GateBook, GateInstance, record_verdict
from engine.mapping import assemble_input
from engine.model import (
    EngineError,
    StageExecutionError,
    StageTimeout,
    ValidationFailed,
    WorkflowSpec,
)
from engine.policies import CAVEAT, COMPENSATE, FAIL, HUMAN, OK, REWORK, on_failure, route_verdict
from engine.runstore import RunStore, artifact_relpath
from engine.validation import validate_artifact, validate_stage_input

# Run states
R_CREATED, R_RUNNING, R_WAITING = "created", "running", "waiting-human"
R_DONE, R_CAVEATS, R_FAILED, R_HARDFAIL, R_ABORTED = (
    "done", "ship-with-caveats", "failed", "hard-fail", "aborted",
)
TERMINAL_RUN_STATES = {R_DONE, R_CAVEATS, R_FAILED, R_HARDFAIL, R_ABORTED}

# Stage states
S_PENDING, S_RUNNING, S_WAITING_GATE, S_SUCCEEDED = "pending", "running", "waiting-gate", "succeeded"
S_HUMAN, S_FAILED, S_GATE_BLOCKED, S_COMPENSATED = "human-queued", "failed", "gate-blocked", "compensated"


def _unpack_decision(decision) -> tuple:
    """An approve_hook returns (verdict, approver, note) — or, for a quorum gate,
    (verdict, approver, note, role). Accept both so existing hooks are unchanged."""
    if len(decision) == 4:
        return tuple(decision)
    verdict, approver, note = decision
    return (verdict, approver, note, None)


class Orchestrator:
    def __init__(
        self,
        workflow: WorkflowSpec,
        gatebook: GateBook,
        binding: RuntimeBinding,
        run_id: str,
        workflow_input: dict,
        mode: str = "replay",
        store: Optional[RunStore] = None,
        approve_hook: Optional[Callable[[GateInstance], Optional[tuple]]] = None,
        executors: Optional[dict] = None,
    ):
        self.workflow = workflow
        self.dag = Dag(workflow)
        self.gatebook = gatebook
        self.binding = binding
        self.input_validation = getattr(binding, "input_validation", "warn")
        self.run_id = run_id
        self.workflow_input = workflow_input
        self.mode = mode
        self.store = store or RunStore(run_id)
        self.audit = AuditLog(self.store.events_path, deterministic_time=(mode == "replay"))
        self.approve_hook = approve_hook
        self._executors = executors or {}
        self._gate_event: Optional[asyncio.Event] = None  # lazy: py3.9 Event binds a loop at construction

        self.run_state = R_CREATED
        self.terminal_reason: Optional[str] = None
        self.request_type = workflow_input.get("request_type", "new-product")
        self.stage: Dict[str, dict] = {
            s.id: {"state": S_PENDING, "attempts": 0, "error": None, "artifact": None,
                   "artifact_sha256": None, "audit_id": None, "caveat": False, "queue": None,
                   "duration_seconds": 0.0}
            for s in workflow.stages
        }
        self.loop_ledger: Dict[str, int] = {}
        self.loop_feedback: Dict[str, dict] = {}  # loop_to stage -> reviewer findings for the re-run
        self.gates: Dict[str, GateInstance] = {}
        self.events: List[dict] = []  # bounded in-memory mirror for the API/pack
        self.pack_seq = 0
        self._started_monotonic = 0.0

    # ── helpers ────────────────────────────────────────────────────────────────
    @property
    def gate_event(self) -> asyncio.Event:
        if self._gate_event is None:
            self._gate_event = asyncio.Event()
        return self._gate_event

    def _executor_for(self, kind: str):
        if kind not in self._executors:
            self._executors[kind] = REGISTRY[kind]()
        return self._executors[kind]

    def emit(self, kind: str, stage_id: Optional[str] = None, **fields) -> None:
        event = self.audit.emit(kind, self.run_id, stage_id, **fields)
        self.events.append(event)
        if len(self.events) > 800:
            del self.events[:200]
        self.pack_seq += 1

    def snapshot(self) -> dict:
        return {
            "run_id": self.run_id,
            "mode": self.mode,
            "state": self.run_state,
            "terminal_reason": self.terminal_reason,
            "request_type": self.request_type,
            "workflow": {"name": self.workflow.name, "version": self.workflow.version},
            "input": self.workflow_input,
            "stages": self.stage,
            "loop_ledger": self.loop_ledger,
            "gates": [g.as_record() for g in self.gates.values()],
            "pack_seq": self.pack_seq,
        }

    def _persist(self) -> None:
        self.store.write_json("state.json", self.snapshot())

    # ── gates ──────────────────────────────────────────────────────────────────
    def pending_gates(self) -> List[GateInstance]:
        return [g for g in self.gates.values() if g.status == "pending"]

    def post_verdict(self, stage_id: str, verdict: str, approver: str,
                     note: Optional[str] = None, role: Optional[str] = None) -> GateInstance:
        gate = self.gates.get(stage_id)
        if gate is None:
            raise EngineError(f"no gate instance for stage {stage_id!r}")
        record_verdict(gate, verdict, approver, note, ts=time.time(), role=role)
        event = {
            "gate": gate.spec.gate, "verdict": verdict, "approver": gate.approver,
            "status": gate.status, "note": note, "contract_sha256": gate.contract_sha256,
        }
        if gate.spec.quorum:
            event.update(role=role, signed_roles=gate.signed_roles,
                         outstanding_roles=gate.outstanding_roles)
        self.emit("gate.verdict", stage_id, **event)
        rec = self.stage[stage_id]
        if gate.status == "pending":
            # Quorum not yet met. Record the signature and change NOTHING about the
            # stage: a partially-signed gate is still an open gate. The event is
            # still set — the waiter re-evaluates, finds nothing ready and sleeps
            # again, which is cheap and avoids a wake-up race with the API caller.
            self._persist()
            self.gate_event.set()
            return gate
        if gate.status in ("released", "released-with-caveat"):
            rec["state"] = S_SUCCEEDED
            rec["caveat"] = rec["caveat"] or gate.status == "released-with-caveat"
        elif self._gate_loop_back(stage_id, gate):
            pass  # the loop-back arm has already reset the cone and emitted
        else:
            rec["state"] = S_GATE_BLOCKED
            rec["queue"] = gate.spec.on_block or gate.spec.exception_queue
        self._persist()
        self.gate_event.set()
        return gate

    def _gate_loop_back(self, stage_id: str, gate: GateInstance) -> bool:
        """A non-releasing verdict on a stage whose failure_policy is loop_back sends
        the work BACK with the reviewers' findings attached, instead of failing the
        run. Without this a three-amigos `split-stories` verdict — an ordinary,
        expected review outcome — would terminate the run.

        The findings come from the GATE (what the humans said), never from the
        stage artifact: _apply_failure re-derives feedback from the artifact, which
        would overwrite the human input and send a blind re-run."""
        spec = self.workflow.stage_by_id[stage_id]
        fp = spec.failure_policy
        if fp.on_failure != "loop_back" or not fp.loop_to_stage:
            return False
        edge = f"{stage_id}->{fp.loop_to_stage}"
        action = on_failure(spec, 1, self.loop_ledger.get(edge, 0),
                            self.binding.for_stage(stage_id, self.mode).backoff_multiplier)
        if action.kind != "loop_back":
            return False  # cycle cap reached -> fall through to blocked/queue as designed
        self.loop_ledger[edge] = self.loop_ledger.get(edge, 0) + 1
        self.loop_feedback[action.loop_to] = {
            "from_stage": stage_id,
            "source": "gate",
            "verdict": gate.verdict,
            "reviewers": [
                {k: a[k] for k in ("role", "approver", "verdict", "note") if a.get(k) is not None}
                for a in gate.approvals
            ] or [{"approver": gate.approver, "verdict": gate.verdict, "note": gate.note}],
            "findings": [a["note"] for a in gate.approvals if a.get("note")]
            or ([gate.note] if gate.note else []),
            "loop_count": self.loop_ledger[edge],
        }
        cone = self.dag.downstream_cone(action.loop_to)
        reset = []
        for sid in cone:
            if self.stage[sid]["state"] != S_PENDING:
                self.stage[sid]["state"] = S_PENDING
                self.stage[sid]["error"] = None
                reset.append(sid)
        self.gates.pop(stage_id, None)  # the re-run opens a fresh gate
        fb = self.loop_feedback[action.loop_to]
        self.emit("gate.loop-back", stage_id, loop_to=action.loop_to,
                  verdict=gate.verdict, loop_count=self.loop_ledger[edge],
                  reset=sorted(reset),
                  # WHO sent it back and WHAT they said belongs in the HITL record;
                  # loop_feedback itself is popped when the re-run consumes it.
                  reviewers=[a.get("approver") for a in gate.approvals] or [gate.approver],
                  findings=fb["findings"])
        return True

    def _open_gate(self, stage_id: str, artifact: dict) -> None:
        spec = self.gatebook.spec_for(stage_id)
        rec = self.stage[stage_id]
        if spec is None or not spec.blocking:
            if spec is not None and spec.gate not in ("auto", "auto+exception"):
                self.emit("gate.advisory", stage_id, gate=spec.gate, owner_role=spec.owner_role)
            rec["state"] = S_SUCCEEDED
            return
        gate = GateInstance(
            run_id=self.run_id, stage_id=stage_id, spec=spec,
            contract_sha256=rec["artifact_sha256"] or "",
            artifact_field_value=(str(artifact.get(spec.on_field)) if spec.on_field else None),
        )
        self.gates[stage_id] = gate
        rec["state"] = S_WAITING_GATE
        self.emit("gate.opened", stage_id, gate=spec.gate, owner_role=spec.owner_role,
                  question=gate.question, blocking=True)
        if self.approve_hook is not None:
            # A quorum gate needs one decision PER ROLE, so the hook is re-invoked
            # while the gate stays pending. The bound is the role count: a hook that
            # keeps returning the same role hits record_verdict's already-signed
            # guard rather than spinning.
            for _ in range(max(1, len(spec.required_roles))):
                if self.gates.get(stage_id) is not gate or gate.status != "pending":
                    break
                decision = self.approve_hook(gate)
                if decision is None:
                    break
                verdict, approver, note, dec_role = _unpack_decision(decision)
                try:
                    self.post_verdict(stage_id, verdict, approver, note, role=dec_role)
                except GateApprovalError as e:
                    # A malformed automated decision must PARK the gate, not spin the
                    # run waiting for a verdict that can never arrive. The gate stays
                    # pending for a human; the reason is on the record.
                    self.emit("gate.hook-refused", stage_id, reason=str(e)[:200])
                    break

    # ── stage attempt ──────────────────────────────────────────────────────────
    async def _run_stage(self, stage_id: str) -> None:
        spec = self.workflow.stage_by_id[stage_id]
        rec = self.stage[stage_id]
        rec["attempts"] += 1
        attempt = rec["attempts"]
        stage_binding = self.binding.for_stage(stage_id, self.mode)
        if attempt > 1 and stage_binding.backoff_multiplier > 0:
            await asyncio.sleep(min(30.0, stage_binding.backoff_multiplier * (2 ** (attempt - 2))))

        audit_id = make_audit_id(self.run_id, stage_id, attempt, deterministic=(self.mode == "replay"))
        rec["audit_id"] = audit_id
        artifacts = {
            src: self.store.read_artifact(src) for src in spec.input_from_stage
        }
        stage_dirs = {src: self.store.stage_dir(src) for src in spec.input_from_stage}
        payload, warnings = assemble_input(spec, self.workflow_input, artifacts,
                                           self.workflow.input_required, stage_dirs)
        if spec.input_from_stage:
            # Where each upstream artifact lives, relative to THIS stage's dir —
            # contracts carry *_file references (e.g. the INDEX's discovery_file)
            # and an agent must not have to guess run-dir topology (run-66666666
            # wrote discovery_file: null five times for lack of exactly this).
            own_dir = self.store.stage_dir(stage_id)
            payload["upstream_artifacts"] = {
                src: os.path.relpath(self.store.artifact_path(src), own_dir)
                for src in spec.input_from_stage
            }
        feedback = self.loop_feedback.pop(stage_id, None)
        if feedback is not None:
            # A downstream reviewer looped back to this stage: the re-run must see
            # WHY ("reroute high findings back" — the loop is pointless blind).
            payload["loop_back_feedback"] = feedback
        for w in warnings:
            self.emit("mapping.warning", stage_id, message=w)

        # The assembled payload must match the consumer's declared input contract.
        # Enforcement is config-gated (engine/config/runtime-binding.yaml
        # input_validation: off | warn | enforce) — the schemas describe the real
        # post-adapter payload since the 2026-07-12 reshape.
        input_findings = validate_stage_input(spec, payload)
        if input_findings:
            self.emit("input.validation.failed", stage_id, attempt=attempt,
                      findings=input_findings[:10], count=len(input_findings))
            if self.input_validation == "enforce":
                raise ValidationFailed(f"{stage_id}: assembled input", input_findings)

        output_path = self.store.artifact_path(stage_id)
        ctx = StageContext(
            run_id=self.run_id, stage=spec, input_payload=payload,
            output_path=output_path, stage_dir=output_path.parent,
            audit_id=audit_id, binding=stage_binding, workspace=WORKSPACE,
        )
        executor = self._executor_for(stage_binding.executor)
        self.emit("stage.started", stage_id, attempt=attempt, executor=stage_binding.executor,
                  model=stage_binding.model, audit_id=audit_id,
                  input_sha256=sha256_hex(json.dumps(payload, sort_keys=True).encode()))

        backstop = max(60.0, spec.timeout_seconds * stage_binding.timeout_multiplier + 60.0)
        result = await asyncio.wait_for(executor.execute(ctx), timeout=backstop)

        artifact = validate_artifact(spec, output_path)
        rec["artifact"] = artifact_relpath(stage_id)
        rec["artifact_sha256"] = sha256_file(output_path)
        rec["duration_seconds"] = round(result.duration_seconds, 3)
        self.emit("stage.executed", stage_id, attempt=attempt, audit_id=audit_id,
                  request=result.request_digest, artifact=rec["artifact"],
                  artifact_sha256=rec["artifact_sha256"], validation="pass",
                  duration_seconds=rec["duration_seconds"])

        route = route_verdict(artifact)
        if route == OK:
            self._open_gate(stage_id, artifact)
        elif route == CAVEAT:
            rec["caveat"] = True
            self.emit("stage.caveat", stage_id, verdict=str(artifact.get("verdict")))
            self._open_gate(stage_id, artifact)
        elif route == HUMAN:
            self._to_human_queue(stage_id, f"verdict {artifact.get('verdict')!r} needs a human")
        elif route == COMPENSATE:
            self.emit("stage.rollback-verdict", stage_id, verdict=str(artifact.get("verdict")))
            await self._compensate(f"{stage_id} verdict demanded rollback")
            rec["state"] = S_FAILED
            rec["error"] = "rollback verdict"
        elif route in (REWORK, FAIL):
            raise StageExecutionError(
                f"{stage_id}: artifact verdict {artifact.get('verdict')!r} routed to {route}"
            )

    def _to_human_queue(self, stage_id: str, reason: str, queue: Optional[str] = None) -> None:
        spec = self.workflow.stage_by_id[stage_id]
        rec = self.stage[stage_id]
        rec["state"] = S_HUMAN
        rec["queue"] = queue or spec.failure_policy.human_queue_name or "delivery-failures"
        rec["error"] = reason
        self.emit("stage.human-queued", stage_id, queue=rec["queue"], reason=reason)

    def _apply_failure(self, stage_id: str, error: Exception) -> None:
        spec = self.workflow.stage_by_id[stage_id]
        rec = self.stage[stage_id]
        rec["error"] = str(error)
        self.emit("stage.failed", stage_id, attempt=rec["attempts"], error=str(error)[:500],
                  error_kind=type(error).__name__)
        edge = f"{stage_id}->{spec.failure_policy.loop_to_stage}"
        action = on_failure(spec, rec["attempts"], self.loop_ledger.get(edge, 0),
                            self.binding.for_stage(stage_id, self.mode).backoff_multiplier)
        if action.kind == "retry":
            rec["state"] = S_PENDING
            self.emit("stage.retry-scheduled", stage_id, next_attempt=rec["attempts"] + 1)
        elif action.kind == "loop_back":
            self.loop_ledger[edge] = self.loop_ledger.get(edge, 0) + 1
            existing = self.loop_feedback.get(action.loop_to)
            if existing and existing.get("source") == "gate":
                # A human already told this stage what to change. Re-deriving feedback
                # from the artifact here would overwrite their words and send a BLIND
                # re-run — the exact failure the loop exists to prevent.
                existing["loop_count"] = self.loop_ledger[edge]
            else:
                try:  # thread the reviewer's findings into the re-run (data, not instructions)
                    artifact = self.store.read_artifact(stage_id)
                    self.loop_feedback[action.loop_to] = {
                        "from_stage": stage_id,
                        "source": "artifact",
                        "verdict": artifact.get("verdict"),
                        "findings": artifact.get("findings", [])[:20],
                        "loop_count": self.loop_ledger[edge],
                    }
                except Exception:
                    pass  # no artifact (execution error) -> the re-run gets no feedback
            cone = self.dag.downstream_cone(action.loop_to)
            reset = []
            for sid in cone:
                if self.stage[sid]["state"] != S_PENDING:
                    self.stage[sid]["state"] = S_PENDING
                    self.stage[sid]["error"] = None
                    reset.append(sid)
            self.emit("stage.loop-back", stage_id, loop_to=action.loop_to,
                      loop_count=self.loop_ledger[edge], reset=sorted(reset))
        elif action.kind == "human-queue":
            self._to_human_queue(stage_id, str(error), queue=action.queue)
        else:  # abort
            rec["state"] = S_FAILED
            self.emit("stage.abort", stage_id, reason=str(error)[:200])
            self._finish(R_HARDFAIL, f"{stage_id}: {spec.failure_policy.after_max_loops or 'abort'}")

    # ── compensation (SAGA) ────────────────────────────────────────────────────
    def _comp_stage_spec(self, s, comp):
        """The compensation runs the COMPENSATING skill against its own boundary
        schema — not the stage's skill (a live revoke must never re-run the
        deploy handoff)."""
        from engine.model import StageSpec
        return StageSpec(
            id=f"{s.id}::compensation", type="notify",
            skill_ref=comp.skill_ref, skill_version=comp.skill_version,
            depends_on=(), input_from_workflow=(), input_from_stage={},
            output_schema_ref=comp.output_schema_ref or "",
            required_fields=(),  # the dual schemas carry the required fields
            timeout_seconds=comp.timeout_seconds,
            failure_policy=self.workflow.default_failure_policy,
            skill_dir=comp.skill_dir or (WORKSPACE / "workflows" / comp.skill_ref),
            output_schema_path=comp.output_schema_path
            or (WORKSPACE / "workflows" / "schemas" / "__no-boundary__.json"),
        )

    async def _compensate(self, reason: str) -> None:
        for s in self.workflow.stages:
            if s.compensating_action is None:
                continue
            rec = self.stage[s.id]
            if rec["state"] not in (S_SUCCEEDED, S_WAITING_GATE):
                continue
            comp = s.compensating_action
            self.emit("compensation.triggered", s.id, action=comp.type,
                      skill_ref=comp.skill_ref, reason=reason)
            if self.mode == "live":
                stage_binding = self.binding.for_stage(s.id, self.mode)
                executor = self._executor_for(
                    stage_binding.executor if stage_binding.executor in ("headless", "sdk")
                    else "headless")
                comp_spec = self._comp_stage_spec(s, comp)
                out = self.store.stage_dir(s.id) / "revoke-receipt.json"
                receipt = None
                try:
                    receipt = self.store.read_artifact(s.id)
                except Exception:
                    pass
                audit_id = make_audit_id(self.run_id, comp_spec.id, 1, False)
                ctx = StageContext(
                    run_id=self.run_id, stage=comp_spec,
                    input_payload={
                        "reason": reason,
                        "original_receipt": receipt,
                        "idempotency_key": self.workflow_input.get("idempotency_key"),
                        "upstream_artifacts": {s.id: artifact_relpath(s.id).rsplit("/", 1)[-1]},
                    },
                    output_path=out, stage_dir=out.parent,
                    audit_id=audit_id, binding=stage_binding, workspace=WORKSPACE,
                )
                try:
                    await asyncio.wait_for(executor.execute(ctx), timeout=comp.timeout_seconds)
                    artifact = validate_artifact(comp_spec, out)
                    self.emit("compensation.executed", s.id, artifact=out.name,
                              artifact_sha256=sha256_file(out), audit_id=audit_id,
                              status=str(artifact.get("status")))
                except Exception as e:  # a failed revoke is an ALERT, not a silent pass
                    self.emit("compensation.failed", s.id, error=str(e)[:300],
                              queue="delivery-handoff-failures")
            else:
                self.emit("compensation.simulated", s.id,
                          note="replay mode records, does not execute, the revoke")
            rec["state"] = S_COMPENSATED

    # ── main loop ──────────────────────────────────────────────────────────────
    def _eligible(self) -> List[str]:
        done = {sid for sid, r in self.stage.items() if r["state"] == S_SUCCEEDED}
        return [
            sid for sid in self.dag.topo_order
            if self.stage[sid]["state"] == S_PENDING
            and all(p in done for p in self.dag.parents[sid])
        ]

    def _derive_terminal(self) -> Optional[tuple]:
        states = {sid: r["state"] for sid, r in self.stage.items()}
        if any(s == S_COMPENSATED for s in states.values()):
            return (R_HARDFAIL, "compensated (SAGA revoke recorded)")
        if any(s == S_FAILED for s in states.values()):
            failed = [sid for sid, s in states.items() if s == S_FAILED]
            return (R_FAILED, f"stage failed: {', '.join(sorted(failed))}")
        if any(s == S_GATE_BLOCKED for s in states.values()):
            blocked = [sid for sid, s in states.items() if s == S_GATE_BLOCKED]
            return (R_FAILED, f"gate blocked: {', '.join(sorted(blocked))}")
        if all(s == S_SUCCEEDED for s in states.values()):
            caveats = [sid for sid, r in self.stage.items() if r["caveat"]]
            if caveats:
                return (R_CAVEATS, f"caveats: {', '.join(sorted(caveats))}")
            return (R_DONE, None)
        return None

    def _finish(self, state: str, reason: Optional[str]) -> None:
        if self.run_state in TERMINAL_RUN_STATES:
            return
        self.run_state = state
        self.terminal_reason = reason
        self.emit("run.finished", state=state, reason=reason)
        if state in (R_DONE, R_CAVEATS):
            self._write_workflow_output()
        self._persist()

    def _write_workflow_output(self) -> None:
        mapping = {
            "ba_brief": "ba-research", "ux_pack": "ux-intake", "tl_design": "tl-design",
            "backend_artifacts": "backend-implement", "frontend_artifacts": "frontend-implement",
            "qa_plan": "qa-plan", "qa_evidence": "qa-validate",
            "handoff_receipt": "release-handoff", "prod_validation": "prod-validate",
        }
        out = {"audit_id": make_audit_id(self.run_id, "workflow-output", 1,
                                         deterministic=(self.mode == "replay"))}
        for field, sid in mapping.items():
            rec = self.stage.get(sid, {})
            out[field] = {"artifact": rec.get("artifact"), "sha256": rec.get("artifact_sha256")}
        self.store.write_json("output.json", out)

    def resolve_stage(self, stage_id: str, action: str, resolver: str,
                      note: Optional[str] = None) -> dict:
        """Typed human resolution of a HUMAN-QUEUED stage (the failure queue,
        distinct from gates). `retry` grants one more attempt and wakes the
        loop; `abort` ends the run. Requires a named resolver — this is a HITL
        record, not an auto path."""
        rec = self.stage.get(stage_id)
        if rec is None:
            raise EngineError(f"unknown stage {stage_id!r}")
        if rec["state"] != S_HUMAN:
            raise EngineError(f"stage {stage_id} is not human-queued (state={rec['state']})")
        if not resolver or not str(resolver).strip():
            raise EngineError("a resolution requires a named human resolver")
        if action == "retry":
            rec["state"] = S_PENDING
            rec["error"] = None
            rec["queue"] = None
        elif action == "abort":
            self._finish(R_ABORTED, f"human abort at {stage_id} by {resolver}")
        else:
            raise EngineError(f"unknown resolution action {action!r} (retry|abort)")
        self.emit("stage.human-resolved", stage_id, action=action,
                  resolver=str(resolver).strip(), note=note)
        self._persist()
        self.gate_event.set()
        return {"stage_id": stage_id, "action": action, "state": self.stage[stage_id]["state"],
                "resolver": str(resolver).strip()}

    def abort(self, reason: str = "operator abort") -> None:
        self._finish(R_ABORTED, reason)
        self.gate_event.set()

    async def start(self) -> str:
        self.run_state = R_RUNNING
        self._started_monotonic = time.monotonic()
        self.emit("run.created", mode=self.mode, request_type=self.request_type,
                  workflow=f"{self.workflow.name}@{self.workflow.version}",
                  input_sha256=sha256_hex(
                      json.dumps(self.workflow_input, sort_keys=True).encode()))
        self._persist()
        tasks: Dict[str, asyncio.Task] = {}
        try:
            while self.run_state not in TERMINAL_RUN_STATES:
                if (self.mode == "live"
                        and time.monotonic() - self._started_monotonic
                        > self.workflow.sla.overall_timeout_seconds):
                    self._finish(R_ABORTED, "overall_timeout_seconds exceeded")
                    break

                for sid in self._eligible():
                    if sid not in tasks:
                        self.stage[sid]["state"] = S_RUNNING
                        tasks[sid] = asyncio.create_task(self._run_stage(sid), name=sid)
                self._persist()

                if not tasks:
                    terminal = self._derive_terminal()
                    if terminal:
                        self._finish(*terminal)
                        break
                    if self.pending_gates() or any(
                        r["state"] == S_HUMAN for r in self.stage.values()
                    ):
                        self.run_state = R_WAITING
                        self._persist()
                        self.gate_event.clear()
                        await self.gate_event.wait()
                        if self.run_state not in TERMINAL_RUN_STATES:
                            self.run_state = R_RUNNING
                        continue
                    self._finish(R_FAILED, "no runnable stages and no open gates (deadlock)")
                    break

                done, _ = await asyncio.wait(set(tasks.values()),
                                             return_when=asyncio.FIRST_COMPLETED)
                for t in done:
                    sid = t.get_name()
                    tasks.pop(sid, None)
                    try:
                        t.result()
                    except (StageExecutionError, StageTimeout, ValidationFailed,
                            asyncio.TimeoutError) as e:
                        err = e if not isinstance(e, asyncio.TimeoutError) else \
                            StageTimeout(f"{sid}: orchestrator backstop timeout")
                        if isinstance(e, ValidationFailed):
                            for m in e.errors[:8]:
                                self.emit("validation.finding", sid, finding=m)
                        self._apply_failure(sid, err)
                    # A loop_back may have reset stages that currently have tasks:
                    for other_sid in [s for s in list(tasks) if
                                      self.stage[s]["state"] == S_PENDING]:
                        tasks.pop(other_sid).cancel()
                self._persist()
        finally:
            for t in tasks.values():
                t.cancel()
            if self.run_state not in TERMINAL_RUN_STATES:
                self._finish(R_FAILED, "orchestrator exited unexpectedly")
        return self.run_state
