"""Direct HTTP tests against the fake Flex backend (no MCP / no real robot)."""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from http.client import HTTPResponse

import pytest

from labscriptai.fake_robot.server import create_app


def _free_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture()
def fake_robot():
    port = _free_port()
    httpd = create_app(host="127.0.0.1", port=port, scenario="healthy", tick_s=0.02)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    # wait ready
    for _ in range(50):
        try:
            _get(base, "/health")
            break
        except Exception:
            time.sleep(0.02)
    yield base, httpd
    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=2)


def _req(base: str, method: str, path: str, body: dict | None = None, *, version: str | None = "4"):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {}
    if version is not None:
        headers["Opentrons-Version"] = version
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=5) as resp:  # type: ignore[assignment]
            raw = resp.read()
            return resp.status, json.loads(raw.decode("utf-8") or "null")
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            payload = json.loads(raw.decode("utf-8") or "null")
        except json.JSONDecodeError:
            payload = raw.decode("utf-8", errors="replace")
        return exc.code, payload


def _get(base: str, path: str, **kwargs):
    return _req(base, "GET", path, **kwargs)


def _post(base: str, path: str, body: dict | None = None, **kwargs):
    return _req(base, "POST", path, body, **kwargs)


def test_health_requires_version_header(fake_robot):
    base, _ = fake_robot
    status, body = _get(base, "/health", version=None)
    assert status == 422
    assert "opentrons-version" in json.dumps(body).lower()


def test_health_and_instruments_shapes(fake_robot):
    base, _ = fake_robot
    status, health = _get(base, "/health")
    assert status == 200
    assert health["robot_model"] == "OT-3 Standard"
    assert health["fake_robot"] is True

    status, instruments = _get(base, "/instruments")
    assert status == 200
    left = next(i for i in instruments["data"] if i["mount"] == "left")
    assert left["state"]["tipDetected"] is False
    assert left["instrumentName"] == "p1000_single_flex"


