"""Stdlib-only Opentrons LAN HTTP API helper."""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib import error, request

DEFAULT_PORT = 31950
DEFAULT_TIMEOUT = 30
DEFAULT_HEADERS = {"Opentrons-Version": "3"}

TERMINAL_RUN_STATUSES = frozenset({
    "succeeded",
    "failed",
    "stopped",
    "awaiting-recovery",
    "blocked-by-open-door",
})

LOCAL_ONLY_COMMANDS = frozenset({"show-connection", "search-labware"})

_CONNECTION_CONFIG_PATH = Path(__file__).resolve().parent.parent / "data" / "robot-connection.json"


@dataclass(frozen=True)
class ConnectionConfig:
    host: str
    port: int = DEFAULT_PORT
    token: str | None = None
    timeout: int = DEFAULT_TIMEOUT

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean value: {value}")


def parse_json_arg(value: str | None, default: Any) -> Any:
    if value is None:
        return default
    return json.loads(value)


def validate_json_object_arg(value: str) -> str:
    """Argparse validator that ensures an option contains a JSON object."""
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON object: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("expected a JSON object")
    return value


def parse_resolution(value: str | None) -> list[int] | None:
    if value is None:
        return None
    width, height = value.lower().split("x", 1)
    return [int(width), int(height)]


def parse_pan(value: str | None) -> list[int] | None:
    if value is None:
        return None
    x, y = value.split(",", 1)
    return [int(x), int(y)]


def build_headers(
    token: str | None = None,
    extra_headers: Mapping[str, str] | None = None,
) -> dict[str, str]:
    headers = dict(DEFAULT_HEADERS)
    if token:
        headers["authenticationBearer"] = token
    if extra_headers:
        headers.update(extra_headers)
    return headers


def encode_multipart_formdata(
    fields: Mapping[str, str],
    files: Sequence[tuple[str, Path]],
) -> tuple[bytes, str]:
    boundary = f"----opentrons-lab-agent-{uuid.uuid4().hex}"
    body = bytearray()

    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        )
        body.extend(value.encode())
        body.extend(b"\r\n")

    for field_name, file_path in files:
        mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{file_path.name}"\r\n'
            ).encode()
        )
        body.extend(f"Content-Type: {mime_type}\r\n\r\n".encode())
        body.extend(file_path.read_bytes())
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode())
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def _decode_response_bytes(data: bytes) -> Any:
    if not data:
        return None
    try:
        return json.loads(data.decode())
    except (UnicodeDecodeError, json.JSONDecodeError):
        return data.decode(errors="replace")


