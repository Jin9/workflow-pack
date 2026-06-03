#!/usr/bin/env python3
"""Bootstrap / drift-check: lift the dashboard DATA module into dashboard-data.json.

Decodes the compressed DATA module from the bundle, evaluates it with node
(scripts/emit_data.js) to capture its 7 data structures, and writes them as a
single authoritative JSON contract. Run once to create the contract, or later to
diff the live bundle against the contract.

Deterministic: same bundle in -> same JSON out. No timestamps, no randomness.

Usage:
  extract.py [--html PATH] [--out PATH] [--data-uuid UUID]
Defaults assume the working directory holds squad-delivery-dashboard.standalone.html.
"""
import argparse
import os
import subprocess
import sys
import tempfile

import bundle_io

DEFAULT_HTML = "squad-delivery-dashboard.standalone.html"
DEFAULT_OUT = "dashboard-data.json"
DATA_UUID = "c7f43bda-1a41-4a72-a2aa-5fac3269ac6d"
EMIT_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emit_data.js")


def extract(html_path, data_uuid):
    html = bundle_io.read_text(html_path)
    module_src = bundle_io.decode_entry(html, data_uuid).decode("utf-8")
    with tempfile.NamedTemporaryFile(
        "w", suffix=".js", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(module_src)
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            ["node", EMIT_JS, tmp_path],
            capture_output=True,
            text=True,
        )
    finally:
        os.unlink(tmp_path)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit("node evaluation of the DATA module failed.")
    return result.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--html", default=DEFAULT_HTML)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--data-uuid", default=DATA_UUID)
    args = ap.parse_args()

    json_text = extract(args.html, args.data_uuid)
    if not json_text.endswith("\n"):
        json_text += "\n"
    bundle_io.write_text(args.out, json_text)
    sys.stderr.write("Wrote %s (%d bytes) from %s\n" % (args.out, len(json_text), args.html))


if __name__ == "__main__":
    main()
