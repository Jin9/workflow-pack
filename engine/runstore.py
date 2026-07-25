"""runs/<run-id>/ layout — byte-compatible with the ShopPilot corpus.

Stage folders and artifact names mirror tmp/runs/shoppilot exactly (the map
below is the same one _sim/validate.py CHECKS encodes), so the existing
validation oracle and the rendering-delivery-review-console skill consume a
live run dir unchanged. T-gates live as gates/<stage-id>.json.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional

from engine import WORKSPACE

RUNS_DIR = WORKSPACE / "runs"
SHOPPILOT = WORKSPACE / "tmp" / "runs" / "shoppilot"

ARTIFACT_RELPATHS: Dict[str, str] = {
    "intake": "S0-intake/run-plan.json",
    "s1-discovery": "S1a-ba-discovery/discovery.json",
    "ba-research": "S1b-ba-brief/INDEX.json",
    "ux-intake": "S1.5-ux-intake/output.json",
    "tl-design": "S2-tl-design/output.json",
    "plan-review": "S2.5-plan-review/plan-review.json",
    "contract-design": "S3-contracts/befe-contracts.json",
    "backend-implement": "S4a-backend/backend-artifacts.json",
    "backend-review": "S4a-backend/review/backend-review.json",
    "frontend-implement": "S4b-frontend/frontend-artifacts.json",
    "frontend-review": "S4b-frontend/review/frontend-review.json",
    "qa-plan": "S4c-qa-test-design/qa-plan.json",
    "qa-validate": "S5-qa-validation/qa-evidence.json",
    "release-handoff": "S6-deploy/handoff-receipt.json",
    "prod-validate": "S7-prod-validation/smoke-slo.json",
}


def artifact_relpath(stage_id: str) -> str:
    return ARTIFACT_RELPATHS.get(stage_id, f"gates/{stage_id}.json")


class RunStore:
    def __init__(self, run_id: str, base: Optional[Path] = None):
        self.run_id = run_id
        self.dir = (base or RUNS_DIR) / run_id
        self.dir.mkdir(parents=True, exist_ok=True)

    def artifact_path(self, stage_id: str) -> Path:
        return self.dir / artifact_relpath(stage_id)

    def stage_dir(self, stage_id: str) -> Path:
        return self.artifact_path(stage_id).parent

    def write_json(self, relpath: str, obj) -> Path:
        return atomic_write_json(self.dir / relpath, obj)

    def read_artifact(self, stage_id: str) -> dict:
        return json.loads(self.artifact_path(stage_id).read_text(encoding="utf-8"))

    @property
    def state_path(self) -> Path:
        return self.dir / "state.json"

    @property
    def events_path(self) -> Path:
        return self.dir / "events.jsonl"


def atomic_write_json(path: Path, obj) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=1, sort_keys=True, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return path
