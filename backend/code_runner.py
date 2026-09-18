# -*- coding: utf-8 -*-
"""Pure-Python Opentrons protocol code generation loop.

SSE event fields stay compatible with run_code_generation_graph_stream.
"""

from __future__ import annotations

import ast
import asyncio
import re
import time
import traceback
from datetime import datetime
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Optional

from backend.config import (
    CODE_EXAMPLES,
    COMMON_PITFALLS_OT2,
    INSTRUMENTS_FOR_FLEX,
    INSTRUMENTS_FOR_OT2,
    LABWARE_FOR_FLEX,
    LABWARE_FOR_OT2,
    MODULES_FOR_FLEX,
    MODULES_FOR_OT2,
)
from backend.langchain_agent import _clean_llm_code_output, prepare_feedback_node
from backend.llm_client import astream_parts, complete
from backend.opentrons_utils import run_opentrons_simulation
from backend.prompts import (
    CODE_GENERATION_PROMPT_TEMPLATE_FLEX,
    CODE_GENERATION_PROMPT_TEMPLATE_OT2,
)

CONFIG_SEPARATOR = "\n---CONFIG_SEPARATOR---\n"
HEARTBEAT_INTERVAL = 15.0
MAX_EMPTY_SCRIPT_ATTEMPTS = 2
EMPTY_SCRIPT_ERROR = "模型没有返回可执行协议代码。"
NON_EXECUTABLE_PROTOCOL_ERROR = (
    "生成结果不是可执行协议（例如只 raise）。必须按 SOP 写出完整 load + 移液步骤"
)
CompleteFn = Callable[[str], Awaitable[str]]
StreamFn = Callable[[str], AsyncIterator[Dict[str, Any]]]
SimulateFn = Callable[..., Any]


def _now() -> str:
    return datetime.now().isoformat()


def _event(event_type: str, **fields: Any) -> Dict[str, Any]:
    payload = {"event_type": event_type, "timestamp": _now()}
    payload.update(fields)
    return payload


def _parse_tool_input(tool_input: str) -> tuple[str, str]:
    if CONFIG_SEPARATOR not in tool_input:
        raise ValueError(
            "Error: Input for ProtocolCodeGenerator must contain SOP and hardware "
            "context separated by '\\n---CONFIG_SEPARATOR---\\n'."
        )
    original_sop, hardware_context = tool_input.split(CONFIG_SEPARATOR, 1)
    return original_sop.strip(), hardware_context.strip()


def _build_generator_prompt(
    original_sop: str,
    hardware_context: str,
    attempts: int,
    python_code: Optional[str],
    feedback_for_llm: Dict[str, str],
) -> str:
    is_flex = "flex" in hardware_context.lower()
    if is_flex:
        valid_labware = LABWARE_FOR_FLEX
        valid_instruments = INSTRUMENTS_FOR_FLEX
        valid_modules = MODULES_FOR_FLEX
        template = CODE_GENERATION_PROMPT_TEMPLATE_FLEX
        common_pitfalls_str = ""
    else:
        valid_labware = LABWARE_FOR_OT2
        valid_instruments = INSTRUMENTS_FOR_OT2
        valid_modules = MODULES_FOR_OT2
        template = CODE_GENERATION_PROMPT_TEMPLATE_OT2
        common_pitfalls_str = "\n".join(f"- {pitfall}" for pitfall in COMMON_PITFALLS_OT2)

    api_version_match = re.search(r"API Version:\s*([\d.]+)", hardware_context)
    api_version = api_version_match.group(1) if api_version_match else "2.19"

    if attempts == 0:
        feedback_text = ""
        previous_code = "N/A"
    else:
        feedback_sections = [
            "Previous attempt failed. Regenerate a fresh, complete script that addresses the issues below.",
            f"- Analysis: {feedback_for_llm.get('analysis', 'N/A')}",
            f"- Recommended Action: {feedback_for_llm.get('action', 'N/A')}",
            f"- Error Log: {feedback_for_llm.get('error_log', 'N/A')}",
        ]
        if python_code:
            feedback_sections.append("Previous Code (for reference):")
            feedback_sections.append("```python")
            feedback_sections.append(python_code)
            feedback_sections.append("```")
        feedback_text = "\n".join(feedback_sections)
        previous_code = python_code if python_code else "N/A"

    chain_input = {
        "hardware_context": hardware_context,
        "sop_text": original_sop,
        "feedback_for_llm": feedback_text,
        "previous_code": previous_code,
        "valid_labware_list_str": "\n".join(f"- {name}" for name in valid_labware),
        "valid_instrument_list_str": "\n".join(f"- {name}" for name in valid_instruments),
        "valid_module_list_str": "\n".join(f"- {name}" for name in valid_modules),
        "code_examples_str": CODE_EXAMPLES,
        "apiLevel": api_version,
    }
    if not is_flex:
        chain_input["common_pitfalls_str"] = common_pitfalls_str
    return template.format(**chain_input)