def test_tip_missing_budget_block_awaiting_recovery(fake_robot):
    base, httpd = fake_robot
    _post(base, "/_fake/scenario", {"scenario_id": "tip_missing_budget_block"})

    # upload protocol (multipart via engine path — use JSON-less multipart manually)
    boundary = "----fake"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="02.py"\r\n'
        f"Content-Type: text/x-python\r\n\r\n"
        f"print('hi')\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    req = urllib.request.Request(
        base + "/protocols",
        data=body,
        headers={
            "Opentrons-Version": "4",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        protocol = json.loads(resp.read().decode("utf-8"))["data"]
    pid = protocol["id"]

    status, created = _post(base, "/runs", {"data": {"protocolId": pid}})
    assert status == 201
    run_id = created["data"]["id"]

    status, _ = _post(base, f"/runs/{run_id}/actions", {"data": {"actionType": "play"}})
    assert status == 201

    deadline = time.time() + 5
    run = None
    while time.time() < deadline:
        _, payload = _get(base, f"/runs/{run_id}")
        run = payload["data"]
        if run["status"] in {"awaiting-recovery", "failed", "succeeded", "stopped"}:
            break
        time.sleep(0.05)

    assert run is not None
    assert run["status"] == "awaiting-recovery"
    assert run["hasEverEnteredErrorRecovery"] is True

    _, cmds = _get(base, f"/runs/{run_id}/commands?pageLength=50")
    failed = [c for c in cmds["data"] if c["status"] == "failed"]
    assert failed
    err = failed[-1]["error"]
    assert err["errorType"] == "tipPhysicallyMissing"
    assert err["errorCode"] == "3003"
    assert err["detail"] == "No Tip Detected"
    assert any(w.get("errorType") == "PickUpTipTipNotAttachedError" for w in err.get("wrappedErrors") or [])


def test_liquid_not_found_with_attached_tip(fake_robot):
    base, _ = fake_robot
    _post(base, "/_fake/scenario", {"scenario_id": "liquid_not_found_with_reserve"})

    boundary = "----fake"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="03.py"\r\n\r\n'
        f"x=1\r\n--{boundary}--\r\n"
    ).encode()
    req = urllib.request.Request(
        base + "/protocols",
        data=body,
        headers={
            "Opentrons-Version": "4",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        pid = json.loads(resp.read().decode())["data"]["id"]

    _, created = _post(base, "/runs", {"data": {"protocolId": pid}})
    run_id = created["data"]["id"]
    _post(base, f"/runs/{run_id}/actions", {"data": {"actionType": "play"}})

    deadline = time.time() + 5
    while time.time() < deadline:
        _, payload = _get(base, f"/runs/{run_id}")
        if payload["data"]["status"] == "awaiting-recovery":
            break
        time.sleep(0.05)

    _, run_payload = _get(base, f"/runs/{run_id}")
    assert run_payload["data"]["status"] == "awaiting-recovery"

    _, instruments = _get(base, "/instruments")
    left = next(i for i in instruments["data"] if i["mount"] == "left")
    assert left["state"]["tipDetected"] is True

    _, cmds = _get(base, f"/runs/{run_id}/commands?pageLength=50")
    failed = next(c for c in cmds["data"] if c["status"] == "failed")
    assert failed["commandType"] == "liquidProbe"
    assert failed["error"]["errorType"] == "liquidNotFound"
    assert failed["error"]["wrappedErrors"][0]["errorType"] == "PipetteLiquidNotFoundError"

    # fixit probe on reserve should succeed
    labware = run_payload["data"]["labware"]
    reservoir = next(l for l in labware if l["location"]["slotName"] == "C2")
    pipette = run_payload["data"]["pipettes"][0]
    status, cmd = _post(
        base,
        f"/runs/{run_id}/commands",
        {
            "data": {
                "commandType": "liquidProbe",
                "intent": "fixit",
                "params": {
                    "pipetteId": pipette["id"],
                    "labwareId": reservoir["id"],
                    "wellName": "A2",
                },
            }
        },
    )
    assert status == 201
    assert cmd["data"]["status"] == "succeeded"


def test_tip_not_attached_fail_run(fake_robot):
    base, _ = fake_robot
    _post(base, "/_fake/scenario", {"scenario_id": "tip_not_attached_fail_run"})
    boundary = "----fake"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="x.py"\r\n\r\n'
        f"x\r\n--{boundary}--\r\n"
    ).encode()
    req = urllib.request.Request(
        base + "/protocols",
        data=body,
        headers={
            "Opentrons-Version": "4",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        pid = json.loads(resp.read().decode())["data"]["id"]
    _, created = _post(base, "/runs", {"data": {"protocolId": pid}})
    run_id = created["data"]["id"]
    _post(base, f"/runs/{run_id}/actions", {"data": {"actionType": "play"}})

    deadline = time.time() + 5
    while time.time() < deadline:
        _, payload = _get(base, f"/runs/{run_id}")
        if payload["data"]["status"] == "failed":
            break
        time.sleep(0.05)
    _, payload = _get(base, f"/runs/{run_id}")
    assert payload["data"]["status"] == "failed"
    assert payload["data"]["errors"]


def test_door_open_blocks_play(fake_robot):
    base, _ = fake_robot
    _post(base, "/_fake/scenario", {"scenario_id": "door_open"})
    _, door = _get(base, "/robot/door/status")
    assert door["data"]["status"] == "open"

    boundary = "----fake"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="x.py"\r\n\r\n'
        f"x\r\n--{boundary}--\r\n"
    ).encode()
    req = urllib.request.Request(
        base + "/protocols",
        data=body,
        headers={
            "Opentrons-Version": "4",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        pid = json.loads(resp.read().decode())["data"]["id"]
    _, created = _post(base, "/runs", {"data": {"protocolId": pid}})
    run_id = created["data"]["id"]
    _post(base, f"/runs/{run_id}/actions", {"data": {"actionType": "play"}})
    _, payload = _get(base, f"/runs/{run_id}")
    assert payload["data"]["status"] == "blocked-by-open-door"
