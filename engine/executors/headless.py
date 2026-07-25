"""HeadlessClaudeExecutor — one `claude -p` subprocess per stage attempt.

Environment rules baked in (see the user CLAUDE.md gotchas):
- ALWAYS pass --effort low (a child inherits high session effort and hangs).
- macOS has no `timeout` binary — asyncio.wait_for + process-group kill.
- The prompt goes via stdin; stdout is NEVER parsed for content (archived to
  the stage dir for debugging). Success = the artifact file exists; the
  orchestrator dual-validates it afterwards.
- Tool surface comes from the stage's permission profile (command policy is
  enforced OUTSIDE the model via --allowedTools/--permission-mode, cwd is the
  stage dir).
"""
from __future__ import annotations

import asyncio
import json
import os
import signal
import time

from engine.audit import sha256_hex
from engine.executors.base import ExecutionResult, StageContext, stage_prompt
from engine.model import StageExecutionError, StageTimeout
from engine.validation import SKILL_SCHEMA_EXEMPT, boundary_schema_path, skill_schema_path


class HeadlessClaudeExecutor:
    def __init__(self, claude_bin: str = "claude"):
        self.claude_bin = claude_bin

    def build_command(self, ctx: StageContext):
        profile = ctx.binding.profile
        cmd = [
            self.claude_bin, "-p",
            "--model", ctx.binding.model,
            "--effort", ctx.binding.effort or "low",
            "--permission-mode", profile.permission_mode,
            "--max-turns", str(profile.max_turns),
        ]
        for tool in profile.allowed_tools:
            cmd += ["--allowedTools", tool]
        return cmd

    def build_prompt(self, ctx: StageContext) -> str:
        skill_md = ctx.stage.skill_dir / "SKILL.md"
        boundary = json.loads(boundary_schema_path(ctx.stage).read_text(encoding="utf-8"))
        skill_schema = None
        sp = skill_schema_path(ctx.stage)
        if ctx.stage.id not in SKILL_SCHEMA_EXEMPT and sp.is_file():
            skill_schema = json.loads(sp.read_text(encoding="utf-8"))
        return stage_prompt(ctx, skill_md.read_text(encoding="utf-8"), boundary, skill_schema)

    async def execute(self, ctx: StageContext) -> ExecutionResult:
        t0 = time.monotonic()
        prompt = self.build_prompt(ctx)
        cmd = self.build_command(ctx)
        ctx.stage_dir.mkdir(parents=True, exist_ok=True)
        agent_dir = ctx.stage_dir / ".agent"
        agent_dir.mkdir(exist_ok=True)

        timeout = max(30.0, ctx.stage.timeout_seconds * ctx.binding.timeout_multiplier)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(ctx.stage_dir),
            start_new_session=True,  # own process group -> clean kill on timeout
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(prompt.encode("utf-8")), timeout=timeout
            )
        except asyncio.TimeoutError:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            raise StageTimeout(f"{ctx.stage.id}: headless claude exceeded {timeout:.0f}s")

        (agent_dir / "stdout.txt").write_bytes(stdout or b"")
        (agent_dir / "stderr.txt").write_bytes(stderr or b"")

        digest = {
            "executor": "headless-claude",
            "model": ctx.binding.model,
            "effort": ctx.binding.effort,
            "permission_mode": ctx.binding.profile.permission_mode,
            "allowed_tools": list(ctx.binding.profile.allowed_tools),
            "prompt_sha256": sha256_hex(prompt.encode("utf-8")),
            "exit_code": proc.returncode,
        }
        if proc.returncode != 0:
            tail = (stderr or b"")[-400:].decode("utf-8", "replace")
            raise StageExecutionError(f"{ctx.stage.id}: claude -p exited {proc.returncode}: {tail}")
        if not ctx.output_path.is_file():
            raise StageExecutionError(
                f"{ctx.stage.id}: agent finished but wrote no artifact at {ctx.output_path}"
            )
        return ExecutionResult(
            status="artifact_written",
            detail="headless claude completed",
            request_digest=digest,
            duration_seconds=time.monotonic() - t0,
        )
