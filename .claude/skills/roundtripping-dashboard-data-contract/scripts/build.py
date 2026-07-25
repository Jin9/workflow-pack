#!/usr/bin/env python3
"""Round-trip: regenerate the dashboard's DATA module from dashboard-data.json.

This is the source-of-truth build. You edit the validated JSON; this script
regenerates the DATA module (the 7 consts + the 3 verbatim merge statements),
gzips it deterministically (mtime=0), and splices ONLY the c7f43bda entry's
base64 back into the bundle. The render module and all 15 fonts stay
byte-identical because nothing else in the manifest is touched.

Validation gates the build: JSON Schema + structural cross-reference checks +
the offline rule. Any blocking finding aborts before the HTML is written.

Deterministic: same dashboard-data.json -> byte-identical HTML every run.

Usage:
  build.py [--data PATH] [--html PATH] [--schema PATH] [--check]
  --check   validate only; do not write the HTML.
"""
import argparse
import json
import os
import sys

import bundle_io

DEFAULT_DATA = "dashboard-data.json"
DEFAULT_HTML = "squad-delivery-dashboard.standalone.html"
DATA_UUID = "c7f43bda-1a41-4a72-a2aa-5fac3269ac6d"
BUNDLED_SCHEMA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "schemas", "dashboard-data.schema.json"
)

# The 3 top-level statements the original DATA module runs to merge EVENTS /
# TEMPLATES / JSON_ONLY into each stage at load time. Reproduced VERBATIM so the
# runtime `stages` the render module reads is identical to the hand-authored
# bundle. If the upstream merge logic ever changes, update this block to match.
MERGE_JS = (
    "\nstages.forEach(s=>Object.assign(s, EVENTS[s.id]));\n"
    "stages.forEach(s=>{ const t=TEMPLATES[s.id]; if(t){ s.template=t.p; s.fmt=t.f; } });\n"
    "stages.forEach(s=>{ if(JSON_ONLY.has(s.id)) s.jsonOnly=true; });\n"
)

HEADER = (
    "/* ============================================================\n"
    "   Squad Delivery Dashboard - data (verbatim from source design)\n"
    "   GENERATED from dashboard-data.json by build.py - do not hand-edit.\n"
    "   Edit dashboard-data.json, then run build.py to regenerate the bundle.\n"
    "   ============================================================ */\n\n"
)

OFFLINE_FORBIDDEN = ("https://", "http://", "src=", "@import", "url(")


