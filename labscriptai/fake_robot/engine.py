"""Stateful fake Flex robot — run/command lifecycle + physical world model."""

from __future__ import annotations

import threading
import time
import uuid
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

from .protocol_script import build_script_from_protocol, inject_scenario_failures
from .scenarios import get_scenario


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _uid() -> str:
    return str(uuid.uuid4())


BLOCKING_STATUSES = {
    "running",
    "paused",
    "awaiting-recovery",
    "stop-requested",
    "blocked-by-open-door",
}
TERMINAL_STATUSES = {"succeeded", "failed", "stopped", "awaiting-recovery", "blocked-by-open-door"}
COMMAND_TERMINAL = {"succeeded", "failed"}


class FakeRobotEngine:
    def __init__(self, scenario_id: str = "healthy", *, tick_s: float = 0.05) -> None:
        self._lock = threading.RLock()
        self.tick_s = tick_s
        self.scenario_id = scenario_id
        self.world: dict[str, Any] = {}
        self.scenario_meta: dict[str, Any] = {}
        self.protocols: dict[str, dict[str, Any]] = {}
        self.runs: dict[str, dict[str, Any]] = {}
        self.commands: dict[str, list[dict[str, Any]]] = {}
        self.maintenance_runs: dict[str, dict[str, Any]] = {}
        self.maintenance_commands: dict[str, list[dict[str, Any]]] = {}
        self._worker: threading.Thread | None = None
        self._stop_worker = threading.Event()
        self.apply_scenario(scenario_id)

    # ------------------------------------------------------------------ admin
    def apply_scenario(self, scenario_id: str) -> dict[str, Any]:
        # Stop worker without holding the lock — worker needs the lock to exit its loop.
        self._stop_worker.set()
        worker = self._worker
        if worker and worker.is_alive():
            worker.join(timeout=3.0)

        with self._lock:
            self._stop_worker = threading.Event()
            scenario = get_scenario(scenario_id)
            self.scenario_id = scenario["id"]
            self.world = deepcopy(scenario["world"])
            self.scenario_meta = deepcopy(scenario.get("meta") or {})
            self.protocols.clear()
            self.runs.clear()
            self.commands.clear()
            self.maintenance_runs.clear()
            self.maintenance_commands.clear()
            self._worker = None
            return {
                "scenario_id": self.scenario_id,
                "description": scenario["description"],
                "meta": self.scenario_meta,
            }

    def snapshot_admin(self) -> dict[str, Any]:
        with self._lock:
            return {
                "scenario_id": self.scenario_id,
                "meta": deepcopy(self.scenario_meta),
                "world": {
                    "door_status": self.world.get("door_status"),
                    "estop_status": self.world.get("estop_status"),
                    "left_tip_attached": self.world.get("left_tip_attached"),
                    "tip_wells_present": deepcopy(self.world.get("tip_wells_present") or {}),
                    "liquid_present": deepcopy(self.world.get("liquid_present") or {}),
                },
                "runs": [
                    {"id": r["id"], "status": r["status"], "protocolId": r.get("protocolId")}
                    for r in self.runs.values()
                ],
            }

    def backdate_commands(
        self,
        run_id: str,
        minutes: float,
        command_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Shift completedAt/startedAt of matching commands into the past (time-window tests)."""
        types = set(command_types or ["dispense", "dispenseInPlace"])
        delta = timedelta(minutes=float(minutes))
        shifted = 0
        with self._lock:
            if run_id not in self.runs:
                raise FakeRobotHttpError(404, {"errors": [{"detail": f"unknown run {run_id}"}]})
            for cmd in self.commands.get(run_id, []):
                if cmd.get("commandType") not in types:
                    continue
                for key in ("completedAt", "startedAt"):
                    raw = cmd.get(key)
                    if not raw:
                        continue
                    try:
                        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
                    except ValueError:
                        continue
                    cmd[key] = (dt - delta).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                shifted += 1
        return {"ok": True, "shifted": shifted, "minutes": minutes}

    # ------------------------------------------------------------------ health / instruments
    def health(self) -> dict[str, Any]:
        return {
            "name": "FakeSilabrobot",
            "robot_model": "OT-3 Standard",
            "api_version": "9.0.0",
            "fw_version": "68",
            "board_revision": "FLEX_B2",
            "logs": ["/logs/api.log", "/logs/server.log"],
            "system_version": "v0.9.14-fake",
            "maximum_protocol_api_version": [2, 28],
            "minimum_protocol_api_version": [2, 15],
            "robot_serial": "FAKEFLEX0001",
            "disk_details": {"systemAvailableMb": 8000.0, "imagesDirectorySizeMb": 1.0},
            "links": {"apiLog": "/logs/api.log", "apiSpec": "/openapi.json"},
            "fake_robot": True,
            "scenario_id": self.scenario_id,
        }

    def instruments(self) -> dict[str, Any]:
        with self._lock:
            tip = bool(self.world.get("left_tip_attached"))
            data = [
                {
                    "mount": "left",
                    "instrumentType": "pipette",
                    "instrumentModel": "p1000_single_v3.6",
                    "serialNumber": "FAKEP1KS0001",
                    "subsystem": "pipette_left",
                    "ok": True,
                    "firmwareVersion": "68",
                    "data": {
                        "channels": 1,
                        "min_volume": 5.0,
                        "max_volume": 1000.0,
                        "calibratedOffset": {
                            "offset": {"x": 0.0, "y": 0.0, "z": 0.0},
                            "source": "user",
                            "last_modified": "2024-09-27T07:41:06.045775Z",
                            "reasonability_check_failures": [],
                        },
                    },
                    "instrumentName": "p1000_single_flex",
                    "state": {"tipDetected": tip},
                    # also expose flat tipDetected for looser parsers
                    "tipDetected": tip,
                },
                {
                    "mount": "right",
                    "instrumentType": "pipette",
                    "instrumentModel": "p1000_multi_v3.5",
                    "serialNumber": "FAKEP1KM0001",
                    "subsystem": "pipette_right",
                    "ok": True,
                    "firmwareVersion": "68",
                    "data": {"channels": 8, "min_volume": 5.0, "max_volume": 1000.0},
                    "instrumentName": "p1000_multi_flex",
                    "state": {"tipDetected": False},
                    "tipDetected": False,
                },
                {
                    "mount": "extension",
                    "instrumentType": "gripper",
                    "instrumentModel": "gripperV1.3",
                    "serialNumber": "FAKEGRP0001",
                    "subsystem": "gripper",
                    "ok": True,
                    "firmwareVersion": "68",
                    "data": {"jawState": "stopped"},
                },
            ]
            return {"data": data, "meta": {"cursor": 0, "totalLength": len(data)}}

    def door_status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "data": {
                    "status": self.world.get("door_status", "closed"),
                    "doorRequiredClosedForProtocol": True,
                }
            }

    def estop_status(self) -> dict[str, Any]:
        with self._lock:
            status = self.world.get("estop_status", "disengaged")
            return {
                "data": {
                    "status": status,
                    "leftEstopPhysicalStatus": status,
                    "rightEstopPhysicalStatus": "notPresent",
                }
            }

    def deck_configuration(self) -> dict[str, Any]:
        with self._lock:
            return {"data": deepcopy(self.world.get("deck") or {})}

    def modules(self) -> dict[str, Any]:
        with self._lock:
            mods = deepcopy(self.world.get("modules") or [])
            return {"data": mods, "meta": {"cursor": 0, "totalLength": len(mods)}}

    def labware_offsets(self) -> dict[str, Any]:
        return {
            "data": [
                {
                    "id": _uid(),
                    "createdAt": _now(),
                    "definitionUri": "opentrons/opentrons_flex_96_tiprack_1000ul/1",
                    "locationSequence": "anyLocation",
                    "vector": {"x": 0.0, "y": 0.0, "z": 0.0},
                },
                {
                    "id": _uid(),
                    "createdAt": _now(),
                    "definitionUri": "opentrons/nest_12_reservoir_15ml/1",
                    "locationSequence": "anyLocation",
                    "vector": {"x": 0.0, "y": 0.0, "z": 0.0},
                },
            ],
            "meta": {"cursor": 0, "totalLength": 2},
        }

    def camera(self) -> dict[str, Any]:
        return {"data": {"cameraEnabled": False, "liveStreamEnabled": False}}

    # ------------------------------------------------------------------ protocols / runs
    def list_protocols(self) -> dict[str, Any]:
        with self._lock:
            data = list(self.protocols.values())
            return {"data": data, "meta": {"cursor": 0, "totalLength": len(data)}}

    def upload_protocol(self, *, filename: str, content: bytes) -> dict[str, Any]:
        with self._lock:
            pid = _uid()
            text = content.decode("utf-8", errors="replace")
            derived = []
            try:
                derived = build_script_from_protocol(text)
            except Exception:
                derived = []
            protocol = {
                "id": pid,
                "createdAt": _now(),
                "files": [{"name": filename, "role": "main"}],
                "protocolKind": "python",
                "metadata": {"protocolName": filename},
                "robotType": "OT-3 Standard",
                "fake_source_excerpt": text[:2000],
                "_source": text,
                "_derived_script": derived,
            }
            self.protocols[pid] = protocol
            return {"data": {k: v for k, v in protocol.items() if not k.startswith("_")}}

    def list_runs(self) -> dict[str, Any]:
        with self._lock:
            data = [self._public_run(r) for r in self.runs.values()]
            data.sort(key=lambda r: r.get("createdAt") or "", reverse=True)
            return {"data": data, "meta": {"cursor": 0, "totalLength": len(data)}}

    def create_run(self, body: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            data = body.get("data") or body
            protocol_id = data.get("protocolId")
            if protocol_id and protocol_id not in self.protocols:
                raise FakeRobotHttpError(404, {"errors": [{"detail": f"protocol {protocol_id} not found"}]})
            for run in self.runs.values():
                if run.get("current") and run["status"] in BLOCKING_STATUSES:
                    raise FakeRobotHttpError(
                        409,
                        {
                            "errors": [
                                {
                                    "id": _uid(),
                                    "errorCode": "4000",
                                    "detail": "RunAlreadyActive: another run is blocking.",
                                    "errorType": "RunAlreadyActive",
                                }
                            ]
                        },
                    )
            for run in self.runs.values():
                run["current"] = False

            rid = _uid()
            pipette_id = _uid()
            tiprack_id = _uid()
            reservoir_id = _uid()
            plate_id = _uid()
            run = {
                "id": rid,
                "createdAt": _now(),
                "status": "idle",
                "current": True,
                "ok": True,
                "protocolId": protocol_id,
                "labwareOffsets": data.get("labwareOffsets") or [],
                "runTimeParameters": data.get("runTimeParameterValues") or [],
                "actions": [],
                "errors": [],
                "hasEverEnteredErrorRecovery": False,
                "currentlyRecoveringFrom": None,
                "pipettes": [
                    {
                        "id": pipette_id,
                        "pipetteName": "p1000_single_flex",
                        "mount": "left",
                    }
                ],
                "labware": [
                    {
                        "id": tiprack_id,
                        "loadName": "opentrons_flex_96_tiprack_1000ul",
                        "definitionUri": "opentrons/opentrons_flex_96_tiprack_1000ul/1",
                        "location": {"slotName": "B2"},
                    },
                    {
                        "id": reservoir_id,
                        "loadName": "nest_12_reservoir_15ml",
                        "definitionUri": "opentrons/nest_12_reservoir_15ml/1",
                        "location": {"slotName": "C2"},
                    },
                    {
                        "id": plate_id,
                        "loadName": "nest_96_wellplate_200ul_flat",
                        "definitionUri": "opentrons/nest_96_wellplate_200ul_flat/2",
                        "location": {"slotName": "D2"},
                    },
                ],
                "modules": [],
                "liquids": [],
                "liquidClasses": [],
                "outputFileIds": [],
                "_ids": {
                    "pipette": pipette_id,
                    "tiprack": tiprack_id,
                    "reservoir": reservoir_id,
                    "plate": plate_id,
                },
                "_script_index": 0,
                "_paused_for_recovery": False,
            }
            self.runs[rid] = run
            self.commands[rid] = []
            return {"data": self._public_run(run)}

    def get_run(self, run_id: str) -> dict[str, Any]:
        with self._lock:
            run = self._require_run(run_id)
            return {"data": self._public_run(run)}

    def list_commands(
        self,
        run_id: str,
        page_length: int = 20,
        cursor: int = 0,
    ) -> dict[str, Any]:
        with self._lock:
            self._require_run(run_id)
            cmds = self.commands.get(run_id, [])
            start = max(0, int(cursor))
            limit = max(1, int(page_length))
            page = cmds[start : start + limit]
            return {
                "data": [self._public_command(c) for c in page],
                "meta": {"cursor": start, "totalLength": len(cmds)},
            }

    def get_command(self, run_id: str, command_id: str) -> dict[str, Any]:
        with self._lock:
            self._require_run(run_id)
            for cmd in self.commands.get(run_id, []):
                if cmd["id"] == command_id:
                    return {"data": self._public_command(cmd)}
            raise FakeRobotHttpError(404, {"errors": [{"detail": "command not found"}]})

    def post_action(self, run_id: str, body: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            run = self._require_run(run_id)
            action_type = ((body.get("data") or body).get("actionType") or "").lower()
            action = {
                "id": _uid(),
                "createdAt": _now(),
                "actionType": action_type,
            }
            run["actions"].append(action)

            # Real Flex uses resume-from-recovery after fixit; treat like play.
            if action_type in {"play", "resume-from-recovery"}:
                if self.world.get("door_status") == "open":
                    run["status"] = "blocked-by-open-door"
                    return {"data": action}
                if self.world.get("estop_status") not in (None, "disengaged"):
                    raise FakeRobotHttpError(
                        409,
                        {
                            "errors": [
                                {
                                    "errorType": "EStopActivatedError",
                                    "detail": "E-stop is engaged",
                                    "errorCode": "3000",
                                }
                            ]
                        },
                    )
                if run["status"] in {"idle", "paused", "awaiting-recovery", "blocked-by-open-door"}:
                    # First play: prefer protocol-derived script over scenario default.
                    if run["status"] == "idle" and not run.get("_script_bound"):
                        self._bind_run_script(run)
                    # Resume from recovery clears recovery marker.
                    if run["status"] == "awaiting-recovery" or action_type == "resume-from-recovery":
                        run["currentlyRecoveringFrom"] = None
                        run["_paused_for_recovery"] = False
                        # Skip the failed script step on resume after fixit.
                        run["_script_index"] = max(run.get("_script_index", 0), 0)
                        failed = self._last_failed_command(run_id)
                        if failed and not run.get("_resume_after_fixit"):
                            # Standard OT behavior: failed command is not auto-retried
                            # unless recovery inserted fixit steps; advance past it.
                            run["_script_index"] = run.get("_script_index", 0) + 1
                        run["_resume_after_fixit"] = False
                    run["status"] = "running"
                    run["startedAt"] = run.get("startedAt") or _now()
                    self._ensure_worker()
            elif action_type == "pause":
                if run["status"] == "running":
                    run["status"] = "paused"
            elif action_type == "stop":
                run["status"] = "stop-requested"
                run["status"] = "stopped"
                run["completedAt"] = _now()
                run["current"] = False
            else:
                raise FakeRobotHttpError(400, {"errors": [{"detail": f"unknown action {action_type}"}]})
            return {"data": action}

    def post_command(self, run_id: str, body: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            run = self._require_run(run_id)
            payload = body.get("data") or body
            command_type = payload.get("commandType")
            params = deepcopy(payload.get("params") or {})
            intent = payload.get("intent") or "protocol"
            if run["status"] not in {
                "idle",
                "running",
                "paused",
                "awaiting-recovery",
                "stop-requested",
            }:
                raise FakeRobotHttpError(
                    409,
                    {"errors": [{"detail": f"cannot enqueue command while status={run['status']}"}]},
                )
            cmd = self._new_command(command_type, params, intent=intent)
            self.commands.setdefault(run_id, []).append(cmd)
            # Execute fixit / maintenance-like commands immediately.
            self._execute_command(run, cmd)
            return {"data": self._public_command(cmd)}

    # ------------------------------------------------------------------ maintenance
    def create_maintenance_run(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            mid = _uid()
            run = {
                "id": mid,
                "createdAt": _now(),
                "status": "idle",
                "current": True,
                "ok": True,
                "pipettes": [],
                "labware": [],
                "errors": [],
            }
            self.maintenance_runs[mid] = run
            self.maintenance_commands[mid] = []
            return {"data": run}

    def get_maintenance_run(self, run_id: str) -> dict[str, Any]:
        with self._lock:
            run = self.maintenance_runs.get(run_id)
            if not run:
                raise FakeRobotHttpError(404, {"errors": [{"detail": "maintenance run not found"}]})
            return {"data": run}

    def post_maintenance_command(self, run_id: str, body: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if run_id not in self.maintenance_runs:
                raise FakeRobotHttpError(404, {"errors": [{"detail": "maintenance run not found"}]})
            payload = body.get("data") or body
            cmd = self._new_command(
                payload.get("commandType"),
                deepcopy(payload.get("params") or {}),
                intent=payload.get("intent") or "setup",
            )
            # Simple tip drop support
            if cmd["commandType"] in {"dropTip", "dropTipInPlace"}:
                self.world["left_tip_attached"] = False
            if cmd["commandType"] == "loadPipette":
                self.maintenance_runs[run_id].setdefault("pipettes", []).append(
                    {
                        "id": params_id(cmd),
                        "pipetteName": cmd["params"].get("pipetteName"),
                        "mount": cmd["params"].get("mount"),
                    }
                )
            cmd["status"] = "succeeded"
            cmd["completedAt"] = _now()
            cmd["result"] = {}
            self.maintenance_commands.setdefault(run_id, []).append(cmd)
            return {"data": self._public_command(cmd)}

    def list_maintenance_commands(
        self,
        run_id: str,
        page_length: int = 20,
        cursor: int = 0,
    ) -> dict[str, Any]:
        with self._lock:
            cmds = self.maintenance_commands.get(run_id, [])
            start = max(0, int(cursor))
            limit = max(1, int(page_length))
            return {
                "data": [self._public_command(c) for c in cmds[start : start + limit]],
                "meta": {"cursor": start, "totalLength": len(cmds)},
            }

    def _bind_run_script(self, run: dict[str, Any]) -> None:
        """Attach execution script for this run (protocol-derived when available)."""
        protocol_id = run.get("protocolId")
        protocol = self.protocols.get(protocol_id or "") or {}
        derived = protocol.get("_derived_script") or []
        motion_types = {"pickUpTip", "liquidProbe", "aspirate", "dispense", "dropTip"}
        derived_has_motion = any(step.get("commandType") in motion_types for step in derived)
        # Tiny upload stubs (tests) parse to load-only scripts — keep scenario script then.
        if derived and derived_has_motion:
            script = inject_scenario_failures(derived, self.scenario_id)
        else:
            script = inject_scenario_failures(
                deepcopy(self.world.get("script") or []),
                self.scenario_id,
            )
        run["_script"] = script
        run["_script_bound"] = True
        run["_script_index"] = 0

    # ------------------------------------------------------------------ worker
    def _ensure_worker(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._stop_worker.clear()
        self._worker = threading.Thread(target=self._run_loop, name="fake-robot-worker", daemon=True)
        self._worker.start()

    def _run_loop(self) -> None:
        while not self._stop_worker.is_set():
            progressed = False
            with self._lock:
                for run in list(self.runs.values()):
                    if run["status"] != "running":
                        continue
                    progressed = True
                    script = run.get("_script") or self.world.get("script") or []
                    idx = run.get("_script_index", 0)
                    if idx >= len(script):
                        run["status"] = "succeeded"
                        run["completedAt"] = _now()
                        run["current"] = False
                        continue
                    step = script[idx]
                    # Synthetic hold: pause with tip/state preserved (decision-bench 08/09/10).
                    if step.get("commandType") == "_pause":
                        run["status"] = "paused"
                        run["_script_index"] = idx + 1
                        continue
                    params = self._materialize_params(run, step)
                    cmd = self._new_command(step["commandType"], params, intent="protocol")
                    if step.get("inject_error"):
                        cmd["_inject_error"] = deepcopy(step["inject_error"])
                    if step.get("force_no_tip"):
                        cmd["_force_no_tip"] = True
                    self.commands.setdefault(run["id"], []).append(cmd)
                    self._execute_command(run, cmd)
                    if cmd["status"] == "failed":
                        policy = (cmd.get("error") or {}).get("recovery_policy") or self._policy_from_notes(
                            cmd
                        )
                        if policy == "FAIL_RUN":
                            run["status"] = "failed"
                            run["completedAt"] = _now()
                            run["current"] = False
                            run["errors"] = [
                                {
                                    "id": _uid(),
                                    "createdAt": _now(),
                                    "isDefined": False,
                                    "errorType": "ExceptionInProtocolError",
                                    "errorCode": "4000",
                                    "detail": (
                                        "ProtocolCommandFailedError [line 1]: "
                                        f"{(cmd.get('error') or {}).get('errorType')}: "
                                        f"{(cmd.get('error') or {}).get('detail')}"
                                    ),
                                    "errorInfo": {},
                                    "wrappedErrors": [deepcopy(cmd.get("error") or {})],
                                }
                            ]
                        else:
                            run["status"] = "awaiting-recovery"
                            run["hasEverEnteredErrorRecovery"] = True
                            run["currentlyRecoveringFrom"] = {
                                "commandId": cmd["id"],
                                "error": deepcopy(cmd.get("error") or {}),
                            }
                            run["_paused_for_recovery"] = True
                        # keep script index pointing at failed step
                        continue
                    run["_script_index"] = idx + 1
            if not progressed:
                time.sleep(self.tick_s)
            else:
                time.sleep(self.tick_s)

    def _execute_command(self, run: dict[str, Any], cmd: dict[str, Any]) -> None:
        cmd["status"] = "running"
        cmd["startedAt"] = _now()
        ctype = cmd["commandType"]
        params = cmd.get("params") or {}
        ids = run.get("_ids") or {}

        # Injected failure (protocol script)
        if cmd.get("_inject_error"):
            err = deepcopy(cmd["_inject_error"])
            # tip missing side effects
            if ctype == "pickUpTip":
                well = params.get("wellName")
                tips = self.world.setdefault("tip_wells_present", {})
                if well is not None:
                    tips[well] = False
                if self.world.get("attach_tip_on_failed_pickup"):
                    self.world["left_tip_attached"] = True
            policy = err.pop("recovery_policy", "WAIT_FOR_RECOVERY")
            notes = err.pop("notes", None)
            err["id"] = _uid()
            err["createdAt"] = _now()
            cmd["error"] = {**err, "recovery_policy": policy}
            if notes:
                cmd["notes"] = notes
            cmd["status"] = "failed"
            cmd["completedAt"] = _now()
            cmd["result"] = None
            if cmd.get("intent") == "fixit":
                # fixit failures do not change run status here
                pass
            return

        try:
            if ctype == "home":
                result = {}
            elif ctype == "loadLabware":
                result = {"labwareId": self._labware_id_for_slot(run, params)}
            elif ctype == "loadPipette":
                result = {"pipetteId": ids.get("pipette")}
            elif ctype == "comment":
                result = {}
            elif ctype == "pickUpTip":
                result = self._do_pick_up_tip(run, cmd, params)
            elif ctype == "liquidProbe":
                result = self._do_liquid_probe(run, cmd, params)
            elif ctype in {"aspirate", "aspirateInPlace"}:
                if not self.world.get("left_tip_attached"):
                    raise CommandFailure(_tip_not_attached_error())
                well_key = self._well_key(params, run)
                if well_key and not self.world.get("liquid_present", {}).get(well_key, True):
                    raise CommandFailure(_liquid_error())
                result = {"volume": params.get("volume")}
            elif ctype in {"dispense", "dispenseInPlace"}:
                if not self.world.get("left_tip_attached"):
                    raise CommandFailure(_tip_not_attached_error())
                well_key = self._well_key(params, run)
                if well_key:
                    self.world.setdefault("liquid_present", {})[well_key] = True
                result = {"volume": params.get("volume")}
            elif ctype in {"dropTip", "dropTipInPlace"}:
                self.world["left_tip_attached"] = False
                result = {}
            elif ctype == "moveToAddressableAreaForDropTip":
                result = {}
            else:
                result = {}
            cmd["status"] = "succeeded"
            cmd["result"] = result
            cmd["completedAt"] = _now()
            if cmd.get("intent") == "fixit":
                run["_resume_after_fixit"] = True
        except CommandFailure as exc:
            err = deepcopy(exc.error)
            policy = err.pop("recovery_policy", "WAIT_FOR_RECOVERY")
            notes = err.pop("notes", None)
            err["id"] = _uid()
            err["createdAt"] = _now()
            cmd["error"] = {**err, "recovery_policy": policy}
            if notes:
                cmd["notes"] = notes
            cmd["status"] = "failed"
            cmd["completedAt"] = _now()
            cmd["result"] = None

    def _next_tip_well(self) -> str:
        tips = self.world.setdefault("tip_wells_present", {})
        order = [f"{c}{r}" for r in range(1, 13) for c in "ABCDEFGH"]
        for well in order:
            if tips.get(well, True):
                return well
        return "A1"

    def _do_pick_up_tip(self, run: dict[str, Any], cmd: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        if self.world.get("left_tip_attached"):
            raise CommandFailure(
                {
                    "errorType": "UnexpectedTipAttachError",
                    "errorCode": "3004",
                    "detail": "Tip already attached on pipette.",
                    "isDefined": True,
                    "errorInfo": {},
                    "wrappedErrors": [],
                    "notes": [
                        {
                            "noteKind": "debugErrorRecovery",
                            "shortMessage": "Handling this command failure with WAIT_FOR_RECOVERY.",
                            "longMessage": "Handling this command failure with WAIT_FOR_RECOVERY.",
                            "source": "execution",
                        }
                    ],
                    "recovery_policy": "WAIT_FOR_RECOVERY",
                }
            )
        well = params.get("wellName") or "auto"
        if well == "auto":
            well = self._next_tip_well()
            params["wellName"] = well
            cmd["params"] = params
        tips = self.world.setdefault("tip_wells_present", {})
        present = tips.get(well, True)
        if not present:
            # Auto-advance once (recovery may have consumed the scripted well).
            alt = self._next_tip_well()
            if alt != well and tips.get(alt, True):
                well = alt
                params["wellName"] = well
                cmd["params"] = params
            else:
                raise CommandFailure(_tip_error_dict())
        tips[well] = False
        self.world["left_tip_attached"] = True
        return {"tipVolume": 1000}

    def _do_liquid_probe(self, run: dict[str, Any], cmd: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        if cmd.get("_force_no_tip") or not self.world.get("left_tip_attached"):
            raise CommandFailure(_tip_not_attached_error())
        well_key = self._well_key(params, run)
        present = True
        if well_key is not None:
            present = bool(self.world.get("liquid_present", {}).get(well_key, True))
        if not present:
            raise CommandFailure(_liquid_error())
        height = (self.world.get("liquid_heights_mm") or {}).get(well_key, 10.0)
        return {"z_position": height, "position": {"x": 0, "y": 0, "z": height}}

    def _well_key(self, params: dict[str, Any], run: dict[str, Any]) -> str | None:
        well = params.get("wellName")
        if not well:
            return None
        slot = params.get("slotName")
        if not slot:
            labware_id = params.get("labwareId")
            for lw in run.get("labware") or []:
                if lw.get("id") == labware_id:
                    slot = (lw.get("location") or {}).get("slotName")
                    break
        if not slot:
            return well
        return f"{slot}.{well}"

    def _labware_id_for_slot(self, run: dict[str, Any], params: dict[str, Any]) -> str | None:
        slot = (params.get("location") or {}).get("slotName")
        for lw in run.get("labware") or []:
            if (lw.get("location") or {}).get("slotName") == slot:
                return lw.get("id")
        return None

    def _materialize_params(self, run: dict[str, Any], step: dict[str, Any]) -> dict[str, Any]:
        params = deepcopy(step.get("params") or {})
        ids = run.get("_ids") or {}
        ctype = step["commandType"]
        if ctype == "pickUpTip":
            params.setdefault("pipetteId", ids.get("pipette"))
            params.setdefault("labwareId", ids.get("tiprack"))
            params.pop("slotName", None)
            if params.get("wellName") in (None, "", "auto"):
                params["wellName"] = self._next_tip_well()
            params.setdefault(
                "wellLocation",
                {"origin": "top", "offset": {"x": 0.0, "y": 0.0, "z": 0.0}},
            )
        elif ctype == "liquidProbe":
            slot = params.pop("slotName", "C2")
            labware_id = ids.get("reservoir") if slot == "C2" else ids.get("plate")
            if slot == "D2":
                labware_id = ids.get("plate")
            params.setdefault("pipetteId", ids.get("pipette"))
            params.setdefault("labwareId", labware_id)
            params.setdefault(
                "wellLocation",
                {
                    "origin": "top",
                    "offset": {"x": 0.0, "y": 0.0, "z": 2.0},
                    "volumeOffset": 0.0,
                },
            )
        elif ctype in {"aspirate", "dispense"}:
            slot = params.pop("slotName", "C2")
            labware_id = ids.get("reservoir") if slot == "C2" else ids.get("plate")
            params.setdefault("pipetteId", ids.get("pipette"))
            params.setdefault("labwareId", labware_id)
            params.setdefault("flowRate", 716)
        elif ctype == "dropTip":
            params.setdefault("pipetteId", ids.get("pipette"))
            params.pop("slotName", None)
        elif ctype == "loadPipette":
            pass
        return params

    def _new_command(self, command_type: str, params: dict[str, Any], *, intent: str) -> dict[str, Any]:
        return {
            "id": _uid(),
            "createdAt": _now(),
            "commandType": command_type,
            "key": _uid(),
            "status": "queued",
            "params": params,
            "result": None,
            "error": None,
            "notes": [],
            "intent": intent,
        }

    def _public_run(self, run: dict[str, Any]) -> dict[str, Any]:
        out = {k: v for k, v in run.items() if not k.startswith("_")}
        return deepcopy(out)

    def _public_command(self, cmd: dict[str, Any]) -> dict[str, Any]:
        out = {k: v for k, v in cmd.items() if not k.startswith("_")}
        if out.get("error") and "recovery_policy" in out["error"]:
            err = dict(out["error"])
            err.pop("recovery_policy", None)
            out["error"] = err
        return deepcopy(out)

    def _require_run(self, run_id: str) -> dict[str, Any]:
        run = self.runs.get(run_id)
        if not run:
            raise FakeRobotHttpError(404, {"errors": [{"detail": f"run {run_id} not found"}]})
        return run

    def _last_failed_command(self, run_id: str) -> dict[str, Any] | None:
        for cmd in reversed(self.commands.get(run_id, [])):
            if cmd.get("status") == "failed":
                return cmd
        return None

    @staticmethod
    def _policy_from_notes(cmd: dict[str, Any]) -> str:
        for note in cmd.get("notes") or []:
            msg = f"{note.get('shortMessage', '')} {note.get('longMessage', '')}".upper()
            if "FAIL_RUN" in msg:
                return "FAIL_RUN"
        return "WAIT_FOR_RECOVERY"


class FakeRobotHttpError(Exception):
    def __init__(self, status: int, body: dict[str, Any]) -> None:
        super().__init__(str(body))
        self.status = status
        self.body = body


class CommandFailure(Exception):
    def __init__(self, error: dict[str, Any]) -> None:
        super().__init__(error.get("detail"))
        self.error = error


def params_id(cmd: dict[str, Any]) -> str:
    return cmd.get("id") or _uid()


def _tip_error_dict() -> dict[str, Any]:
    return {
        "errorType": "tipPhysicallyMissing",
        "errorCode": "3003",
        "detail": "No Tip Detected",
        "isDefined": True,
        "errorInfo": {},
        "wrappedErrors": [
            {
                "errorType": "PickUpTipTipNotAttachedError",
                "errorCode": "3005",
                "detail": "Error 3005 UNEXPECTED_TIP_REMOVAL (PickUpTipTipNotAttachedError)",
                "isDefined": False,
                "errorInfo": {},
                "wrappedErrors": [],
            }
        ],
        "notes": [
            {
                "noteKind": "debugErrorRecovery",
                "shortMessage": "Handling this command failure with WAIT_FOR_RECOVERY.",
                "longMessage": "Handling this command failure with WAIT_FOR_RECOVERY.",
                "source": "execution",
            }
        ],
        "recovery_policy": "WAIT_FOR_RECOVERY",
    }


def _liquid_error() -> dict[str, Any]:
    return {
        "errorType": "liquidNotFound",
        "errorCode": "2017",
        "detail": "Liquid Not Found",
        "isDefined": True,
        "errorInfo": {},
        "wrappedErrors": [
            {
                "errorType": "PipetteLiquidNotFoundError",
                "errorCode": "2017",
                "detail": "Liquid not found during probe.",
                "isDefined": False,
                "errorInfo": {"P_L": "19.749", "Z_L": "158.728"},
                "wrappedErrors": [],
            }
        ],
        "notes": [
            {
                "noteKind": "debugErrorRecovery",
                "shortMessage": "Handling this command failure with WAIT_FOR_RECOVERY.",
                "longMessage": "Handling this command failure with WAIT_FOR_RECOVERY.",
                "source": "execution",
            }
        ],
        "recovery_policy": "WAIT_FOR_RECOVERY",
    }


def _tip_not_attached_error() -> dict[str, Any]:
    return {
        "errorType": "TipNotAttachedError",
        "errorCode": "3005",
        "detail": "Pipette should have a tip attached, but does not.",
        "isDefined": False,
        "errorInfo": {},
        "wrappedErrors": [],
        "notes": [
            {
                "noteKind": "debugErrorRecovery",
                "shortMessage": "Handling this command failure with FAIL_RUN.",
                "longMessage": "Handling this command failure with FAIL_RUN.",
                "source": "execution",
            }
        ],
        "recovery_policy": "FAIL_RUN",
    }
