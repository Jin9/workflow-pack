#!/usr/bin/env python3
"""Static contract-consistency lint for the delivery pipeline.

Rules (per stage in workflows/delivery-pipeline.yaml):
  R1 every `from_stage` field pick exists in the producer stage's `required_fields`
     (or is whitelisted as optional-with-default);
  R2 every pick is described by the consumer skill's schemas/input.json — checked
     POST-ADAPTER: picks nested by the engine (NESTED_HANDOFF) are expected under
     their nest key, and engine-injected keys are exempt;
  R3 the boundary schema's `required` equals the stage's YAML `required_fields`;
  R4 duplicate target keys: the same field name picked flat from two or more
     producers collides last-writer-wins in engine/mapping.py — flagged unless the
     consumer's Input contract declares the winner (whitelist below);
  R5 workflow bookend: delivery-pipeline-output.json `required` equals
     spec.output.required_fields;
  R6 compensation: each compensating_action's skill output.json and boundary
     schema_ref resolve.

Modes: BLOCKING by default (exit 1 on any finding — the fleet holds at ZERO after the
2026-07-12 contract reshape) · --advisory (report only, exit 0) · --baseline FILE
(ratchet: only findings NOT in FILE count; --write-baseline rewrites FILE). --strict is
a deprecated no-op (blocking is the default now).

Deterministic; no network. Run from the repo root:
    engine/.venv/bin/python workflows/scripts/check_contract_consistency.py [--advisory] [--baseline FILE]
"""
import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
YAML_PATH = ROOT / "workflows/delivery-pipeline.yaml"
SKILLS = ROOT / "workflows/skills"

# Mirror of engine/mapping.py NESTED_HANDOFF: (consumer stage, producer stage) -> nest key.
# MUST move in the same commit as engine/mapping.py — a stale mirror reports every
# nested pick as flat drift, in both directions.
NESTED_HANDOFF = {("ba-breakdown", "s1-discovery"): "discovery",
                  ("ba-research", "ba-breakdown"): "breakdown",
                  ("qa-plan", "backend-review"): "backend_review",
                  ("qa-plan", "frontend-review"): "frontend_review"}

# Keys the engine injects into payloads (engine/mapping.py + orchestrator.py) —
# consumers may document them, R2 never requires the raw pick shape for them.
ENGINE_INJECTED = {"idempotency_key", "upstream_artifacts", "loop_back_feedback"}

# R1: (producer_stage_id, field) picks a consumer may take although the producer does
# not guarantee them; each entry must be justified in the consumer's Input contract.
OPTIONAL_PICK_WHITELIST: set = {
    # s1-discovery emits handoff_to_intake only on proceed; the consumer
    # (breaking-down-ba-scope) documents absent == byte-identical no-seeding.
    ("s1-discovery", "handoff_to_intake"),
}

