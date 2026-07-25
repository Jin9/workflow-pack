"""Runtime binding: which executor / model / permission profile runs each stage.

The pipeline YAML deliberately carries no model or executor hints — they live
in engine/config/runtime-binding.yaml. mode="replay" forces every stage onto
the replay executor regardless of binding (token-free); mode="live" uses the
per-stage entry, defaulting to replay for stages not yet taken live.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple

import yaml

from engine import ENGINE_DIR
from engine.model import SpecError

BINDING_PATH = ENGINE_DIR / "config" / "runtime-binding.yaml"
COMMAND_POLICY_PATH = ENGINE_DIR / "config" / "command-policy.yaml"

VALID_EXECUTORS = ("replay", "headless", "sdk", "script")


@dataclass(frozen=True)
class PermissionProfile:
    name: str
    allowed_tools: Tuple[str, ...]
    permission_mode: str
    max_turns: int = 40


@dataclass(frozen=True)
class StageBinding:
    executor: str
    model: str
    effort: str
    profile: PermissionProfile
    timeout_multiplier: float = 1.0
    backoff_multiplier: float = 0.5


_DEFAULT_PROFILE = PermissionProfile(
    name="json-only", allowed_tools=("Read", "Write", "Edit"), permission_mode="acceptEdits"
)


class RuntimeBinding:
    # Enforcement of the per-stage input contract (skills/<s>/schemas/input.json)
    # against the ASSEMBLED payload. off = skip · warn = emit
    # input.validation.failed and continue · enforce = fail the stage (fail-closed).
    INPUT_VALIDATION_MODES = ("off", "warn", "enforce")

    def __init__(self, defaults: StageBinding, stages: Dict[str, StageBinding],
                 input_validation: str = "warn"):
        self.defaults = defaults
        self.stages = stages
        if input_validation not in self.INPUT_VALIDATION_MODES:
            raise SpecError(
                f"input_validation: {input_validation!r} not in {self.INPUT_VALIDATION_MODES}")
        self.input_validation = input_validation

    @classmethod
    def load(cls, path: Path = BINDING_PATH, policy_path: Path = COMMAND_POLICY_PATH) -> "RuntimeBinding":
        profiles = {_DEFAULT_PROFILE.name: _DEFAULT_PROFILE}
        if policy_path.is_file():
            pol = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
            for name, p in (pol.get("profiles") or {}).items():
                profiles[name] = PermissionProfile(
                    name=name,
                    allowed_tools=tuple(p.get("allowed_tools") or ()),
                    permission_mode=p.get("permission_mode", "default"),
                    max_turns=int(p.get("max_turns", 40)),
                )
        if not path.is_file():
            return cls(_binding_from({}, profiles), {})
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        defaults = _binding_from(doc.get("defaults") or {}, profiles)
        stages = {
            sid: _binding_from(raw or {}, profiles, defaults)
            for sid, raw in (doc.get("stages") or {}).items()
        }
        return cls(defaults, stages, str(doc.get("input_validation", "warn")))

    def for_stage(self, stage_id: str, mode: str) -> StageBinding:
        b = self.stages.get(stage_id, self.defaults)
        if mode == "replay":
            return StageBinding(
                executor="replay", model=b.model, effort=b.effort, profile=b.profile,
                timeout_multiplier=b.timeout_multiplier, backoff_multiplier=0.0,
            )
        return b


def _binding_from(raw: dict, profiles: Dict[str, PermissionProfile],
                  base: Optional[StageBinding] = None) -> StageBinding:
    executor = raw.get("executor", base.executor if base else "replay")
    if executor not in VALID_EXECUTORS:
        raise SpecError(f"runtime-binding: unknown executor {executor!r}")
    profile_name = raw.get("profile", base.profile.name if base else _DEFAULT_PROFILE.name)
    if profile_name not in profiles:
        raise SpecError(f"runtime-binding: unknown permission profile {profile_name!r}")
    return StageBinding(
        executor=executor,
        model=raw.get("model", base.model if base else "opus"),
        effort=raw.get("effort", base.effort if base else "low"),
        profile=profiles[profile_name],
        timeout_multiplier=float(raw.get("timeout_multiplier", base.timeout_multiplier if base else 1.0)),
        backoff_multiplier=float(raw.get("backoff_multiplier", base.backoff_multiplier if base else 0.5)),
    )
