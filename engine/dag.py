"""depends_on graph: topological order, ready-set, downstream cones.

Parallelism is emergent — any two stages whose dependencies are satisfied run
concurrently (this is how the backend and frontend legs parallelize; there is
no fan-out keyword in the YAML).
"""
from __future__ import annotations

from collections import deque
from typing import Dict, FrozenSet, List, Set, Tuple

from engine.model import SpecError, WorkflowSpec


class Dag:
    def __init__(self, workflow: WorkflowSpec):
        self.parents: Dict[str, Tuple[str, ...]] = {
            s.id: s.depends_on for s in workflow.stages
        }
        self.children: Dict[str, List[str]] = {s.id: [] for s in workflow.stages}
        for s in workflow.stages:
            for dep in s.depends_on:
                self.children[dep].append(s.id)
        self.topo_order = self._topo()

    def _topo(self) -> Tuple[str, ...]:
        indeg = {sid: len(deps) for sid, deps in self.parents.items()}
        queue = deque(sid for sid, d in indeg.items() if d == 0)
        order: List[str] = []
        while queue:
            sid = queue.popleft()
            order.append(sid)
            for child in self.children[sid]:
                indeg[child] -= 1
                if indeg[child] == 0:
                    queue.append(child)
        if len(order) != len(self.parents):
            cyclic = sorted(sid for sid, d in indeg.items() if d > 0)
            raise SpecError(f"depends_on graph has a cycle involving: {cyclic}")
        return tuple(order)

    def downstream_cone(self, stage_id: str) -> FrozenSet[str]:
        """stage_id plus every transitive dependent (what a loop_back invalidates)."""
        seen: Set[str] = set()
        queue = deque([stage_id])
        while queue:
            sid = queue.popleft()
            if sid in seen:
                continue
            seen.add(sid)
            queue.extend(self.children[sid])
        return frozenset(seen)

    def ready(self, done: Set[str], started_or_done: Set[str]) -> List[str]:
        """Stages whose parents are all done and which have not been started."""
        return [
            sid
            for sid in self.topo_order
            if sid not in started_or_done and all(p in done for p in self.parents[sid])
        ]
