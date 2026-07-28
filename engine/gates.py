"""Human gates: load engine/config/gates.yaml, hold the queue, record verdicts.

Structural guarantees (tested, not prompted):
- A blocking gate clears ONLY through record_verdict(); there is no auto path.
- sync-named / human gates REQUIRE a named human approver string; the engine
  ships no default approver anywhere.
- Verdicts must belong to the gate's own vocabulary — never normalized.
- If gates.yaml is missing the fallback is FAIL-CLOSED: the s1-discovery
  machine gate (mirrored from the pipeline's human_review block) plus a
  mandatory sync-named gate on release-handoff.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from jsonschema import validate as js_validate

from engine import ENGINE_DIR
from engine.model import EngineError, GateSpec, SpecError, WorkflowSpec

GATES_PATH = ENGINE_DIR / "config" / "gates.yaml"
GATES_SCHEMA_PATH = ENGINE_DIR / "config" / "gates.schema.json"

# Verdict values that release a blocking gate; "conditional" releases with a caveat.
RELEASE_VERDICTS = {"approve", "proceed", "pass", "promote", "go"}
CAVEAT_VERDICTS = {"conditional"}


class GateApprovalError(EngineError):
    pass


def _identity(name: str) -> str:
    """Comparison key for 'is this the same human?'.

    Case and whitespace are NOT identity: without this, one person releases a
    three-amigos gate by signing 'Khun Pim', 'khun pim' and 'Khun  Pim'. This
    cannot stop a determined impersonator — no software can — but the guarantee
    must not fall to a capitalisation."""
    return " ".join(str(name).split()).casefold()


@dataclass
class GateInstance:
    run_id: str
    stage_id: str
    spec: GateSpec
    contract_sha256: str
    artifact_field_value: Optional[str] = None  # e.g. the discovery `recommendation`
    status: str = "pending"  # pending | released | released-with-caveat | blocked
    verdict: Optional[str] = None
    approver: Optional[str] = None
    note: Optional[str] = None
    decided_ts: Optional[float] = None
    # QUORUM gates only: one accumulated row per signing role. The single-approver
    # fields above stay populated with the DECISIVE signature, so every existing
    # consumer of as_record() keeps working unchanged.
    approvals: List[dict] = field(default_factory=list)

    @property
    def signed_roles(self) -> List[str]:
        return [a["role"] for a in self.approvals if a.get("role")]

    @property
    def outstanding_roles(self) -> List[str]:
        signed = set(self.signed_roles)
        return [r for r in self.spec.required_roles if r not in signed]

    @property
    def question(self) -> str:
        if self.spec.quorum:
            gap = ""
            if (self.spec.release_requires_field_value is not None
                    and self.artifact_field_value != self.spec.release_requires_field_value):
                gap = (f"; BLOCKED: artifact {self.spec.on_field} is "
                       f"{self.artifact_field_value!r}, release requires "
                       f"{self.spec.release_requires_field_value!r} — no verdict can clear this")
            return (
                f"{self.stage_id}: artifact {self.spec.on_field} = "
                f"{self.artifact_field_value!r}; "
                f"{'/'.join(self.spec.required_roles)} must each sign; "
                f"still outstanding: {self.outstanding_roles or 'none'}; "
                f"release requires every signature to be {self.spec.proceed_when!r}{gap}"
            )
        if self.spec.on_field:
            return (
                f"{self.stage_id}: artifact {self.spec.on_field} = "
                f"{self.artifact_field_value!r}; release requires verdict "
                f"{self.spec.proceed_when!r}"
            )
        return f"{self.stage_id}: {self.spec.gate} gate ({self.spec.owner_role or 'unassigned'})"

    def as_record(self) -> dict:
        rec = {
            "run_id": self.run_id,
            "stage_id": self.stage_id,
            "gate": self.spec.gate,
            "owner_role": self.spec.owner_role,
            "blocking": self.spec.blocking,
            "contract_sha256": self.contract_sha256,
            "artifact_field_value": self.artifact_field_value,
            "status": self.status,
            "verdict": self.verdict,
            "approver": self.approver,
            "note": self.note,
            "question": self.question,
            "verdicts": list(self.spec.verdicts),
        }
        if self.spec.quorum:
            rec["required_roles"] = list(self.spec.required_roles)
            rec["approvals"] = list(self.approvals)
            rec["outstanding_roles"] = self.outstanding_roles
        return rec


class GateBook:
    def __init__(self, specs: Dict[str, GateSpec]):
        self.specs = specs

    @classmethod
    def load(cls, workflow: WorkflowSpec, path: Path = GATES_PATH) -> "GateBook":
        if not path.is_file():
            return cls(_fail_closed_fallback(workflow))
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        schema = json.loads(GATES_SCHEMA_PATH.read_text(encoding="utf-8"))
        js_validate(doc, schema)
        defaults = doc.get("defaults", {})
        specs: Dict[str, GateSpec] = {}
        for g in doc["gates"]:
            sid = g["stage_id"]
            if sid not in workflow.stage_by_id:
                raise SpecError(f"gates.yaml references unknown stage {sid!r}")
            if sid in specs:
                raise SpecError(f"gates.yaml has a duplicate entry for {sid!r}")
            specs[sid] = GateSpec(
                stage_id=sid,
                gate=g["gate"],
                owner_role=g.get("owner_role"),
                blocking=bool(g.get("blocking", defaults.get("blocking", False))),
                mandatory=bool(g.get("mandatory", False)),
                confidence_independent=bool(g.get("confidence_independent", False)),
                on_field=g.get("on_field"),
                proceed_when=g.get("proceed_when"),
                on_block=g.get("on_block"),
                verdicts=tuple(g.get("verdicts", defaults.get("verdicts", ["approve", "reject"]))),
                exception_queue=g.get("exception_queue"),
                # Read explicitly: an unknown key is silently dropped here, which
                # would leave a quorum gate releasable by one signature.
                required_roles=tuple(g.get("required_roles", ())),
                release_requires_field_value=g.get("release_requires_field_value"),
            )
        missing = set(workflow.stage_by_id) - set(specs)
        if missing:
            raise SpecError(f"gates.yaml does not cover stages: {sorted(missing)}")
        # The pipeline's own human_review block must be mirrored, not contradicted.
        for s in workflow.stages:
            if s.human_review:
                g = specs[s.id]
                if (g.on_field, g.proceed_when, g.on_block) != (
                    s.human_review.on_field, s.human_review.proceed_when, s.human_review.on_block
                ):
                    raise SpecError(f"gates.yaml drifted from {s.id} human_review block")
        return cls(specs)

    def spec_for(self, stage_id: str) -> Optional[GateSpec]:
        return self.specs.get(stage_id)


def _fail_closed_fallback(workflow: WorkflowSpec) -> Dict[str, GateSpec]:
    specs: Dict[str, GateSpec] = {}
    for s in workflow.stages:
        if s.human_review:
            specs[s.id] = GateSpec(
                stage_id=s.id, gate=s.human_review.gate, owner_role="ba-lead",
                blocking=True, on_field=s.human_review.on_field,
                proceed_when=s.human_review.proceed_when, on_block=s.human_review.on_block,
                verdicts=("proceed", "needs-work", "do-not-build"),
            )
        elif s.id == "ba-breakdown":
            # Without gates.yaml the three-amigos quorum would vanish entirely and a
            # single approver would release the breakdown. Fail CLOSED: keep the
            # quorum, keep the artifact precondition.
            specs[s.id] = GateSpec(
                stage_id=s.id, gate="sync-named", owner_role="three-amigos",
                blocking=True, mandatory=True,
                required_roles=("ba-lead", "dev-lead", "qa-lead"),
                on_field="state", proceed_when="agreed",
                release_requires_field_value="ready-for-amigos",
                verdicts=("agreed", "split-stories", "descope", "needs-rework"),
                on_block="ba-breakdown-review",
            )
        elif s.compensating_action is not None or s.id == "release-handoff":
            specs[s.id] = GateSpec(
                stage_id=s.id, gate="sync-named", owner_role="release-manager",
                blocking=True, mandatory=True, confidence_independent=True,
            )
        else:
            specs[s.id] = GateSpec(stage_id=s.id, gate="auto", blocking=False)
    return specs


def record_verdict(
    gate: GateInstance, verdict: str, approver: str, note: Optional[str] = None,
    ts: Optional[float] = None, role: Optional[str] = None,
) -> GateInstance:
    """The ONLY way a gate leaves `pending`. Raises GateApprovalError on any
    rule violation; never mutates on failure.

    QUORUM gates (spec.required_roles non-empty) accumulate one signature per
    role and stay `pending` until every role has signed. Two rules make the
    quorum mean what it says: a role may be signed only once, and one human may
    cover only one role — otherwise "three amigos" degenerates into one person
    clicking three times. A dissenting signature resolves the gate immediately;
    there is no point collecting the remaining signatures on a decision that
    cannot release."""
    if gate.status != "pending":
        raise GateApprovalError(f"gate {gate.stage_id} already decided ({gate.status})")
    if verdict not in gate.spec.verdicts:
        raise GateApprovalError(
            f"verdict {verdict!r} not in this gate's vocabulary {list(gate.spec.verdicts)}"
        )
    if not approver or not str(approver).strip():
        raise GateApprovalError("a verdict requires a human approver name")
    if gate.spec.named and len(str(approver).strip()) < 2:
        raise GateApprovalError(f"{gate.spec.gate} gate requires a NAMED human approver")

    name = str(approver).strip()

    if gate.spec.quorum:
        if not role:
            raise GateApprovalError(
                f"gate {gate.stage_id} is a quorum gate; a verdict must name the role it "
                f"signs for (one of {list(gate.spec.required_roles)})"
            )
        if role not in gate.spec.required_roles:
            raise GateApprovalError(
                f"role {role!r} is not required by gate {gate.stage_id} "
                f"{list(gate.spec.required_roles)}"
            )
        if role in gate.signed_roles:
            raise GateApprovalError(f"role {role!r} has already signed gate {gate.stage_id}")
        if any(_identity(a["approver"]) == _identity(name) for a in gate.approvals):
            raise GateApprovalError(
                f"{name!r} has already signed gate {gate.stage_id} for another role; a quorum "
                "requires DISTINCT named humans"
            )
        gate.approvals.append(
            {"role": role, "approver": name, "verdict": verdict, "note": note, "ts": ts}
        )

    gate.verdict = verdict
    gate.approver = name
    gate.note = note
    gate.decided_ts = ts

    if gate.spec.on_field and gate.spec.proceed_when:
        released = verdict == gate.spec.proceed_when
    else:
        released = verdict in RELEASE_VERDICTS or verdict in CAVEAT_VERDICTS

    required_value = gate.spec.release_requires_field_value
    if released and required_value is not None and gate.artifact_field_value != required_value:
        # The humans may vote however they like; a blocked artifact does not
        # become unblocked because three people approved it. Clearing the gap is
        # a separate, named act upstream.
        gate.status = "blocked"
        gate.note = (
            f"{note + ' | ' if note else ''}refused: artifact {gate.spec.on_field} is "
            f"{gate.artifact_field_value!r}, release requires {required_value!r}"
        )
        return gate

    if gate.spec.quorum and released and gate.outstanding_roles:
        gate.status = "pending"  # quorum not yet met — keep waiting, decide nothing
        return gate

    if released:
        gate.status = "released-with-caveat" if verdict in CAVEAT_VERDICTS else "released"
    else:
        gate.status = "blocked"
    return gate
