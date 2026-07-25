"""ScriptExecutor — machine-threshold T-gates run the REAL test commands.

No LLM: `go test -race -json` / `vitest --reporter=json` execute against the
code the stage's upstream manifests describe, and the gate JSON (verdict
PASS|FAIL|ERROR verbatim, totals, failures, audit_id) is computed from the
tool output. Runners are declared in engine/config/gate-runners.yaml; binding
a stage to `script` without a runner entry is an explicit configuration error.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from engine import ENGINE_DIR, WORKSPACE
from engine.executors.base import ExecutionResult, StageContext
from engine.model import StageExecutionError, StageTimeout
from engine.runstore import atomic_write_json

RUNNERS_PATH = ENGINE_DIR / "config" / "gate-runners.yaml"


def parse_go_test_json(stdout: str) -> Tuple[Dict[str, int], List[str]]:
    """`go test -json` emits one JSON event per line; per-test terminal events
    have both Test and Action in {pass, fail, skip}."""
    totals = {"executed": 0, "passed": 0, "failed": 0, "skipped": 0}
    failures: List[str] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not ev.get("Test"):
            continue
        action = ev.get("Action")
        if action == "pass":
            totals["passed"] += 1
        elif action == "fail":
            totals["failed"] += 1
            failures.append(f"{ev.get('Package', '?')}::{ev['Test']}")
        elif action == "skip":
            totals["skipped"] += 1
        else:
            continue
        totals["executed"] += 1
    return totals, failures


def parse_vitest_report(report: dict) -> Tuple[Dict[str, int], List[str]]:
    skipped = int(report.get("numPendingTests", 0)) + int(report.get("numTodoTests", 0))
    totals = {
        "executed": int(report.get("numTotalTests", 0)),
        "passed": int(report.get("numPassedTests", 0)),
        "failed": int(report.get("numFailedTests", 0)),
        "skipped": skipped,
    }
    failures: List[str] = []
    for suite in report.get("testResults", []):
        for a in suite.get("assertionResults", []):
            if a.get("status") == "failed":
                failures.append(a.get("fullName") or a.get("title") or "?")
    return totals, failures


class ScriptExecutor:
    def __init__(self, config_path: Path = RUNNERS_PATH):
        self.config_path = config_path
        self._runners: Optional[dict] = None

    def _runner_for(self, stage_id: str) -> dict:
        if self._runners is None:
            if not self.config_path.is_file():
                raise StageExecutionError(f"no gate-runners config at {self.config_path}")
            doc = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
            self._runners = doc.get("runners") or {}
        runner = self._runners.get(stage_id)
        if runner is None:
            raise StageExecutionError(
                f"{stage_id}: bound to the script executor but has no runner in gate-runners.yaml"
            )
        return runner

    async def _run(self, args, cwd: Path, env: dict, deadline: float):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise StageTimeout("gate-runner budget exhausted")
        proc = await asyncio.create_subprocess_exec(
            *[str(a) for a in args],
            cwd=str(cwd),
            env={**os.environ, **{k: str(v) for k, v in (env or {}).items()}},
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=remaining)
        except asyncio.TimeoutError:
            try:
                import signal
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            raise StageTimeout(f"gate runner exceeded budget in {cwd}")
        return proc.returncode, stdout.decode("utf-8", "replace"), stderr.decode("utf-8", "replace")

    async def execute(self, ctx: StageContext) -> ExecutionResult:
        runner = self._runner_for(ctx.stage.id)
        kind = runner.get("kind")
        base = WORKSPACE / runner["cwd"]
        deadline = time.monotonic() + max(60.0, ctx.stage.timeout_seconds * ctx.binding.timeout_multiplier)
        t0 = time.monotonic()

        totals = {"executed": 0, "passed": 0, "failed": 0, "skipped": 0}
        failures: List[str] = []
        exit_codes: Dict[str, int] = {}
        tool_error: Optional[str] = None

        if kind == "go-test":
            for svc in runner.get("services") or ["."]:
                rc, out, err = await self._run(runner["args"], base / svc, runner.get("env"), deadline)
                exit_codes[svc] = rc
                t, f = parse_go_test_json(out)
                for k in totals:
                    totals[k] += t[k]
                failures.extend(f)
                if rc != 0 and t["failed"] == 0:  # tool broke before running tests
                    tool_error = f"{svc}: go test exited {rc}: {err[-300:]}"
        elif kind == "vitest":
            rc, out, err = await self._run(runner["args"], base, runner.get("env"), deadline)
            exit_codes["vitest"] = rc
            report_path = base / ".vitest-report.json"
            if report_path.is_file():
                totals, failures = parse_vitest_report(
                    json.loads(report_path.read_text(encoding="utf-8")))
            elif rc != 0:
                tool_error = f"vitest exited {rc} with no report: {err[-300:]}"
        else:
            raise StageExecutionError(f"{ctx.stage.id}: unknown runner kind {kind!r}")

        if tool_error:
            verdict = "ERROR"
            failures.append(tool_error)
        else:
            verdict = "FAIL" if totals["failed"] > 0 else "PASS"

        artifact = {
            "verdict": verdict,  # PASS|FAIL|ERROR — the gate's own vocabulary, verbatim
            "totals": totals,
            "failures": failures[:25],
            "audit_id": ctx.audit_id,
        }
        atomic_write_json(ctx.output_path, artifact)
        return ExecutionResult(
            status="artifact_written",
            detail=f"{kind}: {totals['passed']}/{totals['executed']} passed",
            request_digest={
                "executor": "script", "kind": kind,
                "args": [str(a) for a in runner["args"]],
                "cwd": str(runner["cwd"]), "exit_codes": exit_codes,
            },
            duration_seconds=time.monotonic() - t0,
        )
