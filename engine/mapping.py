"""Assemble a stage's input payload from from_workflow_input / from_stage picks.

Pure and unit-testable. Semantics:
- A field listed in from_workflow_input that is missing from the workflow input
  is an error if the workflow declares it required, otherwise omitted + warned.
- A field listed in from_stage that is missing from the producer's artifact is
  omitted + warned (the schema-level example: ux-intake's optional
  component_inventory_path may legitimately be absent on a degraded UX drop).
  Enforcement of what the consumer truly needs happens at the skill's own
  input schema when the stage runs live.
- NESTED_HANDOFF: the pipeline YAML documents (ba-research <- s1-discovery)
  as "orchestrator merges into input.discovery" — the v1 stage schema has no
  `as:` slot, so that rule lives here. Fields from that producer nest under
  the named key instead of merging flat.
- REF-CHAIN HYDRATION: ba-research emits a manifest (epics[]/story_files[] are
  {id, file, ...} refs — "nothing inlined"), but the inline-era consumer skills
  (designing-tech-lead-handoff etc.) expect inline Epic/Story OBJECTS handed
  across the boundary ("the orchestrator hands values across the stage
  boundary, not files" — their own input-schema note). When stage_dirs
  provides the producer's dir, refs whose `file` resolves are loaded inline:
  payload["epics"] becomes the loaded objects and payload["stories"] is added
  from story_files (the original refs stay under "story_files").
- idempotency_key from the workflow input is injected into EVERY payload —
  the workflow carries one idempotency key across stages and most skill input
  contracts require it (same key + same inputs => same output).
- Flat-merge collisions are resolved last-writer-wins with a warning (source
  order = YAML from_stage order).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Tuple

from engine.model import SpecError, StageSpec

# (consumer stage id, producer stage id) -> input key the producer's fields nest under
NESTED_HANDOFF = {
    ("ba-research", "s1-discovery"): "discovery",
    # qa-plan reads BOTH review verdicts; flat-merge would silently keep only the
    # last writer (frontend) — nest each producer under its own key instead.
    ("qa-plan", "backend-review"): "backend_review",
    ("qa-plan", "frontend-review"): "frontend_review",
}

REF_CHAIN_PRODUCER = "ba-research"  # the manifest-emitting stage whose refs hydrate


def _load_ref(producer_dir: Path, ref, warnings: List[str], what: str):
    """A ref is a dict carrying `file` (relative to the producer's stage dir).
    Returns the loaded object, or the ref unchanged (with a warning) on any miss."""
    if not isinstance(ref, dict) or "file" not in ref:
        return ref
    path = producer_dir / ref["file"]
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        warnings.append(f"hydration: {what} ref {ref.get('id', ref['file'])} unreadable ({e})")
        return ref


def _hydrate_ba_research(payload: Dict, producer_dir: Path, warnings: List[str]) -> None:
    if isinstance(payload.get("epics"), list):
        payload["epics"] = [_load_ref(producer_dir, r, warnings, "epic") for r in payload["epics"]]
    if isinstance(payload.get("story_files"), list):
        payload["stories"] = [
            _load_ref(producer_dir, r, warnings, "story") for r in payload["story_files"]
        ]


def assemble_input(
    stage: StageSpec,
    workflow_input: Mapping,
    artifacts: Mapping[str, Mapping],
    workflow_required: Tuple[str, ...] = (),
    stage_dirs: Optional[Mapping[str, Path]] = None,
) -> Tuple[Dict, List[str]]:
    payload: Dict = {}
    warnings: List[str] = []

    for f in stage.input_from_workflow:
        if f in workflow_input:
            payload[f] = workflow_input[f]
        elif f in workflow_required:
            raise SpecError(f"stage {stage.id}: required workflow input {f!r} is missing")
        else:
            warnings.append(f"workflow input {f!r} absent; omitted")

    for producer, fields in stage.input_from_stage.items():
        if producer not in artifacts:
            raise SpecError(
                f"stage {stage.id}: producer {producer!r} has no artifact (scheduling bug)"
            )
        source = artifacts[producer]
        nest_key = NESTED_HANDOFF.get((stage.id, producer))
        target: Dict = {}
        for f in fields:
            if f in source:
                target[f] = source[f]
            else:
                warnings.append(f"{producer}.{f} absent from artifact; omitted")
        if nest_key is not None:
            payload[nest_key] = target
        else:
            for k, v in target.items():
                if k in payload and payload[k] != v:
                    warnings.append(f"input key {k!r} overwritten by {producer}")
                payload[k] = v
        if (producer == REF_CHAIN_PRODUCER and nest_key is None
                and stage_dirs and producer in stage_dirs):
            _hydrate_ba_research(payload, Path(stage_dirs[producer]), warnings)

    if "idempotency_key" in workflow_input and "idempotency_key" not in payload:
        payload["idempotency_key"] = workflow_input["idempotency_key"]

    return payload, warnings