def _walk_strings(value, path="$"):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from _walk_strings(v, "%s.%s" % (path, k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _walk_strings(v, "%s[%d]" % (path, i))


def validate(data, schema_path):
    """Return a list of blocking error strings (empty == valid)."""
    errors = []

    # 1. JSON Schema (draft-07).
    try:
        import jsonschema
        schema = json.load(open(schema_path, encoding="utf-8"))
        validator = jsonschema.Draft7Validator(schema)
        for e in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
            loc = "$" + "".join("[%r]" % p for p in e.path)
            errors.append("schema: %s: %s" % (loc, e.message))
    except ImportError:
        errors.append("jsonschema not installed - cannot run schema validation gate.")

    if not isinstance(data, dict):
        return errors + ["root: contract must be a JSON object."]

    stage_ids = [s.get("id") for s in data.get("stages", []) if isinstance(s, dict)]
    id_set = set(stage_ids)

    # 2. Unique stage ids.
    dupes = sorted({i for i in stage_ids if stage_ids.count(i) > 1})
    if dupes:
        errors.append("stages: duplicate id(s): %s" % ", ".join(map(str, dupes)))

    # 3. events / templates keys must EQUAL the stages[].id set (both directions:
    #    every key names a stage, and every stage has exactly one entry).
    for label in ("events", "templates"):
        block = data.get(label, {})
        if isinstance(block, dict):
            for k in block:
                if k not in id_set:
                    errors.append("%s: key %r has no matching stages[].id" % (label, k))
            for sid in stage_ids:
                if sid not in block:
                    errors.append("%s: missing entry for stage %r" % (label, sid))

    # 4. json_only entries must be stage ids.
    for j in data.get("json_only", []):
        if j not in id_set:
            errors.append("json_only: %r is not a stages[].id" % j)

    # 5. Offline rule: no live URLs / external references in any string value.
    for path, s in _walk_strings(data):
        low = s.lower()
        for token in OFFLINE_FORBIDDEN:
            if token in low:
                errors.append("offline: %s contains forbidden %r" % (path, token))

    return errors


def render_module(data):
    def js(value):
        return json.dumps(value, ensure_ascii=False, indent=2)

    parts = [HEADER]
    parts.append("const TIER = %s;\n\n" % js(data["tier"]))
    parts.append("const stages = %s;\n\n" % js(data["stages"]))
    parts.append("const EVENTS = %s;\n\n" % js(data["events"]))
    parts.append("const TEMPLATES = %s;\n\n" % js(data["templates"]))
    parts.append("const JSON_ONLY = new Set(%s);\n\n" % js(data["json_only"]))
    parts.append("const tests = %s;\n\n" % js(data["tests"]))
    parts.append("const skillmap = %s;\n" % js(data["skillmap"]))
    parts.append(MERGE_JS)
    return "".join(parts)


def verify(data, html_path, schema_path, data_uuid):
    """Read-only drift check: contract valid AND bundle matches the contract.

    Returns a list of blocking findings (empty == in sync). Catches both a
    hand-edited bundle and a JSON edit that was never rebuilt, by comparing the
    bundle's current DATA module to what build would emit from the contract.
    """
    errors = validate(data, schema_path)
    try:
        html = bundle_io.read_text(html_path)
        current = bundle_io.decode_entry(html, data_uuid).decode("utf-8")
    except Exception as exc:  # malformed/unreadable bundle -> report, don't crash
        return errors + ["verify: cannot decode bundle DATA module: %s" % exc]
    if current != render_module(data):
        errors.append(
            "verify: DRIFT - bundle DATA module differs from the contract's build "
            "output (run build.py to regenerate, or extract.py to refresh the contract)."
        )
    return errors


def _reject_duplicate_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate object key: %r" % key)
        obj[key] = value
    return obj


def _reject_nonstandard_constant(name):
    raise ValueError("non-standard JSON constant: %s" % name)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--html", default=DEFAULT_HTML)
    ap.add_argument("--schema", default=BUNDLED_SCHEMA)
    ap.add_argument("--data-uuid", default=DATA_UUID)
    ap.add_argument("--check", action="store_true", help="validate the JSON only; do not write HTML")
    ap.add_argument(
        "--verify",
        action="store_true",
        help="read-only: validate AND assert the bundle matches the contract (CI/drift); no write",
    )
    args = ap.parse_args()

    if os.path.realpath(args.data) == os.path.realpath(args.html):
        raise SystemExit("error: --data resolves to the bundle itself: %s" % args.data)
    try:
        data = json.load(open(args.data, encoding="utf-8"),
                         object_pairs_hook=_reject_duplicate_keys,
                         parse_constant=_reject_nonstandard_constant)
    except ValueError as exc:
        raise SystemExit("error: %s is not strict JSON: %s" % (args.data, exc))

    if args.verify:
        findings = verify(data, args.html, args.schema, args.data_uuid)
        if findings:
            sys.stderr.write("VERIFY FAILED (%d):\n" % len(findings))
            for f in findings:
                sys.stderr.write("  - %s\n" % f)
            raise SystemExit(1)
        sys.stderr.write("VERIFY: in sync (contract valid and bundle matches).\n")
        return

    errors = validate(data, args.schema)
    if errors:
        sys.stderr.write("VALIDATION FAILED (%d):\n" % len(errors))
        for e in errors:
            sys.stderr.write("  - %s\n" % e)
        raise SystemExit(1)
    sys.stderr.write("Validation passed.\n")
    if args.check:
        return

    module_src = render_module(data)
    new_b64 = bundle_io.encode_payload(module_src.encode("utf-8"), compress=True)
    html = bundle_io.read_text(args.html)
    new_html = bundle_io.splice_entry_data(html, args.data_uuid, new_b64)
    bundle_io.write_text(args.html, new_html)
    sys.stderr.write("Spliced DATA module into %s (module %d chars).\n" % (args.html, len(module_src)))


if __name__ == "__main__":
    main()
