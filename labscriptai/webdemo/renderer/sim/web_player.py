"""Interactive Flex and OT-2 views for the local chat site.

Serves the MuJoCo machines on 127.0.0.1 for the web page. The page shows two
images that it can request at any time t (the main view and the follow
close-up, each with its own orbit and zoom), plus the step list and the
analysis JSON. A protocol is loaded with POST /flex3d/load; its robotType
picks the machine, and the key is a hash of the analysis, so the same script
is loaded once. The serial dilution example is always resident. This does not
talk to a robot.

    PYTHONPATH=. /usr/bin/python3 -m sim.web_player

Routes (all under /flex3d):
    POST /load                        analysis JSON body -> info (key, steps, camera, limits)
    GET  /<key>/info                  info for a loaded protocol
    GET  /<key>/analysis.json         the analysis the protocol was built from
    GET  /<key>/main.jpg?t&az&el&dist
    GET  /<key>/close.jpg?t&az&el&dist
    GET  /health
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
from collections import OrderedDict
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlparse

import mujoco

from sim.flex_protocol import ProtocolError
from sim.flex3d_runtime.flex_protocol import ProtocolError as FlexProtocolError
from sim.flex3d_runtime.flex_protocol import load_analysis as flex_load_analysis
from sim.flex3d_runtime.flex_protocol import plan as flex_plan
from sim.flex3d_runtime.flex_protocol import scene_spec as flex_scene_spec
from sim.flex3d_runtime.flex_scene import load_deck, write_model as flex_write_model
from sim.flex_scene import EXPORT, ROOT
from sim.ot2_protocol import load_analysis as ot2_load_analysis
from sim.ot2_protocol import plan as ot2_plan
from sim.ot2_protocol import scene_spec as ot2_scene_spec
from sim.ot2_scene import load_deck as ot2_load_deck
from sim.ot2_scene import write_spec_model as ot2_write_model
from sim.play_ot2_protocol import Renderer as Ot2Renderer
from sim.play_ot2_protocol import check_targets as ot2_check_targets, check_clearance as ot2_check_clearance, check_liquid as ot2_check_liquid
from sim.play_ot2_protocol import Scene as Ot2Scene
from sim.play_ot2_protocol import analyze
from sim.play_protocol import CLOSE_DEFAULT_ORBIT, CLOSE_WEB_H, CLOSE_WEB_W, FRAME_H, MAIN_W
from sim.flex3d_runtime.play_protocol import Renderer as FlexRenderer, Scene as FlexScene
from sim.flex3d_runtime.play_protocol import check_targets as flex_check_targets, check_clearance as flex_check_clearance, check_liquid as flex_check_liquid

HOST = "127.0.0.1"
PORT = 8791
FPS = 30
JPEG_QUALITY = 88
MAX_MODELS = 4
MAX_BODY = 8 * 1024 * 1024
EXAMPLE = ROOT / "protocols" / "flex_serial_dilution.analysis.json"
EXAMPLE_KEY = "example"
# Elevation stays below zero, so no camera drops under the deck.
EL_RANGE = (-89.0, -1.0)
MAIN_DIST = (0.35, 4.0)
CLOSE_DIST = (0.08, 1.2)
ROUTE = re.compile(r"^/flex3d/(?P<key>[a-z0-9]{1,32})/(?P<what>info|analysis\.json|main\.jpg|close\.jpg)$")


@dataclass(frozen=True)
class Machine:
    """One robot type's deck, planner, scene writer and player classes."""

    load_deck: Callable
    load_analysis: Callable
    plan: Callable
    scene_spec: Callable
    write_model: Callable
    scene: type
    renderer: type
    checks: tuple[Callable, Callable, Callable] | None = None


FLEX = Machine(load_deck, flex_load_analysis, flex_plan, flex_scene_spec, flex_write_model, FlexScene, FlexRenderer,
               (flex_check_targets, flex_check_clearance, flex_check_liquid))
