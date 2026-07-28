#!/usr/bin/env python3
"""
check_frame_rule_data_drift.py — F-7 drift check (v1.3.0+).

Verifies that references/frame-rule-data.json (runtime source-of-truth for
FM-17) agrees with the markdown table at references/hidden-requirements-frames.md
lines 183-207. Exits 0 on agreement, 1 on drift (with a diff to stderr).

Comparison key per row: (trigger, sub_topic_id, frozenset(lowercased+stripped
coverage keywords), jurisdiction_note). Markdown keyword cells are
semicolon-separated; JSON keyword lists are explicit. Both sides are normalized
to lowercase + stripped before set comparison so that incidental whitespace and
case differences (e.g., "SCC" in the doc vs "scc " in JSON) do not register as
drift.

Run from the skill root:
    python3 scripts/check_frame_rule_data_drift.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import List, Tuple, Set


SKILL_ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = SKILL_ROOT / "references" / "frame-rule-data.json"
MD_PATH = SKILL_ROOT / "references" / "hidden-requirements-frames.md"

# Markers that bracket the sub-topic table inside hidden-requirements-frames.md.
TABLE_HEADER_RE = re.compile(
    r"^\|\s*Trigger\s*\|\s*sub_topic_id\s*\|\s*Coverage keywords",
    re.IGNORECASE,
)
TABLE_SEPARATOR_RE = re.compile(r"^\|\s*-+\s*\|")
TABLE_ROW_RE = re.compile(r"^\|")

Row = Tuple[str, str, frozenset, str]


def _normalize_keywords(raw: str) -> Set[str]:
    return {part.strip().lower() for part in raw.split(";") if part.strip()}


def parse_markdown_table(md_text: str) -> List[Row]:
    rows: List[Row] = []
    lines = md_text.splitlines()
    in_table = False
    for line in lines:
        if not in_table:
            if TABLE_HEADER_RE.match(line):
                in_table = True
            continue
        if TABLE_SEPARATOR_RE.match(line):
            continue
        if not TABLE_ROW_RE.match(line):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            break
        trigger = cells[0].strip("`")
        sub_id = cells[1].strip("`")
        keywords = frozenset(_normalize_keywords(cells[2]))
        jurisdiction = cells[3].strip()
        rows.append((trigger, sub_id, keywords, jurisdiction))
    return rows


def flatten_json_rules(doc: dict) -> List[Row]:
    rows: List[Row] = []
    for trig, entries in (doc.get("triggers") or {}).items():
        for e in entries:
            kw = frozenset(k.strip().lower() for k in e["coverage_keywords"] if k.strip())
            rows.append((trig, e["sub_topic_id"], kw, e["jurisdiction_note"]))
    return rows


def main() -> int:
    if not JSON_PATH.exists():
        print(f"FAIL: {JSON_PATH} not found", file=sys.stderr)
        return 1
    if not MD_PATH.exists():
        print(f"FAIL: {MD_PATH} not found", file=sys.stderr)
        return 1

    with JSON_PATH.open("r", encoding="utf-8") as fh:
        doc = json.load(fh)
    md_text = MD_PATH.read_text(encoding="utf-8")

    json_rows = sorted(flatten_json_rules(doc))
    md_rows = sorted(parse_markdown_table(md_text))

    if len(md_rows) == 0:
        print("FAIL: parsed 0 rows from markdown table", file=sys.stderr)
        return 1

    json_keys = {(r[0], r[1]) for r in json_rows}
    md_keys = {(r[0], r[1]) for r in md_rows}

    only_in_json = json_keys - md_keys
    only_in_md = md_keys - json_keys

    keyword_mismatches: List[str] = []
    jurisdiction_mismatches: List[str] = []
    json_by_key = {(r[0], r[1]): r for r in json_rows}
    md_by_key = {(r[0], r[1]): r for r in md_rows}
    for key in json_keys & md_keys:
        jr = json_by_key[key]
        mr = md_by_key[key]
        if jr[2] != mr[2]:
            keyword_mismatches.append(
                f"  - {key[0]}/{key[1]}:\n"
                f"      json:   {sorted(jr[2])}\n"
                f"      doc:    {sorted(mr[2])}\n"
                f"      json-only: {sorted(jr[2] - mr[2])}\n"
                f"      doc-only:  {sorted(mr[2] - jr[2])}"
            )
        if jr[3] != mr[3]:
            jurisdiction_mismatches.append(
                f"  - {key[0]}/{key[1]}:\n"
                f"      json: {jr[3]!r}\n"
                f"      doc:  {mr[3]!r}"
            )

    if not (only_in_json or only_in_md or keyword_mismatches or jurisdiction_mismatches):
        print(f"OK: {len(json_rows)} rows agree between frame-rule-data.json and hidden-requirements-frames.md")
        return 0

    print("F-7 DRIFT DETECTED between frame-rule-data.json and hidden-requirements-frames.md:", file=sys.stderr)
    if only_in_json:
        print(f"\nRows in JSON only ({len(only_in_json)}):", file=sys.stderr)
        for trig, sub in sorted(only_in_json):
            print(f"  - {trig}/{sub}", file=sys.stderr)
    if only_in_md:
        print(f"\nRows in markdown only ({len(only_in_md)}):", file=sys.stderr)
        for trig, sub in sorted(only_in_md):
            print(f"  - {trig}/{sub}", file=sys.stderr)
    if keyword_mismatches:
        print(f"\nKeyword set mismatches ({len(keyword_mismatches)}):", file=sys.stderr)
        for m in keyword_mismatches:
            print(m, file=sys.stderr)
    if jurisdiction_mismatches:
        print(f"\nJurisdiction-note mismatches ({len(jurisdiction_mismatches)}):", file=sys.stderr)
        for m in jurisdiction_mismatches:
            print(m, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
