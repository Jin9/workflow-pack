"""Shared helpers for reading and rewriting a self-extracting __bundler bundle.

The dashboard is a single HTML file whose assets live in a JSON object inside a
`<script type="__bundler/manifest">` tag. Each entry is keyed by a UUID and holds
`{"mime", "compressed", "data"}` where `data` is base64 of (optionally) gzipped
bytes. Entries carry no integrity hash, so a targeted replacement of one entry's
`data` value leaves every other entry (render module + fonts) byte-identical.

These helpers deliberately do NOT re-serialize the whole manifest — they splice a
single `data` string in place so unrelated bytes never move.
"""

import base64
import os
import gzip
import io
import re

MANIFEST_RE = re.compile(
    r'(?P<open><script type="__bundler/manifest">\s*)(?P<json>.*?)(?P<close>\s*</script>)',
    re.S,
)


def read_text(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def write_text(path, text):
    """Atomic: write a temp sibling then os.replace — a failed write never
    truncates an existing artifact; nonzero exits leave files unchanged."""
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except OSError:
        if os.path.isfile(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise


def find_manifest_json(html):
    """Return the raw manifest JSON string (the bytes between the script tags)."""
    m = MANIFEST_RE.search(html)
    if not m:
        raise ValueError('No <script type="__bundler/manifest"> block found.')
    return m.group("json")


def decode_entry(html, uuid):
    """Decode one manifest entry's payload to bytes (gunzipped if compressed)."""
    import json

    manifest = json.loads(find_manifest_json(html))
    if uuid not in manifest:
        raise KeyError("Manifest has no entry %r" % uuid)
    entry = manifest[uuid]
    raw = base64.b64decode(entry["data"])
    if entry.get("compressed"):
        raw = gzip.decompress(raw)
    return raw


def gzip_deterministic(data_bytes):
    """gzip with mtime=0 and level 9 — byte-identical for identical input."""
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0, compresslevel=9) as gz:
        gz.write(data_bytes)
    return buf.getvalue()


def encode_payload(data_bytes, compress=True):
    """Produce the base64 string that goes in an entry's `data` field."""
    raw = gzip_deterministic(data_bytes) if compress else data_bytes
    return base64.b64encode(raw).decode("ascii")


def splice_entry_data(html, uuid, new_b64):
    """Replace ONLY the `data` value of one entry, in place.

    Locates the entry by UUID, then the next `"data":"` ... `"` after it, and
    swaps the base64 (the base64 alphabet contains no `"`). Every other byte of
    the file — including all other manifest entries — is preserved exactly.
    """
    key = '"%s"' % uuid
    start = html.find(key)
    if start == -1:
        raise KeyError("UUID %r not found in HTML" % uuid)
    marker = '"data":"'
    data_start = html.find(marker, start)
    if data_start == -1:
        raise ValueError("No data field found for entry %r" % uuid)
    value_start = data_start + len(marker)
    value_end = html.find('"', value_start)
    if value_end == -1:
        raise ValueError("Unterminated data string for entry %r" % uuid)
    return html[:value_start] + new_b64 + html[value_end:]
