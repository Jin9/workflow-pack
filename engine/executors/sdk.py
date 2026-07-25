"""SdkExecutor — claude-agent-sdk sessions (the code-gen half of the hybrid runner).

Shares the same prompt protocol and file-based success signal as the headless
executor. Targets the code-gen stages (S4a/S4b) where richer tool control and
worktree isolation matter; worktree setup itself lands in P5 — until then this
executor is fully functional for any stage whose contract fits the shared
protocol. The import is lazy so the engine (and its tests) run without the
SDK installed.
"""
from __future__ import annotations

import json
import time

from engine.audit import sha256_hex
from engine.executors.base import ExecutionResult, StageContext, stage_prompt
from engine.model import StageExecutionError
from engine.validation import SKILL_SCHEMA_EXEMPT, boundary_schema_path, skill_schema_path


class SdkExecutor:
    def __init__(self):
        self._sdk = None

    def _load_sdk(self):
        if self._sdk is None:
            try:
                import claude_agent_sdk  # lazy: engine works without it until a stage needs it
            except ImportError as e:
                raise StageExecutionError(
                    "SdkExecutor needs the claude-agent-sdk package "
                    "(engine/.venv/bin/pip install claude-agent-sdk)"
                ) from e
            self._sdk = claude_agent_sdk
        return self._sdk

    async def execute(self, ctx: StageContext) -> ExecutionResult:
        sdk = self._load_sdk()
        t0 = time.monotonic()
        skill_md = ctx.stage.skill_dir / "SKILL.md"
        boundary = json.loads(boundary_schema_path(ctx.stage).read_text(encoding="utf-8"))
        skill_schema = None
        sp = skill_schema_path(ctx.stage)
        if ctx.stage.id not in SKILL_SCHEMA_EXEMPT and sp.is_file():
            skill_schema = json.loads(sp.read_text(encoding="utf-8"))
        prompt = stage_prompt(ctx, skill_md.read_text(encoding="utf-8"), boundary, skill_schema)
        ctx.stage_dir.mkdir(parents=True, exist_ok=True)

        options = sdk.ClaudeAgentOptions(
            model=ctx.binding.model,
            cwd=str(ctx.stage_dir),
            allowed_tools=list(ctx.binding.profile.allowed_tools),
            permission_mode=ctx.binding.profile.permission_mode,
            max_turns=ctx.binding.profile.max_turns,
        )
        async for _message in sdk.query(prompt=prompt, options=options):
            pass  # progress is irrelevant: the artifact on disk is the only signal

        if not ctx.output_path.is_file():
            raise StageExecutionError(
                f"{ctx.stage.id}: SDK session finished but wrote no artifact at {ctx.output_path}"
            )
        return ExecutionResult(
            status="artifact_written",
            detail="claude-agent-sdk session completed",
            request_digest={
                "executor": "sdk",
                "model": ctx.binding.model,
                "permission_mode": ctx.binding.profile.permission_mode,
                "allowed_tools": list(ctx.binding.profile.allowed_tools),
                "prompt_sha256": sha256_hex(prompt.encode("utf-8")),
            },
            duration_seconds=time.monotonic() - t0,
        )
