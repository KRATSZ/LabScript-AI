#!/usr/bin/env python3
"""Fetch pressure CSV from a Flex run over the HTTP API.

Opentrons does **not** expose ``/data/user_storage/...`` for download. Options:

1. **Run commands** — protocol emitted ``PRESSURE_CSV_B64:...`` comments
   (canonical). Fetch takes the **last** full CSV payload. Legacy
   ``PRESSURE_TRACE:`` chunked comments are still decoded when present.
2. **Data files** — ``GET /dataFiles`` + ``/dataFiles/{id}/download`` when the
   file was registered as a robot data file.

Pagination matches the validated Flex client:
  cursor += len(page["data"]); stop when cursor >= meta.totalLength.

Usage:
  python scripts/fetch_robot_pressure_csv.py --robot 10.31.2.149:31950
  python scripts/fetch_robot_pressure_csv.py --robot 10.31.2.149:31950 --run-id <UUID>
  python scripts/fetch_robot_pressure_csv.py --robot 10.31.2.149:31950 --name-hint dna_pressure
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path

OPENTRONS_VERSION = "4"
PRESSURE_CSV_B64_PREFIX = "PRESSURE_CSV_B64:"
PRESSURE_NAME_RE = re.compile(r"pressure", re.IGNORECASE)
TRACE_CHUNK_RE = re.compile(r"^PRESSURE_TRACE:([^:]+):(\d+)/(\d+):(.+)$")
TRACE_LEGACY_RE = re.compile(r"^PRESSURE_TRACE:(\d+)/(\d+):(.+)$")
TRACE_ERROR_PREFIX = "PRESSURE_TRACE_ERROR:"


def normalize_base(robot: str) -> str:
    r = robot.strip()
    if r.startswith("http://") or r.startswith("https://"):
        return r.rstrip("/")
    if ":" in r.split("/")[0] and r.count(":") == 1:
        return f"http://{r}"
    return f"http://{r}:31950"


def http_json(url: str, *, timeout: float = 120.0) -> dict:
    req = urllib.request.Request(
        url,
        headers={"Opentrons-Version": OPENTRONS_VERSION, "Accept": "application/json"},
        method="GET",
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_bytes(url: str, *, timeout: float = 120.0) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"Opentrons-Version": OPENTRONS_VERSION},
        method="GET",
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read()


def unwrap_data(payload: object) -> object:
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def latest_run_id(base: str) -> str:
    runs = unwrap_data(http_json(f"{base}/runs")) or []
    if not isinstance(runs, list) or not runs:
        raise SystemExit("No runs on robot")
    runs = sorted(
        [r for r in runs if isinstance(r, dict)],
        key=lambda r: str(r.get("createdAt") or ""),
        reverse=True,
    )
    rid = runs[0].get("id")
    if not rid:
        raise SystemExit("Newest run missing id")
    return str(rid)


def fetch_all_run_commands(base: str, run_id: str, *, page_length: int = 100) -> list:
    """Offset pagination: cursor += len(data) until cursor >= totalLength."""
    all_commands: list = []
    cursor = 0
    while True:
        page = http_json(
            f"{base}/runs/{run_id}/commands?cursor={cursor}&pageLength={page_length}",
        )
        data = page.get("data") if isinstance(page, dict) else None
        if not isinstance(data, list):
            data = unwrap_data(page)
        if not isinstance(data, list):
            data = []
        all_commands.extend(data)
        cursor += len(data)
        meta = page.get("meta") if isinstance(page, dict) else {}
        total = (meta or {}).get("totalLength", cursor)
        try:
            total_i = int(total)
        except (TypeError, ValueError):
            total_i = cursor
        if len(data) == 0 or cursor >= total_i:
            break
        if cursor > 100_000:
            break
    return all_commands


def comment_message(command: object) -> str | None:
    if not isinstance(command, dict):
        return None
    cmd_type = command.get("commandType") or command.get("command_type")
    if cmd_type != "comment":
        return None
    params = command.get("params") or (command.get("data") or {}).get("params") or {}
    if isinstance(params, dict):
        msg = params.get("message")
        return str(msg) if msg is not None else None
    return None


def fetch_csv_from_run_comments(commands: list) -> tuple[bytes | None, list[dict], list[dict]]:
    """Return (latest PRESSURE_CSV_B64 bytes, legacy traces, errors)."""
    payloads: list[str] = []
    errors: list[dict] = []
    chunk_groups: dict[str, dict] = {}

    for command in commands:
        message = comment_message(command)
        if not message:
            continue
        if message.startswith(PRESSURE_CSV_B64_PREFIX):
            payloads.append(message[len(PRESSURE_CSV_B64_PREFIX) :])
            continue
        if message.startswith(TRACE_ERROR_PREFIX):
            raw = message[len(TRACE_ERROR_PREFIX) :]
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"error": raw}
            payload["observation_only"] = True
            payload["advisory"] = True
            errors.append(payload)
            continue

        match = TRACE_CHUNK_RE.match(message)
        if match:
            well, idx, total, b64 = match.groups()
            key = well.upper()
            group = chunk_groups.setdefault(key, {"well": key, "total": int(total), "parts": {}})
            group["total"] = int(total)
            group["parts"][int(idx)] = b64
            continue

        legacy = TRACE_LEGACY_RE.match(message)
        if legacy:
            idx, total, b64 = legacy.groups()
            key = "_"
            group = chunk_groups.setdefault(key, {"well": None, "total": int(total), "parts": {}})
            group["total"] = int(total)
            group["parts"][int(idx)] = b64

    blob: bytes | None = None
    if payloads:
        try:
            blob = base64.b64decode(payloads[-1])
        except Exception:
            blob = None

    legacy_traces: list[dict] = []
    for group in chunk_groups.values():
        ordered: list[str] = []
        missing = False
        for i in range(1, int(group["total"]) + 1):
            if i not in group["parts"]:
                legacy_traces.append(
                    {
                        "well": group["well"],
                        "success": False,
                        "error": f"missing PRESSURE_TRACE chunk {i}/{group['total']}",
                        "observation_only": True,
                        "advisory": True,
                        "legacy": True,
                    }
                )
                missing = True
                break
            ordered.append(group["parts"][i])
        if missing:
            continue
        try:
            csv_text = base64.b64decode("".join(ordered).encode("ascii")).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            legacy_traces.append(
                {
                    "well": group["well"],
                    "success": False,
                    "error": f"base64 decode failed: {exc}",
                    "observation_only": True,
                    "advisory": True,
                    "legacy": True,
                }
            )
            continue
        legacy_traces.append(
            {
                "well": group["well"],
                "success": True,
                "csv_text": csv_text,
                "observation_only": True,
                "advisory": True,
                "legacy": True,
            }
        )

    return blob, legacy_traces, errors


def fetch_csv_from_data_files(base: str, name_hint: str, *, limit: int = 12) -> list[dict]:
    listing = http_json(f"{base}/dataFiles")
    rows = unwrap_data(listing) or []
    if not isinstance(rows, list):
        return []
    hint = str(name_hint or "pressure").lower()
    matches = [
        row
        for row in rows
        if isinstance(row, dict)
        and (
            hint in str(row.get("name") or row.get("filename") or "").lower()
            or PRESSURE_NAME_RE.search(str(row.get("name") or row.get("filename") or ""))
        )
    ]
    matches.sort(key=lambda r: str(r.get("createdAt") or ""), reverse=True)
    return matches[: max(1, limit)]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--robot", default="10.31.2.149:31950")
    p.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/pressure-traces/batch"),
    )
    p.add_argument("--run-id", default=None, help="Run UUID (default: newest run when fetching comments)")
    p.add_argument("--name-hint", default="pressure", help="dataFiles name filter")
    p.add_argument("--limit", type=int, default=12)
    p.add_argument(
        "--prefer",
        choices=["comments", "datafiles", "both"],
        default="both",
        help="Preferred source order (default: try dataFiles then comments)",
    )
    args = p.parse_args()

    base = normalize_base(args.robot)
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    manifest: dict = {
        "robot": base,
        "observation_only": True,
        "advisory": True,
        "resume_authority": False,
        "canonical_comment_prefix": PRESSURE_CSV_B64_PREFIX,
        "files": [],
        "run_traces": [],
        "run_errors": [],
        "note": (
            "Advisory-only. /data/user_storage is not downloadable over HTTP; "
            "prefer PRESSURE_CSV_B64 run comments."
        ),
    }

    saved_primary: Path | None = None

    if args.prefer in ("datafiles", "both"):
        try:
            matches = fetch_csv_from_data_files(base, args.name_hint, limit=args.limit)
        except urllib.error.HTTPError as e:
            matches = []
            manifest["datafiles_error"] = f"HTTP {e.code}"
        except urllib.error.URLError as e:
            raise SystemExit(f"Robot unreachable at {base}: {e}") from e

        for i, row in enumerate(matches):
            fid = row.get("id")
            name = row.get("name") or row.get("filename") or f"file-{fid}"
            if not fid:
                continue
            safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in str(name))[:120]
            dest = out / f"{i:02d}_{safe}"
            if dest.suffix.lower() not in (".csv", ".txt"):
                dest = dest.with_suffix(".csv")
            try:
                blob = http_bytes(f"{base}/dataFiles/{fid}/download")
            except urllib.error.HTTPError as e:
                manifest["files"].append(
                    {"id": fid, "name": name, "error": f"HTTP {e.code}", "saved_to": None}
                )
                continue
            dest.write_bytes(blob)
            if saved_primary is None:
                saved_primary = dest
            manifest["files"].append(
                {
                    "id": fid,
                    "name": name,
                    "createdAt": row.get("createdAt"),
                    "source": "dataFiles",
                    "saved_to": str(dest.resolve()),
                    "bytes": len(blob),
                }
            )

    run_id = args.run_id
    if args.prefer in ("comments", "both") and (run_id or saved_primary is None):
        try:
            if not run_id:
                run_id = latest_run_id(base)
            commands = fetch_all_run_commands(base, run_id)
        except urllib.error.URLError as e:
            raise SystemExit(f"Robot unreachable at {base}: {e}") from e
        except SystemExit:
            raise
        except Exception as e:
            manifest["run_id"] = run_id
            manifest["run_errors"].append({"error": str(e)})
            commands = []

        blob, legacy_traces, errors = fetch_csv_from_run_comments(commands)
        manifest["run_id"] = run_id
        manifest["run_errors"] = errors
        if blob:
            dest = out / f"run_{run_id}_pressure.csv"
            dest.write_bytes(blob)
            saved_primary = dest
            manifest["run_traces"].append(
                {
                    "source": "PRESSURE_CSV_B64",
                    "run_id": run_id,
                    "saved_to": str(dest.resolve()),
                    "bytes": len(blob),
                    "observation_only": True,
                    "advisory": True,
                }
            )
        for i, trace in enumerate(legacy_traces):
            entry = {
                "well": trace.get("well"),
                "success": trace.get("success"),
                "source": "PRESSURE_TRACE_legacy",
                "observation_only": True,
                "advisory": True,
                "legacy": True,
            }
            if trace.get("csv_text"):
                dest = out / f"run_{run_id}_legacy_{i:02d}.csv"
                dest.write_text(trace["csv_text"].rstrip() + "\n", encoding="utf-8")
                entry["saved_to"] = str(dest.resolve())
                entry["bytes"] = dest.stat().st_size
                if saved_primary is None:
                    saved_primary = dest
            else:
                entry["error"] = trace.get("error")
                entry["saved_to"] = None
            manifest["run_traces"].append(entry)

    man_path = out / "manifest.json"
    man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": saved_primary is not None,
                "saved_to": str(saved_primary.resolve()) if saved_primary else None,
                "manifest": str(man_path.resolve()),
                "run_id": manifest.get("run_id"),
                "file_count": len(manifest["files"]),
                "run_trace_count": len(manifest["run_traces"]),
                "observation_only": True,
            },
            indent=2,
        )
    )
    return 0 if saved_primary is not None or manifest["files"] or manifest["run_traces"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
