from engine.executors.base import ExecutionResult, StageContext
from engine.executors.replay import ReplayExecutor
from engine.executors.headless import HeadlessClaudeExecutor
from engine.executors.sdk import SdkExecutor
from engine.executors.script import ScriptExecutor

REGISTRY = {
    "replay": ReplayExecutor,
    "headless": HeadlessClaudeExecutor,
    "sdk": SdkExecutor,
    "script": ScriptExecutor,
}

__all__ = [
    "ExecutionResult", "StageContext", "REGISTRY",
    "ReplayExecutor", "HeadlessClaudeExecutor", "SdkExecutor", "ScriptExecutor",
]