def _empty_simulation_result(error_details: str) -> Dict[str, Any]:
    return {
        "success": False,
        "has_warnings": False,
        "error_details": error_details,
        "warning_details": "",
        "raw_output": error_details,
        "final_status": "失败",
    }


def _is_empty_generated_script(code: str) -> bool:
    stripped = (code or "").strip()
    return not stripped or "def run(" not in stripped


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


_LOAD_FUNCS = {"load_labware", "load_instrument"}
_PIPETTE_FUNCS = {
    "aspirate",
    "dispense",
    "transfer",
    "mix",
    "pick_up_tip",
    "drop_tip",
    "return_tip",
    "blow_out",
    "touch_tip",
}
_EXCEPTION_IN_SIM_RE = re.compile(
    r"traceback|runtimeerror|exception:|invalidaspirate|[a-z][a-z0-9_]*error",
    re.IGNORECASE,
)


def _has_named_call(tree: ast.AST, names: set[str]) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) in names:
            return True
    return False


def _has_load_call(tree: ast.AST) -> bool:
    return _has_named_call(tree, _LOAD_FUNCS)


def _has_pipette_call(tree: ast.AST) -> bool:
    return _has_named_call(tree, _PIPETTE_FUNCS)


def _is_ignorable_run_stmt(stmt: ast.stmt) -> bool:
    if isinstance(stmt, ast.Pass):
        return True
    if isinstance(stmt, ast.Expr):
        value = stmt.value
        if isinstance(value, ast.Constant) and isinstance(value.value, (str, type(...))):
            return True
    return False


def _run_body_is_stub(run_fn: ast.FunctionDef) -> bool:
    meaningful = [stmt for stmt in run_fn.body if not _is_ignorable_run_stmt(stmt)]
    if not meaningful:
        return True
    if all(isinstance(stmt, ast.Raise) for stmt in meaningful):
        return True
    # load + raise、没有真正移液：OT-2 实测里会被标成假成功
    has_raise = any(
        isinstance(stmt, ast.Raise) or _stmt_contains_raise(stmt) for stmt in meaningful
    )
    return has_raise and not _has_pipette_call(run_fn)


def _stmt_contains_raise(stmt: ast.stmt) -> bool:
    return any(isinstance(node, ast.Raise) for node in ast.walk(stmt))


def _find_run_function(tree: ast.AST) -> Optional[ast.FunctionDef]:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "run":
            return node
    return None