# R4: (consumer_stage_id, field) flat-merge collisions explicitly documented in the
# consumer's Input contract (which producer wins today).
COLLISION_WHITELIST: set = {
    # files_generated is picked from BOTH implement stages; each consumer's Input
    # contract documents "the top-level field is the frontend manifest only" and
    # resolves both full artifacts via upstream_artifacts.
    ("appsec-scan", "files_generated"),
    ("contract-tests", "files_generated"),
    ("integration-tests", "files_generated"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--advisory", action="store_true",
                    help="report only (exit 0). Default is BLOCKING: the fleet holds at zero findings.")
    ap.add_argument("--strict", action="store_true",
                    help="deprecated no-op: blocking is now the default")
    ap.add_argument("--baseline", type=Path, help="ratchet file: only NEW findings count")
    ap.add_argument("--write-baseline", action="store_true",
                    help="rewrite --baseline with the current findings")
    args = ap.parse_args()

    spec = yaml.safe_load(YAML_PATH.read_text())["spec"]
    stages = {s["id"]: s for s in spec["stages"]}
    findings: list[str] = []

    for sid, stage in stages.items():
        skill = stage["skill_ref"].split("/")[-1]
        picks = (stage.get("input", {}) or {}).get("from_stage", {}) or {}

        input_schema_path = SKILLS / skill / "schemas/input.json"
        input_props = {}
        if input_schema_path.exists():
            input_props = json.loads(input_schema_path.read_text()).get("properties", {})

        seen_flat: dict[str, str] = {}
        for prod_id, fields in picks.items():
            prod = stages.get(prod_id)
            if prod is None:
                findings.append(f"{sid}: picks from unknown stage `{prod_id}`")
                continue
            nest = NESTED_HANDOFF.get((sid, prod_id))
            prod_required = set((prod.get("output", {}) or {}).get("required_fields", []))
            for f in fields:
                if f not in prod_required and (prod_id, f) not in OPTIONAL_PICK_WHITELIST:
                    findings.append(
                        f"{sid}: picks `{prod_id}.{f}` but producer required_fields "
                        f"does not guarantee it (silent omit+warn at runtime)")
                if nest is None and f not in ENGINE_INJECTED:
                    if f in seen_flat and (sid, f) not in COLLISION_WHITELIST:
                        findings.append(
                            f"{sid}: flat-merge COLLISION on `{f}` "
                            f"({seen_flat[f]} then {prod_id}: last writer wins)")
                    seen_flat[f] = prod_id
                # R2: post-adapter shape in the consumer's advisory input schema
                if input_props:
                    if nest is not None:
                        if nest not in input_props:
                            findings.append(
                                f"{sid}: nested handoff key `{nest}` (from {prod_id}) "
                                f"missing from {skill}/schemas/input.json properties")
                    elif f not in input_props:
                        findings.append(
                            f"{sid}: picks `{prod_id}.{f}` but {skill}/schemas/input.json "
                            f"has no such property (advisory input contract out of date)")

        out = stage.get("output", {}) or {}
        ref = out.get("schema_ref")
        if ref:
            boundary_path = ROOT / "workflows" / ref
            if not boundary_path.exists():
                findings.append(f"{sid}: boundary schema {ref} missing")
            else:
                boundary_required = set(json.loads(boundary_path.read_text()).get("required", []))
                yaml_required = set(out.get("required_fields", []))
                if boundary_required != yaml_required:
                    only_b = sorted(boundary_required - yaml_required)
                    only_y = sorted(yaml_required - boundary_required)
                    findings.append(
                        f"{sid}: boundary `required` != YAML required_fields "
                        f"(boundary-only: {only_b or '-'} · yaml-only: {only_y or '-'})")

        comp = stage.get("compensating_action")
        if comp and "skill_ref" in comp:
            comp_skill = comp["skill_ref"].split("/")[-1]
            if not (SKILLS / comp_skill / "schemas/output.json").exists():
                findings.append(f"{sid}: compensation skill {comp_skill} has no schemas/output.json")
            comp_ref = comp.get("schema_ref")
            if comp_ref and not (ROOT / "workflows" / comp_ref).exists():
                findings.append(f"{sid}: compensation boundary schema {comp_ref} missing")

    # R5: workflow output bookend mirrors spec.output.required_fields
    wf_out_ref = (spec.get("output", {}) or {}).get("schema_ref")
    if wf_out_ref:
        wf_schema = json.loads((ROOT / "workflows" / wf_out_ref).read_text())
        wf_required = set(wf_schema.get("required", []))
        wf_yaml = set((spec.get("output", {}) or {}).get("required_fields", []))
        if wf_required != wf_yaml:
            findings.append(
                "workflow output: schema `required` != spec.output.required_fields "
                f"(schema-only: {sorted(wf_required - wf_yaml) or '-'} · "
                f"yaml-only: {sorted(wf_yaml - wf_required) or '-'})")

    findings = sorted(findings)
    baseline: set[str] = set()
    if args.baseline and args.baseline.exists():
        baseline = set(args.baseline.read_text().splitlines())
    if args.baseline and args.write_baseline:
        args.baseline.write_text("\n".join(findings) + ("\n" if findings else ""))

    new = [f for f in findings if f not in baseline]
    fixed = len(baseline - set(findings))
    report = new if args.baseline else findings
    for f in report:
        print(f"DRIFT  {f}")
    tail = (f" · baseline: {len(baseline)} known, {fixed} fixed, {len(new)} NEW"
            if args.baseline else "")
    print(f"\n{len(findings)} finding(s) across {len(stages)} stages "
          f"({'advisory' if args.advisory else 'BLOCKING'} mode){tail}")
    return 1 if (report and not args.advisory) else 0


if __name__ == "__main__":
    sys.exit(main())
