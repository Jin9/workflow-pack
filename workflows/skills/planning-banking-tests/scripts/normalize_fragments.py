#!/usr/bin/env python3
"""Normalize agent-produced fragments to BA-authoritative vocabulary.

v1.0.0: used by the test harness when test 001 fan-out runs through merge.py.
v1.1+: when ADR #8 relaxes and Stage 4c becomes a sub-graph, this script
becomes a runtime normalization step between sub-agent fragments and the
deterministic merger. Empirically validated in test 001 — without this step,
3 of 5 quality assertions fail on the e-commerce holdout because
independent agents drift on regulator codes and PII field names.

Rules (mechanical, no LLM):
  1. compliance_tests[].regulator_code — map short forms (TRC, CPA, PDPA, CCA)
     to canonical underscore form derived from BA regulatory_dependencies[].code
     (e.g., TRC -> TRC_VAT_7PCT, CPA -> CPA_TH_DISCLOSURE).
  2. compliance_tests[].id — rebuild as COMP-{canonical_regulator_code}-{seq}.
  3. test_data_specs[].pii_field_refs[] — strip dotted prefixes, then map
     common variants to bare BA PII field names (customer.email -> email,
     phone_number -> phone, shipping_address.line1 -> shipping_address, etc.).
  4. test_cases[].compliance_tags[] — same regulator-code normalization.

CLI:
  python3 normalize_fragments.py --brief PATH --fragments-dir PATH [--in-place|--out-dir PATH]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def build_regulator_normalizer(brief: dict) -> dict[str, str]:
    """Build a map from agent-emitted regulator_code to canonical underscore form."""
    authoritative = []
    for r in brief.get("regulatory_dependencies", []):
        code = r.get("code", "")
        if not code:
            continue
        canonical = code.replace("-", "_")
        authoritative.append(canonical)

    mapping: dict[str, str] = {}
    for canon in authoritative:
        mapping[canon] = canon
        mapping[canon.replace("_", "-")] = canon
        # Short form: first underscore-segment
        short = canon.split("_", 1)[0]
        mapping.setdefault(short, canon)
    return mapping


def build_pii_normalizer(brief: dict) -> dict[str, str]:
    """Build a map from agent-emitted PII field name to bare BA field name."""
    authoritative = {p.get("field", "") for p in brief.get("pii_inventory", []) if p.get("field")}
    mapping: dict[str, str] = {f: f for f in authoritative}
    # Manual mapping rules informed by test 001 agent drift.
    extras = {
        "customer.email": "email",
        "user.email": "email",
        "customer.phone": "phone",
        "phone_number": "phone",
        "user.password": "password",
        "customer.name": "name",
        "shipping_address.recipient_name": "name",
        "recipient_name": "name",
        "shipping_address.line1": "shipping_address",
        "shipping_address.line2": "shipping_address",
        "shipping_address.postal_code": "shipping_address",
        "address_line": "shipping_address",
        "address_id": "shipping_address",
        "user_id": "customer_id",
        "order.order_number": "order_number",
        "order.tracking_number": "tracking_number",
    }
    for src, dst in extras.items():
        if dst in authoritative:
            mapping[src] = dst
    return mapping


def normalize_pii_ref(ref: str, pii_map: dict[str, str]) -> str | None:
    """Return canonical PII field name, or None if no match (caller decides drop/keep)."""
    if ref in pii_map:
        return pii_map[ref]
    # Try stripping a dotted prefix
    if "." in ref:
        suffix = ref.split(".", 1)[1]
        if suffix in pii_map:
            return pii_map[suffix]
    return None


COMP_ID_RE = re.compile(r"^COMP-(.+)-(\d{3})$")


def normalize_fragment(frag: dict, reg_map: dict[str, str], pii_map: dict[str, str]) -> tuple[dict, dict]:
    """Return (normalized fragment, change stats)."""
    stats = {
        "regulator_codes_remapped": 0,
        "comp_ids_rebuilt": 0,
        "pii_refs_remapped": 0,
        "pii_refs_dropped": 0,
        "compliance_tags_remapped": 0,
    }

    # compliance_tests
    for c in frag.get("compliance_tests", []):
        old_code = c.get("regulator_code", "")
        new_code = reg_map.get(old_code, old_code)
        if new_code != old_code:
            c["regulator_code"] = new_code
            stats["regulator_codes_remapped"] += 1
        # Rebuild id
        old_id = c.get("id", "")
        m = COMP_ID_RE.match(old_id)
        if m:
            new_id = f"COMP-{new_code}-{m.group(2)}"
            if new_id != old_id:
                c["id"] = new_id
                stats["comp_ids_rebuilt"] += 1

    # test_data_specs.pii_field_refs
    for spec in frag.get("test_data_specs", []):
        old_refs = spec.get("pii_field_refs", []) or []
        new_refs = []
        seen = set()
        for r in old_refs:
            mapped = normalize_pii_ref(r, pii_map)
            if mapped is None:
                stats["pii_refs_dropped"] += 1
                continue
            if mapped not in seen:
                seen.add(mapped)
                new_refs.append(mapped)
            if mapped != r:
                stats["pii_refs_remapped"] += 1
        spec["pii_field_refs"] = new_refs

    # test_cases.compliance_tags
    for tc in frag.get("test_cases", []):
        old_tags = tc.get("compliance_tags", []) or []
        new_tags = []
        for t in old_tags:
            # If tag matches a known regulator short/dashed form, normalize it
            if t in reg_map:
                normalized = reg_map[t]
                if normalized != t:
                    stats["compliance_tags_remapped"] += 1
                new_tags.append(normalized)
            else:
                new_tags.append(t)
        tc["compliance_tags"] = new_tags

    return frag, stats


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--brief", required=True, help="Path to BA brief output.json")
    p.add_argument("--fragments-dir", required=True, help="Directory containing *.json fragments")
    grp = p.add_mutually_exclusive_group()
    grp.add_argument("--in-place", action="store_true", help="Overwrite fragment files in place")
    grp.add_argument("--out-dir", help="Write normalized fragments to this directory instead")
    args = p.parse_args()

    brief = json.loads(Path(args.brief).read_text())
    reg_map = build_regulator_normalizer(brief)
    pii_map = build_pii_normalizer(brief)

    src_dir = Path(args.fragments_dir)
    if not src_dir.is_dir():
        fail(f"fragments-dir is not a directory: {src_dir}")

    out_dir = src_dir if args.in_place else Path(args.out_dir or src_dir.parent / "fragments-normalized")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"regulator code mappings: {len(reg_map)} variants -> {len(set(reg_map.values()))} canonical")
    print(f"PII field mappings:     {len(pii_map)} variants -> {len(set(pii_map.values()))} canonical")
    print()

    aggregate = {"regulator_codes_remapped": 0, "comp_ids_rebuilt": 0, "pii_refs_remapped": 0, "pii_refs_dropped": 0, "compliance_tags_remapped": 0}
    for src in sorted(src_dir.glob("*.json")):
        frag = json.loads(src.read_text())
        normalized, stats = normalize_fragment(frag, reg_map, pii_map)
        dest = out_dir / src.name
        dest.write_text(json.dumps(normalized, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{src.name}: {stats}")
        for k, v in stats.items():
            aggregate[k] += v
    print()
    print(f"AGGREGATE: {aggregate}")
    print(f"wrote -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
