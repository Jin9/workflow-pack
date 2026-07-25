"""Fail-closed dual-schema validation — mirrors tmp/runs/shoppilot/_sim/validate.py.

Every stage artifact must pass BOTH:
  1. the skill's own schemas/output.json (when the skill ships one; absent = n/a,
     exactly like validate.py), and
  2. the boundary schema named by the stage's output.schema_ref,
plus the stage's required_fields. The engine never trusts an executor's
self-report: an artifact that fails here fails the stage, whatever the agent said.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from jsonschema import FormatChecker
from jsonschema.validators import validator_for

from engine import WORKSPACE
from engine.model import StageSpec, ValidationFailed

WORKFLOWS_DIR = WORKSPACE / "workflows"

# Stages whose artifact is a MANIFEST, not the skill's full output shape — the
# oracle (_sim/validate.py CHECKS) validates these against the boundary schema
# only (skill schema entry = None): ba-research emits INDEX.json (ref chain,
# nothing inlined), intake's run-plan predates a skill output schema.
SKILL_SCHEMA_EXEMPT = {"ba-research"}

_schema_cache: dict = {}


def _load_schema(path: Path):
    key = str(path)
    if key not in _schema_cache:
        _schema_cache[key] = json.loads(path.read_text(encoding="utf-8"))
    return _schema_cache[key]


def _errors_against(instance, schema_path: Path) -> Optional[List[str]]:
    if not schema_path.is_file():
        return None  # n/a — mirrors validate.py's None handling for absent skill schemas
    schema = _load_schema(schema_path)
    validator = validator_for(schema)(schema, format_checker=FormatChecker())
    out = []
    for e in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
        loc = "/".join(str(x) for x in e.path) or "<root>"
        out.append(f"[{loc}] {e.message}")
    return out


def skill_schema_path(stage: StageSpec) -> Path:
    return stage.skill_dir / "schemas" / "output.json"


def boundary_schema_path(stage: StageSpec) -> Path:
    return stage.output_schema_path


def validate_artifact(stage: StageSpec, artifact_path: Path) -> dict:
    """Return the parsed artifact; raise ValidationFailed on any finding."""
    if not artifact_path.is_file():
        raise ValidationFailed(str(artifact_path), ["artifact file was not written"])
    try:
        instance = json.loads(artifact_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValidationFailed(str(artifact_path), [f"not valid JSON: {e}"])

    findings: List[str] = []
    checks = [("boundary", boundary_schema_path(stage))]
    if stage.id not in SKILL_SCHEMA_EXEMPT:
        checks.insert(0, ("skill", skill_schema_path(stage)))
    for label, sp in checks:
        errs = _errors_against(instance, sp)
        if errs:
            findings.extend(f"{label}:{m}" for m in errs)
    if isinstance(instance, dict):
        for f in stage.required_fields:
            if f not in instance:
                findings.append(f"required_fields: {f!r} missing")
    else:
        findings.append("artifact root is not a JSON object")

    if findings:
        raise ValidationFailed(str(artifact_path), findings)
    return instance


def validate_workflow_input(workflow, payload: dict) -> List[str]:
    errs = _errors_against(payload, WORKFLOWS_DIR / workflow.input_schema_ref)
    return errs or []


def skill_input_schema_path(stage: StageSpec) -> Path:
    return stage.skill_dir / "schemas" / "input.json"


def validate_stage_input(stage: StageSpec, payload: dict) -> List[str]:
    """Validate the ASSEMBLED stage payload against the skill's schemas/input.json.

    The input schemas describe the POST-adapter payload (picks + NESTED_HANDOFF
    nesting + ba-research hydration + the engine-injected idempotency_key /
    upstream_artifacts / loop_back_feedback) — see the 2026-07-12 contract
    reshape. Returns [] when the skill ships no input schema (n/a) or the payload
    conforms; a non-empty list is a contract breach between the adapter and the
    consumer.
    """
    errs = _errors_against(payload, skill_input_schema_path(stage))
    return errs or []
