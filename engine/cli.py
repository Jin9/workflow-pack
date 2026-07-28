"""CLI: python3 -m engine {replay|serve|validate-run|verify-audit}

replay        run the full 27-stage pipeline token-free from the ShopPilot corpus
serve         FastAPI at localhost (the console's backend)
validate-run  dual-schema validate every artifact in a run dir (the oracle)
verify-audit  walk a run's hash-chained events.jsonl
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from engine import WORKSPACE
from engine.audit import verify_chain
from engine.binding import RuntimeBinding
from engine.gates import GateBook
from engine.loader import load_workflow
from engine.orchestrator import Orchestrator
from engine.pack import build_pack
from engine.runstore import RunStore, artifact_relpath
from engine.validation import validate_artifact
from engine.model import ValidationFailed


def _print_stage_table(orch) -> None:
    for sid in orch.dag.topo_order:
        rec = orch.stage[sid]
        gate = orch.gates.get(sid)
        gate_txt = f" gate={gate.status}" if gate else ""
        caveat = " (caveat)" if rec["caveat"] else ""
        print(f"  {sid:<22} {rec['state']:<14} attempts={rec['attempts']}{gate_txt}{caveat}")


def cmd_replay(args) -> int:
    workflow = load_workflow()
    gatebook = GateBook.load(workflow)
    binding = RuntimeBinding.load()

    amigos = {}
    for pair in (getattr(args, "amigos", None) or []):
        role, _, name = pair.partition("=")
        if not role.strip() or not name.strip():
            raise SystemExit(f"--amigos expects role=Name, got {pair!r}")
        amigos[role.strip()] = name.strip()

    approve_hook = None
    if args.approve_as or amigos:
        approver = args.approve_as

        def approve_hook(gate):
            # An operator-supplied name is a human instruction, not an auto-approval:
            # without --approve-as every blocking gate parks the run.
            verdict = gate.spec.proceed_when or (
                "approve" if "approve" in gate.spec.verdicts else gate.spec.verdicts[0]
            )
            if gate.spec.quorum:
                # A quorum needs a DISTINCT named human per role. One operator name
                # must not be able to impersonate three reviewers, so an unsupplied
                # role parks the run instead of being invented.
                for role in gate.outstanding_roles:
                    if role in amigos:
                        return (verdict, amigos[role], f"replay {role} approval", role)
                return None
            if not approver:
                return None
            return (verdict, approver, "replay operator approval")

    workflow_input = {
        "raw_request": args.request,
        "requester": args.requester,
        "idempotency_key": args.idempotency_key,
    }
    orch = Orchestrator(workflow, gatebook, binding, run_id=args.run_id,
                        workflow_input=workflow_input, mode="replay",
                        approve_hook=approve_hook)
    state = asyncio.run(orch.start())
    print(f"run {args.run_id}: {state}"
          + (f" ({orch.terminal_reason})" if orch.terminal_reason else ""))
    _print_stage_table(orch)
    if args.export_pack:
        Path(args.export_pack).parent.mkdir(parents=True, exist_ok=True)
        Path(args.export_pack).write_text(
            json.dumps(build_pack(orch), indent=1, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(f"pack exported: {args.export_pack}")
    return 0 if state in ("done", "ship-with-caveats") else 1


def cmd_validate_run(args) -> int:
    workflow = load_workflow()
    run_dir = Path(args.run_dir)
    fails = missing = passed = 0
    for stage in workflow.stages:
        artifact = run_dir / artifact_relpath(stage.id)
        if not artifact.is_file():
            print(f"MISSING {stage.id:<22} {artifact_relpath(stage.id)}")
            missing += 1
            continue
        try:
            validate_artifact(stage, artifact)
            print(f"PASS    {stage.id:<22} {artifact_relpath(stage.id)}")
            passed += 1
        except ValidationFailed as e:
            fails += 1
            print(f"FAIL    {stage.id:<22} {artifact_relpath(stage.id)}")
            for m in e.errors[:6]:
                print(f"        {m}")
    total = passed + fails + missing
    print(f"\n{passed}/{total} pass, {fails} fail, {missing} missing"
          f" — {'ALL PASS' if fails == 0 and missing == 0 else 'NOT CLEAN'}")
    return 1 if (fails or (missing and args.strict)) else 0


def cmd_verify_audit(args) -> int:
    path = Path(args.run_dir) / "events.jsonl"
    try:
        n = verify_chain(path)
    except ValueError as e:
        print(f"AUDIT CHAIN BROKEN: {e}")
        return 1
    print(f"audit chain OK — {n} events verified ({path})")
    return 0


def cmd_serve(args) -> int:
    import uvicorn
    from engine.api import create_app
    uvicorn.run(create_app(), host=args.host, port=args.port, log_level="info")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="engine")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("replay", help="token-free full-pipeline replay from the ShopPilot corpus")
    r.add_argument("--run-id", default="replay-1")
    r.add_argument("--approve-as", default=None,
                   help="operator name used to release blocking gates (omit -> run parks at the first gate)")
    r.add_argument("--amigos", action="append", metavar="ROLE=NAME", default=None,
                   help="named human per role for a quorum gate, e.g. --amigos ba-lead='Khun Pim' "
                        "(repeatable). A quorum gate parks unless every role is supplied.")
    r.add_argument("--request", default="ShopPilot replay of the canned corpus")
    r.add_argument("--requester", default="replay-operator")
    r.add_argument("--idempotency-key", default="00000000-0000-4000-8000-000000000000")
    r.add_argument("--export-pack", default=None, help="write the pipeline-pack JSON here")
    r.set_defaults(fn=cmd_replay)

    v = sub.add_parser("validate-run", help="dual-schema validate every artifact in a run dir")
    v.add_argument("run_dir")
    v.add_argument("--strict", action="store_true", help="missing artifacts also fail")
    v.set_defaults(fn=cmd_validate_run)

    a = sub.add_parser("verify-audit", help="verify a run's hash-chained events.jsonl")
    a.add_argument("run_dir")
    a.set_defaults(fn=cmd_verify_audit)

    s = sub.add_parser("serve", help="run the FastAPI engine (console backend)")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    s.set_defaults(fn=cmd_serve)

    args = p.parse_args(argv)
    return args.fn(args)
