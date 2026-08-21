"""HTTP server mirroring Opentrons Flex robot-server on :31950."""

from __future__ import annotations

import argparse
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from .engine import FakeRobotEngine, FakeRobotHttpError
from .scenarios import list_scenarios


VERSION_HEADER = "opentrons-version"


class FakeRobotServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass, engine: FakeRobotEngine):
        super().__init__(server_address, RequestHandlerClass)
        self.engine = engine


def create_app(
    host: str = "127.0.0.1",
    port: int = 31950,
    scenario: str = "healthy",
    *,
    tick_s: float = 0.05,
) -> FakeRobotServer:
    engine = FakeRobotEngine(scenario_id=scenario, tick_s=tick_s)
    return FakeRobotServer((host, port), FakeRobotHandler, engine)


def serve(
    host: str = "127.0.0.1",
    port: int = 31950,
    scenario: str = "healthy",
    *,
    tick_s: float = 0.05,
) -> None:
    httpd = create_app(host=host, port=port, scenario=scenario, tick_s=tick_s)
    print(
        f"[fake_robot] listening on http://{host}:{port} scenario={scenario}",
        flush=True,
    )
    print(f"[fake_robot] scenarios: {', '.join(s['id'] for s in list_scenarios())}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[fake_robot] shutting down", flush=True)
    finally:
        httpd.server_close()


