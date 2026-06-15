"""Small authoring benchmark pilot for generating protocol packages."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

from .package_validator import CRITICAL_FAILURES, REQUIRED_PACKAGE_FILES, validate_package
from .derive_package import derive_package_from_protocol
from .score_record import score_record_from_validation
from .tasks import AuthoringTask, DIFFICULTY_STRATA, load_authoring_tasks, select_stratified_tasks
from labscriptai.authoring.agent import AuthoringAgent, OpenAICompatibleAuthoringClient
from labscriptai.authoring.diff_edit import DiffEditError, apply_search_replace_diff
from labscriptai.agent.facade import UnifiedAuthoringFacade
from labscriptai.runtime.model_adapter import OpenAICompatibleConfig

DEFAULT_LLM_ONLY_BASE_URL = "https://api.vectorengine.ai/v1"


def _authoring_openai_config(
    *,
    default_model: str = "deepseek-v4-pro",
    api_prefix: str = "auto",
) -> OpenAICompatibleConfig:
    """Prefer LLM_ONLY_* when set (frontier direct runs); else DEEPSEEK_*."""
    if api_prefix != "auto":
        return OpenAICompatibleConfig.from_env(
            prefix=api_prefix,
            default_base_url=DEFAULT_LLM_ONLY_BASE_URL if api_prefix == "LLM_ONLY" else "https://api.deepseek.com",
            default_model=default_model,
            default_max_tokens=4096,
        )
    try:
        return OpenAICompatibleConfig.from_env(
            prefix="LLM_ONLY",
            default_base_url=DEFAULT_LLM_ONLY_BASE_URL,
            default_model=default_model,
            default_max_tokens=4096,
        )
    except RuntimeError:
        return OpenAICompatibleConfig.from_env(default_model=default_model, default_max_tokens=4096)


AUTHORING_SYSTEM_PROMPT = """You are LabscriptAI's protocol package author.
Return exactly one JSON object with a top-level "files" object.
The files object must contain exactly these three keys:
protocol.py, setup_card.html, manifest.json.
Each value must be a string containing the full file content.
Keep protocol.py syntactically valid Python. setup_card.html must be a printable
human setup card with deck layout, reagent table, run steps, and risk notes.
manifest.json must be valid JSON with schema_version "0.4". It must include
deck, reagents, tips, risk_flags, critical_failures, off_platform_handoff,
tool_permissions, and budget. manifest.deck must declare every labware/module/
instrument loaded by protocol.py. For each pipette loaded with
protocol.load_instrument, manifest.deck must include an instruments or pipettes
entry with its type/name and mount. manifest.tips must include explicit
tips_required and tips_available quantities.
Do not include Markdown fences or explanations outside the JSON object.
"""

BARE_AUTHORING_SYSTEM_PROMPT = """You are an Opentrons protocol package author.
Return exactly one JSON object with a top-level "files" object containing
protocol.py, setup_card.html, and manifest.json as string values.
Do not include Markdown fences or explanations outside the JSON object.
"""

PY_ONLY_AUTHORING_SYSTEM_PROMPT = """You are an Opentrons protocol author.
Write only protocol.py for the requested experiment.
Return the complete Python file content only. Do not return JSON, Markdown
fences, setup cards, manifests, or explanations.
The benchmark harness will derive manifest.json and setup_card.html from
protocol.py after generation, so spend your effort on a runnable Opentrons
script that matches the experiment intent.
Default to OT-2-compatible protocols unless the task explicitly asks for Flex.
For generic transfers, use OT-2 numeric slots, p300_single_gen2, and OT-2 tip racks.
"""

PROTOCOL_REPAIR_SYSTEM_PROMPT = """You are repairing only protocol.py for an Opentrons package.
Return exactly one JSON object: {"protocol.py": "...full Python file..."}.
Do not modify package metadata. Do not include Markdown fences or explanation.
Use the simulator stdout/stderr to fix the smallest executable issue.
"""

PROTOCOL_PATCH_REPAIR_SYSTEM_PROMPT = """You are repairing only protocol.py for an Opentrons package.
Return only SEARCH/REPLACE blocks in this exact format:
------- SEARCH
existing protocol.py snippet
=======
replacement protocol.py snippet
++++++ REPLACE
Do not return JSON. Do not return a full file. Do not modify package metadata.
Use the simulator stdout/stderr to make the smallest executable local patch.
The final marker must be exactly +++++++ REPLACE. Do not use >>>>>>> REPLACE.
Preserve valid Python indentation in every replacement snippet.
"""


def _prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _strip_json_markdown(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped


def _selected_tasks(
    tasks_path: Path,
    *,
    limit: int,
    task_split: str = "holdout",
    task_ids: tuple[str, ...] = (),
) -> tuple[AuthoringTask, ...]:
    tasks = load_authoring_tasks(tasks_path)
    if task_ids:
        by_id = {task.task_id: task for task in tasks}
        missing = [task_id for task_id in task_ids if task_id not in by_id]
        if missing:
            raise ValueError(f"unknown task ids: {', '.join(missing)}")
        return tuple(by_id[task_id] for task_id in task_ids)
    if task_split == "all":
        return tasks[:limit]
    if task_split != "holdout":
        raise ValueError("task_split must be 'holdout' or 'all'")
    n_strata = len(DIFFICULTY_STRATA)
    per_level = max(1, (limit + n_strata - 1) // n_strata)
    selected = list(select_stratified_tasks(tasks, per_level=per_level))
    if len(selected) < limit:
        selected_ids = {task.task_id for task in selected}
        remaining = [task for task in tasks if task.holdout and task.task_id not in selected_ids]
        remaining.sort(
            key=lambda task: (
                not task.is_new,
                DIFFICULTY_STRATA.index(task.difficulty),
                task.task_id,
            )
        )
        selected.extend(remaining[: limit - len(selected)])
    return selected[:limit]


class UsageString(str):
    """String result with provider usage attached for benchmark accounting."""

    def __new__(cls, value: str, usage: dict[str, Any] | None = None) -> "UsageString":
        obj = str.__new__(cls, value)
        obj.usage = usage or {}
        return obj


class UsageError(ValueError):
    """Provider response error that still carries API usage accounting."""

    def __init__(self, message: str, usage: dict[str, int] | None = None) -> None:
        super().__init__(message)
        self.usage = usage or _usage_stats(None)


class RepairPatchError(ValueError):
    """Patch-only repair could not be applied safely."""

    def __init__(
        self,
        message: str,
        *,
        rejected_count: int = 1,
        usage: dict[str, int] | None = None,
        raw_patch: str = "",
    ) -> None:
        super().__init__(message)
        self.rejected_count = rejected_count
        self.usage = usage or _usage_stats(None)
        self.raw_patch = raw_patch


class ProtocolRepairResult(str):
    """Repair result with provider usage and patch accounting."""

    def __new__(
        cls,
        value: str,
        usage: dict[str, Any] | None = None,
        *,
        patch_count: int = 0,
        patch_rejected_count: int = 0,
        patch_backend: str = "none",
    ) -> "ProtocolRepairResult":
        obj = str.__new__(cls, value)
        obj.usage = usage or {}
        obj.patch_count = patch_count
        obj.patch_rejected_count = patch_rejected_count
        obj.patch_backend = patch_backend
        return obj


def _usage_stats(usage: Any) -> dict[str, int]:
    if not isinstance(usage, dict):
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    input_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or input_tokens + output_tokens)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


_RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}


class ProviderRequestError(RuntimeError):
    """OpenAI-compatible provider rejected a request with a useful response body."""


def _post_chat_completion(config: OpenAICompatibleConfig, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    attempts = max(1, int(config.transport_retries))
    for attempt in range(attempts):
        req = request.Request(
            url=f"{config.base_url}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with request.urlopen(req, timeout=config.timeout_sec) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            nonretryable = "invalid_request_error" in response_body or "Invalid parameter" in response_body
            if nonretryable or exc.code not in _RETRYABLE_HTTP_STATUS or attempt == attempts - 1:
                raise ProviderRequestError(f"HTTP {exc.code}: {response_body[:500]}") from exc
        except (TimeoutError, error.URLError):
            if attempt == attempts - 1:
                raise
        time.sleep(min(30, 5 * (2**attempt)))
    raise RuntimeError("chat completion retry loop exhausted")


def call_package_author(
    config: OpenAICompatibleConfig,
    task: AuthoringTask,
    *,
    prompt_mode: str = "rules",
) -> dict[str, str]:
    if prompt_mode not in {"bare", "rules"}:
        raise ValueError("prompt_mode must be one of: bare, rules")
    prompt = {
        "task_id": task.task_id,
        "difficulty": task.difficulty,
        "prompt": task.prompt,
        "required_package_files": list(REQUIRED_PACKAGE_FILES),
    }
    if prompt_mode == "rules":
        prompt.update(
            {
                "package_format_instruction": (
                    "Use the current three-piece v0.4 package even if the task text "
                    "mentions any older package format."
                ),
                "manifest_requirements": {
                    "schema_version": "0.4",
                    "task_id": task.task_id,
                    "system_id": "labscriptai",
                    "model_id": config.model,
                    "scaffold_id": "authoring-pilot-v0.4",
                    "prompt_hash": _prompt_hash(task.prompt),
                    "budget": {"attempts": 8, "wall_min": 30, "tokens": 24000},
                    "tool_permissions": ["write_package_files", "validate_package", "simulate_protocol"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }
        )
    payload = {
        "model": config.model,
        "messages": [
            {
                "role": "system",
                "content": AUTHORING_SYSTEM_PROMPT
                if prompt_mode == "rules"
                else BARE_AUTHORING_SYSTEM_PROMPT,
            },
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "temperature": 0,
        "max_tokens": config.max_tokens,
    }
    response_payload = _post_chat_completion(config, payload)
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("model response missing choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    usage = _usage_stats(response_payload.get("usage"))
    if not isinstance(content, str) or not content.strip():
        raise UsageError("model response content is empty", usage)
    try:
        decoded = json.loads(_strip_json_markdown(content))
    except json.JSONDecodeError as exc:
        raise UsageError(f"model response is invalid JSON: {exc}", usage) from exc
    files = decoded.get("files")
    if not isinstance(files, dict):
        raise UsageError("authoring response missing files object", usage)
    result = {name: str(files[name]) for name in REQUIRED_PACKAGE_FILES if name in files}
    result["authoring_stats.json"] = json.dumps(
        {
            "tool_calls": 0,
            "skill_loads": 0,
            "simulator_calls": 0,
            **usage,
        },
        indent=2,
    )
    return result


def call_protocol_author(
    config: OpenAICompatibleConfig,
    task: AuthoringTask,
) -> dict[str, str]:
    prompt = {
        "task_id": task.task_id,
        "difficulty": task.difficulty,
        "prompt": task.prompt,
        "output_contract": "protocol.py only",
        "sidecar_policy": (
            "Do not write manifest.json or setup_card.html. The benchmark harness "
            "will derive those files from protocol.py for every compared system."
        ),
    }
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": PY_ONLY_AUTHORING_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "temperature": 0,
        "max_tokens": config.max_tokens,
    }
    response_payload = _post_chat_completion(config, payload)
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("model response missing choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    usage = _usage_stats(response_payload.get("usage"))
    if not isinstance(content, str) or not content.strip():
        raise UsageError("model response content is empty", usage)
    protocol_py = _extract_protocol_py(content)
    return {
        "protocol.py": protocol_py,
        "authoring_stats.json": json.dumps(
            {
                "tool_calls": 0,
                "skill_loads": 0,
                "simulator_calls": 0,
                **usage,
            },
            indent=2,
        ),
    }


def _extract_protocol_py(content: str) -> str:
    stripped = _strip_json_markdown(content).strip()
    try:
        decoded = json.loads(stripped)
    except json.JSONDecodeError:
        decoded = None
    if isinstance(decoded, dict):
        if isinstance(decoded.get("protocol.py"), str):
            return decoded["protocol.py"]
        files = decoded.get("files")
        if isinstance(files, dict) and isinstance(files.get("protocol.py"), str):
            return files["protocol.py"]
    return stripped + ("\n" if not stripped.endswith("\n") else "")


def call_protocol_repair(
    config: OpenAICompatibleConfig,
    task: AuthoringTask,
    *,
    protocol_py: str,
    simulation_result: dict[str, Any],
) -> str:
    prompt = {
        "task_id": task.task_id,
        "difficulty": task.difficulty,
        "prompt": task.prompt,
        "current_protocol_py": protocol_py,
        "simulator_summary": {
            "returncode": simulation_result.get("returncode"),
            "stdout": str(simulation_result.get("stdout", ""))[-4000:],
            "stderr": str(simulation_result.get("stderr", ""))[-4000:],
            "error": simulation_result.get("error"),
        },
        "instruction": "Return only a replacement protocol.py as JSON.",
    }
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": PROTOCOL_REPAIR_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "temperature": 0,
        "max_tokens": config.max_tokens,
    }
    response_payload = _post_chat_completion(config, payload)
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("model response missing choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    usage = _usage_stats(response_payload.get("usage"))
    if not isinstance(content, str) or not content.strip():
        raise UsageError("model response content is empty", usage)
    try:
        decoded = json.loads(_strip_json_markdown(content))
    except json.JSONDecodeError as exc:
        raise UsageError(f"repair response is invalid JSON: {exc}", usage) from exc
    repaired = decoded.get("protocol.py")
    if not isinstance(repaired, str) or not repaired.strip():
        raise UsageError("repair response missing protocol.py", usage)
    return ProtocolRepairResult(
        repaired,
        usage,
        patch_count=0,
        patch_rejected_count=0,
        patch_backend="rewrite",
    )


def call_protocol_patch_repair(
    config: OpenAICompatibleConfig,
    task: AuthoringTask,
    *,
    protocol_py: str,
    simulation_result: dict[str, Any],
) -> str:
    prompt = {
        "task_id": task.task_id,
        "difficulty": task.difficulty,
        "prompt": task.prompt,
        "current_protocol_py": protocol_py,
        "simulator_summary": {
            "returncode": simulation_result.get("returncode"),
            "stdout": str(simulation_result.get("stdout", ""))[-4000:],
            "stderr": str(simulation_result.get("stderr", ""))[-4000:],
            "error": simulation_result.get("error"),
        },
        "instruction": (
            "Return only SEARCH/REPLACE blocks. Do not return JSON or a full protocol.py. "
            "Use one or more blocks with ------- SEARCH, =======, and +++++++ REPLACE markers."
        ),
    }
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": PROTOCOL_PATCH_REPAIR_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "temperature": 0,
        "max_tokens": config.max_tokens,
    }
    response_payload = _post_chat_completion(config, payload)
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("model response missing choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    usage = _usage_stats(response_payload.get("usage"))
    if not isinstance(content, str) or not content.strip():
        raise UsageError("patch repair response content is empty", usage)
    diff_content = _extract_diff_edit_content(content)
    try:
        result = apply_search_replace_diff(protocol_py, diff_content)
    except DiffEditError as exc:
        raise RepairPatchError(
            f"diff_edit patch rejected: {exc}",
            rejected_count=int(getattr(exc, "rejected_count", 1)),
            usage=usage,
            raw_patch=diff_content,
        ) from exc
    return ProtocolRepairResult(
        result.content,
        usage,
        patch_count=result.applied_count,
        patch_rejected_count=result.rejected_count,
        patch_backend="diff_edit",
    )


def _extract_diff_edit_content(content: str) -> str:
    stripped = _strip_json_markdown(content)
    if "SEARCH" in stripped and "REPLACE" in stripped:
        return stripped
    try:
        decoded = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped
    if isinstance(decoded, dict):
        for key in ("diff", "patch", "patches", "content"):
            value = decoded.get(key)
            if isinstance(value, str):
                return _strip_json_markdown(value)
    return stripped


def _build_protocol_repairer(
    config: OpenAICompatibleConfig,
    repair_edit_mode: str,
) -> Callable[[AuthoringTask, str, dict[str, Any]], str]:
    if repair_edit_mode == "rewrite":
        return lambda task, protocol_py, simulation_result: call_protocol_repair(
            config,
            task,
            protocol_py=protocol_py,
            simulation_result=simulation_result,
        )
    if repair_edit_mode == "patch_only":
        return lambda task, protocol_py, simulation_result: call_protocol_patch_repair(
            config,
            task,
            protocol_py=protocol_py,
            simulation_result=simulation_result,
        )
    raise ValueError("repair_edit_mode must be one of: rewrite, patch_only")


def write_package_files(package_dir: Path, files: dict[str, str]) -> None:
    package_dir.mkdir(parents=True, exist_ok=True)
    for file_name, content in files.items():
        if file_name not in REQUIRED_PACKAGE_FILES and file_name not in {
            "authoring_stats.json",
            "trace.jsonl",
        }:
            continue
        (package_dir / file_name).write_text(content, encoding="utf-8")


def _read_authoring_stats(package_dir: Path) -> dict[str, int]:
    empty = {
        "tool_calls": 0,
        "skill_loads": 0,
        "simulator_calls": 0,
        "protocol_hits": 0,
        "memory_hits": 0,
        "kb_context_tokens_estimate": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }
    path = package_dir / "authoring_stats.json"
    if not path.exists():
        return dict(empty)
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return dict(empty)
    if not isinstance(loaded, dict):
        return dict(empty)
    return {
        "tool_calls": int(loaded.get("tool_calls", 0)),
        "skill_loads": int(loaded.get("skill_loads", 0)),
        "simulator_calls": int(loaded.get("simulator_calls", 0)),
        "protocol_hits": int(loaded.get("protocol_hits", 0)),
        "memory_hits": int(loaded.get("memory_hits", 0)),
        "kb_context_tokens_estimate": int(loaded.get("kb_context_tokens_estimate", 0)),
        "input_tokens": int(loaded.get("input_tokens", 0)),
        "output_tokens": int(loaded.get("output_tokens", 0)),
        "total_tokens": int(loaded.get("total_tokens", 0)),
    }


def stamp_manifest(package_dir: Path, task: AuthoringTask, *, model_id: str) -> None:
    """Stamp harness-owned provenance fields after model package generation."""

    manifest_path = package_dir / "manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                manifest = loaded
        except json.JSONDecodeError:
            manifest = {}
    schema_version = "0.4"
    manifest.update(
        {
            "schema_version": schema_version,
            "task_id": task.task_id,
            "system_id": "labscriptai",
            "model_id": model_id,
            "scaffold_id": manifest.get("scaffold_id") or "authoring-pilot-v0.4",
            "prompt_hash": _prompt_hash(task.prompt),
            "tool_permissions": manifest.get("tool_permissions")
            or ["write_package_files", "validate_package", "simulate_protocol"],
            "timestamp": manifest.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        }
    )
    manifest.setdefault("deck", {"slots": [], "modules": [], "instruments": []})
    manifest.setdefault("reagents", [])
    manifest.setdefault("tips", {"tips_required": 0, "tips_available": 0})
    manifest.setdefault("risk_flags", [])
    manifest.setdefault("critical_failures", [])
    manifest.setdefault("off_platform_handoff", {"declared": False})
    manifest["budget"] = {
        "attempts": 8,
        "wall_min": 30,
        "tokens": 24000,
        **(manifest.get("budget") if isinstance(manifest.get("budget"), dict) else {}),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _keyword_string(call: ast.Call, name: str) -> str | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return _literal_string(keyword.value)
    return None


def _protocol_instruments(protocol_path: Path) -> list[dict[str, str]]:
    try:
        tree = ast.parse(protocol_path.read_text(encoding="utf-8"), filename=str(protocol_path))
    except SyntaxError:
        return []
    instruments: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "load_instrument":
            continue
        name = _literal_string(node.args[0]) if node.args else _keyword_string(node, "instrument_name")
        mount = _literal_string(node.args[1]) if len(node.args) > 1 else _keyword_string(node, "mount")
        if name and mount and (name, mount) not in seen:
            seen.add((name, mount))
            instruments.append({"name": name, "type": name, "mount": mount})
    return instruments


def _protocol_labware(protocol_path: Path) -> list[dict[str, str]]:
    try:
        tree = ast.parse(protocol_path.read_text(encoding="utf-8"), filename=str(protocol_path))
    except SyntaxError:
        return []
    labware: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "load_labware":
            continue
        load_name = _literal_string(node.args[0]) if node.args else _keyword_string(node, "load_name")
        slot = (
            _literal_string(node.args[1])
            if len(node.args) > 1
            else _keyword_string(node, "location") or _keyword_string(node, "slot")
        )
        if load_name and slot and (load_name, slot) not in seen:
            seen.add((load_name, slot))
            labware.append({"name": load_name, "load_name": load_name, "slot": slot})
    return labware


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _normalize_protocol_for_simulator(protocol_path: Path) -> list[str]:
    if not protocol_path.exists():
        return []
    protocol_text = protocol_path.read_text(encoding="utf-8")
    replacements = {
        "flex_1channel_200ul": "flex_1channel_1000",
        "flex_8channel_200ul": "flex_8channel_1000",
        "opentrons_flex_96_wellplate_200ul": "opentrons_96_wellplate_200ul_pcr_full_skirt",
        "opentrons_flex_96_tiprack_300ul": "opentrons_flex_96_tiprack_200ul",
    }
    flex_protocol = (
        '"robotType": "Flex"' in protocol_text
        or "opentrons_flex_" in protocol_text
        or "flex_1channel_" in protocol_text
        or "flex_8channel_" in protocol_text
    )
    if flex_protocol:
        replacements.update(
            {
                "p20_single_gen2": "flex_1channel_1000",
                "p300_single_gen3": "flex_1channel_1000",
                "p300_multi_gen3": "flex_8channel_1000",
                "p300_single_gen2": "flex_1channel_1000",
                "p300_multi_gen2": "flex_8channel_1000",
                "p1000_single_gen2": "flex_1channel_1000",
            }
        )
    else:
        replacements.update(
            {
                "p300_single_gen3": "p300_single_gen2",
                "p300_multi_gen3": "p300_multi_gen2",
            }
        )
    repaired = protocol_text
    repairs: list[str] = []
    for invalid_name, valid_name in replacements.items():
        if invalid_name in repaired:
            repaired = repaired.replace(invalid_name, valid_name)
            repairs.append(f"normalized {invalid_name} to {valid_name}")
    if flex_protocol and "requirements =" not in repaired:
        repaired = 'requirements = {"robotType": "Flex", "apiLevel": "2.24"}\n\n' + repaired
        repairs.append("added Flex protocol requirements")
    for quote in ('"', "'"):
        data_prefix = f"{quote}/data/"
        if data_prefix in repaired:
            repaired = repaired.replace(data_prefix, f"{quote}/tmp/")
            repairs.append("normalized /data file path to /tmp for simulator")
    pipette_labware_pattern = re.compile(
        r"protocol\.load_labware\(\s*"
        r"(?P<quote>['\"])(?P<name>(?:flex_|p20_|p300_|p1000_)[^'\"]+)(?P=quote)\s*,\s*"
        r"mount\s*=\s*(?P<mount_quote>['\"])(?P<mount>left|right)(?P=mount_quote)\s*"
        r"\)",
        flags=re.DOTALL,
    )

    def replace_pipette_labware(match: re.Match[str]) -> str:
        return f"protocol.load_instrument('{match.group('name')}', mount='{match.group('mount')}')"

    normalized_pipette_loads = pipette_labware_pattern.sub(replace_pipette_labware, repaired)
    if normalized_pipette_loads != repaired:
        repaired = normalized_pipette_loads
        repairs.append("normalized pipette load_labware call to load_instrument")
    flattened_columns = re.sub(
        r"(?P<indent>[ \t]*)for (?P<container>\w+) in "
        r"(?P<expr>[^\n]*columns_by_name\(\)[^\n]*(?:\n(?P=indent)\+[^\n]+)+)"
        r"\n(?P=indent)for (?P<item>\w+) in (?P=container)\b",
        r"\g<indent>for \g<item> in \g<expr>",
        repaired,
    )
    if flattened_columns != repaired:
        repaired = flattened_columns
        repairs.append("flattened columns_by_name well iteration")
    p300_default_requires_sub_20_ul = (
        re.search(r'default\s*=\s*["\']p300_single_gen2["\']', repaired) is not None
        and re.search(r"REQUIRED_MIN_VOL\s*=\s*(?:2(?:\.0)?|[3-9](?:\.0)?|1[0-9](?:\.0)?)\b", repaired)
        is not None
    )
    if p300_default_requires_sub_20_ul:
        repaired = re.sub(
            r"REQUIRED_MIN_VOL\s*=\s*(?:2(?:\.0)?|[3-9](?:\.0)?|1[0-9](?:\.0)?)\b",
            "REQUIRED_MIN_VOL = 20.0",
            repaired,
            count=1,
        )
        repairs.append("normalized p300 minimum required volume to 20 uL")
    repaired, deterministic_repairs = _add_deterministic_protocol_guards(repaired)
    repairs.extend(deterministic_repairs)
    repaired, hygiene_repairs = _add_simulator_hygiene(repaired, flex_protocol=flex_protocol)
    repairs.extend(hygiene_repairs)
    if repaired != protocol_text:
        protocol_path.write_text(repaired, encoding="utf-8")
    return repairs


def _add_deterministic_protocol_guards(protocol_text: str) -> tuple[str, list[str]]:
    """Patch common simulator failures without spending an LLM repair round."""

    repaired = protocol_text
    repairs: list[str] = []
    fixed_trash_pattern = re.compile(
        r"(?m)^[ \t]*(?:\w+\s*=\s*)?protocol\.load_labware\(\s*"
        r"(?P<quote>['\"])opentrons_1_trash_1100ml_fixed(?P=quote)\s*,\s*"
        r"(?P<slot_quote>['\"])12(?P=slot_quote)[^\n]*\)\s*(?:#.*)?$"
    )
    without_fixed_trash = fixed_trash_pattern.sub("", repaired)
    if without_fixed_trash != repaired:
        repaired = without_fixed_trash
        repairs.append("removed duplicate fixed trash labware load")

    current_volume_pattern = re.compile(
        r"(?m)^(?P<indent>[ \t]*)(?P<pipette>\w+)\.aspirate\((?P<volume>[^,\n]+),\s*(?P<source>.+?)\)\s*\n"
        r"(?P=indent)(?P=pipette)\.dispense\(\s*(?P=pipette)\.current_volume\s*,\s*(?P<dest>.+?)\)"
    )

    def replace_current_volume(match: re.Match[str]) -> str:
        return (
            f"{match.group('indent')}_safe_aspirate_dispense("
            f"{match.group('pipette')}, {match.group('volume').strip()}, "
            f"{match.group('source').strip()}, {match.group('dest').strip()})"
        )

    with_safe_transfers = current_volume_pattern.sub(replace_current_volume, repaired)
    if with_safe_transfers != repaired:
        repaired = with_safe_transfers
        repairs.append("split oversized aspirate/dispense pairs")

    matching_volume_pattern = re.compile(
        r"(?m)^(?P<indent>[ \t]*)(?P<pipette>\w+)\.aspirate\((?P<volume>[^,\n]+),\s*(?P<source>.+?)\)\s*\n"
        r"(?P=indent)(?P=pipette)\.dispense\(\s*(?P=volume)\s*,\s*(?P<dest>.+?)\)"
    )
    with_safe_matching_transfers = matching_volume_pattern.sub(replace_current_volume, repaired)
    if with_safe_matching_transfers != repaired:
        repaired = with_safe_matching_transfers
        repairs.append("guarded matching aspirate/dispense pairs by pipette capacity")

    oversized_mix_pattern = re.compile(
        r"(?m)^(?P<indent>[ \t]*)(?P<pipette>\w+)\.mix\((?P<repetitions>[^,\n]+),\s*(?P<volume>[^,\n]+),\s*(?P<location>.+?)\)"
    )

    def replace_mix(match: re.Match[str]) -> str:
        return (
            f"{match.group('indent')}_safe_mix("
            f"{match.group('pipette')}, {match.group('repetitions').strip()}, "
            f"{match.group('volume').strip()}, {match.group('location').strip()})"
        )

    with_safe_mix = oversized_mix_pattern.sub(replace_mix, repaired)
    if with_safe_mix != repaired:
        repaired = with_safe_mix
        repairs.append("guarded mix volumes by pipette capacity")

    wait_temperature_pattern = re.compile(
        r"(?m)^[ \t]*\w+\.(?:wait_for_temperature|wait_for_temp)\(\)[ \t]*(?:#.*)?(?:\n|$)"
    )
    without_wait_temperature = wait_temperature_pattern.sub("", repaired)
    if without_wait_temperature != repaired:
        repaired = without_wait_temperature
        repairs.append("removed unsupported temperature wait call")

    bare_magnet_engage_pattern = re.compile(r"\.engage\(\)")
    with_magnet_height = bare_magnet_engage_pattern.sub(".engage(height_from_base=6.0)", repaired)
    if with_magnet_height != repaired:
        repaired = with_magnet_height
        repairs.append("added default magnetic module engage height")

    if "_safe_pick_up_tip(" not in repaired and re.search(r"\b\w+\.pick_up_tip\(\)", repaired):
        repaired = re.sub(r"\b(?P<pipette>\w+)\.pick_up_tip\(\)", r"_safe_pick_up_tip(\g<pipette>)", repaired)
        repairs.append("guarded pick_up_tip with tiprack reset")

    if "_safe_aspirate_dispense(" in repaired and "def _safe_aspirate_dispense(" not in repaired:
        repaired = _insert_helper_after_imports(repaired, _SAFE_ASPIRATE_DISPENSE_HELPER)
    if "_safe_mix(" in repaired and "def _safe_mix(" not in repaired:
        repaired = _insert_helper_after_imports(repaired, _SAFE_MIX_HELPER)
    if "_safe_pick_up_tip(" in repaired and "def _safe_pick_up_tip(" not in repaired:
        repaired = _insert_helper_after_imports(repaired, _SAFE_PICK_UP_TIP_HELPER)

    canonicalized = _canonicalize_safe_helpers(repaired)
    if canonicalized != repaired:
        repaired = canonicalized
        repairs.append("canonicalized deterministic safe helper bodies")

    thermocycler_load_pattern = re.compile(
        r"(?m)^(?P<indent>[ \t]*)(?P<plate>\w+)\s*=\s*(?P<module>\w+)\.load_labware\([^\n]+\)\s*$"
    )
    for match in list(thermocycler_load_pattern.finditer(repaired)):
        module = match.group("module")
        prefix = repaired[: match.start()]
        module_loaded = re.search(rf"\b{re.escape(module)}\s*=\s*.*load_module\([^)]*thermocycler", prefix, re.IGNORECASE | re.DOTALL)
        already_opened_before_access = re.search(rf"\b{re.escape(module)}\.open_lid\(\)", prefix)
        if module_loaded and not already_opened_before_access:
            insertion = f"\n{match.group('indent')}{module}.open_lid()"
            repaired = repaired[: match.end()] + insertion + repaired[match.end() :]
            repairs.append("opened thermocycler lid before pipetting to module labware")
            break

    if 'rcfg["slot"]' in repaired or "rcfg['slot']" in repaired:
        updated = repaired.replace(
            'slot = rcfg["slot"]',
            'slot = rcfg.get("slot") or rcfg.get("source_slot") or rcfg.get("labware_slot")',
        ).replace(
            "slot = rcfg['slot']",
            "slot = rcfg.get('slot') or rcfg.get('source_slot') or rcfg.get('labware_slot')",
        )
        if updated != repaired:
            repaired = updated
            repairs.append("made reagent slot lookup tolerant of plan aliases")
    if 'rcfg["well"]' in repaired or "rcfg['well']" in repaired:
        updated = repaired.replace(
            'well = rcfg["well"]',
            'well = rcfg.get("well") or rcfg.get("source_well") or rcfg.get("well_name")',
        ).replace(
            "well = rcfg['well']",
            "well = rcfg.get('well') or rcfg.get('source_well') or rcfg.get('well_name')",
        )
        if updated != repaired:
            repaired = updated
            repairs.append("made reagent well lookup tolerant of plan aliases")

    return repaired, repairs


_SAFE_PICK_UP_TIP_HELPER = '''
def _safe_pick_up_tip(pipette):
    try:
        pipette.pick_up_tip()
    except Exception as exc:
        if exc.__class__.__name__ != "OutOfTipsError":
            raise
        pipette.reset_tipracks()
        pipette.pick_up_tip()

'''


_SAFE_ASPIRATE_DISPENSE_HELPER = '''
def _safe_aspirate_dispense(pipette, volume, source, destination):
    remaining = float(volume)
    max_volume = float(getattr(pipette, "max_volume", 300))
    while remaining > 0:
        step = min(remaining, max_volume)
        pipette.aspirate(step, source)
        pipette.dispense(step, destination)
        remaining -= step

'''


_SAFE_MIX_HELPER = '''
def _safe_mix(pipette, repetitions, volume, location):
    step = min(float(volume), float(getattr(pipette, "max_volume", 300)))
    pipette.mix(int(repetitions), step, location)

'''


def _insert_helper_after_imports(protocol_text: str, helper: str) -> str:
    lines = protocol_text.splitlines()
    insert_at = 0
    for index, line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            insert_at = index + 1
    lines[insert_at:insert_at] = helper.strip("\n").splitlines() + [""]
    return "\n".join(lines) + "\n"


def _canonicalize_safe_helpers(protocol_text: str) -> str:
    helper_bodies = {
        "_safe_pick_up_tip": _SAFE_PICK_UP_TIP_HELPER,
        "_safe_aspirate_dispense": _SAFE_ASPIRATE_DISPENSE_HELPER,
        "_safe_mix": _SAFE_MIX_HELPER,
    }
    try:
        tree = ast.parse(protocol_text)
    except SyntaxError:
        return protocol_text

    replacements: list[tuple[int, int, str]] = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name not in helper_bodies:
            continue
        if not hasattr(node, "end_lineno"):
            continue
        replacements.append((node.lineno, node.end_lineno, helper_bodies[node.name].strip("\n")))

    if not replacements:
        return protocol_text

    lines = protocol_text.splitlines()
    for start, end, replacement in sorted(replacements, reverse=True):
        lines[start - 1 : end] = replacement.splitlines()
    return "\n".join(lines) + "\n"


def _estimated_pick_up_tip_calls(protocol_text: str) -> int:
    kept_lines: list[str] = []
    in_safe_helper = False
    for line in protocol_text.splitlines():
        if line.startswith("def _safe_pick_up_tip("):
            in_safe_helper = True
            continue
        if in_safe_helper:
            if line and not line.startswith((" ", "\t")):
                in_safe_helper = False
                kept_lines.append(line)
            continue
        kept_lines.append(line)
    without_helper_bodies = "\n".join(kept_lines)
    direct_calls = len(re.findall(r"\.\s*pick_up_tip\(\)", without_helper_bodies))
    guarded_calls = len(re.findall(r"(?<!def )_safe_pick_up_tip\(", without_helper_bodies))
    return direct_calls + guarded_calls


def _add_simulator_hygiene(protocol_text: str, *, flex_protocol: bool) -> tuple[str, list[str]]:
    try:
        tree = _attach_parents(ast.parse(protocol_text))
    except SyntaxError:
        return protocol_text, []
    tiprack_var: str | None = None
    tiprack_end_line: int | None = None
    instrument_end_lines: dict[str, int] = {}
    instrument_has_tip_racks: set[str] = set()
    loaded_slots: set[str] = set()
    pick_up_receivers: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr == "load_labware":
            load_name = _literal_string(node.args[0]) if node.args else _keyword_string(node, "load_name")
            slot = (
                _literal_string(node.args[1])
                if len(node.args) > 1
                else _keyword_string(node, "location") or _keyword_string(node, "slot")
            )
            if slot:
                loaded_slots.add(slot)
            if load_name and "_tiprack_" in load_name:
                parent = getattr(node, "parent", None)
                if isinstance(parent, ast.Assign) and parent.targets and isinstance(parent.targets[0], ast.Name):
                    tiprack_var = parent.targets[0].id
                    tiprack_end_line = getattr(parent, "end_lineno", None)
        elif node.func.attr == "load_instrument":
            parent = getattr(node, "parent", None)
            if isinstance(parent, ast.Assign) and parent.targets and isinstance(parent.targets[0], ast.Name):
                receiver = parent.targets[0].id
                instrument_end_lines[receiver] = getattr(parent, "end_lineno", None) or 0
                if any(keyword.arg == "tip_racks" for keyword in node.keywords):
                    instrument_has_tip_racks.add(receiver)
        elif node.func.attr == "pick_up_tip" and not node.args and isinstance(node.func.value, ast.Name):
            pick_up_receivers.add(node.func.value.id)
    if not tiprack_var or not tiprack_end_line:
        return protocol_text, []
    lines = protocol_text.splitlines()
    insertions: list[str] = []
    repairs: list[str] = []
    for receiver in sorted(pick_up_receivers):
        assignment = f"{receiver}.tip_racks"
        if (
            assignment not in protocol_text
            and receiver in instrument_end_lines
            and receiver not in instrument_has_tip_racks
        ):
            insertions.append(f"    {assignment} = [{tiprack_var}]")
            repairs.append(f"bound {receiver} to {tiprack_var}")
    if flex_protocol and ".drop_tip(" in protocol_text and "load_trash_bin(" not in protocol_text:
        trash_slot = next((slot for slot in ("A3", "B3", "C3", "D3") if slot not in loaded_slots), "A3")
        insertions.append(f"    protocol.load_trash_bin(\"{trash_slot}\")")
        repairs.append(f"added Flex trash bin in slot {trash_slot}")
    if not insertions:
        return protocol_text, []
    latest_receiver_line = max(
        (instrument_end_lines[receiver] for receiver in pick_up_receivers if receiver in instrument_end_lines),
        default=0,
    )
    insert_at = min(max(tiprack_end_line, latest_receiver_line, 0), len(lines))
    lines[insert_at:insert_at] = insertions
    return "\n".join(lines) + "\n", repairs


def _attach_parents(tree: ast.AST) -> ast.AST:
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            setattr(child, "parent", parent)
    return tree


def _deck_labware_key(item: dict[str, Any]) -> tuple[str | None, str | None]:
    return (
        item.get("load_name") or item.get("definition") or item.get("name") or item.get("type"),
        str(item.get("slot") or item.get("location")) if item.get("slot") or item.get("location") else None,
    )


def _looks_like_instrument_entry(item: dict[str, Any]) -> bool:
    name = str(item.get("load_name") or item.get("definition") or item.get("name") or item.get("type") or "")
    return name.startswith(("p20_", "p300_", "p1000_", "flex_"))


def _numeric_tip_quantity(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    if not isinstance(value, dict):
        return None
    for key in (
        "total",
        "tips_required",
        "required",
        "tips_available",
        "available",
        "total_tips_available",
        "count",
        "quantity",
        "capacity",
    ):
        nested = value.get(key)
        if isinstance(nested, bool):
            continue
        if isinstance(nested, int | float):
            return nested
    return None


def _sum_tip_rack_capacity(tip_racks: Any) -> int | float | None:
    if not isinstance(tip_racks, list):
        return None
    total: int | float = 0
    found = False
    for rack in tip_racks:
        quantity = _numeric_tip_quantity(rack)
        if quantity is None:
            continue
        total += quantity
        found = True
    return total if found else None


def _normalize_critical_failures(
    manifest: dict[str, Any],
    repairs: list[str],
) -> None:
    raw_failures = manifest.get("critical_failures")
    if not isinstance(raw_failures, list):
        manifest["critical_failures"] = []
        repairs.append("added manifest critical_failures")
        return

    valid_failures: list[str] = []
    risk_flags = manifest.get("risk_flags")
    if not isinstance(risk_flags, list):
        risk_flags = []
    moved_risks: list[Any] = []
    for item in raw_failures:
        if isinstance(item, str) and item in CRITICAL_FAILURES:
            valid_failures.append(item)
        else:
            moved_risks.append(item)
    if moved_risks:
        risk_flags.extend(moved_risks)
        manifest["risk_flags"] = risk_flags
        repairs.append("moved non-enum manifest critical_failures to risk_flags")
    manifest["critical_failures"] = valid_failures


def _repair_three_piece_metadata(package_dir: Path) -> list[str]:
    repairs: list[str] = []
    protocol_path = package_dir / "protocol.py"
    manifest_path = package_dir / "manifest.json"
    repairs.extend(_normalize_protocol_for_simulator(protocol_path))
    manifest = _read_json_object(manifest_path)
    manifest["schema_version"] = "0.4"
    deck = manifest.get("deck")
    if not isinstance(deck, dict):
        deck = {"slots": [], "modules": [], "instruments": []}
        repairs.append("added manifest deck")

    labware = _protocol_labware(protocol_path)
    if labware:
        slots = deck.get("slots") or deck.get("labware")
        if not isinstance(slots, list):
            slots = []
        existing_pairs = {_deck_labware_key(item) for item in slots if isinstance(item, dict)}
        for item in labware:
            if (item["load_name"], item["slot"]) not in existing_pairs:
                slots.append(item)
                repairs.append(f"added manifest deck slot {item['load_name']} in {item['slot']}")
        deck["slots"] = slots

    instruments = _protocol_instruments(protocol_path)
    if instruments:
        existing = deck.get("instruments") or deck.get("pipettes")
        if not isinstance(existing, list):
            existing = []
        existing_pairs = {
            (item.get("type") or item.get("name"), item.get("mount"))
            for item in existing
            if isinstance(item, dict)
        }
        for instrument in instruments:
            if (instrument["type"], instrument["mount"]) not in existing_pairs:
                existing.append(instrument)
                repairs.append(
                    f"added manifest instrument {instrument['type']} on {instrument['mount']}"
                )
        deck["instruments"] = existing
    manifest["deck"] = deck

    if not isinstance(manifest.get("reagents"), list):
        manifest["reagents"] = []
        repairs.append("added manifest reagents list")
    tips = manifest.get("tips")
    if not isinstance(tips, dict):
        tips = {}
    protocol_text = protocol_path.read_text(encoding="utf-8") if protocol_path.exists() else ""
    tips_required = _numeric_tip_quantity(tips.get("tips_required"))
    if tips_required is None:
        tips["tips_required"] = max(1, _estimated_pick_up_tip_calls(protocol_text))
        repairs.append("added manifest tips_required")
    elif not isinstance(tips.get("tips_required"), int | float):
        tips["tips_required"] = tips_required
        repairs.append("normalized manifest tips_required")
    available_candidates = [
        value
        for value in (
            _numeric_tip_quantity(tips.get("tips_available")),
            _numeric_tip_quantity(tips.get("total_tips_available")),
            _sum_tip_rack_capacity(tips.get("tip_racks")),
        )
        if value is not None
    ]
    if not available_candidates:
        tips["tips_available"] = 96
        repairs.append("added manifest tips_available")
    else:
        tips_available = max(available_candidates)
        if tips.get("tips_available") != tips_available:
            tips["tips_available"] = tips_available
            repairs.append("normalized manifest tips_available")
    manifest["tips"] = tips
    if not isinstance(manifest.get("risk_flags"), list):
        manifest["risk_flags"] = []
        repairs.append("added manifest risk_flags")
    _normalize_critical_failures(manifest, repairs)
    if not isinstance(manifest.get("off_platform_handoff"), dict):
        manifest["off_platform_handoff"] = {"declared": False}
        repairs.append("added manifest off_platform_handoff")
    budget = manifest.get("budget")
    if not isinstance(budget, dict):
        budget = {}
    manifest["budget"] = {"attempts": 8, "wall_min": 30, "tokens": 24000, **budget}
    manifest.setdefault("tool_permissions", ["write_package_files", "validate_package", "simulate_protocol"])
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return repairs


def _legacy_files_present(package_dir: Path) -> bool:
    return any(
        (package_dir / name).exists()
        for name in ("deck_plan.json", "tip_plan.json", "risk_checklist.json")
    )


def _seed_manifest_from_legacy_files(package_dir: Path) -> None:
    manifest_path = package_dir / "manifest.json"
    if manifest_path.exists():
        return
    tip_plan = _read_json_object(package_dir / "tip_plan.json")
    risk_checklist = _read_json_object(package_dir / "risk_checklist.json")
    manifest: dict[str, Any] = {
        "schema_version": "0.4",
        "deck": {"slots": [], "modules": [], "instruments": []},
        "reagents": [],
        "tips": {},
        "risk_flags": [],
        "critical_failures": [],
        "off_platform_handoff": {"declared": False},
        "tool_permissions": ["write_package_files", "validate_package", "simulate_protocol"],
        "budget": {"attempts": 8, "wall_min": 30, "tokens": 24000},
    }
    if tip_plan:
        manifest["tips"] = tip_plan
    if risk_checklist:
        manifest["critical_failures"] = risk_checklist.get("critical_failures", [])
        risks = risk_checklist.get("risks")
        if isinstance(risks, list):
            manifest["risk_flags"] = risks
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _write_legacy_metadata_projection(package_dir: Path) -> None:
    manifest = _read_json_object(package_dir / "manifest.json")
    deck = manifest.get("deck") if isinstance(manifest.get("deck"), dict) else {}
    slots = deck.get("slots") or deck.get("labware") or []
    instruments = deck.get("instruments") or []
    if (package_dir / "deck_plan.json").exists():
        normalized_instruments = [
            {
                "name": item.get("name") or item.get("type"),
                "type": item.get("type") or item.get("name"),
                "mount": item.get("mount"),
            }
            for item in instruments
            if isinstance(item, dict)
        ]
        normalized_instruments = [
            item for item in normalized_instruments if item["name"] and item["mount"]
        ]
        (package_dir / "deck_plan.json").write_text(
            json.dumps(
                {
                    "labware": slots if isinstance(slots, list) else [],
                    "instruments": normalized_instruments,
                    "pipettes": [
                        {"name": item["name"], "mount": item["mount"]}
                        for item in normalized_instruments
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    if (package_dir / "tip_plan.json").exists():
        (package_dir / "tip_plan.json").write_text(
            json.dumps(manifest.get("tips") if isinstance(manifest.get("tips"), dict) else {}, indent=2),
            encoding="utf-8",
        )
    if (package_dir / "risk_checklist.json").exists():
        (package_dir / "risk_checklist.json").write_text(
            json.dumps(
                {
                    "critical_failures": manifest.get("critical_failures", []),
                    "risks": manifest.get("risk_flags", []),
                },
                indent=2,
            ),
            encoding="utf-8",
        )


def _legacy_repair_aliases(package_dir: Path, repairs: list[str]) -> list[str]:
    aliases: list[str] = []
    if (package_dir / "deck_plan.json").exists():
        if any("added manifest instrument" in repair for repair in repairs):
            aliases.append("added deck_plan instrument")
        if any("added manifest deck slot" in repair for repair in repairs):
            aliases.append("added deck_plan labware")
    if (package_dir / "tip_plan.json").exists() and any(
        repair
        in {
            "added manifest tips_required",
            "added manifest tips_available",
            "normalized manifest tips_required",
            "normalized manifest tips_available",
        }
        for repair in repairs
    ):
        aliases.append("added tip_plan quantities")
    if (package_dir / "risk_checklist.json").exists() and any(
        "moved non-enum manifest critical_failures" in repair for repair in repairs
    ):
        aliases.extend(
            [
                "moved structured critical_failures to risks",
                "moved unknown critical_failures to risks",
            ]
        )
    return aliases


def repair_package_metadata(package_dir: Path) -> list[str]:
    """PRE v0: deterministic repairs for package metadata and simulator compatibility."""

    legacy = _legacy_files_present(package_dir)
    if legacy:
        _seed_manifest_from_legacy_files(package_dir)
    repairs = _repair_three_piece_metadata(package_dir)
    if legacy:
        _write_legacy_metadata_projection(package_dir)
        repairs.extend(_legacy_repair_aliases(package_dir, repairs))
    return repairs


def simulate_protocol_file(
    protocol_path: Path,
    *,
    opentrons_python: str | None = None,
    workspace_root: Path | None = None,
    timeout_sec: int = 180,
) -> dict[str, Any]:
    """Run the repository verify wrapper against one protocol file."""

    repo_root = Path(__file__).resolve().parents[3]
    _sync_tmp_plan_files_for_simulator(protocol_path)
    verify_script = repo_root / "skills" / "opentrons-protocol-verify" / "scripts" / "verify_protocol.py"
    cmd = [
        "uv",
        "run",
        "python",
        str(verify_script),
        "simulate",
    ]
    if workspace_root is not None:
        cmd.extend(["--workspace-root", str(workspace_root)])
    if opentrons_python:
        cmd.extend(["--python", opentrons_python])
    cmd.append(str(protocol_path))
    started = time.monotonic()
    try:
        completed = subprocess.run(
            cmd,
            cwd=protocol_path.parent,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "ok": False,
            "returncode": None,
            "duration_sec": time.monotonic() - started,
            "error": f"simulation timed out after {timeout_sec}s",
            "stdout": stdout,
            "stderr": stderr,
            "command": cmd,
        }
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "duration_sec": time.monotonic() - started,
        "stdout": completed.stdout[-6000:],
        "stderr": completed.stderr[-6000:],
        "command": cmd,
    }


def _sync_tmp_plan_files_for_simulator(protocol_path: Path) -> None:
    if not protocol_path.exists():
        return
    try:
        protocol_text = protocol_path.read_text(encoding="utf-8")
    except OSError:
        return
    package_dir = protocol_path.parent
    for name in ("manifest.json",):
        if f"/tmp/{name}" not in protocol_text:
            continue
        source = package_dir / name
        if not source.exists():
            continue
        try:
            shutil.copyfile(source, Path("/tmp") / name)
        except OSError:
            continue


def _write_summary(output_dir: Path, model_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    attempts_per_task = {
        str(record.get("task_id")): int(record.get("attempts", 0))
        for record in records
        if record.get("task_id")
    }
    first_pass_validator_pass_count = sum(
        1
        for record in records
        if isinstance(record.get("first_pass_validation"), dict)
        and record["first_pass_validation"].get("ok")
    )
    repaired_simulation_pass_count = sum(
        1
        for record in records
        if int(record.get("simulation_repair_attempts", 0)) > 0
        and isinstance(record.get("simulation"), dict)
        and record["simulation"].get("ok")
    )
    repaired_validator_pass_count = sum(
        1
        for record in records
        if int(record.get("simulation_repair_attempts", 0)) > 0
        and record.get("validation", {}).get("ok")
    )
    repaired_records = [
        record for record in records if int(record.get("simulation_repair_attempts", 0)) > 0
    ]
    wall_times = [
        float(record.get("wall_time_sec", record.get("score", {}).get("wall_time_sec", 0.0)) or 0.0)
        for record in records
    ]
    input_tokens = sum(int(record.get("input_tokens", 0)) for record in records)
    output_tokens = sum(int(record.get("output_tokens", 0)) for record in records)
    total_tokens = sum(int(record.get("total_tokens", 0)) for record in records)
    summary = {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_id": model_id,
        "scaffold_label": next(
            (str(record.get("scaffold_label")) for record in records if record.get("scaffold_label")),
            "",
        ),
        "task_count": len(records),
        "package_complete_count": sum(
            1 for record in records if record.get("validation", {}).get("package_complete")
        ),
        "deterministic_pass_count": sum(
            1 for record in records if record.get("deterministic_checks_pass")
        ),
        "validator_ok_count": sum(1 for record in records if record.get("validation", {}).get("ok")),
        "simulation_attempted_count": sum(1 for record in records if record.get("simulation") is not None),
        "simulation_pass_count": sum(
            1
            for record in records
            if isinstance(record.get("simulation"), dict) and record["simulation"].get("ok")
        ),
        "first_pass_simulation_pass_count": sum(
            1
            for record in records
            if isinstance(record.get("first_simulation"), dict)
            and record["first_simulation"].get("ok")
        ),
        "first_pass_validator_pass_count": first_pass_validator_pass_count,
        "repaired_simulation_pass_count": repaired_simulation_pass_count,
        "repaired_validator_pass_count": repaired_validator_pass_count,
        "simulation_repair_attempts": sum(
            int(record.get("simulation_repair_attempts", 0)) for record in records
        ),
        "repair_success_count": sum(1 for record in records if record.get("repair_success")),
        "avg_repair_attempts_when_repaired": (
            sum(int(record.get("simulation_repair_attempts", 0)) for record in repaired_records)
            / len(repaired_records)
            if repaired_records
            else 0.0
        ),
        "max_repair_attempts_observed": max(
            [int(record.get("simulation_repair_attempts", 0)) for record in records] or [0]
        ),
        "provider_error_count": sum(int(record.get("provider_error_count", 0)) for record in records),
        "provider_errors_per_task": {
            str(record.get("task_id")): int(record.get("provider_error_count", 0))
            for record in records
            if record.get("task_id")
        },
        "generation_attempts_per_task": {
            str(record.get("task_id")): int(record.get("generation_attempts", 0))
            for record in records
            if record.get("task_id")
        },
        "repair_attempts_per_task": {
            str(record.get("task_id")): int(record.get("simulation_repair_attempts", 0))
            for record in records
            if record.get("task_id")
        },
        "attempts_per_task": attempts_per_task,
        "error_count": sum(1 for record in records if "error" in record),
        "total_attempts": sum(int(record.get("attempts", 0)) for record in records),
        "total_wall_time_sec": sum(wall_times),
        "avg_wall_time_sec": sum(wall_times) / len(wall_times) if wall_times else 0.0,
        "max_wall_time_sec": max(wall_times or [0.0]),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "tokens_per_task": {
            str(record.get("task_id")): int(record.get("total_tokens", 0))
            for record in records
            if record.get("task_id")
        },
        "tool_calls": sum(int(record.get("tool_calls", 0)) for record in records),
        "skill_loads": sum(int(record.get("skill_loads", 0)) for record in records),
        "protocol_hits": sum(int(record.get("protocol_hits", 0)) for record in records),
        "memory_hits": sum(int(record.get("memory_hits", 0)) for record in records),
        "kb_context_tokens_estimate": sum(
            int(record.get("kb_context_tokens_estimate", 0)) for record in records
        ),
        "repair_patch_count": sum(int(record.get("repair_patch_count", 0)) for record in records),
        "repair_patch_rejected_count": sum(
            int(record.get("repair_patch_rejected_count", 0)) for record in records
        ),
        "repair_patch_backend": _summary_patch_backend(records),
        "simulator_calls": sum(int(record.get("simulator_calls", 0)) for record in records),
        "records": records,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _write_record(task_dir: Path, record: dict[str, Any]) -> None:
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")


def _summary_patch_backend(records: list[dict[str, Any]]) -> str:
    backends = {
        str(record.get("repair_patch_backend", "none"))
        for record in records
        if record.get("repair_patch_backend")
    }
    if not backends:
        return "none"
    if len(backends) == 1:
        return next(iter(backends))
    return "mixed:" + ",".join(sorted(backends))


def _simulator_summary(simulation_result: dict[str, Any] | None) -> dict[str, Any] | None:
    if simulation_result is None:
        return None
    return {
        "ok": bool(simulation_result.get("ok")),
        "returncode": simulation_result.get("returncode"),
        "stdout_tail": str(simulation_result.get("stdout", ""))[-1200:],
        "stderr_tail": str(simulation_result.get("stderr", ""))[-1200:],
        "error": simulation_result.get("error"),
    }


def _offline_author(task: AuthoringTask, *, model_id: str) -> dict[str, str]:
    now = datetime.now(timezone.utc).isoformat()
    manifest = {
        "schema_version": "0.4",
        "task_id": task.task_id,
        "system_id": "labscriptai",
        "model_id": model_id,
        "scaffold_id": "authoring-pilot-offline-v0.4",
        "prompt_hash": _prompt_hash(task.prompt),
        "deck": {
            "slots": [
                {"name": "opentrons_96_wellplate_200ul_pcr_full_skirt", "slot": "D1"},
                {"name": "opentrons_flex_96_tiprack_200ul", "slot": "A1"},
            ],
            "modules": [],
            "instruments": [{"name": "flex_1channel_1000", "mount": "left"}],
        },
        "reagents": [
            {
                "name": "water",
                "required_volume_ul": 100,
                "available_volume_ul": 500,
                "dead_volume_ul": 50,
            }
        ],
        "tips": {"tips_required": 1, "tips_available": 96},
        "risk_flags": [],
        "critical_failures": [],
        "off_platform_handoff": {"declared": False},
        "tool_permissions": ["validate_package"],
        "budget": {"attempts": 8, "wall_min": 30, "tokens": 24000},
        "timestamp": now,
    }
    return {
        "protocol.py": 'metadata = {"protocolName": "authoring pilot placeholder", "apiLevel": "2.15"}\ndef run(protocol):\n    pass\n',
        "setup_card.html": f"<h1>Setup</h1><p>Review task {task.task_id} and load declared labware.</p>\n",
        "manifest.json": json.dumps(manifest, indent=2),
    }


def run_authoring_pilot(
    *,
    tasks_path: Path,
    output_dir: Path,
    package_author: Callable[[AuthoringTask], dict[str, str]],
    model_id: str,
    limit: int = 6,
    task_split: str = "holdout",
    task_ids: tuple[str, ...] = (),
    simulate: bool = False,
    opentrons_python: str | None = None,
    workspace_root: Path | None = None,
    simulation_timeout_sec: int = 180,
    retry_attempts: int = 1,
    protocol_repairer: Callable[[AuthoringTask, str, dict[str, Any]], str] | None = None,
    simulation_repair_attempts: int = 3,
    scaffold_label: str = "",
    repair_edit_mode: str = "rewrite",
    derive_from_protocol: bool = False,
    derive_scaffold_id: str = "protocol-py-derived-v0.4",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    if retry_attempts < 1:
        raise ValueError("retry_attempts must be >= 1")
    for task in _selected_tasks(
        tasks_path,
        limit=limit,
        task_split=task_split,
        task_ids=task_ids,
    ):
        task_dir = output_dir / task.task_id
        started = time.monotonic()
        errors: list[str] = []
        for generation_attempt in range(1, retry_attempts + 1):
            attempt = generation_attempt
            package_dir = task_dir / f"attempt{attempt}" / "package"
            try:
                files = package_author(task)
                write_package_files(package_dir, files)
                authoring_stats = _read_authoring_stats(package_dir)
                derive_result: dict[str, Any] | None = None
                if derive_from_protocol:
                    derive_result = derive_package_from_protocol(
                        package_dir,
                        task,
                        model_id=model_id,
                        scaffold_id=derive_scaffold_id,
                    )
                else:
                    stamp_manifest(package_dir, task, model_id=model_id)
                initial_validation = validate_package(package_dir, simulation_pass=False)
                repairs = repair_package_metadata(package_dir)
                if derive_from_protocol:
                    derive_result = derive_package_from_protocol(
                        package_dir,
                        task,
                        model_id=model_id,
                        scaffold_id=derive_scaffold_id,
                    )
                simulation_result: dict[str, Any] | None = None
                first_simulation: dict[str, Any] | None = None
                first_pass_validation = validate_package(package_dir, simulation_pass=False)
                repair_errors: list[str] = []
                repair_success = False
                repair_count = 0
                repair_input_tokens = 0
                repair_output_tokens = 0
                repair_total_tokens = 0
                repair_patch_count = 0
                repair_patch_rejected_count = 0
                if simulate:
                    simulation_result = simulate_protocol_file(
                        package_dir / "protocol.py",
                        opentrons_python=opentrons_python,
                        workspace_root=workspace_root,
                        timeout_sec=simulation_timeout_sec,
                    )
                    first_simulation = simulation_result
                    first_pass_validation = validate_package(
                        package_dir,
                        simulation_pass=bool(simulation_result.get("ok")),
                    )
                    while (
                        protocol_repairer is not None
                        and not simulation_result.get("ok")
                        and repair_count < simulation_repair_attempts
                    ):
                        repair_count += 1
                        next_attempt = attempt + 1
                        next_package_dir = task_dir / f"attempt{next_attempt}" / "package"
                        if next_package_dir.exists():
                            shutil.rmtree(next_package_dir)
                        shutil.copytree(package_dir, next_package_dir)
                        current_protocol = (package_dir / "protocol.py").read_text(encoding="utf-8")
                        try:
                            repaired_protocol = protocol_repairer(
                                task,
                                current_protocol,
                                simulation_result,
                            )
                            usage = getattr(repaired_protocol, "usage", None)
                            usage_stats = _usage_stats(usage)
                            repair_input_tokens += usage_stats["input_tokens"]
                            repair_output_tokens += usage_stats["output_tokens"]
                            repair_total_tokens += usage_stats["total_tokens"]
                            repair_patch_count += int(getattr(repaired_protocol, "patch_count", 0))
                            repair_patch_rejected_count += int(
                                getattr(repaired_protocol, "patch_rejected_count", 0)
                            )
                            (next_package_dir / "protocol.py").write_text(
                                repaired_protocol,
                                encoding="utf-8",
                            )
                            package_dir = next_package_dir
                            attempt = next_attempt
                            if derive_from_protocol:
                                derive_result = derive_package_from_protocol(
                                    package_dir,
                                    task,
                                    model_id=model_id,
                                    scaffold_id=derive_scaffold_id,
                                )
                            repairs = repair_package_metadata(package_dir)
                            if derive_from_protocol:
                                derive_result = derive_package_from_protocol(
                                    package_dir,
                                    task,
                                    model_id=model_id,
                                    scaffold_id=derive_scaffold_id,
                                )
                            simulation_result = simulate_protocol_file(
                                package_dir / "protocol.py",
                                opentrons_python=opentrons_python,
                                workspace_root=workspace_root,
                                timeout_sec=simulation_timeout_sec,
                            )
                            repair_success = bool(simulation_result.get("ok"))
                        except Exception as exc:
                            usage_stats = _usage_stats(getattr(exc, "usage", None))
                            repair_input_tokens += usage_stats["input_tokens"]
                            repair_output_tokens += usage_stats["output_tokens"]
                            repair_total_tokens += usage_stats["total_tokens"]
                            repair_patch_rejected_count += int(
                                getattr(exc, "rejected_count", 0)
                            )
                            repair_errors.append(f"{type(exc).__name__}: {exc}")
                            package_dir = next_package_dir
                            attempt = next_attempt
                            continue
                simulation_pass = bool(simulation_result and simulation_result.get("ok"))
                validation = validate_package(package_dir, simulation_pass=simulation_pass)
                manifest_path = package_dir / "manifest.json"
                manifest = {}
                if manifest_path.exists():
                    try:
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    except json.JSONDecodeError:
                        manifest = {"task_id": task.task_id, "system_id": "labscriptai", "model_id": model_id, "scaffold_id": "invalid"}
                score = score_record_from_validation(
                    validation,
                    manifest,
                    first_pass=generation_attempt == 1 and repair_count == 0,
                    attempts=attempt,
                    wall_time_sec=time.monotonic() - started,
                    input_tokens=authoring_stats["input_tokens"] + repair_input_tokens,
                    output_tokens=authoring_stats["output_tokens"] + repair_output_tokens,
                ).to_dict()
                wall_time_sec = float(score["wall_time_sec"])
                input_tokens = authoring_stats["input_tokens"] + repair_input_tokens
                output_tokens = authoring_stats["output_tokens"] + repair_output_tokens
                total_tokens = (
                    authoring_stats["total_tokens"] + repair_total_tokens
                    if authoring_stats["total_tokens"] or repair_total_tokens
                    else input_tokens + output_tokens
                )
                record = {
                    "task_id": task.task_id,
                    "scaffold_label": scaffold_label,
                    "difficulty": task.difficulty,
                    "holdout": task.holdout,
                    "package_dir": str(package_dir),
                    "attempts": attempt,
                    "generation_attempts": generation_attempt,
                    "provider_error_count": len(errors),
                    "prior_errors": errors,
                    "wall_time_sec": wall_time_sec,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "authoring_input_tokens": authoring_stats["input_tokens"],
                    "authoring_output_tokens": authoring_stats["output_tokens"],
                    "authoring_total_tokens": authoring_stats["total_tokens"],
                    "repair_input_tokens": repair_input_tokens,
                    "repair_output_tokens": repair_output_tokens,
                    "repair_total_tokens": repair_total_tokens,
                    "repair_edit_mode": repair_edit_mode,
                    "repair_patch_backend": "diff_edit"
                    if repair_edit_mode == "patch_only"
                    else "rewrite",
                    "repair_patch_count": repair_patch_count,
                    "repair_patch_rejected_count": repair_patch_rejected_count,
                    "initial_validation": initial_validation.to_dict(),
                    "first_pass_validation": first_pass_validation.to_dict()
                    if first_pass_validation is not None
                    else None,
                    "repairs": repairs,
                    "derive": derive_result,
                    "first_simulation": first_simulation,
                    "simulation": simulation_result,
                    "simulator_summary": _simulator_summary(simulation_result),
                    "simulation_repair_attempts": repair_count,
                    "repair_success": repair_success,
                    "repair_errors": repair_errors,
                    "tool_calls": authoring_stats["tool_calls"],
                    "skill_loads": authoring_stats["skill_loads"],
                    "protocol_hits": authoring_stats["protocol_hits"],
                    "memory_hits": authoring_stats["memory_hits"],
                    "kb_context_tokens_estimate": authoring_stats["kb_context_tokens_estimate"],
                    "simulator_calls": authoring_stats["simulator_calls"]
                    + (1 if first_simulation is not None else 0)
                    + repair_count,
                    "validation": validation.to_dict(),
                    "deterministic_checks_pass": validation.package_complete
                    and not validation.critical_failures
                    and not validation.issues,
                    "score": score,
                }
            except Exception as exc:  # pragma: no cover - exercised by live API failures.
                errors.append(f"{type(exc).__name__}: {exc}")
                usage_stats = _usage_stats(getattr(exc, "usage", None))
                record = {
                    "task_id": task.task_id,
                    "scaffold_label": scaffold_label,
                    "difficulty": task.difficulty,
                    "holdout": task.holdout,
                    "package_dir": str(package_dir),
                    "attempts": attempt,
                    "generation_attempts": generation_attempt,
                    "provider_error_count": len(errors),
                    "wall_time_sec": time.monotonic() - started,
                    "input_tokens": usage_stats["input_tokens"],
                    "output_tokens": usage_stats["output_tokens"],
                    "total_tokens": usage_stats["total_tokens"],
                    "error": errors[-1],
                    "errors": errors,
                }
                _write_record(task_dir, record)
                if generation_attempt < retry_attempts:
                    continue
            _write_record(task_dir, record)
            break
        records.append(record)
        _write_summary(output_dir, model_id, records)

    return _write_summary(output_dir, model_id, records)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=Path("benchmarks/authoring/tasks.yaml"))
    parser.add_argument("--output-dir", type=Path, default=Path("runs/authoring-pilot/latest"))
    parser.add_argument("--provider", choices=("offline", "deepseek", "labscriptai-authoring", "labscriptai-unified"), default="offline")
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument(
        "--task-ids",
        default="",
        help="Comma-separated task ids to run exactly, e.g. T056,T057. Overrides --limit/--task-split.",
    )
    parser.add_argument(
        "--task-split",
        choices=("holdout", "all"),
        default="holdout",
        help="Task subset to run. Use 'all' with --limit 90 for the full benchmark.",
    )
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--opentrons-python")
    parser.add_argument("--workspace-root", type=Path)
    parser.add_argument("--simulation-timeout-sec", type=int, default=180)
    parser.add_argument("--retry-attempts", type=int, default=4)
    parser.add_argument("--simulation-repair-attempts", type=int, default=3)
    parser.add_argument(
        "--repair-edit-mode",
        choices=("rewrite", "patch_only"),
        default="rewrite",
        help="How simulation repair edits protocol.py. patch_only applies DiffEdit SEARCH/REPLACE blocks.",
    )
    parser.add_argument("--agent-max-steps", type=int, default=12)
    parser.add_argument(
        "--direct-prompt-mode",
        choices=("bare", "rules"),
        default="rules",
        help="Prompt detail for --provider deepseek direct generation.",
    )
    parser.add_argument(
        "--direct-output-mode",
        choices=("package", "protocol"),
        default="protocol",
        help="For --provider deepseek, benchmark runs use py-only generation and derive sidecars from protocol.py.",
    )
    parser.add_argument(
        "--derive-from-protocol",
        action="store_true",
        help="Derive manifest.json and setup_card.html from protocol.py before validation.",
    )
    parser.add_argument(
        "--derive-scaffold-id",
        default="",
        help="Optional scaffold_id to stamp into derived manifest.json.",
    )
    parser.add_argument(
        "--api-prefix",
        choices=("auto", "DEEPSEEK", "LLM_ONLY"),
        default="auto",
        help="Which OpenAI-compatible environment prefix to use. auto prefers LLM_ONLY then DEEPSEEK.",
    )
    parser.add_argument(
        "--authoring-skill-mode",
        choices=("full", "light", "off"),
        default="light",
        help="Skill exposure for --provider labscriptai-authoring. Use off/light for external ablations.",
    )
    parser.add_argument(
        "--tool-profile",
        choices=("edit", "simulate", "kb", "kb_strong"),
        default="kb",
        help="Tool exposure for --provider labscriptai-authoring scaffold ablations.",
    )
    parser.add_argument(
        "--kb-context-mode",
        choices=("full", "compact", "compact_v2", "none"),
        default="full",
        help="KB context size for --tool-profile kb_strong. compact_v2 injects only route, obligations, and one failure pattern.",
    )
    parser.add_argument(
        "--scaffold-label",
        default="",
        help="Optional label copied into records and summary for ablation tables.",
    )
    args = parser.parse_args(argv)
    args.simulation_repair_attempts = min(args.simulation_repair_attempts, 3)
    if args.provider in {"deepseek", "labscriptai-authoring", "labscriptai-unified"}:
        args.derive_from_protocol = True
    if args.provider == "deepseek":
        args.direct_output_mode = "protocol"
    task_ids = tuple(task_id.strip() for task_id in args.task_ids.split(",") if task_id.strip())

    protocol_repairer = None
    if args.provider == "deepseek":
        config = _authoring_openai_config(default_model="deepseek-v4-pro", api_prefix=args.api_prefix)
        author = lambda task: call_protocol_author(config, task)
        model_id = config.model
        protocol_repairer = _build_protocol_repairer(config, args.repair_edit_mode)
    elif args.provider == "labscriptai-authoring":
        config = _authoring_openai_config(default_model="deepseek-v4-pro", api_prefix=args.api_prefix)
        model_id = config.model
        protocol_repairer = _build_protocol_repairer(config, args.repair_edit_mode)

        def author(task: AuthoringTask) -> dict[str, str]:
            with tempfile.TemporaryDirectory() as tmp:
                agent = AuthoringAgent(
                    client=OpenAICompatibleAuthoringClient(config),
                    max_steps=args.agent_max_steps,
                    skill_mode=args.authoring_skill_mode,
                    tool_profile=args.tool_profile,
                    protocol_only=args.derive_from_protocol,
                )
                return agent.run_to_files(
                    task=task,
                    work_dir=Path(tmp),
                    opentrons_python=args.opentrons_python,
                    workspace_root=args.workspace_root,
                    simulation_timeout_sec=args.simulation_timeout_sec,
                )
    elif args.provider == "labscriptai-unified":
        config = _authoring_openai_config(default_model="deepseek-v4-pro", api_prefix=args.api_prefix)
        model_id = config.model
        protocol_repairer = _build_protocol_repairer(config, args.repair_edit_mode)

        def author(task: AuthoringTask) -> dict[str, str]:
            with tempfile.TemporaryDirectory() as tmp:
                facade = UnifiedAuthoringFacade(
                    client=OpenAICompatibleAuthoringClient(config),
                    max_steps=args.agent_max_steps,
                    skill_mode=args.authoring_skill_mode,
                    tool_profile=args.tool_profile,
                    kb_context_mode=args.kb_context_mode,
                    protocol_only=args.derive_from_protocol,
                )
                return facade.run_to_files(
                    task=task,
                    work_dir=Path(tmp),
                    opentrons_python=args.opentrons_python,
                    workspace_root=args.workspace_root,
                    simulation_timeout_sec=args.simulation_timeout_sec,
                )
    else:
        model_id = "offline-placeholder"
        author = lambda task: _offline_author(task, model_id=model_id)

    summary = run_authoring_pilot(
        tasks_path=args.tasks,
        output_dir=args.output_dir,
        package_author=author,
        model_id=model_id,
        limit=args.limit,
        task_split=args.task_split,
        task_ids=task_ids,
        simulate=args.simulate,
        opentrons_python=args.opentrons_python,
        workspace_root=args.workspace_root,
        simulation_timeout_sec=args.simulation_timeout_sec,
        retry_attempts=args.retry_attempts,
        protocol_repairer=protocol_repairer,
        simulation_repair_attempts=args.simulation_repair_attempts,
        scaffold_label=args.scaffold_label,
        repair_edit_mode=args.repair_edit_mode,
        derive_from_protocol=args.derive_from_protocol,
        derive_scaffold_id=args.derive_scaffold_id
        or (
            "llm-only-py-derived-v0.4"
            if args.provider == "deepseek" and args.direct_output_mode == "protocol"
            else "agent-py-derived-v0.4"
            if args.derive_from_protocol
            else "protocol-py-derived-v0.4"
        ),
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