OT2 = Machine(ot2_load_deck, ot2_load_analysis, ot2_plan, ot2_scene_spec, ot2_write_model, Ot2Scene, Ot2Renderer,
              (ot2_check_targets, ot2_check_clearance, ot2_check_liquid))


def machine_for(raw: dict) -> Machine:
    kind = raw.get("robotType")
    if kind == "OT-2 Standard":
        return OT2
    if kind == "OT-3 Standard":
        return FLEX
    raise ProtocolError(f"Cannot select a 3D scene for robotType {kind!r}; expected OT-2 Standard or OT-3 Standard")


class Model:
    """One protocol: its MuJoCo model, the renderers, and the step list the page shows."""

    def __init__(self, key: str, analysis: Path, folder: Path, machine: Machine = FLEX) -> None:
        deck = machine.load_deck()
        run = machine.load_analysis(analysis, deck)
        plan = machine.plan(run)
        xml = machine.write_model(deck, machine.scene_spec(plan), folder)
        model = mujoco.MjModel.from_xml_path(str(xml))
        data = mujoco.MjData(model)
        self.key = key
        self.title = run.title
        self.duration = float(plan.duration)
        self.analysis_path = analysis
        scene = machine.scene(plan, model, data)
        self.validation = {"status": "not_run", "scope": "Digital model replay, not physical robot acceptance."}
        if machine.checks:
            targets, clearance, liquid = machine.checks
            try:
                hits, json_error, sim_error = targets(plan, scene)
                gap, tightest, count = clearance(plan, scene)
                liquid(plan)
            except (RuntimeError, ValueError) as exc:
                raise ProtocolError(f"3D replay check failed: {exc}") from exc
            self.validation.update(status="passed", target_commands=len(hits), json_error_mm=json_error,
                                   simulator_error_mm=sim_error, clearance_samples=count,
                                   min_enclosure_gap_mm=gap*1000, tightest=tightest)
        self.warnings = list(plan.warnings)
        if self.warnings and self.validation["status"] == "passed":
            self.validation["status"] = "partial"
        self.renderer = machine.renderer(plan, scene)
        self.renderer.build_track(FPS)
        self._closed = False
        self.main_default = self.renderer.default_orbit()
        self.close_default = getattr(self.renderer, "close_default_orbit", CLOSE_DEFAULT_ORBIT)
        self.pipettes = [{"mount": p.mount, "name": p.name, "tool": p.tool} for p in run.pipettes.values()]
        self.steps = [
            {
                "index": i,
                "cmd": step.cmd,
                "commandId": run.commands[step.cmd].get("id"),
                "kind": step.kind,
                "text": step.text,
                "detail": step.detail,
                "t0": round(step.t0, 3),
                "t1": round(step.t1, 3),
                "slots": list(step.slots),
                "tool": step.tool,
            }
            for i, step in enumerate(plan.steps)
        ]

    def info(self) -> dict:
        return {
            "key": self.key,
            "title": self.title,
            "duration": round(self.duration, 3),
            "warnings": self.warnings,
            "validation": self.validation,
            "pipettes": self.pipettes,
            "camera": {
                "main": {
                    "azimuth": self.main_default["azimuth"],
                    "elevation": self.main_default["elevation"],
                    "distance": self.main_default["distance"],
                    "lookat": self.main_default["lookat"],
                },
                "close": {"azimuth": self.close_default[0], "elevation": self.close_default[1], "distance": self.close_default[2]},
            },
            "limits": {
                "elevation": list(EL_RANGE),
                "mainDistance": list(MAIN_DIST),
                "closeDistance": list(CLOSE_DIST),
            },
            "frame": {
                "main_width": MAIN_W,
                "main_height": FRAME_H,
                "close_width": CLOSE_WEB_W,
                "close_height": CLOSE_WEB_H,
                "fps": FPS,
            },
            "steps": self.steps,
        }

    def main_jpeg(self, t: float, azimuth: float, elevation: float, distance: float) -> bytes:
        t = min(max(t, 0.0), self.duration)
        orbit = (azimuth, _clamp(elevation, EL_RANGE), _clamp(distance, MAIN_DIST))
        return _jpeg(self.renderer.web_main(t, orbit))

    def close_jpeg(self, t: float, azimuth: float, elevation: float, distance: float) -> bytes:
        t = min(max(t, 0.0), self.duration)
        orbit = (azimuth, _clamp(elevation, EL_RANGE), _clamp(distance, CLOSE_DIST))
        return _jpeg(self.renderer.web_close(t, orbit))

    def close(self) -> None:
        """Release renderers while each native GL context owns the deletion.

        MuJoCo 3.17's ``Renderer.close()`` frees the ``MjrContext`` without
        first making that renderer's ``GLContext`` current.  Registry eviction
        usually happens immediately after constructing the next model, so the
        newly-created model's context may be current while an older model's
        framebuffer and textures are deleted.  On macOS that cross-context
        delete can corrupt the active renderer and produce the colored stripe
        frames seen after several protocol loads.

        Flex uses three lightweight targets over one native renderer; OT-2
        uses three native renderers.  Close each native owner once, and make
        its context current immediately before the close.  The guard also
        makes repeated eviction/cleanup calls harmless.
        """
        if self._closed:
            return
        closed: set[int] = set()
        for target in (self.renderer.main, self.renderer.close, self.renderer.close_web):
            owner = getattr(target, "_renderer", target)
            owner_id = id(owner)
            if owner_id in closed:
                continue
            closed.add(owner_id)
            context = getattr(owner, "_gl_context", None)
            if context is not None:
                context.make_current()
            target.close()
        self._closed = True


