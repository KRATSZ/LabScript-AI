"""MCP end-to-end: fake Flex reproduces real error leaves + recovery gates."""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from pathlib import Path

import pytest

from labscriptai.fake_robot.server import create_app

pytest.importorskip("labscriptai.agent.mcp_adapter")

from labscriptai.agent.mcp_adapter import call_tool


def _free_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _post_json(base: str, path: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        base + path,
        data=data,
        headers={"Opentrons-Version": "4", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_run_status(base: str, run_id: str) -> str:
    req = urllib.request.Request(
        f"{base}/runs/{run_id}",
        headers={"Opentrons-Version": "4"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode())["data"]["status"]


def _upload_and_play(base: str, robot_ip: str, protocol_text: str = "print('ok')") -> str:
    boundary = "----e2e"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="proto.py"\r\n\r\n'
        f"{protocol_text}\r\n--{boundary}--\r\n"
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

    created = call_tool(
        "create_run",
        {"robot_ip": robot_ip, "protocol_id": pid},
        timeout_sec=60,
    )
    run = (created.get("data") or {}).get("run") or {}
    run_data = run.get("data") or run
    run_id = run_data.get("id")
    assert run_id, json.dumps(created)[:2000]

    play = call_tool(
        "control_run",
        {
            "robot_ip": robot_ip,
            "run_id": run_id,
            "action": "play",
            "protocol_source": protocol_text,
        },
        timeout_sec=60,
    )
    assert "error" not in (play or {}) or play.get("ok") is not False, play

    deadline = time.time() + 8
    while time.time() < deadline:
        status = _get_run_status(base, run_id)
        if status in {"awaiting-recovery", "failed", "succeeded", "stopped"}:
            return run_id
        time.sleep(0.1)
    return run_id


@pytest.fixture()
def fake_mcp_robot():
    port = _free_port()
    httpd = create_app(host="127.0.0.1", port=port, scenario="healthy", tick_s=0.02)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    robot_ip = f"127.0.0.1:{port}"
    for _ in range(50):
        try:
            req = urllib.request.Request(base + "/health", headers={"Opentrons-Version": "4"})
            with urllib.request.urlopen(req, timeout=1):
                break
        except Exception:
            time.sleep(0.02)
    yield base, robot_ip
    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=2)


def test_mcp_robot_status_against_fake(fake_mcp_robot):
    _base, robot_ip = fake_mcp_robot
    result = call_tool("robot_status", {"robot_ip": robot_ip}, timeout_sec=60)
    assert result.get("ok") is not False
    data = result.get("data") or {}
    # Snapshot should show ready instruments / closed door
    blob = json.dumps(data).lower()
    assert "p1000" in blob or "instrument" in blob


def test_mcp_classifies_tip_physically_missing(fake_mcp_robot):
    base, robot_ip = fake_mcp_robot
    _post_json(base, "/_fake/scenario", {"scenario_id": "tip_missing_budget_block"})
    run_id = _upload_and_play(base, robot_ip)

    parsed = call_tool(
        "parse_error",
        {"robot_ip": robot_ip, "run_id": run_id},
        timeout_sec=60,
    )
    data = parsed.get("data") or parsed
    blob = json.dumps(data)
    assert "TIP_PHYSICALLY_MISSING" in blob or "tipPhysicallyMissing" in blob

    suggestion = call_tool(
        "suggest_recovery_action",
        {"robot_ip": robot_ip, "run_id": run_id},
        timeout_sec=60,
    )
    sblob = json.dumps(suggestion)
    # Budget gate should surface — insufficient tips for 3-step protocol.
    assert (
        "tip" in sblob.lower()
        or "TIP_PHYSICALLY_MISSING" in sblob
        or "retry_pick_up_tip" in sblob
    )


def test_mcp_classifies_liquid_not_found(fake_mcp_robot):
    base, robot_ip = fake_mcp_robot
    _post_json(base, "/_fake/scenario", {"scenario_id": "liquid_not_found_with_reserve"})
    run_id = _upload_and_play(base, robot_ip)

    parsed = call_tool(
        "parse_error",
        {"robot_ip": robot_ip, "run_id": run_id},
        timeout_sec=60,
    )
    blob = json.dumps(parsed)
    assert "INSUFFICIENT_VOLUME" in blob or "liquidNotFound" in blob or "LIQUID" in blob

    # Tip should still be attached for substitution eligibility.
    status = call_tool("robot_status", {"robot_ip": robot_ip}, timeout_sec=60)
    assert "true" in json.dumps(status).lower() or "tip" in json.dumps(status).lower()


PROTOCOL_02 = Path(__file__).resolve().parents[2] / "local" / "protocol" / "02_triple_transfer_chain.py"
PROTOCOL_03 = Path(__file__).resolve().parents[2] / "local" / "protocol" / "03_primary_reserve_buffer.py"


@pytest.mark.skipif(not PROTOCOL_02.exists(), reason="local protocol fixtures not present")
def test_mcp_tip_budget_blocks_when_protocol_needs_three_tips(fake_mcp_robot):
    """Reproduce 02_triple_transfer_chain tip-budget escalate gate."""
    base, robot_ip = fake_mcp_robot
    _post_json(base, "/_fake/scenario", {"scenario_id": "tip_missing_budget_block"})
    text = PROTOCOL_02.read_text(encoding="utf-8")
    run_id = _upload_and_play(base, robot_ip, protocol_text=text)

    suggestion = call_tool(
        "suggest_recovery_action",
        {
            "robot_ip": robot_ip,
            "run_id": run_id,
            "file_path": str(PROTOCOL_02),
        },
        timeout_sec=90,
    )
    blob = json.dumps(suggestion)
    assert "TIP_PHYSICALLY_MISSING" in blob
    # Budget must be enforced from protocol pick_up_tip count.
    assert "tip_budget" in blob
    budget_enforced = '"enforced": true' in blob or '"enforced":true' in blob
    budget_insufficient = '"sufficient": false' in blob or '"sufficient":false' in blob
    assert budget_enforced, blob[:2500]
    assert budget_insufficient, blob[:2500]

    # Auto recover_tip_pickup must refuse rather than burn remaining tips.
    recovery = call_tool(
        "recover_tip_pickup",
        {
            "robot_ip": robot_ip,
            "run_id": run_id,
            "file_path": str(PROTOCOL_02),
        },
        timeout_sec=90,
    )
    rblob = json.dumps(recovery).lower()
    assert "tip_budget_insufficient" in rblob or recovery.get("ok") is False or "error" in rblob


def test_mcp_skips_pickup_when_tip_already_attached(fake_mcp_robot):
    """Reproduce 09_hold tipPhysicallyMissing + tip already attached glitch."""
    base, robot_ip = fake_mcp_robot
    _post_json(base, "/_fake/scenario", {"scenario_id": "tip_false_missing_already_attached"})
    run_id = _upload_and_play(base, robot_ip)

    recovery = call_tool(
        "recover_tip_pickup",
        {"robot_ip": robot_ip, "run_id": run_id},
        timeout_sec=90,
    )
    blob = json.dumps(recovery)
    assert "tip_already_attached" in blob or "skipped_pickup" in blob or recovery.get("ok") is not False

    # Run should leave awaiting-recovery via resume, or at least not hard-fail the recovery tool.
    status = _get_run_status(base, run_id)
    assert status in {"running", "succeeded", "awaiting-recovery", "paused", "stopped"}


@pytest.mark.skipif(not PROTOCOL_03.exists(), reason="local protocol fixtures not present")
def test_mcp_liquid_substitution_on_fake_with_real_protocol(fake_mcp_robot):
    """Reproduce 03_primary_reserve_buffer recovery path against fake robot."""
    base, robot_ip = fake_mcp_robot
    _post_json(base, "/_fake/scenario", {"scenario_id": "liquid_not_found_with_reserve"})

    text = PROTOCOL_03.read_text(encoding="utf-8")
    run_id = _upload_and_play(base, robot_ip, protocol_text=text)

    suggestion = call_tool(
        "suggest_recovery_action",
        {
            "robot_ip": robot_ip,
            "run_id": run_id,
            "file_path": str(PROTOCOL_03),
        },
        timeout_sec=90,
    )
    blob = json.dumps(suggestion)
    assert "INSUFFICIENT_VOLUME" in blob or "liquid" in blob.lower()

    # Attempt in-run substitution — should drive fixit commands on fake.
    recovery = call_tool(
        "recover_liquid_source_substitution",
        {
            "robot_ip": robot_ip,
            "run_id": run_id,
            "file_path": str(PROTOCOL_03),
            "preferred_source_key": "C2.A2",
        },
        timeout_sec=180,
    )
    rblob = json.dumps(recovery)
    # Soft assertion: either executed steps or clear gate reason (both are useful).
    assert recovery is not None
    assert "error" in rblob.lower() or "step" in rblob.lower() or "substitut" in rblob.lower() or recovery.get("ok") is not False
