"""FastAPI surface — the minimal contract the HELL FACTORY console consumes.

POST /api/runs                      {raw_request, requester, request_type?, idempotency_key?, mode?}
GET  /api/runs                      run summaries
GET  /api/runs/{id}                 full snapshot
GET  /api/runs/{id}/pack            live pipeline-pack (ETag/pack_seq short-circuit)
GET  /api/runs/{id}/events?after=N  incremental event poll
POST /api/runs/{id}/gates/{stage}/verdict   {verdict, approver, note?} -> 200/422
POST /api/runs/{id}/abort

In prod the app also serves workflows-ui/dist at / (one origin, no CORS).
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from engine import WORKSPACE
from engine.binding import RuntimeBinding
from engine.gates import GateApprovalError, GateBook
from engine.loader import load_workflow
from engine.model import EngineError
from engine.orchestrator import Orchestrator
from engine.pack import build_pack
from engine.validation import validate_workflow_input


class CreateRun(BaseModel):
    raw_request: str
    requester: str
    request_type: Optional[str] = None
    idempotency_key: Optional[str] = None
    mode: str = "replay"  # replay | live


class Verdict(BaseModel):
    verdict: str
    approver: str
    note: Optional[str] = None


class Resolution(BaseModel):
    action: str  # retry | abort
    resolver: str
    note: Optional[str] = None


class Hub:
    def __init__(self):
        self.workflow = load_workflow()
        self.gatebook = GateBook.load(self.workflow)
        self.binding = RuntimeBinding.load()
        self.runs: Dict[str, Orchestrator] = {}
        self.by_key: Dict[str, str] = {}
        self.tasks: Dict[str, asyncio.Task] = {}


def create_app(hub: Optional[Hub] = None) -> FastAPI:
    app = FastAPI(title="delivery-pipeline engine", version="0.1.0")
    app.state.hub = hub or Hub()

    def _hub() -> Hub:
        return app.state.hub

    def _orch(run_id: str) -> Orchestrator:
        orch = _hub().runs.get(run_id)
        if orch is None:
            raise HTTPException(404, f"unknown run {run_id}")
        return orch

    @app.post("/api/runs", status_code=201)
    async def create_run(body: CreateRun):
        hub = _hub()
        key = body.idempotency_key or str(uuid.uuid4())
        if key in hub.by_key:  # idempotent create
            rid = hub.by_key[key]
            return {"run_id": rid, "state": hub.runs[rid].run_state, "existing": True}
        if body.mode not in ("replay", "live"):
            raise HTTPException(422, "mode must be replay|live")
        payload = {"raw_request": body.raw_request, "requester": body.requester,
                   "idempotency_key": key}
        if body.request_type:
            payload["request_type"] = body.request_type
        errs = validate_workflow_input(hub.workflow, payload)
        if errs:
            raise HTTPException(422, {"input_errors": errs})
        run_id = f"run-{key[:8]}"
        n = 2
        while run_id in hub.runs:  # distinct keys can share an 8-char prefix
            run_id = f"run-{key[:8]}-{n}"
            n += 1
        orch = Orchestrator(hub.workflow, hub.gatebook, hub.binding,
                            run_id=run_id, workflow_input=payload, mode=body.mode)
        hub.runs[run_id] = orch
        hub.by_key[key] = run_id
        hub.tasks[run_id] = asyncio.create_task(orch.start(), name=f"run:{run_id}")
        return {"run_id": run_id, "state": orch.run_state, "existing": False}

    @app.get("/api/runs")
    async def list_runs():
        return [
            {"run_id": rid, "state": o.run_state, "mode": o.mode,
             "request_type": o.request_type, "requester": o.workflow_input.get("requester"),
             "pack_seq": o.pack_seq}
            for rid, o in _hub().runs.items()
        ]

    @app.get("/api/runs/{run_id}")
    async def get_run(run_id: str):
        return _orch(run_id).snapshot()

    @app.get("/api/runs/{run_id}/pack")
    async def get_pack(run_id: str, request: Request, response: Response):
        orch = _orch(run_id)
        etag = f'W/"{orch.pack_seq}"'
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304)
        response.headers["ETag"] = etag
        return build_pack(orch)

    @app.get("/api/runs/{run_id}/events")
    async def get_events(run_id: str, after: int = -1):
        orch = _orch(run_id)
        return [e for e in orch.events if e["seq"] > after]

    @app.post("/api/runs/{run_id}/gates/{stage_id}/verdict")
    async def post_verdict(run_id: str, stage_id: str, body: Verdict):
        orch = _orch(run_id)
        try:
            gate = orch.post_verdict(stage_id, body.verdict, body.approver, body.note)
        except GateApprovalError as e:
            raise HTTPException(422, str(e))
        except EngineError as e:
            raise HTTPException(404, str(e))
        return gate.as_record()

    @app.post("/api/runs/{run_id}/stages/{stage_id}/resolve")
    async def resolve_stage(run_id: str, stage_id: str, body: Resolution):
        orch = _orch(run_id)
        try:
            return orch.resolve_stage(stage_id, body.action, body.resolver, body.note)
        except EngineError as e:
            raise HTTPException(422, str(e))

    @app.post("/api/runs/{run_id}/abort")
    async def abort(run_id: str):
        orch = _orch(run_id)
        orch.abort()
        return {"run_id": run_id, "state": orch.run_state}

    dist = WORKSPACE / "workflows-ui" / "dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="console")

    return app
