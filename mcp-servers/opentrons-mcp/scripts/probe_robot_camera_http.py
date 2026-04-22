#!/usr/bin/env python3
"""
Quick HTTP probe for Flex deck camera endpoints (no Opentrons Python dep).

Requires header `Opentrons-Version` (same as MCP; default "4").

Example:
  uv run python mcp-servers/opentrons-mcp/scripts/probe_robot_camera_http.py --robot 10.31.2.149:31950
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--robot", default="10.31.2.149:31950", help="host:port or http URL")
    p.add_argument(
        "--version",
        default="4",
        help="Opentrons-Version header value (MCP default; robot may accept other values)",
    )
    args = p.parse_args()

    base = args.robot.strip().rstrip("/")
    if not base.startswith("http"):
        if ":" in base.split("/")[0]:
            base = f"http://{base}"
        else:
            base = f"http://{base}:31950"

    def get(path: str) -> tuple[int, str]:
        req = urllib.request.Request(
            f"{base}{path}",
            headers={"Accept": "application/json", "Opentrons-Version": args.version},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return resp.status, body[:2000]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return e.code, body[:2000]

    def post_json(path: str, payload: dict) -> tuple[int, str]:
        data = json.dumps({"data": payload}).encode("utf-8")
        req = urllib.request.Request(
            f"{base}{path}",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Opentrons-Version": args.version,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return resp.status, body[:500]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return e.code, body[:500]

    print(f"Base: {base}\nOpentrons-Version: {args.version}\n")

    for path in ("/camera",):
        code, body = get(path)
        print(f"GET {path} -> {code}\n{body}\n")

    for path, pl in (
        ("/camera/capturePreviewImage", {}),
        ("/camera/cameraSettings", {"zoom": 1.0}),
    ):
        code, body = post_json(path, pl)
        print(f"POST {path} -> {code}\n{body}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