class FakeRobotHandler(BaseHTTPRequestHandler):
    server_version = "FakeOpentrons/0.1"

    @property
    def engine(self) -> FakeRobotEngine:
        return self.server.engine  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: Any) -> None:
        # Quiet by default; uncomment for debug.
        # super().log_message(fmt, *args)
        return

    def _header_map(self) -> dict[str, str]:
        return {k.lower(): v for k, v in self.headers.items()}

    def _require_version(self) -> bool:
        headers = self._header_map()
        if VERSION_HEADER not in headers:
            self._json(
                422,
                {"message": "header.opentrons-version: Field required", "errorCode": "4000"},
            )
            return False
        return True

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _read_multipart_file(self) -> tuple[str, bytes]:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        content_type = self.headers.get("Content-Type") or ""
        match = re.search(r"boundary=([^\s;]+)", content_type)
        if not match:
            return "protocol.py", body
        boundary = match.group(1).encode("utf-8")
        if boundary.startswith(b'"') and boundary.endswith(b'"'):
            boundary = boundary[1:-1]
        parts = body.split(b"--" + boundary)
        filename = "protocol.py"
        content = b""
        for part in parts:
            if b"Content-Disposition" not in part:
                continue
            if b"filename=" in part:
                m = re.search(br'filename="([^"]+)"', part)
                if m:
                    filename = m.group(1).decode("utf-8", errors="replace")
                _, _, payload = part.partition(b"\r\n\r\n")
                content = payload.rstrip(b"\r\n")
                if content.endswith(b"--"):
                    content = content[:-2].rstrip(b"\r\n")
                break
        return filename, content

    def _json(self, status: int, payload: Any) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _bytes(self, status: int, data: bytes, content_type: str = "application/octet-stream") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Opentrons-Version")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        try:
            if not self._require_version():
                return
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query)
            page_length = int((qs.get("pageLength") or ["20"])[0])

            if path == "/health":
                return self._json(200, self.engine.health())
            if path == "/instruments":
                return self._json(200, self.engine.instruments())
            if path == "/robot/door/status":
                return self._json(200, self.engine.door_status())
            if path == "/robot/control/estopStatus":
                return self._json(200, self.engine.estop_status())
            if path == "/deck_configuration":
                return self._json(200, self.engine.deck_configuration())
            if path == "/modules":
                return self._json(200, self.engine.modules())
            if path == "/labwareOffsets":
                return self._json(200, self.engine.labware_offsets())
            if path == "/camera":
                return self._json(200, self.engine.camera())
            if path == "/protocols":
                return self._json(200, self.engine.list_protocols())
            if path == "/runs":
                return self._json(200, self.engine.list_runs())
            if path == "/dataFiles":
                return self._json(200, {"data": [], "meta": {"cursor": 0, "totalLength": 0}})
            if path == "/_fake/scenario":
                return self._json(200, {"data": self.engine.snapshot_admin()})
            if path == "/_fake/scenarios":
                return self._json(200, {"data": list_scenarios()})

            m = re.fullmatch(r"/runs/([^/]+)", path)
            if m:
                return self._json(200, self.engine.get_run(m.group(1)))
            m = re.fullmatch(r"/runs/([^/]+)/commands", path)
            if m:
                return self._json(200, self.engine.list_commands(m.group(1), page_length))
            m = re.fullmatch(r"/runs/([^/]+)/commands/([^/]+)", path)
            if m:
                return self._json(200, self.engine.get_command(m.group(1), m.group(2)))
            m = re.fullmatch(r"/maintenance_runs/([^/]+)", path)
            if m:
                return self._json(200, self.engine.get_maintenance_run(m.group(1)))
            m = re.fullmatch(r"/maintenance_runs/([^/]+)/commands", path)
            if m:
                return self._json(200, self.engine.list_maintenance_commands(m.group(1), page_length))
            m = re.fullmatch(r"/protocols/([^/]+)/analyses", path)
            if m:
                return self._json(
                    200,
                    {
                        "data": [
                            {
                                "id": m.group(1) + "-analysis",
                                "status": "completed",
                                "result": "ok",
                            }
                        ]
                    },
                )

            return self._json(404, {"errors": [{"detail": f"no route GET {path}"}]})
        except FakeRobotHttpError as exc:
            return self._json(exc.status, exc.body)
        except Exception as exc:  # noqa: BLE001 — keep server alive under concurrent MCP polls
            return self._json(500, {"errors": [{"detail": str(exc), "errorType": "FakeRobotInternalError"}]})

    def do_POST(self) -> None:  # noqa: N802
        try:
            if not self._require_version():
                return
            parsed = urlparse(self.path)
            path = parsed.path

            if path == "/protocols":
                filename, content = self._read_multipart_file()
                return self._json(201, self.engine.upload_protocol(filename=filename, content=content))
            if path == "/runs":
                return self._json(201, self.engine.create_run(self._read_json()))
            if path == "/maintenance_runs":
                return self._json(201, self.engine.create_maintenance_run(self._read_json()))
            if path == "/camera":
                return self._json(200, self.engine.camera())
            if path == "/camera/cameraSettings":
                return self._json(200, {"data": {"ok": True}})
            if path == "/camera/capturePreviewImage":
                # Minimal JPEG-ish bytes
                return self._bytes(200, b"\xff\xd8\xff\xd9", "image/jpeg")
            if path == "/_fake/scenario":
                body = self._read_json()
                scenario_id = body.get("scenario_id") or body.get("scenario") or "healthy"
                return self._json(200, {"data": self.engine.apply_scenario(scenario_id)})
            if path == "/_fake/reset":
                return self._json(200, {"data": self.engine.apply_scenario(self.engine.scenario_id)})
            if path == "/_fake/backdate_commands":
                body = self._read_json()
                return self._json(
                    200,
                    {
                        "data": self.engine.backdate_commands(
                            body.get("run_id") or "",
                            float(body.get("minutes") or 0),
                            body.get("command_types"),
                        )
                    },
                )

            m = re.fullmatch(r"/runs/([^/]+)/actions", path)
            if m:
                return self._json(201, self.engine.post_action(m.group(1), self._read_json()))
            m = re.fullmatch(r"/runs/([^/]+)/commands", path)
            if m:
                return self._json(201, self.engine.post_command(m.group(1), self._read_json()))
            m = re.fullmatch(r"/maintenance_runs/([^/]+)/commands", path)
            if m:
                return self._json(
                    201, self.engine.post_maintenance_command(m.group(1), self._read_json())
                )

            return self._json(404, {"errors": [{"detail": f"no route POST {path}"}]})
        except FakeRobotHttpError as exc:
            return self._json(exc.status, exc.body)
        except Exception as exc:  # noqa: BLE001
            return self._json(500, {"errors": [{"detail": str(exc), "errorType": "FakeRobotInternalError"}]})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fake Opentrons Flex HTTP backend")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=31950)
    parser.add_argument(
        "--scenario",
        default="healthy",
        help=f"One of: {', '.join(s['id'] for s in list_scenarios())}",
    )
    parser.add_argument("--tick-ms", type=int, default=50, help="Worker tick in milliseconds")
    args = parser.parse_args(argv)
    serve(host=args.host, port=args.port, scenario=args.scenario, tick_s=args.tick_ms / 1000.0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
