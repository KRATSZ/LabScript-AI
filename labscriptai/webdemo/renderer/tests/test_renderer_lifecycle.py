"""MuJoCo renderer lifetime regressions.

The first tests use tiny fakes to assert the ownership ordering without
requiring a display.  The real multi-model GL comparison is opt-in because it
creates several native contexts and is intentionally slower:

    RENDERER_GL_TESTS=1 PYTHONPATH=. /path/to/qa-venv/bin/python \
        -m unittest discover -s tests -p 'test_renderer_lifecycle.py' -v
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image


class _FakeContext:
    def __init__(self, name: str, events: list, current: list) -> None:
        self.name = name
        self.events = events
        self.current = current

    def make_current(self) -> None:
        self.events.append(("make_current", self.name))
        self.current[0] = self.name


class _FakeOwner:
    def __init__(self, name: str, events: list, current: list) -> None:
        self.name = name
        self.events = events
        self.current = current
        self._gl_context = _FakeContext(name, events, current)

    def close(self) -> None:
        self.events.append(("owner.close", self.name, self.current[0]))


class _FakeTarget:
    def __init__(self, owner: _FakeOwner, events: list, current: list) -> None:
        self._renderer = owner
        self.events = events
        self.current = current

    def close(self) -> None:
        self.events.append(("target.close", self._renderer.name, self.current[0]))


class RendererLifecycleTests(unittest.TestCase):
    def _web_player(self):
        try:
            from sim import web_player
        except (ImportError, OSError) as exc:
            self.skipTest(f"MuJoCo web renderer unavailable: {exc}")
        return web_player

    def test_model_close_makes_each_native_owner_current_and_deduplicates_flex_wrapper(self):
        web_player = self._web_player()
        events: list = []
        current = ["new-model-context"]
        shared = _FakeOwner("flex-shared", events, current)
        model = object.__new__(web_player.Model)
        model.renderer = SimpleNamespace(
            main=_FakeTarget(shared, events, current),
            close=_FakeTarget(shared, events, current),
            close_web=_FakeTarget(shared, events, current),
        )
        model._closed = False

        model.close()
        first_close_events = list(events)
        model.close()

        self.assertEqual(first_close_events, [
            ("make_current", "flex-shared"),
            ("target.close", "flex-shared", "flex-shared"),
        ])
        self.assertEqual(events, first_close_events)

    def test_model_close_switches_context_before_each_ot2_target(self):
        web_player = self._web_player()
        events: list = []
        current = ["new-model-context"]
        owners = [_FakeOwner(f"ot2-{i}", events, current) for i in range(3)]
        model = object.__new__(web_player.Model)
        model.renderer = SimpleNamespace(
            main=_FakeTarget(owners[0], events, current),
            close=_FakeTarget(owners[1], events, current),
            close_web=_FakeTarget(owners[2], events, current),
        )
        model._closed = False

        model.close()

        self.assertEqual(events, [
            ("make_current", "ot2-0"),
            ("target.close", "ot2-0", "ot2-0"),
            ("make_current", "ot2-1"),
            ("target.close", "ot2-1", "ot2-1"),
            ("make_current", "ot2-2"),
            ("target.close", "ot2-2", "ot2-2"),
        ])

    def test_flex_render_target_close_is_owner_context_safe_and_idempotent(self):
        web_player = self._web_player()
        from sim.flex3d_runtime.play_protocol import _RenderTarget

        events: list = []
        current = ["other-context"]
        owner = _FakeOwner("flex-owner", events, current)
        target = object.__new__(_RenderTarget)
        target._renderer = owner
        target.width, target.height = 12, 8
        target._closed = False

        target.close()
        target.close()

        self.assertEqual(events, [
            ("make_current", "flex-owner"),
            ("owner.close", "flex-owner", "flex-owner"),
        ])

    @unittest.skipUnless(os.environ.get("RENDERER_GL_TESTS") == "1", "set RENDERER_GL_TESTS=1 for native GL eviction test")
    def test_real_clean_flex_matches_same_frame_after_five_evictions(self):
        """Compare real RGB frames, not merely HTTP status or JPEG non-emptiness."""

        web_player = self._web_player()
        root = Path(__file__).resolve().parents[1]
        flex_analysis = root / "protocols/flex_serial_dilution.analysis.json"
        fixtures = Path(__file__).resolve().parent / "fixtures"

        def frame(model, which: str) -> np.ndarray:
            if which == "main":
                camera = model.main_default
                payload = model.main_jpeg(0.0, camera["azimuth"], camera["elevation"], camera["distance"])
            else:
                azimuth, elevation, distance = model.close_default
                payload = model.close_jpeg(0.0, azimuth, elevation, distance)
            return np.asarray(Image.open(io.BytesIO(payload)).convert("RGB"), dtype=np.int16)

        with tempfile.TemporaryDirectory(prefix="renderer-lifecycle-") as folder:
            folder_path = Path(folder)
            analyzed = {}
            for relative in (
                "protocols/single_p20.py", "protocols/eight_p300.py",
                "protocols/single_p1000.py", "protocols/thermocycler.py",
                "edge-protocols/air_gap_224.py", "edge-protocols/absolute_move.py",
                "protocols/dilution_mix.py",
            ):
                protocol = fixtures / relative
                destination = folder_path / f"{protocol.stem}.json"
                result = subprocess.run(
                    [os.environ.get("OPENTRONS_PYTHON", sys.executable),
                     "-m", "opentrons.cli", "analyze", "--check",
                     "--json-output", str(destination), str(protocol)],
                    cwd=root, capture_output=True, text=True, timeout=120,
                )
                self.assertEqual(result.returncode, 0, result.stderr[-4000:])
                analysis = json.loads(destination.read_text(encoding="utf-8"))
                self.assertEqual(analysis.get("result"), "ok")
                self.assertFalse(analysis.get("errors"))
                analyzed[protocol.stem] = destination
            sequence = [
                analyzed["single_p20"], analyzed["eight_p300"],
                analyzed["single_p1000"], analyzed["thermocycler"],
                analyzed["air_gap_224"], analyzed["absolute_move"],
                flex_analysis, analyzed["dilution_mix"], analyzed["single_p20"],
            ]
            raw = json.loads(flex_analysis.read_text(encoding="utf-8"))
            clean = web_player.Model(
                "clean-flex",
                flex_analysis,
                folder_path / "clean-flex",
                web_player.machine_for(raw),
            )
            baseline = {which: frame(clean, which) for which in ("main", "close")}
            clean.close()
            clean.close()

            registry = web_player.Registry()
            models = []
            flex_model = None
            try:
                for index, analysis in enumerate(sequence):
                    raw = json.loads(analysis.read_text(encoding="utf-8"))
                    model = web_player.Model(
                        f"lifecycle-{index}",
                        analysis,
                        folder_path / f"lifecycle-{index}",
                        web_player.machine_for(raw),
                    )
                    models.append(model)
                    if analysis == flex_analysis:
                        flex_model = model
                    registry.put(model)
                self.assertIsNotNone(flex_model)
                self.assertGreaterEqual(len(sequence) - web_player.MAX_MODELS, 5)
                after = {which: frame(flex_model, which) for which in ("main", "close")}
                for which in ("main", "close"):
                    self.assertEqual(after[which].shape, baseline[which].shape)
                    # JPEG decode plus platform AA can vary by a small amount;
                    # colored-row corruption is orders of magnitude larger.
                    mean_abs = float(np.abs(after[which] - baseline[which]).mean())
                    self.assertLess(mean_abs, 2.0, f"{which} diverged after eviction: mean abs {mean_abs}")
                    self.assertTrue(np.isfinite(after[which]).all())
            finally:
                for model in models:
                    model.close()
                    model.close()


if __name__ == "__main__":
    unittest.main()
