"""Typed model of delivery-pipeline.yaml (cognitive-os/v1) as the engine consumes it."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Mapping, Optional, Tuple


@dataclass(frozen=True)
class FailurePolicy:
    on_failure: str  # retry | loop_back | human-queue
    max_retries: int = 0
    backoff: str = "none"
    after_max_retries: Optional[str] = None  # human-queue
    human_queue_name: Optional[str] = None
    loop_to_stage: Optional[str] = None
    max_loops: int = 0
    after_max_loops: Optional[str] = None  # abort | human-queue


@dataclass(frozen=True)
class HumanReview:
    gate: str
    on_field: str
    proceed_when: str
    on_block: str


@dataclass(frozen=True)
class Compensation:
    type: str
    skill_ref: str
    skill_version: str
    timeout_seconds: int
    skill_dir: Optional[Path] = None  # resolved by the loader
    output_schema_ref: Optional[str] = None  # e.g. schemas/revoke-receipt.json
    output_schema_path: Optional[Path] = None


@dataclass(frozen=True)
class StageSpec:
    id: str
    type: str
    skill_ref: str  # e.g. "skills/eliciting-banking-brief", relative to workflows/
    skill_version: str
    depends_on: Tuple[str, ...]
    input_from_workflow: Tuple[str, ...]
    input_from_stage: Mapping[str, Tuple[str, ...]]  # producer stage id -> field names
    output_schema_ref: str  # e.g. "schemas/ba-brief.json", relative to workflows/
    required_fields: Tuple[str, ...]
    timeout_seconds: int
    failure_policy: FailurePolicy
    skill_dir: Path  # resolved by the loader relative to the YAML's dir
    output_schema_path: Path
    human_review: Optional[HumanReview] = None
    compensating_action: Optional[Compensation] = None

    @property
    def skill_name(self) -> str:
        return self.skill_ref.rsplit("/", 1)[-1]


@dataclass(frozen=True)
class Sla:
    p95_latency_seconds: int
    max_retries_per_stage: int
    overall_timeout_seconds: int


@dataclass(frozen=True)
class WorkflowSpec:
    name: str
    version: str
    stages: Tuple[StageSpec, ...]
    input_schema_ref: str
    input_required: Tuple[str, ...]
    output_schema_ref: str
    output_required: Tuple[str, ...]
    sla: Sla
    default_failure_policy: FailurePolicy
    compensation_enabled: bool
    compensation_timeout_seconds: int
    stage_by_id: Mapping[str, StageSpec] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "stage_by_id", {s.id: s for s in self.stages})


@dataclass(frozen=True)
class GateSpec:
    stage_id: str
    gate: str  # auto | auto+exception | async-peer | sync | sync-named | human | hitl-on-hardfail
    owner_role: Optional[str] = None
    blocking: bool = False
    mandatory: bool = False
    confidence_independent: bool = False
    on_field: Optional[str] = None
    proceed_when: Optional[str] = None
    on_block: Optional[str] = None
    verdicts: Tuple[str, ...] = ("approve", "reject")
    exception_queue: Optional[str] = None

    @property
    def named(self) -> bool:
        """sync-named and human gates require a named human approver."""
        return self.gate in ("sync-named", "human")


class EngineError(Exception):
    """Base class for engine failures (all carry a stage/run context message)."""


class SpecError(EngineError):
    """The pipeline YAML / gate policy / config is invalid — fail closed at load."""


class ValidationFailed(EngineError):
    def __init__(self, artifact: str, errors):
        super().__init__(f"{artifact}: {len(errors)} validation error(s)")
        self.artifact = artifact
        self.errors = list(errors)


class StageExecutionError(EngineError):
    pass


class StageTimeout(EngineError):
    pass
