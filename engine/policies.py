"""Failure policies (retry / loop_back / human-queue) + verdict routing.

The YAML declares per-stage failure_policy; terminal states are engine-derived
(the YAML header says so explicitly). Verdict routing is the engine-derived
rule for review/validate stages whose artifact VALIDATES but whose `verdict`
field demands rework: vocabularies are per-stage and never normalized — the
table below routes known values and fails CLOSED (route to a human) on any
verdict it does not recognize.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from engine.model import StageSpec

# verdict value -> route
OK = "ok"
CAVEAT = "ok-with-caveat"   # counts toward ship-with-caveats
REWORK = "rework"           # feeds the stage's loop_back policy
FAIL = "fail"               # feeds the stage's failure policy
HUMAN = "human"             # straight to the stage's human queue
COMPENSATE = "compensate"   # trigger the SAGA compensating action

VERDICT_ROUTES = {
    "PASS": OK, "pass": OK, "approve": OK, "approved": OK, "promote": OK,
    "proceed": OK, "PROCEED": OK, "go": OK, "green": OK,
    "REVISE": REWORK,  # plan-review's rework vocabulary (see the round-1 corpus artifact)
    "conditional": CAVEAT, "conditional-go": CAVEAT, "ship-with-caveats": CAVEAT,
    "pass-with-caveats": CAVEAT,
    "loop_back": REWORK, "rework": REWORK, "reject": REWORK, "changes-requested": REWORK,
    # plan-review's full vocabulary (boundary enum): BLOCK/reroute feed the stage's
    # loop_back policy — "reroute high findings back to TL; cap exceeded -> HardFail".
    "BLOCK": REWORK, "reroute": REWORK, "hard-fail": FAIL,
    "FAIL": FAIL, "fail": FAIL, "failed": FAIL, "ERROR": FAIL, "error": FAIL,
    "human-queue": HUMAN, "hold": HUMAN, "needs-work": HUMAN, "escalate": HUMAN,
    "rollback": COMPENSATE, "do-not-build": HUMAN,
}


def route_verdict(artifact: dict) -> str:
    if not isinstance(artifact, dict) or "verdict" not in artifact:
        return OK
    v = artifact["verdict"]
    if isinstance(v, dict):  # some evidence shapes wrap the verdict
        v = v.get("overall", v.get("value"))
    return VERDICT_ROUTES.get(str(v), HUMAN)  # unknown vocabulary -> fail closed to a human


@dataclass(frozen=True)
class Action:
    kind: str  # retry | loop_back | human-queue | abort
    delay_seconds: float = 0.0
    queue: Optional[str] = None
    loop_to: Optional[str] = None


def backoff_delay(policy_backoff: str, attempt: int, multiplier: float) -> float:
    if multiplier <= 0:
        return 0.0
    if policy_backoff == "exponential":
        return multiplier * (2 ** max(0, attempt - 1))
    return multiplier


def on_failure(
    stage: StageSpec,
    attempts_so_far: int,
    loops_taken: int,
    backoff_multiplier: float = 0.5,
) -> Action:
    """Decide what happens after a failed attempt (execution, validation, or
    verdict routed to fail/rework). attempts_so_far counts the attempt that
    just failed (first failure => 1). loops_taken counts completed loop_backs
    on this stage's loop edge."""
    fp = stage.failure_policy

    if fp.on_failure == "retry":
        if attempts_so_far <= fp.max_retries:
            return Action("retry", delay_seconds=backoff_delay(fp.backoff, attempts_so_far, backoff_multiplier))
        if fp.after_max_retries == "human-queue":
            return Action("human-queue", queue=fp.human_queue_name or "delivery-failures")
        return Action("abort")

    if fp.on_failure == "human-queue":
        return Action("human-queue", queue=fp.human_queue_name or "delivery-failures")

    if fp.on_failure == "loop_back":
        if loops_taken < fp.max_loops:
            return Action("loop_back", loop_to=fp.loop_to_stage)
        if fp.after_max_loops == "human-queue":
            return Action("human-queue", queue=fp.human_queue_name or "delivery-failures")
        return Action("abort")  # after_max_loops: abort -> HardFail upstream

    return Action("human-queue", queue="delivery-failures")  # unknown policy: fail closed
