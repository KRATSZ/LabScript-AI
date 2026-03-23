"""Stdlib-only Opentrons LAN HTTP API helper."""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib import error, request

DEFAULT_PORT = 31950
DEFAULT_TIMEOUT = 30
DEFAULT_HEADERS = {"Opentrons-Version": "3"}


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

    fields: dict[str, str] = {}
    if args.key:
        fields["key"] = args.key
    if args.protocol_kind:
        fields["protocolKind"] = args.protocol_kind
    if args.rtp_values:
        fields["runTimeParameterValues"] = args.rtp_values
    if args.rtp_files:
        fields["runTimeParameterFiles"] = args.rtp_files

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
    body: dict[str, Any] = {"data": {}}
    if args.protocol_id:
        body["data"]["protocolId"] = args.protocol_id
    if args.rtp_values:
        body["data"]["runTimeParameterValues"] = parse_json_arg(args.rtp_values, {})
    if args.rtp_files:
        body["data"]["runTimeParameterFiles"] = parse_json_arg(args.rtp_files, {})
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Opentrons robot LAN API helper")
    parser.add_argument("--host", required=True, help="Robot hostname or IP")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Robot API port")
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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = ConnectionConfig(
        host=args.host,
        port=args.port,
        token=args.token,
        timeout=args.timeout,
    )
    return args.handler(args, config)


if __name__ == "__main__":
    raise SystemExit(main())

