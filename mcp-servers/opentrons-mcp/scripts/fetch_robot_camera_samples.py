#!/usr/bin/env python3
"""
Download recent robot-generated camera images (dataFiles) for offline labeling / MVP checkslot.

Usage:
  uv run python mcp-servers/opentrons-mcp/scripts/fetch_robot_camera_samples.py --robot 10.31.2.149:31950 --out artifacts/camera-captures/mvp-annotation-batch --limit 12

Requires LAN access to the Flex/OT-2 HTTP API. Does not use preview endpoints (often 404 on some Flex builds).
"""

from __future__ import annotations

import argparse
import json
import ssl
import urllib.error
import urllib.request
from pathlib import Path


def normalize_base(robot: str) -> str:
    r = robot.strip()
    if r.startswith("http://") or r.startswith("https://"):
        return r.rstrip("/")
    if ":" in r.split("/")[0] and r.count(":") == 1:
        return f"http://{r}"
    return f"http://{r}:31950"


def http_json(url: str, *, timeout: float = 60.0) -> dict:
    req = urllib.request.Request(
        url,
        headers={"Opentrons-Version": "4", "Accept": "application/json"},
        method="GET",
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def http_bytes(url: str, *, timeout: float = 120.0) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"Opentrons-Version": "4"},
        method="GET",
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read()


def unwrap_data(payload: object) -> object:
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--robot", default="10.31.2.149:31950", help="Robot host:port or full http URL")
    p.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/camera-captures/mvp-annotation-batch"),
        help="Output directory for JPEGs + manifest",
    )
    p.add_argument("--limit", type=int, default=12, help="Max files to download (newest first)")
    args = p.parse_args()

    base = normalize_base(args.robot)
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    listing = http_json(f"{base}/dataFiles")
    data = unwrap_data(listing)
    if not isinstance(data, list):
        raise SystemExit(f"Unexpected /dataFiles shape: {type(data)}")

    # Newest first (API usually returns recent-first; sort by createdAt if present)
    def sort_key(item: object) -> str:
        if isinstance(item, dict):
            return str(item.get("createdAt") or "")
        return ""

    rows = sorted([x for x in data if isinstance(x, dict)], key=sort_key, reverse=True)
    rows = rows[: max(1, args.limit)]

    manifest: list[dict] = []
    for i, row in enumerate(rows):
        fid = row.get("id")
        name = row.get("name") or f"file-{fid}"
        if not fid:
            continue
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in str(name))[:120]
        dest = out / f"{i:02d}_{safe}"
        if dest.suffix.lower() not in (".jpeg", ".jpg", ".png"):
            dest = dest.with_suffix(".jpeg")

        url = f"{base}/dataFiles/{fid}/download"
        try:
            blob = http_bytes(url)
        except urllib.error.HTTPError as e:
            manifest.append(
                {
                    "id": fid,
                    "name": name,
                    "error": f"HTTP {e.code}",
                    "saved_to": None,
                },
            )
            continue

        dest.write_bytes(blob)
        manifest.append(
            {
                "id": fid,
                "name": name,
                "createdAt": row.get("createdAt"),
                "source": row.get("source"),
                "saved_to": str(dest.resolve()),
                "bytes": len(blob),
            },
        )

    man_path = out / "manifest.json"
    man_path.write_text(json.dumps({"robot": base, "files": manifest}, indent=2), encoding="utf-8")
    print(f"Wrote {len(manifest)} entries to {man_path}")


if __name__ == "__main__":
    main()