class Registry:
    """Loaded protocols, most recent last. The example stays; live scripts are evicted oldest first."""

    def __init__(self) -> None:
        self._models: OrderedDict[str, Model] = OrderedDict()

    def get(self, key: str) -> Model | None:
        model = self._models.get(key)
        if model is not None:
            self._models.move_to_end(key)
        return model

    def put(self, model: Model) -> None:
        self._models[model.key] = model
        self._models.move_to_end(model.key)
        while len(self._models) > MAX_MODELS:
            victim = next(k for k in self._models if k != EXAMPLE_KEY)
            self._models.pop(victim).close()

    def keys(self) -> list[str]:
        return list(self._models)


def _clamp(value: float, bounds: tuple[float, float]) -> float:
    return min(max(value, bounds[0]), bounds[1])


def _jpeg(image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=JPEG_QUALITY)
    return buf.getvalue()


def _num(qs: dict[str, list[str]], key: str, default: float) -> float:
    raw = qs.get(key, [None])[0]
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    if not math.isfinite(value):
        return default
    return value


def load_live(registry: Registry, body: bytes) -> Model:
    """Build a protocol from an analysis JSON body. Raises ValueError for bad input, ProtocolError for unsupported scripts."""

    try:
        raw = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"body is not JSON: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("commands"), list) or not raw["commands"]:
        raise ValueError("analysis has no commands")
    key = hashlib.sha256(body).hexdigest()[:16]
    existing = registry.get(key)
    if existing is not None:
        return existing
    folder = EXPORT / "live" / key
    folder.mkdir(parents=True, exist_ok=True)
    analysis = folder / f"{key}.analysis.json"
    analysis.write_bytes(body)
    model = Model(key, analysis, folder, machine_for(raw))
    registry.put(model)
    return model


