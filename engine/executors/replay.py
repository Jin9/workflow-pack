"""ReplayExecutor — token-free stage execution from the ShopPilot corpus.

Copies each stage's canned artifact byte-verbatim into the run dir (plus the
ba-research ref-chain sidecars), which keeps replay runs byte-deterministic
and lets the _sim/validate.py oracle pass unchanged.
"""
from __future__ import annotations

import shutil
import time

from engine.audit import sha256_file
from engine.executors.base import ExecutionResult, StageContext
from engine.model import StageExecutionError
from engine.runstore import SHOPPILOT, artifact_relpath


class ReplayExecutor:
    def __init__(self, corpus=SHOPPILOT):
        self.corpus = corpus

    async def execute(self, ctx: StageContext) -> ExecutionResult:
        t0 = time.monotonic()
        source = self.corpus / artifact_relpath(ctx.stage.id)
        if not source.is_file():
            raise StageExecutionError(
                f"replay corpus has no artifact for {ctx.stage.id} ({source})"
            )
        ctx.output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, ctx.output_path)

        copied_extra = 0
        if ctx.stage.id == "ba-research":
            # INDEX.json references one file per epic/story — copy the ref chain.
            for sib in sorted(source.parent.glob("*.json")):
                if sib.name != source.name:
                    shutil.copyfile(sib, ctx.output_path.parent / sib.name)
                    copied_extra += 1

        return ExecutionResult(
            status="artifact_written",
            detail=f"replayed {source.relative_to(self.corpus)}"
            + (f" (+{copied_extra} ref files)" if copied_extra else ""),
            request_digest={
                "executor": "replay",
                "source": str(source.relative_to(self.corpus)),
                "source_sha256": sha256_file(source),
            },
            duration_seconds=time.monotonic() - t0,
        )
