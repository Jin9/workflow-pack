"""Append-only, hash-chained audit log (runs/<id>/events.jsonl) + audit_id policy.

Both halves are recorded per attempt: the request half (executor kind, model,
prompt sha256 — never the prompt body) and the effect half (artifact path,
artifact sha256, validation outcome). Events never carry raw_request bodies,
artifact contents, or anything PII-shaped — digests and field NAMES only.
Each line carries prev_sha256 of the previous line; verify() walks the chain.

audit_id: deterministic uuid5(NS, "run:stage:attempt") in replay mode (so a
replay is byte-reproducible), uuid4 in live mode.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Optional

NS = uuid.UUID("6ba7b812-9dad-11d1-80b4-00c04fd430c8")  # uuid.NAMESPACE_OID
GENESIS = "genesis"


def make_audit_id(run_id: str, stage_id: str, attempt: int, deterministic: bool) -> str:
    if deterministic:
        return str(uuid.uuid5(NS, f"{run_id}:{stage_id}:{attempt}"))
    return str(uuid.uuid4())


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_hex(path.read_bytes())


class AuditLog:
    def __init__(self, path: Path, deterministic_time: bool = False):
        self.path = path
        self.deterministic_time = deterministic_time
        self._seq = 0
        self._prev = GENESIS
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self._prev = sha256_hex(line.encode("utf-8"))
                    self._seq += 1

    def emit(self, kind: str, run_id: str, stage_id: Optional[str] = None, **fields) -> dict:
        event = {
            "seq": self._seq,
            "ts": 0 if self.deterministic_time else round(time.time(), 3),
            "kind": kind,
            "run_id": run_id,
            "stage": stage_id,
            "prev_sha256": self._prev,
        }
        event.update(fields)
        line = json.dumps(event, sort_keys=True, ensure_ascii=False)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        self._prev = sha256_hex(line.encode("utf-8"))
        self._seq += 1
        return event


def verify_chain(path: Path) -> int:
    """Return the number of verified events; raise ValueError on a broken chain."""
    prev = GENESIS
    count = 0
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("prev_sha256") != prev:
            raise ValueError(f"audit chain broken at line {i}: prev_sha256 mismatch")
        if event.get("seq") != count:
            raise ValueError(f"audit chain broken at line {i}: seq {event.get('seq')} != {count}")
        prev = sha256_hex(line.encode("utf-8"))
        count += 1
    return count