def make_handler(registry: Registry) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        # HTTP/1.0 closes each request. HTTP/1.1 keep-alive on this
        # single thread would pin the MuJoCo context and stall a second client.
        protocol_version = "HTTP/1.0"

        def do_GET(self) -> None:
            try:
                self._get()
            except (BrokenPipeError, ConnectionResetError):
                return

        def do_POST(self) -> None:
            try:
                self._post()
            except (BrokenPipeError, ConnectionResetError):
                return

        def _get(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/flex3d/health":
                self._json({"ok": True, "models": registry.keys()})
                return
            match = ROUTE.match(parsed.path)
            if match is None:
                self._json({"error": "not_found"}, code=404)
                return
            model = registry.get(match["key"])
            if model is None:
                self._json({"error": "unknown_model"}, code=404)
                return
            what = match["what"]
            if what == "info":
                self._json(model.info())
            elif what == "analysis.json":
                self._bytes(model.analysis_path.read_bytes(), "application/json; charset=utf-8")
            else:
                qs = parse_qs(parsed.query)
                main = what == "main.jpg"
                default = model.main_default if main else None
                az = _num(qs, "az", default["azimuth"] if main else model.close_default[0])
                el = _num(qs, "el", default["elevation"] if main else model.close_default[1])
                dist = _num(qs, "dist", default["distance"] if main else model.close_default[2])
                t = _num(qs, "t", 0.0)
                jpeg = model.main_jpeg(t, az, el, dist) if main else model.close_jpeg(t, az, el, dist)
                self._bytes(jpeg, "image/jpeg")

        def _post(self) -> None:
            if urlparse(self.path).path != "/flex3d/load":
                self._json({"error": "not_found"}, code=404)
                return
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                self._json({"error": "bad_length", "message": "Content-Length must be a number"}, code=400)
                return
            if length <= 0 or length > MAX_BODY:
                self._json({"error": "bad_length", "message": f"body must be 1 to {MAX_BODY} bytes"}, code=400)
                return
            body = self.rfile.read(length)
            try:
                model = load_live(registry, body)
            except ValueError as exc:
                self._json({"error": "bad_analysis", "message": str(exc)}, code=400)
                return
            except (ProtocolError, FlexProtocolError) as exc:
                self._json({"error": "unsupported", "message": str(exc)}, code=422)
                return
            except Exception as exc:  # the page shows the message; the server keeps running
                self._json({"error": "load_failed", "message": f"{type(exc).__name__}: {exc}"}, code=500)
                return
            self._json(model.info())

        def _json(self, body: dict, code: int = 200) -> None:
            raw = json.dumps(body).encode()
            self._bytes(raw, "application/json; charset=utf-8", code)

        def _bytes(self, raw: bytes, content_type: str, code: int = 200) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            # A local page opened from disk (viewer.html) reads /info cross-origin.
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, fmt: str, *args) -> None:
            if len(args) >= 2 and args[1] != "200":
                super().log_message(fmt, *args)

    return Handler


def resolve_analysis(protocol: Path) -> Path:
    protocol = protocol.resolve()
    if not protocol.exists():
        raise SystemExit(f"protocol not found: {protocol}")
    if protocol.suffix == ".py":
        return analyze(protocol)
    return protocol


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve interactive Flex protocol views on 127.0.0.1")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--protocol", type=Path, default=EXAMPLE, help="the example that is always loaded")
    args = parser.parse_args()
    if args.host != HOST:
        raise SystemExit("refusing to bind anything except 127.0.0.1")
    analysis = resolve_analysis(args.protocol)
    machine = machine_for(json.loads(analysis.read_text()))
    registry = Registry()
    example = Model(EXAMPLE_KEY, analysis, EXPORT / "protocols" / analysis.name.replace(".analysis.json", "").replace(".json", ""), machine)
    registry.put(example)
    # One thread: the MuJoCo GL contexts have to stay on the thread that created them.
    server = HTTPServer((args.host, args.port), make_handler(registry))
    print(
        f"flex3d http://{args.host}:{args.port}/flex3d/{EXAMPLE_KEY}/info  {example.title}  {example.duration:.1f}s",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
