"""User-facing chat controller for LabscriptAI runtime recovery."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .actions import CandidateAction
from .agent_loop import CandidateProvider, ScriptedCandidateProvider, run_offline_loop
from .gatekeeper import GatekeeperDecision, evaluate_action
from .state import RuntimeState

StatusLoader = Callable[[], tuple[RuntimeState, Mapping[str, Any] | None]]
ChatProvider = Callable[..., str]
UnifiedChatHandler = Callable[[str, str], "ChatResponse"]


@dataclass(frozen=True)
class ChatMessage:
    role: str
    title: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class ChatResponse:
    messages: tuple[ChatMessage, ...]
    should_exit: bool = False


AuthoringRunner = Callable[[str, str], ChatResponse]


class RuntimeChatController:
    """Stateful conversation brain shared by the Textual UI and tests."""

    def __init__(
        self,
        *,
        state: RuntimeState,
        package_dir: Path,
        trace_path: Path,
        patch_log_path: Path,
        candidate_provider: CandidateProvider,
        chat_provider: ChatProvider | None = None,
        authoring_runner: AuthoringRunner | None = None,
        authoring_tasks_path: Path = Path("benchmarks/authoring/tasks.yaml"),
        authoring_output_dir: Path = Path("runs/tui-authoring"),
        authoring_opentrons_python: str | None = None,
        authoring_max_steps: int = 8,
        authoring_skill_mode: str = "light",
        authoring_tool_profile: str = "kb",
        authoring_simulation_timeout_sec: int = 180,
        unified_agent_chat: bool = False,
        simulation_pass: bool = False,
        status_loader: StatusLoader | None = None,
        unified_chat_handler: UnifiedChatHandler | None = None,
        robot_adapter: Any | None = None,
    ) -> None:
        self.state = state
        self.package_dir = package_dir
        self.trace_path = trace_path
        self.patch_log_path = patch_log_path
        self.candidate_provider = candidate_provider
        self.chat_provider = chat_provider
        self.authoring_runner = authoring_runner
        self.authoring_tasks_path = authoring_tasks_path
        self.authoring_output_dir = authoring_output_dir
        self.authoring_opentrons_python = authoring_opentrons_python
        self.authoring_max_steps = authoring_max_steps
        self.authoring_skill_mode = authoring_skill_mode
        self.authoring_tool_profile = authoring_tool_profile
        self.authoring_simulation_timeout_sec = authoring_simulation_timeout_sec
        self.unified_agent_chat = unified_agent_chat
        self.simulation_pass = simulation_pass
        self.status_loader = status_loader
        self.unified_chat_handler = unified_chat_handler
        self.robot_adapter = robot_adapter
        self.pending_action: CandidateAction | None = None
        self.pending_decision: GatekeeperDecision | None = None

    def welcome(self) -> ChatResponse:
        return ChatResponse(
            (
                ChatMessage(
                        "assistant",
                        "labscriptAI",
                        (
                            "Hi, I'm LabscriptAI. Tell me what you want to do in plain language.",
                            "I can chat, check robot status, help draft protocols, or look at run problems.",
                            "If anything could affect hardware, I will ask before doing it.",
                        ),
                    ),
            )
        )

    def handle_text(self, text: str) -> ChatResponse:
        normalized = text.strip()
        language = _detect_language(normalized)
        if not normalized:
            return ChatResponse(())
        if normalized in {"/exit", "/quit", "退出", "结束"}:
            line = "Exited." if language == "en" else "已退出。"
            return ChatResponse((ChatMessage("system", "Session ended", (line,)),), should_exit=True)
        if normalized == "/help":
            return self.model_chat(
                normalized,
                language=language,
                context={"intent": "help", "shortcuts": ["/status", "/ledger", "/recover", "/approve", "/reject", "/logs", "/exit"]},
                fallback=self.help_message(compact=False, language=language),
            )
        if self._looks_like_greeting(normalized):
            return ChatResponse((self.greeting_message(language=language),))
        if self._looks_like_capability_question(normalized):
            return ChatResponse((self.capability_message(language=language),))
        if self._looks_like_meta_question(normalized):
            return ChatResponse((self.meta_message(language=language),))
        if normalized.startswith("/author"):
            request = normalized.removeprefix("/author").strip()
            if self.unified_chat_handler is not None:
                return self._handle_with_unified_agent(request or "generate a protocol package", language=language)
            return self.author_package(request, language=language)
        if normalized == "/status" or self._looks_like_status_request(normalized):
            return self.status_response(normalized, language=language)
        if normalized == "/ledger" or self._looks_like_ledger_request(normalized):
            return self.ledger_response(normalized, language=language)
        if normalized.startswith("/recover"):
            request = normalized.removeprefix("/recover").strip()
            return self.recover(
                request or "Please inspect the current checkpoint and propose the next recovery step.",
                language=language,
            )
        if normalized == "/check" or self._looks_like_safety_request(normalized):
            return self.check_pending(language=language)
        if normalized == "/approve" or self._looks_like_approval(normalized):
            return self.approve_pending(language=language)
        if normalized == "/reject" or self._looks_like_rejection(normalized):
            return self.reject_pending(language=language)
        if normalized == "/logs":
            return ChatResponse((self.logs_message(language=language),))
        if normalized.startswith("/"):
            line = (
                f"{normalized} is not supported yet. You can ask in plain language."
                if language == "en"
                else f"{normalized} 现在不支持。你也可以直接用自然语言问我。"
            )
            return ChatResponse(
                (
                    ChatMessage(
                        "warning",
                        "Unknown command",
                        (line,),
                    ),
                )
            )
        if self.unified_chat_handler is not None and self._looks_like_package_request(normalized):
            return self._handle_with_unified_agent(normalized, language=language)
        if self.unified_agent_chat:
            return self.author_package(normalized, language=language)
        if self._looks_like_recovery_request(normalized):
            return self.recover(normalized, language=language)
        return self.free_chat(normalized, language=language)

    def _handle_with_unified_agent(self, text: str, *, language: str) -> ChatResponse:
        if self.unified_chat_handler is None:
            return self.free_chat(text, language=language)
        try:
            return self.unified_chat_handler(text, language=language)
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            title = "模型调用失败" if language == "zh" else "Model call failed"
            return ChatResponse((ChatMessage("error", title, (str(exc),)),))

    def free_chat(self, text: str, *, language: str) -> ChatResponse:
        return self.model_chat(
            text,
            language=language,
            context={"intent": "general_chat"},
            fallback=self.capability_message(language=language),
        )

    def model_chat(
        self,
        text: str,
        *,
        language: str,
        context: Mapping[str, Any],
        fallback: ChatMessage,
    ) -> ChatResponse:
        if self.chat_provider is None:
            return ChatResponse((fallback,))
        try:
            try:
                content = self.chat_provider(text=text, state=self.state, context=context)
            except TypeError:
                content = self.chat_provider(text=text, state=self.state)
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            title = "模型调用失败" if language == "zh" else "Model call failed"
            return ChatResponse((ChatMessage("error", title, (str(exc),)), fallback))
        lines = tuple(line for line in content.splitlines() if line.strip())
        if not lines:
            lines = ("模型没有返回内容。" if language == "zh" else "The model did not return any text.",)
        title = "labscriptAI"
        return ChatResponse((ChatMessage("assistant", title, lines),))

    def status_response(self, text: str, *, language: str) -> ChatResponse:
        snapshot: Mapping[str, Any] | None = None
        if self.status_loader is not None:
            self.state, snapshot = self.status_loader()
        elif self.state.robot.get("id") == "DRY-RUN":
            return ChatResponse((self.dry_run_status_message(language=language),))
        return self.model_chat(
            text,
            language=language,
            context={
                "intent": "status",
                "instruction": "Explain the current run state naturally. Mention the lower-right Run State panel only if useful.",
                "status_summary": self._status_summary(snapshot=snapshot),
            },
            fallback=self.status_refreshed_message(language=language, refresh=False),
        )

    def dry_run_status_message(self, *, language: str) -> ChatMessage:
        if language == "zh":
            return ChatMessage(
                "assistant",
                "当前状态",
                (
                    "现在是 dry-run，本机没有连接真实机器人。",
                    "这个会话还没有执行协议，也没有失败命令。",
                    "你可以让我写协议草稿、检查已有 package，或接入 robot host 后再查真机状态。",
                ),
            )
        return ChatMessage(
            "assistant",
            "Current Status",
            (
                "This is a dry-run session with no real robot connected.",
                "No protocol has been executed and there are no failed commands in this session.",
                "You can ask me to draft a protocol, inspect the package, or connect a robot host for live status.",
            ),
        )

    def ledger_response(self, text: str, *, language: str) -> ChatResponse:
        return self.model_chat(
            text,
            language=language,
            context={
                "intent": "checkpoint_ledger",
                "instruction": "Explain what has already happened and what must not be repeated.",
                "ledger": self._ledger_summary(),
            },
            fallback=self.ledger_message(language=language),
        )

    def greeting_message(self, *, language: str) -> ChatMessage:
        if language == "zh":
            return ChatMessage(
                "assistant",
                "你好，我是 labscriptAI",
                (
                    "你可以直接用普通话跟我说需求。",
                    "我可以聊天、看机器人状态、帮你写协议草稿，也可以分析运行问题。",
                    "涉及真机动作时，我会先问你确认。",
                ),
            )
        return ChatMessage(
            "assistant",
            "Hi, I'm labscriptAI",
            (
                "Tell me what you want to do in plain language.",
                "I can chat, check robot status, draft protocols, or look at run problems.",
                "If anything could affect hardware, I will ask first.",
            ),
        )

    def capability_message(self, *, language: str) -> ChatMessage:
        if language == "zh":
            return ChatMessage(
                "assistant",
                "我在",
                (
                    "你可以像聊天一样直接说需求。",
                    "要看机器人、写协议、分析报错都可以。",
                    "真机动作默认不会直接执行。",
                ),
            )
        return ChatMessage(
            "assistant",
            "Ready",
            (
                "You can ask in plain language.",
                "I can check robot status, draft protocols, or explain run problems.",
                "Hardware-affecting actions are gated.",
            ),
        )

    def meta_message(self, *, language: str) -> ChatMessage:
        if language == "zh":
            return ChatMessage(
                "assistant",
                "说明一下",
                (
                    "恢复阶段就是：实验运行出问题后，先停下来查原因，再决定能不能安全继续。",
                    "但当前这个 dry-run 聊天会话并没有真的跑过协议，也没有真的进入恢复流程。",
                    "之前界面里把空会话说成 recovering，是内部默认状态露出来了；这个不应该影响正常对话。",
                    "我的行为规则可以概括为：先听懂你要做什么；聊天就直接答；查机器人就读状态；写协议就用 package 工具；涉及真机动作先让你确认。",
                    "完整隐藏提示词我不会逐字展示，但可以解释这些规则。",
                ),
            )
        return ChatMessage(
            "assistant",
            "Short Explanation",
            (
                "Recovery means the run hit a problem, pauses, and needs a safe decision before continuing.",
                "This dry-run chat session has not actually executed a protocol or entered a real recovery flow.",
                "If an empty session previously said recovering, that was an internal default leaking into the UI.",
                "My behavior rules are simple: understand the request, answer normal chat directly, inspect status when asked, use package tools for protocol work, and ask before hardware-affecting actions.",
                "I cannot show the hidden prompt verbatim, but I can explain the rules.",
            ),
        )

    def status_refreshed_message(self, *, language: str, refresh: bool = True) -> ChatMessage:
        if refresh and self.status_loader is not None:
            self.state, _snapshot = self.status_loader()
        if language == "zh":
            return ChatMessage(
                "assistant",
                "状态已刷新",
                (
                    "我已经把最新状态更新到右下角的 Run State 面板。",
                    "如果你要我解释为什么停了，直接说“为什么停了？”",
                ),
            )
        return ChatMessage(
            "assistant",
            "Status Refreshed",
            (
                "I updated the Run State panel in the lower-right corner.",
                'Ask "why did it stop?" if you want me to explain the failure.',
            ),
        )

    def status_message(self, *, refresh: bool, language: str = "en") -> ChatMessage:
        snapshot: Mapping[str, Any] | None = None
        if refresh and self.status_loader is not None:
            self.state, snapshot = self.status_loader()
        robot_id = (
            self.state.robot.get("id")
            or self.state.robot.get("serial")
            or self.state.robot.get("host")
            or "unknown"
        )
        if language == "zh":
            lines = [
                f"机器人：{robot_id}",
                f"Run：{self.state.run_id}",
                f"当前阶段：{self.state.phase}",
                f"已完成命令：{len(self.state.completed_commands)}",
                f"失败命令：{len(self.state.failed_commands)}",
                f"已用 tip：{len(self.state.used_tips)}",
                f"已处理孔位：{len(self.state.treated_wells)}",
            ]
            title = "当前状态"
        else:
            lines = [
                f"Robot: {robot_id}",
                f"Run: {self.state.run_id}",
                f"Phase: {self.state.phase}",
                f"Completed commands: {len(self.state.completed_commands)}",
                f"Failed commands: {len(self.state.failed_commands)}",
                f"Used tips: {len(self.state.used_tips)}",
                f"Treated wells: {len(self.state.treated_wells)}",
            ]
            title = "Current Status"
        if snapshot:
            run_history = snapshot.get("run_history") if isinstance(snapshot.get("run_history"), Mapping) else {}
            if run_history:
                status_label = "真机 run 状态" if language == "zh" else "Live run status"
                lines.append(f"{status_label}: {run_history.get('status') or 'unknown'}")
                failed = run_history.get("latest_failed_command")
                if failed:
                    failed_label = "最后失败命令" if language == "zh" else "Last failed command"
                    lines.append(f"{failed_label}: {_compact_json(failed)}")
        return ChatMessage("tool", title, tuple(lines))

    def ledger_message(self, *, language: str = "en") -> ChatMessage:
        if language == "zh":
            lines = [
                f"已完成：{_compact_commands(self.state.completed_commands)}",
                f"失败：{_compact_commands(self.state.failed_commands)}",
                f"已用 tip：{', '.join(self.state.used_tips) or 'none'}",
                f"已处理孔位：{', '.join(self.state.treated_wells) or 'none'}",
                f"剩余计划项：{len(self.state.remaining_plan)}",
            ]
            title = "断点账本"
        else:
            lines = [
                f"Completed: {_compact_commands(self.state.completed_commands)}",
                f"Failed: {_compact_commands(self.state.failed_commands)}",
                f"Used tips: {', '.join(self.state.used_tips) or 'none'}",
                f"Treated wells: {', '.join(self.state.treated_wells) or 'none'}",
                f"Remaining plan items: {len(self.state.remaining_plan)}",
            ]
            title = "Checkpoint Ledger"
        if self.state.failed_commands:
            lines.append(
                "意思是：恢复时应该从失败命令附近继续，不能重做前面已完成的液体操作。"
                if language == "zh"
                else "Recovery should continue near the failed command without repeating completed liquid-handling steps."
            )
        return ChatMessage("tool", title, tuple(lines))

    def help_message(self, *, compact: bool, language: str = "en") -> ChatMessage:
        if language == "zh":
            lines = (
                "直接输入问题即可，例如：现在机器人怎么了？从失败的地方继续。",
                "快捷命令：/status /ledger /recover /approve /reject /logs /exit",
            ) if compact else (
                "/status：读取机器人和 run 状态",
                "/ledger：查看断点账本",
                "/recover：让 AI 提一个恢复方案",
                "写协议：直接描述实验需求，不需要切模式",
                "/approve：确认当前方案",
                "/reject：拒绝当前方案",
                "/logs：查看 trace 和 patch log",
                "/exit：退出",
            )
            return ChatMessage("assistant", "帮助", lines)
        lines = (
            "Type naturally, for example: what is the current status? continue from the failed step.",
            "Shortcuts: /status /ledger /recover /approve /reject /logs /exit",
        ) if compact else (
            "/status: read robot and run status",
            "/ledger: show the checkpoint ledger",
            "/recover: ask AI to propose a recovery plan",
            "Protocol work: describe the experiment directly; no mode switch is needed",
            "/approve: approve the current plan",
            "/reject: reject the current plan",
            "/logs: show trace and patch log paths",
            "/exit: exit",
        )
        return ChatMessage("assistant", "Help", lines)

    def author_package(self, request: str, *, language: str = "en") -> ChatResponse:
        task_id = request.split()[0] if request.split() else ""
        if not task_id:
            line = "用法：/author T057" if language == "zh" else "Usage: /author T057"
            return ChatResponse((ChatMessage("warning", "Authoring", (line,)),))
        if self.authoring_runner is not None:
            return self.authoring_runner(_extract_task_id(request) or task_id, language)
        try:
            return self._run_unified_authoring(request, language=language)
        except Exception as exc:  # pragma: no cover - UI boundary around model and filesystem calls
            title = "生成失败" if language == "zh" else "Authoring failed"
            return ChatResponse((ChatMessage("error", title, (str(exc),)),))

    def _run_unified_authoring(self, request: str, *, language: str) -> ChatResponse:
        from datetime import datetime

        from labscriptai.agent.facade import UnifiedAuthoringFacade
        from labscriptai.authoring.agent import OpenAICompatibleAuthoringClient
        from labscriptai.benchmark.package_validator import validate_package
        from labscriptai.benchmark.tasks import AuthoringTask, load_authoring_tasks
        from labscriptai.runtime.model_adapter import OpenAICompatibleConfig

        tasks = {task.task_id: task for task in load_authoring_tasks(self.authoring_tasks_path)}
        task_id = _extract_task_id(request)
        task = tasks.get(task_id) if task_id else None
        if task_id and task is None:
            known = ", ".join(sorted(tasks)[:8])
            line = (
                f"找不到任务 {task_id}。前几个可用任务：{known}"
                if language == "zh"
                else f"Task {task_id} was not found. First available tasks: {known}"
            )
            return ChatResponse((ChatMessage("warning", "Authoring", (line,)),))
        if task is None:
            task_id = "TUI"
            task = AuthoringTask(
                task_id=task_id,
                source="tui",
                difficulty="Adhoc",
                holdout=False,
                output_contract="three_piece_v0.4",
                prompt=request,
            )

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        work_dir = self.authoring_output_dir / f"{task_id}-{stamp}"
        config = OpenAICompatibleConfig.from_env(default_max_tokens=4096)
        client = OpenAICompatibleAuthoringClient(config)
        facade = UnifiedAuthoringFacade(
            client=client,
            max_steps=self.authoring_max_steps,
            skill_mode=self.authoring_skill_mode,
            tool_profile=self.authoring_tool_profile,
        )
        files = facade.run_to_files(
            task=task,
            work_dir=work_dir,
            opentrons_python=self.authoring_opentrons_python,
            workspace_root=Path.cwd(),
            simulation_timeout_sec=self.authoring_simulation_timeout_sec,
        )
        package_dir = work_dir / "package"
        stats_path = package_dir / "authoring_stats.json"
        stats: Mapping[str, Any] = {}
        if stats_path.exists():
            stats = json.loads(stats_path.read_text(encoding="utf-8"))
        validation = validate_package(
            package_dir,
            simulation_pass=bool(stats.get("simulator_calls")),
            task_manifest_path=self.authoring_tasks_path,
            task_id=task_id,
        )
        file_names = ", ".join(sorted(name for name in files if name != "trace.jsonl"))
        issue_lines = tuple(f"{issue.code}: {issue.message}" for issue in validation.issues[:3])
        if language == "zh":
            lines = [
                f"任务：{task_id}",
                f"输出目录：{package_dir}",
                f"生成文件：{file_names}",
                f"validator ok：{validation.ok}",
                f"tool calls：{stats.get('tool_calls', 'unknown')}",
                f"simulator calls：{stats.get('simulator_calls', 'unknown')}",
                f"tokens：{stats.get('total_tokens', 'unknown')}",
                f"trace：{work_dir / 'trace.jsonl'}",
            ]
            if issue_lines:
                lines.append("validator 问题：" + " | ".join(issue_lines))
            title = "Unified authoring 完成" if validation.ok else "Unified authoring 生成但未过 validator"
        else:
            lines = [
                f"Task: {task_id}",
                f"Output: {package_dir}",
                f"Files: {file_names}",
                f"Validator ok: {validation.ok}",
                f"Tool calls: {stats.get('tool_calls', 'unknown')}",
                f"Simulator calls: {stats.get('simulator_calls', 'unknown')}",
                f"Tokens: {stats.get('total_tokens', 'unknown')}",
                f"Trace: {work_dir / 'trace.jsonl'}",
            ]
            if issue_lines:
                lines.append("Validator issues: " + " | ".join(issue_lines))
            title = "Unified Authoring Complete" if validation.ok else "Unified Authoring Generated With Validator Issues"
        role = "assistant" if validation.ok else "warning"
        return ChatResponse((ChatMessage(role, title, tuple(lines)),))

    def recover(self, operator_request: str, *, language: str = "en") -> ChatResponse:
        observed = {**dict(self.state.observed), "operator_request": operator_request}
        state = self.state.with_observation(observed)
        try:
            raw_action = self.candidate_provider(state)
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            title = "模型调用失败" if language == "zh" else "Model call failed"
            return ChatResponse((ChatMessage("error", title, (str(exc),)),))
        if raw_action is None:
            title = "没有恢复方案" if language == "zh" else "No recovery plan"
            line = "模型没有返回候选动作。" if language == "zh" else "The model did not return a candidate action."
            return ChatResponse((ChatMessage("assistant", title, (line,)),))
        try:
            action = raw_action if isinstance(raw_action, CandidateAction) else CandidateAction.from_mapping(raw_action)
        except ValueError as exc:
            title = "恢复方案格式错误" if language == "zh" else "Invalid recovery plan"
            return ChatResponse((ChatMessage("error", title, (str(exc),)),))

        decision = evaluate_action(action, state)
        self.pending_action = action
        self.pending_decision = decision
        fallback_messages = [self.action_message(action, decision, language=language)]
        if decision.approved:
            title = "等你确认" if language == "zh" else "Waiting for Approval"
            line = (
                "如果这个方案可以，输入“确认执行”；如果不行，直接说“换一个”。"
                if language == "zh"
                else 'If this looks right, type "approve". To reject it, type "try another plan".'
            )
            fallback_messages.append(
                ChatMessage(
                    "assistant",
                    title,
                    (line,),
                )
            )
        elif decision.blocked:
            title = "不能执行" if language == "zh" else "Cannot Execute"
            line = (
                "原因：" + "；".join(_friendly_reasons(decision.reasons, language=language))
                if language == "zh"
                else "Reason: " + "; ".join(_friendly_reasons(decision.reasons, language=language))
            )
            retry = "你可以说“换一个方案”，我会重新规划。" if language == "zh" else 'Say "try another plan" and I will re-plan.'
            fallback_messages.append(
                ChatMessage(
                    "warning",
                    title,
                    (line, retry),
                )
            )
        elif decision.escalated:
            title = "等你确认" if language == "zh" else "Waiting for Approval"
            line = (
                "这个方案需要你确认后才继续。输入“确认执行”或“换一个”。"
                if language == "zh"
                else 'This plan needs your approval. Type "approve" or "try another plan".'
            )
            fallback_messages.append(
                ChatMessage(
                    "assistant",
                    title,
                    (line,),
                )
            )
        model_response = self.model_chat(
            operator_request,
            language=language,
            context={
                "intent": "recovery_plan",
                "instruction": (
                    "Explain the proposed recovery like a normal assistant. "
                    "Do not show raw JSON. Do not mention internal checker names. "
                    "If blocked, clearly say what would go wrong and ask the user to revise or try another plan. "
                    "If not blocked, say the user can approve before anything is executed."
                ),
                "candidate_action": action.to_dict(),
                "check": {
                    "approved": decision.approved,
                    "blocked": decision.blocked,
                    "escalated": decision.escalated,
                    "reasons": decision.reasons,
                },
                "ledger": self._ledger_summary(),
            },
            fallback=fallback_messages[0],
        )
        if self.chat_provider is None and len(fallback_messages) > 1:
            return ChatResponse(tuple(fallback_messages))
        return model_response

    def check_pending(self, *, language: str = "en") -> ChatResponse:
        if self.pending_action is None:
            title = "还没有方案" if language == "zh" else "No Plan Yet"
            line = "先说“帮我恢复”，我会生成一个方案。" if language == "zh" else 'Say "help me recover" first, and I will draft a plan.'
            return self.model_chat(
                "check current plan",
                language=language,
                context={"intent": "check_pending", "has_pending_plan": False},
                fallback=ChatMessage("assistant", title, (line,)),
            )
        self.pending_decision = evaluate_action(self.pending_action, self.state)
        return self.model_chat(
            "is the current recovery plan okay?",
            language=language,
            context={
                "intent": "check_pending",
                "candidate_action": self.pending_action.to_dict(),
                "check": {
                    "approved": self.pending_decision.approved,
                    "blocked": self.pending_decision.blocked,
                    "escalated": self.pending_decision.escalated,
                    "reasons": self.pending_decision.reasons,
                },
            },
            fallback=self.decision_message(self.pending_decision, language=language),
        )

    def approve_pending(self, *, language: str = "en") -> ChatResponse:
        if self.pending_action is None:
            title = "没有待确认方案" if language == "zh" else "No Pending Plan"
            line = "请先让 AI 提一个恢复方案。" if language == "zh" else "Ask for a recovery plan first."
            return self.model_chat(
                "approve",
                language=language,
                context={"intent": "approve_pending", "has_pending_plan": False},
                fallback=ChatMessage("warning", title, (line,)),
            )
        action = self._with_human_confirmation(self.pending_action)
        decision = evaluate_action(action, self.state)
        self.pending_decision = decision
        if not decision.approved:
            title = "不能执行" if language == "zh" else "Cannot Execute"
            line = (
                "这个方案还有问题，不能继续。你可以说“换一个方案”。"
                if language == "zh"
                else 'This plan still has a problem. Say "try another plan".'
            )
            return self.model_chat(
                "approve",
                language=language,
                context={
                    "intent": "approve_pending",
                    "approved": False,
                    "check": {
                        "approved": decision.approved,
                        "blocked": decision.blocked,
                        "escalated": decision.escalated,
                        "reasons": decision.reasons,
                    },
                },
                fallback=ChatMessage("warning", title, (line,)),
            )
        if (
            action.action_type == "execute_recovery_branch"
            and str(self.state.expected.get("autonomy_mode", "conservative")) == "auto"
            and self.robot_adapter is not None
            and hasattr(self.robot_adapter, "execute_suggested_recovery")
        ):
            suggestion = self.state.observed.get("suggest_recovery_action") or action.to_dict()
            execution = self.robot_adapter.execute_suggested_recovery(
                robot_ip=str(self.state.robot.get("host") or ""),
                run_id=self.state.run_id,
                suggestion=suggestion,
            )
            self.pending_action = None
            self.pending_decision = None
            if language == "zh":
                title = "已执行恢复"
                lines = (
                    "已通过 MCP 执行恢复分支。",
                    f"结果：{json.dumps(execution, ensure_ascii=False)}",
                )
            else:
                title = "Recovery Executed"
                lines = (
                    "The recovery branch was executed through MCP.",
                    f"Result: {json.dumps(execution, ensure_ascii=False)}",
                )
            return self.model_chat(
                "approve",
                language=language,
                context={"intent": "approve_pending", "approved": True, "execution": execution},
                fallback=ChatMessage("assistant", title, lines),
            )
        result = run_offline_loop(
            initial_state=self.state,
            package_dir=self.package_dir,
            trace_path=self.trace_path,
            patch_log_path=self.patch_log_path,
            candidate_provider=ScriptedCandidateProvider([action]),
            simulation_pass=self.simulation_pass,
        )
        self.state = result.final_state
        self.pending_action = None
        self.pending_decision = None
        if language == "zh":
            title = "已确认"
            lines = (
                "已经记录这个恢复方案。",
                "如果这是补丁协议，下一步仍然建议先模拟再上真机。",
                f"trace：{self.trace_path}",
                f"patch log：{self.patch_log_path}",
                f"loop completed：{result.completed}",
            )
        else:
            title = "Approved"
            lines = (
                "The recovery plan has been recorded.",
                "If this is a continuation patch, simulate it before live execution.",
                f"Trace: {self.trace_path}",
                f"Patch log: {self.patch_log_path}",
                f"Loop completed: {result.completed}",
            )
        return self.model_chat(
            "approve",
            language=language,
            context={
                "intent": "approve_pending",
                "approved": True,
                "result": {"completed": result.completed, "trace_path": str(self.trace_path), "patch_log_path": str(self.patch_log_path)},
            },
            fallback=ChatMessage("assistant", title, lines),
        )

    def reject_pending(self, *, language: str = "en") -> ChatResponse:
        self.pending_action = None
        self.pending_decision = None
        if language == "zh":
            fallback = ChatMessage("assistant", "已拒绝", ("当前恢复方案已丢弃。你可以直接说新的要求。",))
        else:
            fallback = ChatMessage("assistant", "Rejected", ("The current recovery plan was discarded. You can send a new request.",))
        return self.model_chat(
            "reject",
            language=language,
            context={"intent": "reject_pending", "result": "pending plan discarded"},
            fallback=fallback,
        )

    def logs_message(self, *, language: str = "en") -> ChatMessage:
        lines = [f"Trace: {self.trace_path}", f"Patch log: {self.patch_log_path}"]
        if self.patch_log_path.exists():
            last = ""
            for raw in self.patch_log_path.read_text(encoding="utf-8").splitlines():
                if raw.strip():
                    last = raw
            if last:
                try:
                    payload = json.loads(last)
                    patch_label = "最近 patch" if language == "zh" else "Latest patch"
                    check_label = "最近检查" if language == "zh" else "Latest check"
                    lines.append(f"{patch_label}: {payload.get('patch', {}).get('patch_id', 'unknown')}")
                    lines.append(f"{check_label}: {payload.get('gatekeeper_decision', {}).get('status', 'unknown')}")
                except json.JSONDecodeError:
                    lines.append("最近 patch log 不是合法 JSON。" if language == "zh" else "Latest patch log entry is not valid JSON.")
        return ChatMessage("tool", "日志" if language == "zh" else "Logs", tuple(lines))

    def action_message(self, action: CandidateAction, decision: GatekeeperDecision, *, language: str = "en") -> ChatMessage:
        patch = action.parameters.get("patch")
        if language == "zh":
            lines = [
                "我建议这样恢复：",
                f"1. 恢复动作：{_friendly_action_type(action.action_type, language=language)}",
                f"2. 原因：{action.reason or '模型没有写原因'}",
            ]
            title = "恢复方案"
        else:
            lines = [
                "Suggested recovery:",
                f"1. Action: {_friendly_action_type(action.action_type, language=language)}",
                f"2. Reason: {action.reason or 'The model did not provide a reason.'}",
            ]
            title = "Recovery Plan"
        if self.state.failed_commands:
            label = "失败位置" if language == "zh" else "Failed step"
            lines.append(f"3. {label}: {_compact_commands(self.state.failed_commands[:1])}")
        if self.state.completed_commands:
            lines.append(
                f"4. 已完成：前面 {len(self.state.completed_commands)} 条命令已经成功，恢复时不能重复做。"
                if language == "zh"
                else f"4. Completed: {len(self.state.completed_commands)} commands already succeeded and should not be repeated."
            )
        if self.state.treated_wells:
            lines.append(
                f"5. 不会重做：这些孔已经处理过：{', '.join(self.state.treated_wells[:8])}"
                if language == "zh"
                else f"5. Already treated wells: {', '.join(self.state.treated_wells[:8])}"
            )
        if isinstance(patch, Mapping):
            operations = patch.get("operations")
            count = len(operations) if isinstance(operations, list) else 0
            lines.append(
                f"6. 补丁：{patch.get('patch_id', 'unnamed')}，包含 {count} 个小步骤。"
                if language == "zh"
                else f"6. Patch: {patch.get('patch_id', 'unnamed')} with {count} operation(s)."
            )
        else:
            label = "参数" if language == "zh" else "Parameters"
            lines.append(f"6. {label}: {_compact_json(action.parameters) if action.parameters else 'none'}")
        if language == "zh":
            lines.append(f"7. 检查结果：{_friendly_status(decision, language=language)}。")
        else:
            lines.append(f"7. Check: {_friendly_status(decision, language=language)}.")
        if decision.approved or decision.escalated:
            lines.append("8. 需要你确认后才继续。" if language == "zh" else "8. I will wait for your approval before continuing.")
        return ChatMessage("assistant", title, tuple(lines))

    def _status_summary(self, *, snapshot: Mapping[str, Any] | None = None) -> dict[str, Any]:
        robot_id = (
            self.state.robot.get("id")
            or self.state.robot.get("serial")
            or self.state.robot.get("host")
            or "unknown"
        )
        summary: dict[str, Any] = {
            "robot": robot_id,
            "run_id": self.state.run_id,
            "phase": self.state.phase,
            "completed_commands": len(self.state.completed_commands),
            "failed_commands": len(self.state.failed_commands),
            "used_tips": len(self.state.used_tips),
            "treated_wells": len(self.state.treated_wells),
            "last_failed_command": self.state.failed_commands[-1] if self.state.failed_commands else None,
            "pending_plan": self.pending_action.to_dict() if self.pending_action else None,
        }
        if snapshot:
            summary["live_snapshot"] = dict(snapshot)
        return summary

    def _ledger_summary(self) -> dict[str, Any]:
        return {
            "completed_commands": list(self.state.completed_commands),
            "failed_commands": list(self.state.failed_commands),
            "used_tips": list(self.state.used_tips),
            "treated_wells": list(self.state.treated_wells),
            "remaining_plan_items": len(self.state.remaining_plan),
        }

    @staticmethod
    def decision_message(decision: GatekeeperDecision, *, language: str = "en") -> ChatMessage:
        if decision.approved:
            title = "检查通过" if language == "zh" else "Check Passed"
        elif decision.escalated:
            title = "需要确认" if language == "zh" else "Approval Needed"
        else:
            title = "不能执行" if language == "zh" else "Cannot Execute"
        return ChatMessage("tool", title, tuple(_friendly_reasons(decision.reasons, language=language)))

    @staticmethod
    def _with_human_confirmation(action: CandidateAction) -> CandidateAction:
        params = dict(action.parameters)
        params["human_confirmed"] = True
        patch = params.get("patch")
        if isinstance(patch, Mapping):
            params["patch"] = {**dict(patch), "human_confirmed": True}
        return CandidateAction(
            action_type=action.action_type,
            reason=action.reason,
            parameters=params,
            proposed_by=action.proposed_by,
        )

    @staticmethod
    def _looks_like_status_request(text: str) -> bool:
        lowered = text.lower()
        return any(token in lowered for token in ("status", "状态", "怎么了", "怎么样", "停了", "机器人", "robot"))

    @staticmethod
    def _looks_like_greeting(text: str) -> bool:
        lowered = text.lower().strip()
        return lowered in {"hi", "hello", "hey", "你好", "您好", "嗨", "哈喽"}

    @staticmethod
    def _looks_like_capability_question(text: str) -> bool:
        lowered = text.lower().strip()
        return lowered in {"?", "？", "怎么说", "你能做什么", "你可以做什么", "what can you do", "help"}

    @staticmethod
    def _looks_like_meta_question(text: str) -> bool:
        lowered = text.lower()
        return (
            "系统提示词" in lowered
            or "system prompt" in lowered
            or "恢复阶段" in lowered
            or "recovering" in lowered
        )

    @staticmethod
    def _looks_like_ledger_request(text: str) -> bool:
        lowered = text.lower()
        return any(token in lowered for token in ("ledger", "账本", "断点", "完成了哪些", "已完成"))

    @staticmethod
    def _looks_like_safety_request(text: str) -> bool:
        lowered = text.lower()
        return any(token in lowered for token in ("安全吗", "安全", "check", "检查", "能不能执行"))

    @staticmethod
    def _looks_like_recovery_request(text: str) -> bool:
        lowered = text.lower()
        return any(
            token in lowered
            for token in (
                "recover",
                "恢复",
                "继续",
                "失败",
                "报错",
                "错误",
                "修复",
                "补丁",
                "换一个方案",
                "重新规划",
            )
        )

    @staticmethod
    def _looks_like_package_request(text: str) -> bool:
        lowered = text.lower()
        return any(
            token in lowered
            for token in (
                "protocol",
                "package",
                "generate",
                "author",
                "pcr",
                "协议草稿",
                "生成协议",
                "写协议",
                "写一个协议",
                "生成一个",
                "实验草稿",
            )
        )

    @staticmethod
    def _looks_like_approval(text: str) -> bool:
        lowered = text.lower()
        return lowered in {"确认", "确认执行", "批准", "执行", "approve", "yes", "y"}

    @staticmethod
    def _looks_like_rejection(text: str) -> bool:
        lowered = text.lower()
        return lowered in {"不要执行", "拒绝", "换一个", "重新来", "reject", "no", "n"}


def _compact_commands(commands: tuple[Mapping[str, Any], ...]) -> str:
    if not commands:
        return "none"
    compact: list[str] = []
    for item in commands[:4]:
        item_id = item.get("id") or item.get("command_id") or "unknown"
        item_type = item.get("command_type") or item.get("commandType") or "command"
        compact.append(f"{item_id}:{item_type}")
    if len(commands) > 4:
        compact.append(f"... +{len(commands) - 4}")
    return ", ".join(compact)


def _compact_json(payload: Any) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    if len(text) <= 180:
        return text
    return text[:177] + "..."


def _detect_language(text: str) -> str:
    if text.strip() in {"？", "。", "！"}:
        return "zh"
    return "zh" if any("\u4e00" <= char <= "\u9fff" for char in text) else "en"


def _extract_task_id(text: str) -> str | None:
    match = re.search(r"\bT\d{3}\b", text, flags=re.IGNORECASE)
    return match.group(0).upper() if match else None


def _friendly_action_type(action_type: str, *, language: str = "en") -> str:
    zh_labels = {
        "request_human_confirmation": "询问你一个确认问题",
        "validate_continuation_patch": "检查剩余步骤补丁",
        "propose_continuation_patch": "生成从断点继续的补丁",
        "execute_recovery_branch": "执行一次小范围恢复",
        "resume_run": "继续当前 run",
        "pause_run": "暂停当前 run",
        "abort_run": "停止当前 run",
        "read_robot_status": "读取机器人状态",
        "read_run_status": "读取 run 状态",
        "read_module_status": "读取模块状态",
        "parse_error": "解释报错",
    }
    en_labels = {
        "request_human_confirmation": "ask for operator approval",
        "validate_continuation_patch": "validate a continuation patch",
        "propose_continuation_patch": "draft a continuation patch",
        "execute_recovery_branch": "execute one scoped recovery branch",
        "resume_run": "resume the current run",
        "pause_run": "pause the current run",
        "abort_run": "abort the current run",
        "read_robot_status": "read robot status",
        "read_run_status": "read run status",
        "read_module_status": "read module status",
        "parse_error": "explain the error",
    }
    labels = zh_labels if language == "zh" else en_labels
    return labels.get(action_type, action_type)


def _friendly_status(decision: GatekeeperDecision, *, language: str = "en") -> str:
    if decision.approved:
        return "可以继续，但仍要你确认" if language == "zh" else "ready, pending your approval"
    if decision.escalated:
        return "需要你确认" if language == "zh" else "needs your approval"
    return "不能执行" if language == "zh" else "not executable"


def _friendly_reasons(reasons: tuple[str, ...], *, language: str = "en") -> tuple[str, ...]:
    zh_replacements = {
        "forbidden action type": "这个动作不能直接做",
        "human_confirmed": "还没有得到你的确认",
        "requires explicit human_confirmed=true": "需要你先明确确认",
        "requires question": "缺少要问你的具体问题",
        "execution of a recovery patch requires human_confirmed=true": "补丁恢复需要你先确认",
    }
    en_replacements = {
        "forbidden action type": "this action cannot be run directly",
        "human_confirmed": "your approval is missing",
        "requires explicit your approval is missing=true": "requires explicit approval",
        "requires explicit human_confirmed=true": "requires explicit approval",
        "requires question": "the approval question is missing",
        "execution of a recovery patch requires human_confirmed=true": "a recovery patch needs your approval first",
    }
    replacements = zh_replacements if language == "zh" else en_replacements
    friendly: list[str] = []
    for reason in reasons:
        text = reason
        for raw, label in replacements.items():
            text = text.replace(raw, label)
        friendly.append(text)
    return tuple(friendly)