def send_request(
    config: ConnectionConfig,
    method: str,
    path: str,
    *,
    json_body: Any | None = None,
    binary_body: bytes | None = None,
    extra_headers: Mapping[str, str] | None = None,
) -> tuple[int, Mapping[str, str], bytes]:
    headers = build_headers(config.token, extra_headers)
    data: bytes | None = None

    if json_body is not None:
        data = json.dumps(json_body).encode()
        headers["Content-Type"] = "application/json"
    elif binary_body is not None:
        data = binary_body

    req = request.Request(
        url=f"{config.base_url}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with request.urlopen(req, timeout=config.timeout) as response:
            return response.status, dict(response.headers), response.read()
    except error.HTTPError as exc:
        payload = exc.read()
        decoded = _decode_response_bytes(payload)
        raise SystemExit(
            json.dumps(
                {
                    "status": exc.code,
                    "reason": exc.reason,
                    "error": decoded,
                },
                indent=2,
                ensure_ascii=False,
            )
        )


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _unwrap_data(payload: Any) -> Any:
    if isinstance(payload, dict):
        return payload.get("data", payload)
    return payload


def _normalize_search_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _redact_connection_config(entry: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if entry is None:
        return None
    redacted = dict(entry)
    if redacted.get("token"):
        redacted["token"] = "***redacted***"
    return redacted


def _build_upload_fields(args: argparse.Namespace) -> dict[str, str]:
    fields: dict[str, str] = {}
    if getattr(args, "key", None):
        fields["key"] = args.key
    if getattr(args, "protocol_kind", None):
        fields["protocolKind"] = args.protocol_kind
    if getattr(args, "rtp_values", None):
        fields["runTimeParameterValues"] = args.rtp_values
    if getattr(args, "rtp_files", None):
        fields["runTimeParameterFiles"] = args.rtp_files
    return fields


def _build_create_run_body(
    args: argparse.Namespace, *, protocol_id: str | None = None
) -> dict[str, Any]:
    body: dict[str, Any] = {"data": {}}
    effective_protocol_id = protocol_id or getattr(args, "protocol_id", None)
    if effective_protocol_id:
        body["data"]["protocolId"] = effective_protocol_id
    if getattr(args, "rtp_values", None):
        body["data"]["runTimeParameterValues"] = parse_json_arg(args.rtp_values, {})
    if getattr(args, "rtp_files", None):
        body["data"]["runTimeParameterFiles"] = parse_json_arg(args.rtp_files, {})
    return body


def _labware_version_key(path: Path) -> tuple[int, str]:
    try:
        return (int(path.stem), path.name)
    except ValueError:
        return (-1, path.name)


def _extract_flex_slot_name(value: Any) -> str | None:
    text = str(value or "").strip()
    match = re.search(r"([A-Da-d][1-3])$", text)
    return match.group(1).upper() if match else None


# ---------------------------------------------------------------------------
# Connection config persistence
# ---------------------------------------------------------------------------

def load_connection_config() -> dict[str, Any] | None:
    """Load saved robot connection config from disk."""
    if not _CONNECTION_CONFIG_PATH.exists():
        return None
    try:
        return json.loads(_CONNECTION_CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_connection_config(host: str, port: int, token: str | None) -> dict[str, Any]:
    """Save robot connection config to disk."""
    _CONNECTION_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry: dict[str, Any] = {
        "host": host,
        "port": port,
        "token": token,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _CONNECTION_CONFIG_PATH.write_text(
        json.dumps(entry, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return entry


def resolve_config(args: argparse.Namespace) -> ConnectionConfig:
    """Build ConnectionConfig from *args*, falling back to saved config."""
    saved = load_connection_config() or {}
    explicit_host = getattr(args, "host", None)
    host = explicit_host or saved.get("host")
    if not host:
        raise SystemExit(
            "No --host provided and no saved connection found. "
            "Use --host or run 'save-connection' first."
        )

    raw_port = getattr(args, "port", None)
    if raw_port is None:
        raw_port = DEFAULT_PORT if explicit_host else saved.get("port", DEFAULT_PORT)
    raw_token = getattr(args, "token", None)
    if raw_token is None:
        raw_token = saved.get("token")
    raw_timeout = getattr(args, "timeout", None)
    if raw_timeout is None:
        raw_timeout = DEFAULT_TIMEOUT

    return ConnectionConfig(
        host=str(host),
        port=int(raw_port),
        token=raw_token,
        timeout=int(raw_timeout),
    )


# ---------------------------------------------------------------------------
# Polling helpers
# ---------------------------------------------------------------------------

def poll_analysis(
    config: ConnectionConfig,
    protocol_key: str,
    *,
    timeout: int = 120,
    interval: int = 2,
) -> dict[str, Any]:
    """Poll ``GET /protocols/{key}`` until analysis completes or *timeout*."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        _, _, data = send_request(config, "GET", f"/protocols/{protocol_key}")
        proto = _unwrap_data(_decode_response_bytes(data))
        if not isinstance(proto, dict):
            raise SystemExit(f"Unexpected analysis payload for {protocol_key}")
        summaries = proto.get("analysisSummaries") or proto.get("analyses") or []
        if not summaries:
            time.sleep(interval)
            continue
        statuses = {
            str(s.get("status", "")).strip().lower()
            for s in summaries
            if isinstance(s, dict) and s.get("status")
        }
        if statuses & {"failed", "error"}:
            raise SystemExit(f"Protocol analysis failed for {protocol_key}")
        if statuses and statuses <= {"completed", "succeeded"}:
            return proto
        time.sleep(interval)
    raise SystemExit(f"Analysis polling timed out after {timeout}s for {protocol_key}")


def handle_health(args: argparse.Namespace, config: ConnectionConfig) -> int:
    _, _, data = send_request(config, "GET", "/health")
    print_json(_decode_response_bytes(data))
    return 0


def handle_list_protocols(args: argparse.Namespace, config: ConnectionConfig) -> int:
    _, _, data = send_request(config, "GET", "/protocols")
    print_json(_decode_response_bytes(data))
    return 0


def handle_upload_protocol(args: argparse.Namespace, config: ConnectionConfig) -> int:
    files = [("files", Path(path).resolve()) for path in args.files]
    for _, file_path in files:
        if not file_path.exists():
            raise SystemExit(f"protocol file not found: {file_path}")

    fields = _build_upload_fields(args)
    body, content_type = encode_multipart_formdata(fields, files)
    _, _, data = send_request(
        config,
        "POST",
        "/protocols",
        binary_body=body,
        extra_headers={"Content-Type": content_type},
    )
    print_json(_decode_response_bytes(data))
    return 0


def handle_analyze_protocol(args: argparse.Namespace, config: ConnectionConfig) -> int:
    payload = {
        "data": {
            "runTimeParameterValues": parse_json_arg(args.rtp_values, {}),
            "runTimeParameterFiles": parse_json_arg(args.rtp_files, {}),
            "forceReAnalyze": args.force_reanalyze,
        }
    }
    _, _, data = send_request(
        config, "POST", f"/protocols/{args.protocol_key}/analyses", json_body=payload
    )
    print_json(_decode_response_bytes(data))
    return 0


def handle_create_run(args: argparse.Namespace, config: ConnectionConfig) -> int:
    body = _build_create_run_body(args)
    _, _, data = send_request(config, "POST", "/runs", json_body=body)
    print_json(_decode_response_bytes(data))
    return 0


def handle_list_runs(args: argparse.Namespace, config: ConnectionConfig) -> int:
    _, _, data = send_request(config, "GET", "/runs")
    print_json(_decode_response_bytes(data))
    return 0


def handle_get_run(args: argparse.Namespace, config: ConnectionConfig) -> int:
    _, _, data = send_request(config, "GET", f"/runs/{args.run_id}")
    print_json(_decode_response_bytes(data))
    return 0


def handle_run_action(args: argparse.Namespace, config: ConnectionConfig) -> int:
    body = {"data": {"actionType": args.action}}
    _, _, data = send_request(
        config, "POST", f"/runs/{args.run_id}/actions", json_body=body
    )
    print_json(_decode_response_bytes(data))
    return 0


def handle_get_camera(args: argparse.Namespace, config: ConnectionConfig) -> int:
    _, _, data = send_request(config, "GET", "/camera")
    print_json(_decode_response_bytes(data))
    return 0


def handle_set_camera(args: argparse.Namespace, config: ConnectionConfig) -> int:
    body = {
        "data": {
            "cameraEnabled": args.camera_enabled,
            "liveStreamEnabled": args.live_stream_enabled,
            "errorRecoveryCameraEnabled": args.error_recovery_camera_enabled,
        }
    }
    _, _, data = send_request(config, "POST", "/camera", json_body=body)
    print_json(_decode_response_bytes(data))
    return 0


def handle_set_camera_image(args: argparse.Namespace, config: ConnectionConfig) -> int:
    image_settings: dict[str, Any] = {}
    if args.camera_id:
        image_settings["cameraId"] = args.camera_id
    if args.resolution:
        image_settings["resolution"] = parse_resolution(args.resolution)
    if args.zoom is not None:
        image_settings["zoom"] = args.zoom
    if args.contrast is not None:
        image_settings["contrast"] = args.contrast
    if args.brightness is not None:
        image_settings["brightness"] = args.brightness
    if args.saturation is not None:
        image_settings["saturation"] = args.saturation
    if args.pan:
        image_settings["pan"] = parse_pan(args.pan)

    _, _, data = send_request(
        config, "POST", "/camera/cameraSettings", json_body={"data": image_settings}
    )
    print_json(_decode_response_bytes(data))
    return 0


def handle_capture_preview(args: argparse.Namespace, config: ConnectionConfig) -> int:
    image_settings: dict[str, Any] = {}
    if args.camera_id:
        image_settings["cameraId"] = args.camera_id
    if args.resolution:
        image_settings["resolution"] = parse_resolution(args.resolution)
    if args.zoom is not None:
        image_settings["zoom"] = args.zoom
    if args.contrast is not None:
        image_settings["contrast"] = args.contrast
    if args.brightness is not None:
        image_settings["brightness"] = args.brightness
    if args.saturation is not None:
        image_settings["saturation"] = args.saturation
    if args.pan:
        image_settings["pan"] = parse_pan(args.pan)

    _, headers, data = send_request(
        config, "POST", "/camera/capturePreviewImage", json_body={"data": image_settings}
    )
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)
    print_json(
        {
            "saved_to": str(output_path),
            "content_type": headers.get("Content-Type"),
            "bytes": len(data),
        }
    )
    return 0


def handle_save_connection(args: argparse.Namespace, config: ConnectionConfig) -> int:
    saved = save_connection_config(args.host, config.port, config.token)
    print_json(_redact_connection_config(saved))
    return 0


def handle_show_connection(args: argparse.Namespace, config: ConnectionConfig) -> int:
    saved = load_connection_config()
    if saved is None:
        raise SystemExit("No saved connection config found.")
    print_json(_redact_connection_config(saved))
    return 0


# ---------------------------------------------------------------------------
# deploy-and-run
# ---------------------------------------------------------------------------

def handle_deploy_and_run(args: argparse.Namespace, config: ConnectionConfig) -> int:
    """Upload → poll analysis → create run → play."""
    # 1. Upload
    files = [("files", Path(p).resolve()) for p in args.files]
    for _, fp in files:
        if not fp.exists():
            raise SystemExit(f"protocol file not found: {fp}")

    fields = _build_upload_fields(args)
    body, ct = encode_multipart_formdata(fields, files)
    _, _, raw = send_request(
        config, "POST", "/protocols",
        binary_body=body,
        extra_headers={"Content-Type": ct},
    )
    proto_data = _unwrap_data(_decode_response_bytes(raw))
    if not isinstance(proto_data, dict):
        raise SystemExit("Upload response did not include protocol data.")
    proto_id = proto_data["id"]
    proto_key = proto_data.get("key", proto_id)
    print_json({"step": "uploaded", "protocol_id": proto_id, "key": proto_key})

    # 2. Poll analysis
    poll_analysis(
        config, proto_key,
        timeout=args.analysis_timeout,
        interval=args.analysis_interval,
    )
    print_json({"step": "analysis_complete", "protocol_id": proto_id})

    # 3. Create run
    _, _, raw = send_request(
        config, "POST", "/runs",
        json_body=_build_create_run_body(args, protocol_id=proto_id),
    )
    run_data = _unwrap_data(_decode_response_bytes(raw))
    if not isinstance(run_data, dict):
        raise SystemExit("Run creation response did not include run data.")
    run_id = run_data["id"]
    print_json({"step": "run_created", "run_id": run_id})

    # 4. Play
    _, _, raw = send_request(
        config, "POST", f"/runs/{run_id}/actions",
        json_body={"data": {"actionType": "play"}},
    )
    print_json({"step": "started", "run_id": run_id, "protocol_id": proto_id, "status": "running"})
    return 0


# ---------------------------------------------------------------------------
# search-labware
# ---------------------------------------------------------------------------

def _labware_definitions_dir() -> Path | None:
    """Find the opentrons shared-data labware definitions directory."""
    # Walk up from script to find .venv
    candidate = Path(__file__).resolve()
    for _ in range(10):
        candidate = candidate.parent
        venv = candidate / ".venv"
        if venv.is_dir():
            # Find site-packages/opentrons_shared_data/...
            for sp in venv.glob("lib/python*/site-packages"):
                d = sp / "opentrons_shared_data" / "data" / "labware" / "definitions" / "2"
                if d.is_dir():
                    return d
    return None


def handle_search_labware(args: argparse.Namespace, config: ConnectionConfig) -> int:
    labware_dir = _labware_definitions_dir()
    if labware_dir is None:
        raise SystemExit(
            "Could not locate labware definitions directory. "
            "Ensure .venv with opentrons_shared_data is present."
        )

    query = _normalize_search_text(args.query)
    results: list[dict[str, Any]] = []

    for entry in sorted(labware_dir.iterdir()):
        if not entry.is_dir():
            continue
        jsons = list(entry.glob("*.json"))
        if not jsons:
            continue
        try:
            defn = json.loads(max(jsons, key=_labware_version_key).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        params = defn.get("parameters", {})
        meta = defn.get("metadata", {})
        load_name = str(params.get("loadName", entry.name))
        display_name = str(meta.get("displayName", ""))
        display_cat = str(meta.get("displayCategory", ""))
        is_tiprack = params.get("isTiprack", False)

        load_name_norm = _normalize_search_text(load_name)
        display_name_norm = _normalize_search_text(display_name)
        display_cat_norm = _normalize_search_text(display_cat)

        score = 0
        if query == load_name_norm:
            score = 3
        elif query in load_name_norm:
            score = 2
        elif query in display_name_norm or query in display_cat_norm:
            score = 1
        if score == 0:
            continue

        wells = defn.get("wells", {})
        well_count = len(wells) if isinstance(wells, dict) else 0
        max_vol = max(
            (
                int(w.get("totalLiquidVolume", 0))
                for w in (wells.values() if isinstance(wells, dict) else [])
                if isinstance(w, dict)
            ),
            default=0,
        )

        results.append({
            "loadName": load_name,
            "displayName": display_name,
            "displayCategory": display_cat,
            "isTiprack": is_tiprack,
            "wellCount": well_count,
            "maxVolumeUl": max_vol,
            "_score": score,
        })

    results.sort(key=lambda r: (-r["_score"], r["loadName"]))
    results = results[: args.limit]
    for r in results:
        r.pop("_score", None)

    print_json({"query": args.query, "count": len(results), "results": results})
    return 0


# ---------------------------------------------------------------------------
# watch-run
# ---------------------------------------------------------------------------

def handle_watch_run(args: argparse.Namespace, config: ConnectionConfig) -> int:
    """Poll run status; only output on change. Exit on terminal status."""
    run_id = args.run_id
    interval = args.interval
    timeout = args.timeout
    start_time = time.monotonic()
    deadline = start_time + timeout
    last_status: str | None = None
    changes: list[dict[str, str]] = []

    while time.monotonic() < deadline:
        _, _, raw = send_request(config, "GET", f"/runs/{run_id}")
        run_data = _unwrap_data(_decode_response_bytes(raw))
        status = "unknown"
        if isinstance(run_data, dict):
            status = str(run_data.get("status", "unknown")).strip().lower() or "unknown"

        if status != last_status:
            ts = datetime.now(timezone.utc).isoformat()
            print_json({"timestamp": ts, "run_id": run_id, "status": status, "changed": True})
            changes.append({"timestamp": ts, "status": status})
            last_status = status

        if status in TERMINAL_RUN_STATUSES:
            break

        time.sleep(interval)
    else:
        print_json(
            {
                "run_id": run_id,
                "final_status": last_status,
                "elapsed_seconds": int(time.monotonic() - start_time),
                "status_changes": changes,
                "error": "timeout",
            }
        )
        return 2

    print_json({
        "run_id": run_id,
        "final_status": last_status,
        "elapsed_seconds": int(time.monotonic() - start_time),
        "status_changes": changes,
    })
    return 0 if last_status == "succeeded" else 1


# ---------------------------------------------------------------------------
# deck-check
# ---------------------------------------------------------------------------

_FLEX_SLOT_RE = re.compile(r"^[A-D][1-3]$", re.IGNORECASE)
_LOAD_LABWARE_RE = re.compile(
    r'load_labware\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']?([A-Da-d][1-3])["\']?'
)
_LOAD_TRASH_RE = re.compile(
    r'load_trash_bin\s*\(\s*["\']?([A-Da-d][1-3])["\']?'
)
_LOAD_MODULE_RE = re.compile(
    r'load_module\s*\(\s*[^,]+\s*,\s*["\']?([A-Da-d][1-3])["\']?'
)


def extract_declared_loads(source: str) -> list[dict[str, str | None]]:
    """Parse protocol source to extract labware/module/trash declarations."""
    loads: list[dict[str, str | None]] = []
    seen: set[str] = set()

    def push(kind: str, load_name: str | None, slot_raw: str) -> None:
        slot = slot_raw.upper()
        if not _FLEX_SLOT_RE.match(slot):
            return
        key = f"{kind}:{slot}:{load_name or ''}"
        if key in seen:
            return
        seen.add(key)
        loads.append({"kind": kind, "load_name": load_name, "slot": slot})

    for m in _LOAD_LABWARE_RE.finditer(source):
        push("labware", m.group(1), m.group(2))
    for m in _LOAD_TRASH_RE.finditer(source):
        push("trash_bin", None, m.group(1))
    for m in _LOAD_MODULE_RE.finditer(source):
        push("module", None, m.group(1))

    return loads


def _normalize_load_name(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def load_names_compatible(declared: str | None, observed: str | None) -> bool:
    """Return True when two labware load names look equivalent enough to match."""
    if not declared or not observed:
        return False
    declared_normalized = _normalize_load_name(declared)
    observed_normalized = _normalize_load_name(observed)
    if declared_normalized == observed_normalized:
        return True
    return (
        declared_normalized in observed_normalized
        or observed_normalized in declared_normalized
    )


def _extract_observed_load_name(record: Mapping[str, Any]) -> str | None:
    """Read a future labware load name from a deck/config record if present."""
    candidate_keys = ("loadName", "load_name", "labwareLoadName", "labware_load_name")
    for key in candidate_keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for nested_key in ("labware", "labwareDefinition", "labware_definition"):
        nested = record.get(nested_key)
        if not isinstance(nested, dict):
            continue
        for key in candidate_keys:
            value = nested.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def handle_deck_check(args: argparse.Namespace, config: ConnectionConfig) -> int:
    """Compare protocol declarations vs live robot deck configuration."""
    protocol_path = Path(args.protocol_file).resolve()
    if not protocol_path.exists():
        raise SystemExit(f"protocol file not found: {protocol_path}")

    source = protocol_path.read_text(encoding="utf-8")
    declared = extract_declared_loads(source)

    # Fetch live deck configuration
    _, _, raw = send_request(config, "GET", "/deck_configuration")
    deck_cfg = _unwrap_data(_decode_response_bytes(raw))
    if not isinstance(deck_cfg, dict):
        deck_cfg = {}

    # Build slot map from live deck
    observed: dict[str, dict[str, Any]] = {}
    for fixture in deck_cfg.get("cutoutFixtures", []):
        if not isinstance(fixture, dict):
            continue
        slot = _extract_flex_slot_name(fixture.get("cutoutId", fixture.get("slotName", "")))
        if not slot:
            continue
        fixture_id = str(fixture.get("cutoutFixtureId", fixture.get("fixtureId", ""))).strip()
        load_name = _extract_observed_load_name(fixture)
        fixture_lower = fixture_id.lower()
        if "trashbinadapter" in fixture_lower or fixture_lower == "trash" or "trash" in fixture_lower:
            observed[slot] = {"kind": "trash_bin", "name": fixture_id, "load_name": load_name}
        elif "module" in fixture_lower:
            observed[slot] = {"kind": "module", "name": fixture_id, "load_name": load_name}
        elif fixture_id:
            observed[slot] = {"kind": "deck_fixture", "name": fixture_id, "load_name": load_name}

    # Compare
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    matches: list[dict[str, str]] = []

    for decl in declared:
        slot = decl["slot"]
        kind = decl["kind"]
        load_name = decl.get("load_name")
        obs = observed.get(slot)

        if kind == "labware":
            if obs is None:
                warnings.append({
                    "slot": slot,
                    "issue": "labware_not_visible",
                    "declared_kind": kind,
                    "declared_name": load_name or "",
                    "message": (
                        f"Protocol declares labware at {slot}, but /deck_configuration "
                        "does not expose the actual labware load. Confirm the physical slot before running."
                    ),
                })
            elif obs["kind"] in {"trash_bin", "module"}:
                errors.append({
                    "slot": slot,
                    "issue": "kind_mismatch",
                    "declared_kind": kind,
                    "declared_name": load_name or "",
                    "observed_kind": obs["kind"],
                    "observed_name": obs["name"],
                })
            elif obs.get("load_name"):
                observed_load_name = obs["load_name"]
                if load_names_compatible(load_name, observed_load_name):
                    matches.append({
                        "slot": slot,
                        "kind": kind,
                        "declared_name": load_name or "",
                        "observed_name": observed_load_name,
                    })
                else:
                    errors.append({
                        "slot": slot,
                        "issue": "labware_load_name_mismatch",
                        "declared_kind": kind,
                        "declared_name": load_name or "",
                        "observed_kind": obs["kind"],
                        "observed_name": observed_load_name,
                    })
            else:
                warnings.append({
                    "slot": slot,
                    "issue": "labware_not_confirmed",
                    "declared_kind": kind,
                    "declared_name": load_name or "",
                    "observed_kind": obs["kind"],
                    "observed_name": obs["name"],
                    "message": (
                        f"Protocol declares labware at {slot}, but /deck_configuration only confirms "
                        f"the slot fixture ({obs['name'] or 'unknown'}). Recheck the physical labware."
                    ),
                })
            continue

        if obs is None:
            errors.append({
                "slot": slot,
                "issue": "missing_required_fixture",
                "declared_kind": kind,
                "declared_name": load_name or "",
                "message": f"Protocol declares {kind} at {slot}, but the live deck does not show it.",
            })
        elif obs["kind"] == kind:
            matches.append({"slot": slot, "kind": kind, "declared_name": load_name or obs["name"]})
        else:
            errors.append({
                "slot": slot,
                "issue": "kind_mismatch",
                "declared_kind": kind,
                "declared_name": load_name or "",
                "observed_kind": obs["kind"],
                "observed_name": obs["name"],
            })

    result = {
        "protocol": str(protocol_path),
        "declared": declared,
        "matches": matches,
        "errors": errors,
        "warnings": warnings,
    }
    print_json(result)
    return 1 if errors else 0


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Opentrons robot LAN API helper")
    parser.add_argument("--host", required=False, help="Robot hostname or IP (or use saved config)")
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Robot API port (defaults to saved port or 31950)",
    )
    parser.add_argument("--token", help="Optional Opentrons auth token")
    parser.add_argument(
        "--timeout", type=int, default=DEFAULT_TIMEOUT, help="HTTP timeout in seconds"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    health = subparsers.add_parser("health", help="GET /health")
    health.set_defaults(handler=handle_health)

    list_protocols = subparsers.add_parser("list-protocols", help="GET /protocols")
    list_protocols.set_defaults(handler=handle_list_protocols)

    upload = subparsers.add_parser("upload-protocol", help="POST /protocols")
    upload.add_argument("files", nargs="+", help="Protocol files to upload")
    upload.add_argument("--key", help="Optional protocol key")
    upload.add_argument("--protocol-kind", help="Optional protocol kind")
    upload.add_argument("--rtp-values", help="Runtime parameter values JSON string")
    upload.add_argument("--rtp-files", help="Runtime parameter files JSON string")
    upload.set_defaults(handler=handle_upload_protocol)

    analyze = subparsers.add_parser(
        "analyze-protocol", help="POST /protocols/{protocolKey}/analyses"
    )
    analyze.add_argument("protocol_key", help="Protocol key or id")
    analyze.add_argument("--rtp-values", help="Runtime parameter values JSON string")
    analyze.add_argument("--rtp-files", help="Runtime parameter files JSON string")
    analyze.add_argument(
        "--force-reanalyze",
        action="store_true",
        help="Request a fresh analysis",
    )
    analyze.set_defaults(handler=handle_analyze_protocol)

    create_run = subparsers.add_parser("create-run", help="POST /runs")
    create_run.add_argument("--protocol-id", help="Protocol id returned by upload")
    create_run.add_argument("--rtp-values", help="Runtime parameter values JSON string")
    create_run.add_argument("--rtp-files", help="Runtime parameter files JSON string")
    create_run.set_defaults(handler=handle_create_run)

    list_runs = subparsers.add_parser("list-runs", help="GET /runs")
    list_runs.set_defaults(handler=handle_list_runs)

    get_run = subparsers.add_parser("get-run", help="GET /runs/{runId}")
    get_run.add_argument("run_id", help="Run id")
    get_run.set_defaults(handler=handle_get_run)

    run_action = subparsers.add_parser("run-action", help="POST /runs/{runId}/actions")
    run_action.add_argument("run_id", help="Run id")
    run_action.add_argument(
        "action",
        choices=[
            "play",
            "pause",
            "stop",
            "resume-from-recovery",
            "resume-from-recovery-assuming-false-positive",
        ],
        help="Run action to submit",
    )
    run_action.set_defaults(handler=handle_run_action)

    get_camera = subparsers.add_parser("get-camera", help="GET /camera")
    get_camera.set_defaults(handler=handle_get_camera)

    set_camera = subparsers.add_parser("set-camera", help="POST /camera")
    set_camera.add_argument("--camera-enabled", type=parse_bool, required=True)
    set_camera.add_argument("--live-stream-enabled", type=parse_bool, required=True)
    set_camera.add_argument(
        "--error-recovery-camera-enabled", type=parse_bool, required=True
    )
    set_camera.set_defaults(handler=handle_set_camera)

    camera_image = subparsers.add_parser(
        "set-camera-image", help="POST /camera/cameraSettings"
    )
    camera_image.add_argument("--camera-id")
    camera_image.add_argument("--resolution", help="Format: WIDTHxHEIGHT")
    camera_image.add_argument("--zoom", type=float)
    camera_image.add_argument("--contrast", type=float)
    camera_image.add_argument("--brightness", type=float)
    camera_image.add_argument("--saturation", type=float)
    camera_image.add_argument("--pan", help="Format: X,Y")
    camera_image.set_defaults(handler=handle_set_camera_image)

    preview = subparsers.add_parser(
        "capture-preview", help="POST /camera/capturePreviewImage"
    )
    preview.add_argument("--camera-id")
    preview.add_argument("--resolution", help="Format: WIDTHxHEIGHT")
    preview.add_argument("--zoom", type=float)
    preview.add_argument("--contrast", type=float)
    preview.add_argument("--brightness", type=float)
    preview.add_argument("--saturation", type=float)
    preview.add_argument("--pan", help="Format: X,Y")
    preview.add_argument(
        "--output", required=True, help="Where to save the preview image"
    )
    preview.set_defaults(handler=handle_capture_preview)

    # --- New subcommands ---

    save_conn = subparsers.add_parser("save-connection", help="Save robot connection for reuse")
    save_conn.add_argument("--host", required=True, help="Robot hostname or IP")
    save_conn.set_defaults(handler=handle_save_connection)

    show_conn = subparsers.add_parser("show-connection", help="Show saved robot connection")
    show_conn.set_defaults(handler=handle_show_connection)

    deploy = subparsers.add_parser(
        "deploy-and-run", help="Upload protocol, wait for analysis, create run, and play",
    )
    deploy.add_argument("files", nargs="+", help="Protocol files to upload")
    deploy.add_argument("--key", help="Optional protocol key")
    deploy.add_argument("--protocol-kind", help="Optional protocol kind")
    deploy.add_argument(
        "--rtp-values",
        type=validate_json_object_arg,
        help="Runtime parameter values as a JSON object",
    )
    deploy.add_argument(
        "--rtp-files",
        type=validate_json_object_arg,
        help="Runtime parameter files as a JSON object",
    )
    deploy.add_argument(
        "--analysis-timeout", type=int, default=120, help="Analysis poll timeout in seconds"
    )
    deploy.add_argument(
        "--analysis-interval", type=int, default=2, help="Analysis poll interval in seconds"
    )
    deploy.set_defaults(handler=handle_deploy_and_run)

    search = subparsers.add_parser("search-labware", help="Search labware definitions by name")
    search.add_argument("query", help="Search query (e.g. 'PCR', 'reservoir', 'tiprack')")
    search.add_argument("--limit", type=int, default=20, help="Max results")
    search.set_defaults(handler=handle_search_labware)

    watch = subparsers.add_parser("watch-run", help="Poll run status until terminal; only output on change")
    watch.add_argument("run_id", help="Run id to monitor")
    watch.add_argument("--interval", type=int, default=30, help="Poll interval in seconds")
    watch.add_argument("--timeout", type=int, default=1800, help="Maximum wait in seconds")
    watch.set_defaults(handler=handle_watch_run)

    deck = subparsers.add_parser("deck-check", help="Compare protocol declarations vs live robot deck")
    deck.add_argument("protocol_file", help="Protocol file to check")
    deck.set_defaults(handler=handle_deck_check)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = None if args.command in LOCAL_ONLY_COMMANDS else resolve_config(args)
    rc = args.handler(args, config)
    # Auto-save connection on success when host was explicitly provided
    if rc == 0 and args.host and args.command != "save-connection" and args.command not in LOCAL_ONLY_COMMANDS:
        save_connection_config(args.host, config.port, config.token)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