def _is_executable_protocol_heuristic(code: str) -> bool:
    if "def run(" not in code:
        return False
    if "load_labware" not in code and "load_instrument" not in code:
        return False
    in_run = False
    body_lines: list[str] = []
    for line in code.splitlines():
        if not in_run:
            if re.match(r"def run\s*\(", line):
                in_run = True
            continue
        if line.strip() and not line[0].isspace():
            break
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(('"""', "'''")):
            continue
        body_lines.append(stripped)
    if not body_lines:
        return False
    if all(item == "pass" or item == "..." or item.startswith("raise ") for item in body_lines):
        return False
    has_raise = any(item.startswith("raise ") for item in body_lines)
    has_pipette = any(
        name in "\n".join(body_lines) for name in _PIPETTE_FUNCS
    )
    if has_raise and not has_pipette:
        return False
    return True


def _is_executable_protocol(code: str) -> bool:
    if _is_empty_generated_script(code):
        return False
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return _is_executable_protocol_heuristic(code)
    run_fn = _find_run_function(tree)
    if run_fn is None:
        return False
    if not _has_load_call(tree):
        return False
    if _run_body_is_stub(run_fn):
        return False
    return True


def _simulation_hides_exception(simulation_result: Dict[str, Any]) -> bool:
    blob = "\n".join(
        [
            str(simulation_result.get("raw_output") or ""),
            str(simulation_result.get("warning_details") or ""),
            str(simulation_result.get("error_details") or ""),
        ]
    )
    return bool(_EXCEPTION_IN_SIM_RE.search(blob))


def _failure_report(
    current_attempt: int,
    error_details: str,
    final_code: str,
    original_sop: str,
) -> str:
    return f"""**协议生成失败报告**

**总体状态**: 经过 {current_attempt} 次尝试后失败

**最后一次错误详情**:
{error_details}

**最后生成的代码** (可参考修改):
```python
{final_code}
```

**原始SOP**:
{original_sop}

**建议**:
- 检查SOP中是否包含不兼容的硬件要求
- 确认试剂体积和移液器容量匹配
- 验证deck layout是否正确配置
- 如果错误持续，请考虑简化实验步骤"""


async def _complete_with_heartbeat(
    prompt: str,
    complete_fn: CompleteFn,
    heartbeat_interval: float,
) -> AsyncIterator[Any]:
    """Await complete_fn; yield thinking dicts every heartbeat_interval seconds.

    Timeout does not cancel the pending complete task. Caller cancel happens
    in the finally block when the consumer disconnects.
    """
    pending = asyncio.ensure_future(complete_fn(prompt))
    try:
        while True:
            done, _pending = await asyncio.wait({pending}, timeout=heartbeat_interval)
            if not done:
                yield _event("thinking", message="Model is reasoning...")
                continue
            yield pending.result()
            return
    finally:
        if not pending.done():
            pending.cancel()


async def _stream_with_heartbeat(
    prompt: str,
    stream_fn: StreamFn,
    heartbeat_interval: float,
) -> AsyncIterator[Any]:
    """Yield thinking events from reasoning parts; then the joined content.

    Empty 15s gaps still emit a heartbeat. Reasoning never enters the content.
    """
    aiter = stream_fn(prompt).__aiter__()
    pending = asyncio.ensure_future(aiter.__anext__())
    content_parts: list[str] = []
    think_buf: list[str] = []
    last_flush = time.monotonic()

    def _flush_thinking(force: bool = False) -> Optional[Dict[str, Any]]:
        nonlocal last_flush
        if not think_buf:
            return None
        joined = "".join(think_buf)
        if not force and len(joined) < 40 and time.monotonic() - last_flush < 0.08:
            return None
        think_buf.clear()
        last_flush = time.monotonic()
        return _event("thinking", token=joined, message=joined)

    try:
        while True:
            done, _pending = await asyncio.wait({pending}, timeout=heartbeat_interval)
            if not done:
                flushed = _flush_thinking(force=True)
                if flushed:
                    yield flushed
                yield _event("thinking", message="Model is reasoning...")
                continue
            try:
                item = pending.result()
            except StopAsyncIteration:
                break
            kind = item.get("kind") if isinstance(item, dict) else None
            text = item.get("text") if isinstance(item, dict) else None
            text = text if isinstance(text, str) else ""
            if kind == "reasoning" and text:
                think_buf.append(text)
                flushed = _flush_thinking()
                if flushed:
                    yield flushed
            elif kind == "content" and text:
                flushed = _flush_thinking(force=True)
                if flushed:
                    yield flushed
                content_parts.append(text)
            pending = asyncio.ensure_future(aiter.__anext__())
        flushed = _flush_thinking(force=True)
        if flushed:
            yield flushed
        yield "".join(content_parts)
    finally:
        if not pending.done():
            pending.cancel()


