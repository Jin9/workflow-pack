#!/usr/bin/env python3
"""Validate the fenced JSON examples in each skill's contract sections.

House contract v2 requires each `## Input contract` / `## Output contract` section to
carry ONE fenced ```json example that validates against the referenced schema
(schemas/input.json / schemas/output.json). This lint extracts the FIRST fenced json
block under each contract heading and validates it, so examples cannot drift.

Deterministic; no network. BLOCKING by default (non-zero on any finding — the fleet
holds at ZERO); --advisory reports only. Run from the repo root:
    engine/.venv/bin/python workflows/scripts/check_contract_examples.py [--advisory] [skill-dir ...]
With no args, scans all of workflows/skills/*/.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
SECTIONS = {"## Input contract": "input.json", "## Output contract": "output.json"}
FENCE = re.compile(r"```json\n(.*?)```", re.DOTALL)


def first_json_block(body: str, heading: str) -> str | None:
    idx = body.find(heading)
    if idx < 0:
        return None
    nxt = body.find("\n## ", idx + len(heading))
    section = body[idx:nxt if nxt > 0 else len(body)]
    m = FENCE.search(section)
    return m.group(1) if m else None


def check_skill(skill_dir: Path, findings: list[str]) -> None:
    skill = skill_dir.name
    body = (skill_dir / "SKILL.md").read_text()
    for heading, schema_name in SECTIONS.items():
        schema_path = skill_dir / "schemas" / schema_name
        example = first_json_block(body, heading)
        if example is None:
            if schema_path.exists():
                findings.append(f"{skill}: {heading} has no fenced json example")
            continue
        try:
            payload = json.loads(example)
        except json.JSONDecodeError as exc:
            findings.append(f"{skill}: {heading} example is not valid JSON ({exc})")
            continue
        if not schema_path.exists():
            findings.append(f"{skill}: {heading} example present but schemas/{schema_name} missing")
            continue
        schema = json.loads(schema_path.read_text())
        validator = jsonschema.validators.validator_for(schema)(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
        for err in errors[:3]:
            loc = "/".join(str(p) for p in err.path) or "(root)"
            findings.append(f"{skill}: {heading} example fails schema at {loc}: {err.message}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="*", help="skill dirs (default: workflows/skills/*)")
    ap.add_argument("--advisory", action="store_true",
                    help="report only (exit 0). Default is BLOCKING: the fleet holds at zero findings.")
    ap.add_argument("--strict", action="store_true",
                    help="deprecated no-op: blocking is now the default")
    args = ap.parse_args()

    dirs = ([Path(d) for d in args.dirs] if args.dirs
            else sorted(p for p in (ROOT / "workflows/skills").iterdir()
                        if p.is_dir() and (p / "SKILL.md").exists()))
    findings: list[str] = []
    for d in dirs:
        check_skill(d, findings)

    for f in findings:
        print(f"EXAMPLE  {f}")
    print(f"\n{len(findings)} finding(s) across {len(dirs)} skills "
          f"({'advisory' if args.advisory else 'BLOCKING'} mode)")
    return 1 if (findings and not args.advisory) else 0


if __name__ == "__main__":
    sys.exit(main())
