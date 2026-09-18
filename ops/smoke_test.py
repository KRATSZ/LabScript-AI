#!/usr/bin/env python3
"""Smoke backend.labscriptai.cn: health, simulate, raise-only, short OT-2 codegen."""
import json, os, sys, urllib.error, urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

API = os.environ.get("LABSCRIPTAI_SMOKE_API", "https://backend.labscriptai.cn")
LOG_DIR = Path("/var/log/labscriptai-smoke")
TZ = ZoneInfo("Asia/Shanghai")
FAIL = 0

OT2 = """from opentrons import protocol_api
metadata = {"apiLevel": "2.19"}
def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "2")
    p300 = protocol.load_instrument("p300_single_gen2", "right", tip_racks=[tiprack])
    p300.pick_up_tip()
    p300.aspirate(50, plate["A1"])
    p300.dispense(50, plate["A2"])
    p300.drop_tip()
"""
RAISE = """from opentrons import protocol_api
metadata = {"apiLevel": "2.19"}
def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware("opentrons_96_tiprack_20ul", "1")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "2")
    p20 = protocol.load_instrument("p20_single_gen2", "left", tip_racks=[tiprack])
    raise RuntimeError("P20 cannot aspirate 300 uL")
"""
GEN = {
    "sop_markdown": "Transfer 50 uL from reservoir A1 to plate A1 on OT-2 using p300_single_gen2.",
    "hardware_config": (
        "Robot Model: OT-2\nAPI Version: 2.19\nLeft Pipette: p300_single_gen2\n"
        "Deck Layout:\n  1: opentrons_96_tiprack_300ul\n"
        "  2: corning_96_wellplate_360ul_flat\n  3: nest_12_reservoir_15ml\n"
    ),
}


def now():
    return datetime.now(TZ).strftime("%H:%M:%S")


def say(msg, log):
    line = f"[{now()}] {msg}"
    print(line)
    log.write(line + "\n")


def http(path, body=None, timeout=40):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        API + path,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="GET" if body is None else "POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)


def main():
    global FAIL
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(TZ).strftime("%Y%m%d-%H%M%S")
    log_path = LOG_DIR / f"smoke-{stamp}.log"
    with log_path.open("w") as log:
        say(f"start smoke against {API}", log)
        code, body = http("/api/health", timeout=10)
        if code != 200:
            say(f"FAIL health http={code}", log); FAIL = 1
        else:
            say(f"OK health 200 {body[:160]}", log)

        code, body = http("/api/simulate-protocol", {"protocol_code": OT2})
        ok = code == 200 and json.loads(body).get("success")
        say(("OK" if ok else "FAIL") + f" simulate http={code}", log)
        FAIL |= int(not ok)

        code, body = http("/api/simulate-protocol", {"protocol_code": RAISE})
        fake = code == 200 and json.loads(body).get("success")
        if fake:
            say("FAIL fake-success: raise-only marked success", log); FAIL = 1
        elif code != 200:
            say(f"FAIL raise-only http={code}", log); FAIL = 1
        else:
            say("OK raise-only rejected", log)

        code, body = http("/api/generate-protocol-code", GEN, timeout=180)
        status, src = None, ""
        for line in body.splitlines():
            if not line.startswith("data:"):
                continue
            try:
                d = json.loads(line[5:].strip())
            except json.JSONDecodeError:
                continue
            if d.get("event_type") == "final_result":
                status, src = d.get("status"), d.get("generated_code") or ""
        pip = any(t in src.lower() for t in ("aspirate", "dispense", "transfer(", "pick_up_tip"))
        raise_only = "raise " in src and not pip
        ok = code == 200 and status == "success" and not raise_only and len(src) > 40
        say(f"generate http={code} final={status} code_len={len(src)} raise_only={raise_only}", log)
        if ok:
            say("OK generate-protocol-code", log)
        else:
            say("FAIL generate-protocol-code", log); FAIL = 1

        say("SMOKE FAILED" if FAIL else "SMOKE PASSED", log)
    link = LOG_DIR / ("last-fail.log" if FAIL else "last-ok.log")
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(log_path)
    for p in sorted(LOG_DIR.glob("smoke-*.log"))[:-8]:
        p.unlink(missing_ok=True)
    for p in LOG_DIR.glob("*.sse"):
        p.unlink()
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
