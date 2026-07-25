"""Minimal runtime engine for workflows/delivery-pipeline.yaml.

Executes the 27-stage delivery pipeline with fail-closed dual-schema JSON
handoffs, externalized human gates (engine/config/gates.yaml), retry /
loop_back / human-queue failure policies, SAGA compensation, and a
hash-chained audit log. Executors are pluggable: replay (token-free, from
the ShopPilot corpus), headless `claude -p`, claude-agent-sdk (code-gen),
and scripted test gates.

Posture: this runtime is the recorded departure of
.claude/history/2026-07-04-live-engine-adr.md — shipped HTML stays offline,
generators stay deterministic, and no code path can auto-approve a
sync-named gate.
"""

from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
WORKSPACE = ENGINE_DIR.parent

__version__ = "0.1.0"