async def run_code_generation_python_stream(
    tool_input: str,
    max_iterations: int = 9,
    *,
    complete_fn: Optional[CompleteFn] = None,
    stream_fn: Optional[StreamFn] = None,
    simulate_fn: Optional[SimulateFn] = None,
    heartbeat_interval: float = HEARTBEAT_INTERVAL,
) -> AsyncIterator[Dict[str, Any]]:
    injected_complete = complete_fn
    complete_fn = complete_fn or complete
    simulate_fn = simulate_fn or run_opentrons_simulation
    original_sop = ""
    current_attempt = 0
    python_code: Optional[str] = None
    simulation_result: Dict[str, Any] = {}
    feedback_for_llm: Dict[str, str] = {}

    try:
        print("Debug - [run_code_generation_python_stream] 开始纯 Python 流式代码生成")
        yield _event("start", message="开始协议代码生成流程...")

        try:
            original_sop, hardware_context = _parse_tool_input(tool_input)
        except ValueError as exc:
            yield _event("error", message=str(exc))
            return

        if not original_sop:
            yield _event(
                "error",
                message="Error: SOP is empty. Protocol generation requires a non-empty SOP.",
            )
            return
        if not hardware_context:
            yield _event(
                "error",
                message=(
                    "Error: hardware_context is empty. "
                    "Protocol generation requires hardware context."
                ),
            )
            return

        yield _event(
            "initialization",
            message=f"初始化完成，最大尝试次数: {max_iterations}",
            max_attempts=max_iterations,
        )

        empty_script_count = 0
        while current_attempt < max_iterations:
            prompt = _build_generator_prompt(
                original_sop,
                hardware_context,
                current_attempt,
                python_code,
                feedback_for_llm,
            )
            raw_code = None
            if injected_complete is not None:
                async for item in _complete_with_heartbeat(
                    prompt, complete_fn, heartbeat_interval
                ):
                    if isinstance(item, dict) and item.get("event_type") == "thinking":
                        yield item
                    else:
                        raw_code = item
            else:
                async for item in _stream_with_heartbeat(
                    prompt, stream_fn or astream_parts, heartbeat_interval
                ):
                    if isinstance(item, dict) and item.get("event_type") == "thinking":
                        yield item
                    else:
                        raw_code = item

            python_code = _clean_llm_code_output(raw_code or "")
            current_attempt += 1
            yield _event(
                "node_complete",
                node_name="generator",
                message=f"第 {current_attempt} 次代码生成完成",
                attempt_num=current_attempt,
                has_code=bool(python_code),
            )

            if _is_empty_generated_script(python_code):
                empty_script_count += 1
                simulation_result = _empty_simulation_result(EMPTY_SCRIPT_ERROR)
            else:
                simulation_result = await asyncio.to_thread(
                    simulate_fn, python_code, True
                )
                if simulation_result.get("success") and not _is_executable_protocol(
                    python_code or ""
                ):
                    simulation_result = _empty_simulation_result(
                        NON_EXECUTABLE_PROTOCOL_ERROR
                    )
                elif simulation_result.get("success") and _simulation_hides_exception(
                    simulation_result
                ):
                    hidden = (
                        simulation_result.get("error_details")
                        or simulation_result.get("warning_details")
                        or simulation_result.get("raw_output")
                        or NON_EXECUTABLE_PROTOCOL_ERROR
                    )
                    simulation_result = _empty_simulation_result(str(hidden))

            success = bool(simulation_result.get("success", False))
            has_warnings = bool(simulation_result.get("has_warnings", False))
            yield _event(
                "node_complete",
                node_name="simulator",
                message=f"第 {current_attempt} 次模拟验证完成",
                attempt_num=current_attempt,
                simulation_success=success,
                has_warnings=has_warnings,
                error_details=simulation_result.get("error_details", "") if not success else "",
                warning_details=simulation_result.get("warning_details", "") if has_warnings else "",
                raw_output=simulation_result.get("raw_output", ""),
            )

            if success and not has_warnings:
                yield _event(
                    "attempt_result",
                    status="SUCCESS",
                    attempt_num=current_attempt,
                    message=f"第 {current_attempt} 次尝试成功！",
                    final_code=python_code or "",
                    warning_details="",
                )
                break

            if success and has_warnings:
                yield _event(
                    "attempt_result",
                    status="SUCCESS_WITH_WARNINGS",
                    attempt_num=current_attempt,
                    message=f"第 {current_attempt} 次尝试成功！" + " (有警告)",
                    final_code=python_code or "",
                    warning_details=simulation_result.get("warning_details", ""),
                )
                break

            empty_budget_exhausted = (
                _is_empty_generated_script(python_code)
                and empty_script_count >= MAX_EMPTY_SCRIPT_ATTEMPTS
            )
            if empty_budget_exhausted:
                yield _event(
                    "attempt_result",
                    status="FINAL_FAILED",
                    attempt_num=current_attempt,
                    message="模型没有返回可执行协议代码，已停止重试",
                    final_code=python_code or "",
                    error_details=EMPTY_SCRIPT_ERROR,
                )
                break

            if current_attempt >= max_iterations:
                yield _event(
                    "attempt_result",
                    status="FINAL_FAILED",
                    attempt_num=current_attempt,
                    message=f"达到最大尝试次数 ({max_iterations})，代码生成失败",
                    final_code=python_code or "",
                    error_details=simulation_result.get("error_details", ""),
                )
                break

            feedback_state = {
                "simulation_result": simulation_result,
                "feedback_for_llm": feedback_for_llm,
                "attempts": current_attempt,
                "iteration_reporter": None,
            }
            feedback_update = prepare_feedback_node(feedback_state)
            feedback_for_llm = feedback_update.get("feedback_for_llm", {})
            yield _event(
                "node_complete",
                node_name="feedback_preparer",
                message=f"第 {current_attempt} 次错误分析完成，准备下一轮修正",
                attempt_num=current_attempt,
                has_feedback=bool(feedback_for_llm),
                error_analysis=feedback_for_llm.get("analysis", ""),
            )

        final_success = bool(simulation_result.get("success", False))
        final_warnings = bool(simulation_result.get("has_warnings", False))
        final_code = python_code or ""
        if final_success:
            yield _event(
                "final_result",
                status="success",
                message="协议代码生成成功完成！",
                generated_code=final_code,
                has_warnings=final_warnings,
                warning_details=simulation_result.get("warning_details", "") if final_warnings else "",
                total_attempts=current_attempt,
            )
        else:
            error_details = simulation_result.get("error_details", "Unknown failure")
            yield _event(
                "final_result",
                status="failure",
                message="协议代码生成失败",
                error_report=_failure_report(
                    current_attempt, error_details, final_code, original_sop
                ),
                generated_code=final_code,
                error_details=error_details,
                total_attempts=current_attempt,
            )

    except Exception as exc:
        print(f"Debug - [run_code_generation_python_stream] Exception: {exc}")
        error_traceback = traceback.format_exc()
        print(f"Debug - 完整错误堆栈: {error_traceback}")
        yield _event(
            "error",
            message=f"协议生成过程中发生异常: {str(exc)}",
            error_traceback=error_traceback,
        )
