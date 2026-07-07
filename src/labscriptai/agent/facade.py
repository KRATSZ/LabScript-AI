"""Benchmark-compatible facade for the unified authoring loop."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from labscriptai.agent.loop import LabscriptAgentLoop, LoopResult
from labscriptai.agent.registry import build_default_registry
from labscriptai.agent.state import AgentState
from labscriptai.authoring.agent import _write_missing_metadata_files
from labscriptai.authoring.kb_context import KBContext, build_kb_context
from labscriptai.authoring.prompts import AUTHORING_AGENT_SYSTEM_PROMPT, AUTHORING_ROLE_PIPELINE_PROMPT
from labscriptai.authoring.skills import SkillLoader
from labscriptai.benchmark.derive_package import derive_package_from_protocol
from labscriptai.benchmark.package_validator import REQUIRED_PACKAGE_FILES
from labscriptai.benchmark.tasks import AuthoringTask
from labscriptai.benchmark.validators.models import CRITICAL_FAILURES
from labscriptai.benchmark.validators.opentrons import extract_protocol_refs
from labscriptai.runtime.trace import TraceEvent


class UnifiedAuthoringFacade:
    def __init__(
        self,
        *,
        client: Any,
        skill_loader: SkillLoader | None = None,
        max_steps: int = 12,
        skill_mode: str = "light",
        tool_profile: str = "kb",
        kb_context_mode: str = "full",
        protocol_only: bool = False,
    ) -> None:
        if kb_context_mode not in {"full", "compact", "compact_v2", "none"}:
            raise ValueError("kb_context_mode must be one of: full, compact, compact_v2, none")
        self.client = client
        self.skill_loader = skill_loader or SkillLoader()
        self.max_steps = max_steps
        self.skill_mode = skill_mode
        self.tool_profile = tool_profile
        self.kb_context_mode = kb_context_mode
        self.protocol_only = protocol_only
        self._last_kb_context: KBContext | None = None

    def run(
        self,
        *,
        task: AuthoringTask,
        package_dir: Path,
        trace_path: Path,
        opentrons_python: str | None = None,
        workspace_root: Path | None = None,
        simulation_timeout_sec: int = 180,
    ) -> LoopResult:
        permissions = set(_author_permissions(self.skill_mode, self.tool_profile))
        if self.tool_profile == "kb_strong" and self.kb_context_mode == "compact_v2":
            permissions.discard("protocol.search")
        state = AgentState.for_author(
            task=task,
            package_dir=package_dir,
            trace_path=trace_path,
            permissions=frozenset(permissions),
            required_files=("protocol.py",) if self.protocol_only else REQUIRED_PACKAGE_FILES,
        )
        registry = build_default_registry(
            skill_mode=self.skill_mode,
            tool_profile=self.tool_profile,
            opentrons_python=opentrons_python,
            workspace_root=workspace_root,
            simulation_timeout_sec=simulation_timeout_sec,
        )
        initial_messages = self._initial_messages(task)
        if self._last_kb_context is not None:
            state.trace.append(
                TraceEvent(
                    run_id=state.run_id,
                    event_type="memory_retrieval",
                    actor="system",
                    payload={
                        "source": "kb_strong_context",
                        **self._last_kb_context.to_prompt_payload(),
                    },
                    state_hash=state.stable_hash(),
                )
            )
        loop = LabscriptAgentLoop(
            client=self.client,
            registry=registry,
            max_steps=self.max_steps,
            initial_messages=initial_messages,
        )
        result = loop.run(state)
        final_state = self._align_manifest_to_protocol(result.final_state)
        completed = result.completed and all(
            (final_state.package.dir / name).exists()
            for name in (("protocol.py",) if self.protocol_only else REQUIRED_PACKAGE_FILES)
        )
        aligned = LoopResult(final_state=final_state, completed=completed)
        self._write_stats(aligned.final_state)
        return aligned

    def run_to_files(self, *, task: AuthoringTask, work_dir: Path, **kwargs: Any) -> dict[str, str]:
        result = self.run(
            task=task,
            package_dir=work_dir / "package",
            trace_path=work_dir / "trace.jsonl",
            **kwargs,
        )
        if self.protocol_only:
            derive_package_from_protocol(
                result.final_state.package.dir,
                task,
                model_id=str(getattr(getattr(self.client, "config", None), "model", "unknown")),
                scaffold_id="unified-py-derived-v0.4",
            )
        else:
            _write_missing_metadata_files(result.final_state.package.dir, task)
        missing = [
            name for name in REQUIRED_PACKAGE_FILES if not (result.final_state.package.dir / name).exists()
        ]
        if missing:
            raise ValueError(f"unified authoring agent did not produce required files: {missing}")
        files = {
            name: (result.final_state.package.dir / name).read_text(encoding="utf-8")
            for name in REQUIRED_PACKAGE_FILES
        }
        stats_path = result.final_state.package.dir / "authoring_stats.json"
        if stats_path.exists():
            files["authoring_stats.json"] = stats_path.read_text(encoding="utf-8")
        if result.final_state.trace_path.exists():
            files["trace.jsonl"] = result.final_state.trace_path.read_text(encoding="utf-8")
        return files

    def _write_stats(self, state: AgentState) -> None:
        payload = {
            "run_id": state.run_id,
            "task_id": state.task_spec.task_id,
            "phase": state.phase,
            "tool_calls": state.counters.tool_calls,
            "skill_loads": state.counters.skill_loads,
            "simulator_calls": state.counters.simulator_calls,
            "notes": [],
            "input_tokens": int(getattr(self.client, "input_tokens", state.counters.input_tokens)),
            "output_tokens": int(getattr(self.client, "output_tokens", state.counters.output_tokens)),
            "total_tokens": int(getattr(self.client, "total_tokens", state.counters.total_tokens)),
            "package_ready": state.package_ready,
        }
        if self._last_kb_context is not None:
            payload.update(self._last_kb_context.to_stats())
        (state.package.dir / "authoring_stats.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

    def _initial_messages(self, task: AuthoringTask) -> list[dict[str, Any]]:
        kb_context: KBContext | None = None
        if self.tool_profile == "kb_strong" and self.kb_context_mode != "none":
            kb_context = build_kb_context(task, context_mode=self.kb_context_mode)
            self._last_kb_context = kb_context
        else:
            self._last_kb_context = None

        if self.tool_profile not in {"kb", "kb_strong"}:
            skill_catalog = "(KB disabled for this run)"
        elif self.skill_mode == "off":
            skill_catalog = "(skills disabled for this run)"
        elif self.tool_profile == "kb_strong":
            skill_catalog = "task templates: dilution, serial_dilution, plate_transfer, normalization, pcr_setup"
        elif self.skill_mode == "light":
            skill_catalog = "common_errors, deck_layout"
        else:
            skill_catalog = self.skill_loader.get_catalog() or "(none)"
        required_files = ["protocol.py"] if self.protocol_only else list(REQUIRED_PACKAGE_FILES)
        user_payload: dict[str, Any] = {
            "task_id": task.task_id,
            "difficulty": task.difficulty,
            "prompt": task.prompt,
            "required_package_files": required_files,
            "manifest_v04_rules": {
                "deck": (
                    "manifest.deck must be an object with labware and instruments arrays. "
                    "Every protocol.load_labware(load_name, slot) must appear as "
                    '{"load_name": load_name, "slot": string_slot}. '
                    "Every protocol.load_instrument(name, mount) must appear as "
                    '{"instrument_name": name, "mount": mount}.'
                ),
                "reagents": "manifest.reagents must be a list, not a mapping.",
                "tips": "manifest.tips must include numeric tips_required and tips_available.",
                "critical_failures": (
                    "manifest.critical_failures may only contain these strings: "
                    + ", ".join(CRITICAL_FAILURES)
                ),
            },
            "semantic_output_contract": _semantic_output_contract(protocol_only=self.protocol_only),
        }
        if self.protocol_only:
            user_payload["package_format_instruction"] = (
                "Write only protocol.py. Do not write manifest.json or setup_card.html; "
                "the benchmark harness will derive those sidecars from protocol.py."
            )
        else:
            user_payload["package_format_instruction"] = (
                "Use the current three-piece v0.4 package even if the task text "
                "mentions any older package format."
            )
        if kb_context is not None:
            user_payload["kb_strong_context"] = kb_context.to_prompt_payload()
        return [
            {
                "role": "system",
                "content": _system_prompt(skill_catalog=skill_catalog, protocol_only=self.protocol_only),
            },
            {
                "role": "user",
                "content": json.dumps(user_payload, ensure_ascii=False),
            },
        ]

    def _align_manifest_to_protocol(self, state: AgentState) -> AgentState:
        package_dir = state.package.dir
        manifest_path = package_dir / "manifest.json"
        protocol_path = package_dir / "protocol.py"
        if not manifest_path.exists() or not protocol_path.exists():
            return state.refresh_package()
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return state.refresh_package()
        if not isinstance(manifest, dict):
            return state.refresh_package()

        protocol_labware, protocol_instruments = extract_protocol_refs(protocol_path)
        manifest["schema_version"] = "0.4"
        manifest["deck"] = _aligned_deck(
            manifest.get("deck"),
            protocol_labware=protocol_labware,
            protocol_instruments=protocol_instruments,
        )
        manifest["reagents"] = _reagents_as_list(manifest.get("reagents"))
        manifest["tips"] = _aligned_tips(manifest.get("tips"), manifest.get("budget"), protocol_labware)
        manifest["risk_flags"] = manifest.get("risk_flags") if isinstance(manifest.get("risk_flags"), list) else []
        manifest["critical_failures"] = _critical_failure_strings(manifest.get("critical_failures"))
        manifest["tool_permissions"] = (
            manifest.get("tool_permissions") if isinstance(manifest.get("tool_permissions"), list) else []
        )
        manifest["budget"] = _aligned_budget(manifest.get("budget"))
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return state.refresh_package()


def _author_permissions(skill_mode: str, tool_profile: str) -> frozenset[str]:
    permissions = {"package.read_write"}
    if tool_profile in {"simulate", "kb", "kb_strong"}:
        permissions.update({"package.validate", "package.simulate"})
    if tool_profile in {"kb", "kb_strong"}:
        permissions.update({"protocol.search", "memory.read_write.search"})
        if skill_mode != "off":
            permissions.add("skill.search_load")
    return frozenset(permissions)


def _system_prompt(*, skill_catalog: str, protocol_only: bool) -> str:
    role_pipeline = AUTHORING_ROLE_PIPELINE_PROMPT
    if not protocol_only:
        return AUTHORING_AGENT_SYSTEM_PROMPT.format(
            skill_catalog=skill_catalog,
            role_pipeline=role_pipeline,
        )
    return (
        "You are LabscriptAI's Opentrons protocol authoring agent.\n\n"
        "Goal: produce only protocol.py for the requested experiment. Do not write "
        "manifest.json or setup_card.html; benchmark tools will derive those files "
        "from protocol.py after the loop.\n\n"
        f"{role_pipeline}\n"
        "Use tools deliberately. Prefer concise domain rules and simulation when "
        "available. Never claim a simulation passed unless the simulator reports ok=true.\n\n"
        "Default to OT-2-compatible protocols unless the task explicitly asks for Flex. "
        "For generic transfers, use OT-2 numeric slots, p300_single_gen2, and OT-2 tip racks. "
        "Only use Flex pipettes/tipracks/deck slots when the task requires Flex.\n\n"
        "When using tools, return JSON:\n"
        '{"role":"Planner|Coder|Reviewer","tool_calls":[{"name":"tool_name","arguments":{...}}]}\n\n'
        "When protocol.py is written, return JSON:\n"
        '{"role":"Reviewer","final":{"package_ready":true,"notes":"short summary"}}\n\n'
        f"Available skills:\n{skill_catalog}\n"
    )


def _semantic_output_contract(*, protocol_only: bool = False) -> dict[str, Any]:
    return {
        "required_files": ["protocol.py"] if protocol_only else ["protocol.py", "setup_card.html", "manifest.json"],
        "manifest_schema_version": "0.4",
        "manifest_reagents": (
            "manifest.reagents must be a list; every item must include name. "
            "Use total_volume_ul or required_volume_ul for reagent totals."
        ),
        "manifest_tips": "tips_required and tips_available must be numeric.",
        "module_state_terms": [
            "pause",
            "open_lid",
            "deactivate_lid",
            "cool",
            "engage",
            "disengage",
        ],
        "controls_rule": (
            "If controls are already inside the requested sample wells, do not add them "
            "again to the sample count or transfer count."
        ),
        "field_precedence": "This contract wins over informal field names in the task prompt.",
    }


def _aligned_deck(
    deck: Any,
    *,
    protocol_labware: set[tuple[str, str]],
    protocol_instruments: set[tuple[str, str]],
) -> dict[str, Any]:
    modules: list[dict[str, Any]] = []
    if isinstance(deck, dict):
        raw_modules = deck.get("modules")
        if isinstance(raw_modules, list):
            modules = [dict(item) for item in raw_modules if isinstance(item, dict)]
    labware = [
        {"load_name": load_name, "slot": str(slot)}
        for load_name, slot in sorted(protocol_labware, key=lambda item: (str(item[1]), item[0]))
    ]
    instruments = [
        {"instrument_name": name, "mount": mount}
        for name, mount in sorted(protocol_instruments, key=lambda item: (item[1], item[0]))
    ]
    return {"labware": labware, "modules": modules, "instruments": instruments}


def _reagents_as_list(reagents: Any) -> list[dict[str, Any]]:
    if isinstance(reagents, list):
        return [dict(item) if isinstance(item, dict) else {"name": str(item)} for item in reagents]
    if isinstance(reagents, dict):
        items: list[dict[str, Any]] = []
        for name, value in reagents.items():
            if isinstance(value, dict):
                items.append({"name": str(name), **value})
            else:
                items.append({"name": str(name), "description": str(value)})
        return items
    return []


def _aligned_tips(tips: Any, budget: Any, protocol_labware: set[tuple[str, str]]) -> dict[str, Any]:
    tiprack_count = sum(1 for load_name, _slot in protocol_labware if "tiprack" in load_name.lower())
    tips_available = max(1, tiprack_count) * 96
    tips_required = _numeric_tip_value(tips) or _numeric_tip_value(budget) or 1
    return {
        "tips_required": int(tips_required),
        "tips_available": int(max(tips_required, tips_available)),
        "tip_racks": [
            {"labware": load_name, "slot": str(slot), "tips_available": 96}
            for load_name, slot in sorted(protocol_labware, key=lambda item: (str(item[1]), item[0]))
            if "tiprack" in load_name.lower()
        ],
    }


def _numeric_tip_value(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, dict):
        for key in ("tips_required", "total_tip_usage", "wells_used", "tips_used", "tips_per_run"):
            item = value.get(key)
            if isinstance(item, (int, float)) and not isinstance(item, bool):
                return int(item)
        for item in value.values():
            found = _numeric_tip_value(item)
            if found is not None:
                return found
    return None


def _critical_failure_strings(value: Any) -> list[str]:
    allowed = set(CRITICAL_FAILURES)
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        if isinstance(item, str) and item in allowed:
            normalized.append(item)
        elif item:
            normalized.append("other")
    return sorted(set(normalized), key=normalized.index)


def _aligned_budget(budget: Any) -> dict[str, Any]:
    result = dict(budget) if isinstance(budget, dict) else {}
    result["attempts"] = int(result.get("attempts", 1)) if isinstance(result.get("attempts", 1), int) else 1
    result["wall_min"] = int(result.get("wall_min", 30)) if isinstance(result.get("wall_min", 30), int) else 30
    result["tokens"] = int(result.get("tokens", 24000)) if isinstance(result.get("tokens", 24000), int) else 24000
    return result
