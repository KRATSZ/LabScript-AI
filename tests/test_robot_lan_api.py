from __future__ import annotations

import argparse
import contextlib
import json
import io
import runpy
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "skills" / "opentrons-robot-lan" / "scripts" / "opentrons_robot_api.py"
_MOD = runpy.run_path(str(SCRIPT_PATH))

ConnectionConfig = _MOD["ConnectionConfig"]
main = _MOD["main"]
handle_deploy_and_run = _MOD["handle_deploy_and_run"]
handle_deck_check = _MOD["handle_deck_check"]
handle_watch_run = _MOD["handle_watch_run"]
load_names_compatible = _MOD["load_names_compatible"]
poll_analysis = _MOD["poll_analysis"]
resolve_config = _MOD["resolve_config"]
_GLOBALS = main.__globals__


class RobotLanApiTests(unittest.TestCase):
    def _patch_module(self, name: str, value) -> None:
        original = _GLOBALS[name]
        _GLOBALS[name] = value

        def restore() -> None:
            _GLOBALS[name] = original

        self.addCleanup(restore)

    def _patch_time_attr(self, name: str, value) -> None:
        original = getattr(_GLOBALS["time"], name)
        setattr(_GLOBALS["time"], name, value)

        def restore() -> None:
            setattr(_GLOBALS["time"], name, original)

        self.addCleanup(restore)

    def test_resolve_config_uses_saved_port_and_token(self) -> None:
        self._patch_module(
            "load_connection_config",
            lambda: {"host": "10.31.2.149", "port": 12345, "token": "saved-token"},
        )

        config = resolve_config(argparse.Namespace(host=None, port=None, token=None, timeout=None))

        self.assertEqual(config.host, "10.31.2.149")
        self.assertEqual(config.port, 12345)
        self.assertEqual(config.token, "saved-token")
        self.assertEqual(config.timeout, 30)

    def test_load_names_compatible_normalizes_hyphens_and_suffixes(self) -> None:
        self.assertTrue(
            load_names_compatible(
                "nest_96_wellplate_100ul_pcr_full_skirt",
                "nest-96-wellplate-100ul-pcr-full-skirt-v2",
            )
        )
        self.assertFalse(
            load_names_compatible(
                "nest_96_wellplate_100ul_pcr_full_skirt",
                "opentrons_96_tiprack_300ul",
            )
        )

    def test_show_connection_command_does_not_require_resolved_host(self) -> None:
        captured: list[dict[str, object]] = []
        self._patch_module("resolve_config", lambda _: (_ for _ in ()).throw(AssertionError("resolve_config should not run")))
        self._patch_module(
            "load_connection_config",
            lambda: {"host": "10.31.2.149", "port": 31950, "token": "secret-token"},
        )
        self._patch_module("print_json", lambda data: captured.append(data))

        rc = main(["show-connection"])

        self.assertEqual(rc, 0)
        self.assertEqual(captured[0]["host"], "10.31.2.149")
        self.assertEqual(captured[0]["token"], "***redacted***")

    def test_search_labware_command_does_not_require_resolved_host(self) -> None:
        captured: list[dict[str, object]] = []
        self._patch_module("resolve_config", lambda _: (_ for _ in ()).throw(AssertionError("resolve_config should not run")))
        self._patch_module("print_json", lambda data: captured.append(data))

        with TemporaryDirectory() as tmpdir:
            labware_root = Path(tmpdir) / "opentrons_shared_data" / "data" / "labware" / "definitions" / "2"
            entry = labware_root / "nest_96_wellplate_100ul_pcr_full_skirt"
            entry.mkdir(parents=True)
            (entry / "2.json").write_text(
                json.dumps(
                    {
                        "parameters": {
                            "loadName": "nest_96_wellplate_100ul_pcr_full_skirt",
                            "isTiprack": False,
                        },
                        "metadata": {
                            "displayName": "NEST 96 Well Plate PCR Full Skirt v2",
                            "displayCategory": "wellPlate",
                        },
                        "wells": {"A1": {"totalLiquidVolume": 100}},
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            (entry / "10.json").write_text(
                json.dumps(
                    {
                        "parameters": {
                            "loadName": "nest_96_wellplate_100ul_pcr_full_skirt",
                            "isTiprack": False,
                        },
                        "metadata": {
                            "displayName": "NEST 96 Well Plate PCR Full Skirt v10",
                            "displayCategory": "wellPlate",
                        },
                        "wells": {"A1": {"totalLiquidVolume": 150}},
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            self._patch_module("_labware_definitions_dir", lambda: labware_root)

            rc = main(["search-labware", "PCR full skirt", "--limit", "5"])

        self.assertEqual(rc, 0)
        self.assertEqual(captured[0]["query"], "PCR full skirt")
        self.assertEqual(captured[0]["count"], 1)
        self.assertEqual(captured[0]["results"][0]["displayName"], "NEST 96 Well Plate PCR Full Skirt v10")
        self.assertEqual(captured[0]["results"][0]["maxVolumeUl"], 150)

    def test_deploy_and_run_rejects_invalid_rtp_values_json(self) -> None:
        with TemporaryDirectory() as tmpdir:
            protocol_path = Path(tmpdir) / "protocol.py"
            protocol_path.write_text("print('hello')\n", encoding="utf-8")

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as ctx:
                    main(
                        [
                            "deploy-and-run",
                            str(protocol_path),
                            "--rtp-values",
                            "{not valid json}",
                        ]
                    )

        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("--rtp-values", stderr.getvalue())
        self.assertIn("invalid JSON object", stderr.getvalue())

    def test_poll_analysis_returns_after_completed_summary(self) -> None:
        responses = iter(
            [
                {"data": {"analysisSummaries": [{"status": "running"}]}},
                {"data": {"analysisSummaries": [{"status": "completed"}]}},
            ]
        )
        calls: list[str] = []

        def fake_send_request(config, method, path, **kwargs):
            calls.append(path)
            payload = next(responses)
            return 200, {}, json.dumps(payload).encode("utf-8")

        self._patch_module("send_request", fake_send_request)

        proto = poll_analysis(ConnectionConfig(host="robot"), "proto-key", timeout=5, interval=0)

        self.assertEqual(proto["analysisSummaries"][0]["status"], "completed")
        self.assertEqual(calls, ["/protocols/proto-key", "/protocols/proto-key"])

    def test_deploy_and_run_forwards_upload_and_run_parameters(self) -> None:
        captured: list[dict[str, object]] = []
        responses = {
            ("POST", "/protocols"): {"data": {"id": "protocol-1", "key": "proto-key"}},
            ("POST", "/runs"): {"data": {"id": "run-1"}},
            ("POST", "/runs/run-1/actions"): {"data": {"id": "action-1"}},
        }

        def fake_send_request(config, method, path, *, json_body=None, binary_body=None, extra_headers=None):
            captured.append(
                {
                    "method": method,
                    "path": path,
                    "json_body": json_body,
                    "binary_body": binary_body,
                    "extra_headers": dict(extra_headers or {}),
                }
            )
            payload = responses.get((method, path))
            if payload is None:
                raise AssertionError(f"Unexpected request: {method} {path}")
            return 200, {}, json.dumps(payload).encode("utf-8")

        self._patch_module("send_request", fake_send_request)
        self._patch_module("poll_analysis", lambda *args, **kwargs: {"analysisSummaries": [{"status": "completed"}]})
        self._patch_module("print_json", lambda data: None)

        with TemporaryDirectory() as tmpdir:
            protocol_path = Path(tmpdir) / "protocol.py"
            protocol_path.write_text("print('hello')\n", encoding="utf-8")
            args = argparse.Namespace(
                files=[str(protocol_path)],
                key="custom-key",
                protocol_kind="custom-protocol",
                rtp_values='{"sampleVolume": 25}',
                rtp_files='{"csv": "params.csv"}',
                analysis_timeout=17,
                analysis_interval=3,
            )

            rc = handle_deploy_and_run(args, ConnectionConfig(host="robot"))

        self.assertEqual(rc, 0)
        upload_call = captured[0]
        self.assertEqual(upload_call["path"], "/protocols")
        self.assertIn(b'name="key"', upload_call["binary_body"])
        self.assertIn(b'name="protocolKind"', upload_call["binary_body"])
        self.assertIn(b"custom-protocol", upload_call["binary_body"])
        self.assertIn(b"name=\"runTimeParameterValues\"", upload_call["binary_body"])

        run_call = captured[1]
        self.assertEqual(run_call["path"], "/runs")
        self.assertEqual(run_call["json_body"]["data"]["protocolId"], "protocol-1")
        self.assertEqual(run_call["json_body"]["data"]["runTimeParameterValues"], {"sampleVolume": 25})
        self.assertEqual(run_call["json_body"]["data"]["runTimeParameterFiles"], {"csv": "params.csv"})

        play_call = captured[2]
        self.assertEqual(play_call["path"], "/runs/run-1/actions")
        self.assertEqual(play_call["json_body"], {"data": {"actionType": "play"}})

    def test_watch_run_timeout_includes_status_changes(self) -> None:
        responses = iter(
            [
                {"data": {"status": "running"}},
                {"data": {"status": "running"}},
            ]
        )
        captured: list[dict[str, object]] = []

        def fake_send_request(config, method, path, **kwargs):
            payload = next(responses)
            return 200, {}, json.dumps(payload).encode("utf-8")

        self._patch_module("send_request", fake_send_request)
        self._patch_module("print_json", lambda data: captured.append(data))
        self._patch_time_attr("monotonic", iter([0.0, 0.0, 0.4, 1.2, 1.2]).__next__)
        self._patch_time_attr("sleep", lambda _: None)

        rc = handle_watch_run(argparse.Namespace(run_id="run-1", interval=1, timeout=1), ConnectionConfig(host="robot"))

        self.assertEqual(rc, 2)
        self.assertGreaterEqual(len(captured), 2)
        self.assertEqual(captured[-1]["error"], "timeout")
        self.assertEqual(captured[-1]["final_status"], "running")
        self.assertEqual(captured[-1]["elapsed_seconds"], 1)
        self.assertEqual(captured[-1]["status_changes"][0]["status"], "running")

    def test_deck_check_warns_on_labware_and_blocks_missing_fixture(self) -> None:
        captured: list[dict[str, object]] = []

        def fake_send_request(config, method, path, **kwargs):
            if method == "GET" and path == "/deck_configuration":
                return (
                    200,
                    {},
                    json.dumps(
                        {
                            "data": {
                                "cutoutFixtures": [
                                    {"cutoutFixtureId": "singleCenterSlot", "cutoutId": "cutoutC2"},
                                    {"cutoutFixtureId": "trashBinAdapter", "cutoutId": "cutoutA3"},
                                ]
                            }
                        }
                    ).encode("utf-8"),
                )
            raise AssertionError(f"Unexpected request: {method} {path}")

        self._patch_module("send_request", fake_send_request)
        self._patch_module("print_json", lambda data: captured.append(data))

        with TemporaryDirectory() as tmpdir:
            protocol_path = Path(tmpdir) / "protocol.py"
            protocol_path.write_text(
                "\n".join(
                    [
                        "from opentrons import protocol_api",
                        "",
                        'metadata = {"protocolName": "Deck Check"}',
                        'requirements = {"robotType": "Flex", "apiLevel": "2.22"}',
                        "",
                        "def run(protocol: protocol_api.ProtocolContext) -> None:",
                        '    protocol.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "C2")',
                        '    protocol.load_trash_bin("A3")',
                        '    protocol.load_module(SomeModule, "D1")',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            rc = handle_deck_check(argparse.Namespace(protocol_file=str(protocol_path)), ConnectionConfig(host="robot"))

        self.assertEqual(rc, 1)
        result = captured[0]
        self.assertTrue(any(item["slot"] == "C2" and item["issue"] == "labware_not_confirmed" for item in result["warnings"]))
        self.assertTrue(any(item["slot"] == "A3" and item["kind"] == "trash_bin" for item in result["matches"]))
        self.assertTrue(any(item["slot"] == "D1" and item["issue"] == "missing_required_fixture" for item in result["errors"]))
        self.assertFalse(any(item["slot"] == "C2" for item in result["matches"]))

    def test_deck_check_matches_labware_when_load_name_is_available(self) -> None:
        captured: list[dict[str, object]] = []

        def fake_send_request(config, method, path, **kwargs):
            if method == "GET" and path == "/deck_configuration":
                return (
                    200,
                    {},
                    json.dumps(
                        {
                            "data": {
                                "cutoutFixtures": [
                                    {
                                        "cutoutFixtureId": "singleCenterSlot",
                                        "cutoutId": "cutoutC2",
                                        "loadName": "nest-96-wellplate-100ul-pcr-full-skirt-v2",
                                    }
                                ]
                            }
                        }
                    ).encode("utf-8"),
                )
            raise AssertionError(f"Unexpected request: {method} {path}")

        self._patch_module("send_request", fake_send_request)
        self._patch_module("print_json", lambda data: captured.append(data))

        with TemporaryDirectory() as tmpdir:
            protocol_path = Path(tmpdir) / "protocol.py"
            protocol_path.write_text(
                "\n".join(
                    [
                        "from opentrons import protocol_api",
                        "",
                        'metadata = {"protocolName": "Deck Check"}',
                        'requirements = {"robotType": "Flex", "apiLevel": "2.22"}',
                        "",
                        "def run(protocol: protocol_api.ProtocolContext) -> None:",
                        '    protocol.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "C2")',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            rc = handle_deck_check(argparse.Namespace(protocol_file=str(protocol_path)), ConnectionConfig(host="robot"))

        self.assertEqual(rc, 0)
        result = captured[0]
        self.assertTrue(any(item["slot"] == "C2" and item["kind"] == "labware" for item in result["matches"]))
        self.assertFalse(any(item["slot"] == "C2" for item in result["warnings"]))
        self.assertFalse(any(item["slot"] == "C2" for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
