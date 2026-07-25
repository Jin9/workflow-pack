"""Parse workflows/delivery-pipeline.yaml into a WorkflowSpec — fail closed.

Every ref is resolved at load: schema_ref -> existing file under workflows/,
skill_ref -> existing folder with SKILL.md whose frontmatter `version:` equals
the exact YAML pin (supply-chain rule: bumping a skill bumps both together).
Stages without a failure_policy inherit spec.default_failure_policy explicitly.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import yaml

from engine import WORKSPACE
from engine.model import (
    Compensation,
    FailurePolicy,
    HumanReview,
    Sla,
    SpecError,
    StageSpec,
    WorkflowSpec,
)

PIPELINE_PATH = WORKSPACE / "workflows" / "delivery-pipeline.yaml"
WORKFLOWS_DIR = WORKSPACE / "workflows"

_EXACT_PIN = re.compile(r"^\d+\.\d+\.\d+$")
_FM_VERSION = re.compile(r"^version:\s*[\"']?([\d.]+)", re.M)


def _policy(raw: Optional[dict], default: Optional[FailurePolicy] = None) -> FailurePolicy:
    if raw is None:
        if default is None:
            raise SpecError("stage has no failure_policy and no default exists")
        return default
    return FailurePolicy(
        on_failure=raw["on_failure"],
        max_retries=int(raw.get("max_retries", 0)),
        backoff=raw.get("backoff", "none"),
        after_max_retries=raw.get("after_max_retries"),
        human_queue_name=raw.get("human_queue_name"),
        loop_to_stage=raw.get("loop_to_stage"),
        max_loops=int(raw.get("max_loops", 0)),
        after_max_loops=raw.get("after_max_loops"),
    )


def _skill_folder_version(skill_dir: Path) -> Optional[str]:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    parts = text.split("---")
    if len(parts) < 3:
        return None
    m = _FM_VERSION.search(parts[1])
    return m.group(1) if m else None


def _check_skill_ref(base: Path, skill_ref: str, pin: str, where: str) -> Path:
    if not _EXACT_PIN.match(pin):
        raise SpecError(f"{where}: skill_version {pin!r} is not an exact pin")
    skill_dir = base / skill_ref
    if not (skill_dir / "SKILL.md").is_file():
        raise SpecError(f"{where}: skill_ref {skill_ref!r} does not resolve to a SKILL.md")
    folder_version = _skill_folder_version(skill_dir)
    if folder_version != pin:
        raise SpecError(
            f"{where}: pin {pin} != skill folder version {folder_version} ({skill_ref})"
        )
    return skill_dir


def _check_schema_ref(base: Path, schema_ref: str, where: str) -> Path:
    p = base / schema_ref
    if not p.is_file():
        raise SpecError(f"{where}: schema_ref {schema_ref!r} does not resolve to a file")
    return p


def load_workflow(path: Path = PIPELINE_PATH) -> WorkflowSpec:
    base = path.resolve().parent  # schema_ref/skill_ref resolve relative to the YAML's dir
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if doc.get("apiVersion") != "cognitive-os/v1" or doc.get("kind") != "Workflow":
        raise SpecError(f"{path}: not a cognitive-os/v1 Workflow")
    spec = doc["spec"]
    default_policy = _policy(spec["default_failure_policy"])
    sla = Sla(
        p95_latency_seconds=int(spec["sla"]["p95_latency_seconds"]),
        max_retries_per_stage=int(spec["sla"]["max_retries_per_stage"]),
        overall_timeout_seconds=int(spec["sla"]["overall_timeout_seconds"]),
    )

    stages = []
    seen = set()
    for raw in spec["stages"]:
        sid = raw["id"]
        if sid in seen:
            raise SpecError(f"duplicate stage id {sid!r}")
        seen.add(sid)
        where = f"stage {sid}"
        skill_dir = _check_skill_ref(base, raw["skill_ref"], str(raw["skill_version"]), where)
        schema_path = _check_schema_ref(base, raw["output"]["schema_ref"], where)

        inp = raw.get("input", {}) or {}
        from_stage = {
            src: tuple(fields) for src, fields in (inp.get("from_stage") or {}).items()
        }
        hr = None
        if "human_review" in raw:
            h = raw["human_review"]
            hr = HumanReview(
                gate=h["gate"], on_field=h["on_field"],
                proceed_when=h["proceed_when"], on_block=h["on_block"],
            )
        comp = None
        if "compensating_action" in raw:
            c = raw["compensating_action"]
            comp_dir = _check_skill_ref(base, c["skill_ref"], str(c["skill_version"]),
                                        f"{where} compensation")
            comp_schema_ref = c.get("schema_ref")
            comp = Compensation(
                type=c["type"], skill_ref=c["skill_ref"],
                skill_version=str(c["skill_version"]),
                timeout_seconds=int(c["timeout_seconds"]),
                skill_dir=comp_dir,
                output_schema_ref=comp_schema_ref,
                output_schema_path=(
                    _check_schema_ref(base, comp_schema_ref, f"{where} compensation")
                    if comp_schema_ref else None),
            )
        stages.append(StageSpec(
            id=sid,
            type=raw["type"],
            skill_ref=raw["skill_ref"],
            skill_version=str(raw["skill_version"]),
            depends_on=tuple(raw.get("depends_on") or ()),
            input_from_workflow=tuple(inp.get("from_workflow_input") or ()),
            input_from_stage=from_stage,
            output_schema_ref=raw["output"]["schema_ref"],
            required_fields=tuple(raw["output"].get("required_fields") or ()),
            timeout_seconds=int(raw["timeout_seconds"]),
            failure_policy=_policy(raw.get("failure_policy"), default_policy),
            skill_dir=skill_dir,
            output_schema_path=schema_path,
            human_review=hr,
            compensating_action=comp,
        ))

    # Referential integrity of the graph + input mappings. A from_stage source
    # must be an ANCESTOR (direct or transitive) — the YAML legitimately maps
    # e.g. backend-review <- tl-design while depending only on backend-implement,
    # because tl-design is transitively upstream and its artifact exists by then.
    ids = {s.id for s in stages}
    by_id = {s.id: s for s in stages}
    ancestors: dict = {}

    def _ancestors(sid: str, trail=()) -> set:
        if sid in trail:
            raise SpecError(f"depends_on cycle through {sid!r}")
        if sid not in ancestors:
            acc = set()
            for dep in by_id[sid].depends_on:
                if dep not in ids:
                    raise SpecError(f"stage {sid}: depends_on unknown stage {dep!r}")
                acc.add(dep)
                acc |= _ancestors(dep, trail + (sid,))
            ancestors[sid] = acc
        return ancestors[sid]

    for s in stages:
        anc = _ancestors(s.id)
        for src in s.input_from_stage:
            if src not in ids:
                raise SpecError(f"stage {s.id}: from_stage references unknown stage {src!r}")
            if src not in anc:
                raise SpecError(f"stage {s.id}: from_stage {src!r} is not an ancestor")
        if s.failure_policy.on_failure == "loop_back" and s.failure_policy.loop_to_stage not in ids:
            raise SpecError(f"stage {s.id}: loop_to_stage {s.failure_policy.loop_to_stage!r} unknown")

    _check_schema_ref(base, spec["input"]["schema_ref"], "spec.input")
    _check_schema_ref(base, spec["output"]["schema_ref"], "spec.output")

    meta = doc["metadata"]
    return WorkflowSpec(
        name=meta["name"],
        version=str(meta["version"]),
        stages=tuple(stages),
        input_schema_ref=spec["input"]["schema_ref"],
        input_required=tuple(spec["input"]["required_fields"]),
        output_schema_ref=spec["output"]["schema_ref"],
        output_required=tuple(spec["output"]["required_fields"]),
        sla=sla,
        default_failure_policy=default_policy,
        compensation_enabled=bool(spec.get("compensation", {}).get("enabled", False)),
        compensation_timeout_seconds=int(spec.get("compensation", {}).get("timeout_seconds", 600)),
    )
