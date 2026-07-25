"""API acceptance: create a replay run over HTTP, approve every gate, reach done."""
import time

from fastapi.testclient import TestClient

from engine.api import create_app

KEY = "11111111-1111-4111-8111-111111111111"


def _drain_gates(client, run_id, deadline=30.0):
    t0 = time.time()
    while time.time() - t0 < deadline:
        pack = client.get(f"/api/runs/{run_id}/pack").json()
        state = pack["run"]["state"]
        if state in ("done", "ship-with-caveats", "failed", "hard-fail", "aborted"):
            return pack
        for gate in pack["gates"]["pending"]:
            verdict = "proceed" if gate["stage_id"] == "s1-discovery" else (
                "pass" if gate["stage_id"] == "adversarial-pentest" else "approve")
            r = client.post(
                f"/api/runs/{run_id}/gates/{gate['stage_id']}/verdict",
                json={"verdict": verdict, "approver": "Web Human", "note": "api test"},
            )
            assert r.status_code == 200, r.text
        time.sleep(0.05)
    raise AssertionError("run did not reach a terminal state in time")


def test_create_replay_run_and_approve_via_api():
    with TestClient(create_app()) as client:
        r = client.post("/api/runs", json={
            "raw_request": "API replay of the canned corpus",
            "requester": "api-test",
            "request_type": "enhance",
            "idempotency_key": KEY,
            "mode": "replay",
        })
        assert r.status_code == 201, r.text
        run_id = r.json()["run_id"]

        # idempotent create: same key returns the same run
        r2 = client.post("/api/runs", json={
            "raw_request": "x", "requester": "y", "idempotency_key": KEY})
        assert r2.json() == {"run_id": run_id, "state": r2.json()["state"], "existing": True}

        # a nameless verdict on a named gate is structurally refused
        t0 = time.time()
        while time.time() - t0 < 20:
            pack = client.get(f"/api/runs/{run_id}/pack").json()
            if pack["gates"]["pending"]:
                break
            time.sleep(0.05)
        first_gate = pack["gates"]["pending"][0]["stage_id"]
        bad = client.post(f"/api/runs/{run_id}/gates/{first_gate}/verdict",
                          json={"verdict": "proceed", "approver": " "})
        assert bad.status_code == 422

        final = _drain_gates(client, run_id)
        assert final["run"]["state"] in ("done", "ship-with-caveats")
        assert final["run"]["request_type"] == "enhance"

        # ETag short-circuit
        pack_resp = client.get(f"/api/runs/{run_id}/pack")
        etag = pack_resp.headers["etag"]
        assert client.get(f"/api/runs/{run_id}/pack",
                          headers={"If-None-Match": etag}).status_code == 304

        # events poll is incremental
        events = client.get(f"/api/runs/{run_id}/events", params={"after": -1}).json()
        assert events and events[0]["kind"] == "run.created"
        later = client.get(f"/api/runs/{run_id}/events",
                           params={"after": events[-1]["seq"]}).json()
        assert later == []
