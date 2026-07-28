"""OpenAI-compatible LLM client for the lean agent (stdlib only).

Copied and slimmed from core model_adapter + authoring llm_client.
One complete() surface: normalized tool_calls or final content.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from http.client import IncompleteRead
from json import JSONDecodeError
from pathlib import Path
from typing import Any
from urllib import error, request


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    base_url: str
    api_key: str
    model: str
    timeout_sec: int = 90
    max_tokens: int = 8192
    transport_retries: int = 3

    @classmethod
    def from_env(
        cls,
        *,
        prefix: str = "DEEPSEEK",
        default_base_url: str = "https://api.deepseek.com",
        default_model: str = "deepseek-v4-pro",
        default_max_tokens: int = 8192,
        require_key: bool = True,
    ) -> OpenAICompatibleConfig:
        """Load config from env (default DeepSeek OpenAI-compatible).

        Loads ``cwd``, ``labscriptai/``, and repo-root ``.env`` without
        overwriting existing env.
        """
        _load_package_dotenv()
        api_key = os.environ.get(f"{prefix}_API_KEY", "")
        if require_key and not api_key:
            raise RuntimeError(f"{prefix}_API_KEY is not set")
        return cls(
            base_url=os.environ.get(f"{prefix}_BASE_URL", default_base_url).rstrip("/"),
            api_key=api_key or "offline",
            model=os.environ.get(f"{prefix}_MODEL", default_model),
            timeout_sec=int(os.environ.get(f"{prefix}_TIMEOUT_SEC", "90")),
            max_tokens=int(os.environ.get(f"{prefix}_MAX_TOKENS", str(default_max_tokens))),
            transport_retries=max(1, int(os.environ.get(f"{prefix}_TRANSPORT_RETRIES", "3"))),
        )


def _load_dotenv_if_present(path: str | Path) -> None:
    """Load simple KEY=VALUE or export KEY=VALUE entries without overwriting env."""
    path = Path(path)
    if not path.is_file():
        return
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line.removeprefix("export ").strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if key and key not in os.environ:
                os.environ[key] = value


def _load_package_dotenv() -> None:
    """Load cwd, labscriptai/, and repo-root .env without overwriting existing keys.

    Search order (first wins for each key): process env → cwd/.env →
    ``labscriptai/.env`` → repo-root ``.env``.
    """
    _load_dotenv_if_present(".env")
    here = Path(__file__).resolve()
    # labscriptai/agent/llm.py → package root parents[1], repo root parents[2]
    package_root = here.parents[1]
    repo_root = here.parents[2]
    _load_dotenv_if_present(package_root / ".env")
    _load_dotenv_if_present(repo_root / ".env")


def _strip_json_markdown(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped


def _load_first_json_object(content: str) -> dict[str, Any]:
    stripped = _strip_json_markdown(content)
    decoder = json.JSONDecoder()
    try:
        parsed = json.loads(stripped)
    except JSONDecodeError:
        start = stripped.find("{")
        if start < 0:
            raise
        parsed, _ = decoder.raw_decode(stripped[start:])
    if not isinstance(parsed, dict):
        raise ValueError("model response JSON must be an object")
    return parsed


def _native_tool_specs(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pass through OpenAI function-tool specs; accept lean {name, description, parameters}."""
    native: list[dict[str, Any]] = []
    for tool in tools:
        if tool.get("type") == "function" and isinstance(tool.get("function"), dict):
            native.append(tool)
            continue
        name = str(tool.get("name") or "")
        native.append(
            {
                "type": "function",
                "function": {
                    "name": name.replace(".", "_"),
                    "description": str(tool.get("description") or f"tool {name}"),
                    "parameters": tool.get("parameters")
                    if isinstance(tool.get("parameters"), dict)
                    else {"type": "object", "properties": {}},
                },
            }
        )
    return native


def _normalize_tool_calls(tool_calls: list[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for call in tool_calls:
        if not isinstance(call, dict):
            continue
        function = call.get("function", {}) if isinstance(call.get("function"), dict) else {}
        args = function.get("arguments", "{}")
        if isinstance(args, str):
            try:
                parsed_args = json.loads(args) if args.strip() else {}
            except JSONDecodeError:
                parsed_args = {"_raw": args}
        elif isinstance(args, dict):
            parsed_args = args
        else:
            parsed_args = {"_raw": args}
        name = function.get("name") or call.get("name")
        normalized.append(
            {
                "id": call.get("id"),
                "name": name,
                "arguments": parsed_args if isinstance(parsed_args, dict) else {},
            }
        )
    return normalized


class OpenAICompatibleClient:
    """Chat completions client returning tool_calls or final content."""

    def __init__(
        self,
        config: OpenAICompatibleConfig,
        *,
        opener: Any | None = None,
    ) -> None:
        self.config = config
        self.opener = opener or request.urlopen
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        tools = tools or []
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": self.config.max_tokens,
        }
        if tools:
            payload["tools"] = _native_tool_specs(tools)
            payload["tool_choice"] = "auto"
            # DeepSeek-compatible thinking off when tools are present
            payload["thinking"] = {"type": "disabled"}

        req = request.Request(
            url=f"{self.config.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
        )
        last_error: Exception | None = None
        response_payload: dict[str, Any] | None = None
        for attempt in range(1, self.config.transport_retries + 1):
            try:
                with self.opener(req, timeout=self.config.timeout_sec) as response:
                    response_payload = json.loads(response.read().decode("utf-8"))
                break
            except error.HTTPError as exc:
                if attempt >= self.config.transport_retries or exc.code not in {
                    429,
                    500,
                    502,
                    503,
                    504,
                }:
                    raise
                last_error = exc
            except (JSONDecodeError, TimeoutError, error.URLError, IncompleteRead, OSError) as exc:
                if attempt >= self.config.transport_retries:
                    raise
                last_error = exc
        else:
            if last_error is not None:
                raise last_error
            raise RuntimeError("model request failed without response")

        assert response_payload is not None
        usage = response_payload.get("usage")
        if isinstance(usage, dict):
            input_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
            output_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
            total_tokens = int(usage.get("total_tokens") or input_tokens + output_tokens)
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens
            self.total_tokens += total_tokens

        return _parse_completion_message(response_payload)


def _parse_completion_message(response_payload: dict[str, Any]) -> dict[str, Any]:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("model response missing choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        raise ValueError("model response missing message")

    tool_calls = message.get("tool_calls")
    if isinstance(tool_calls, list) and tool_calls:
        normalized = _normalize_tool_calls(tool_calls)
        return {
            "tool_calls": normalized,
            "_assistant_message": {
                "role": "assistant",
                "content": message.get("content") or "",
                "tool_calls": tool_calls,
            },
        }

    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        finish_reason = choices[0].get("finish_reason") if isinstance(choices[0], dict) else None
        raise ValueError(f"model response content is empty; finish_reason={finish_reason}")

    # JSON-content / markdown-fence fallback → treat as structured final or plain text
    try:
        parsed = _load_first_json_object(content)
        if "tool_calls" in parsed and isinstance(parsed["tool_calls"], list):
            return {
                "tool_calls": _normalize_tool_calls(parsed["tool_calls"]),
                "_assistant_message": {"role": "assistant", "content": content},
            }
        if "final" in parsed:
            return parsed
        return {"final": parsed}
    except (JSONDecodeError, ValueError):
        return {"final": {"message": content.strip(), "completed": False}}


class OfflineClient:
    """Stub provider: one chat turn without API key."""

    def __init__(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        del tools
        prompt = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    prompt = content.strip()
                    break
        preview = prompt if len(prompt) <= 100 else prompt[:97] + "..."
        return {
            "final": {
                "message": (
                    f"Offline stub ack: {preview or '(empty)'}. "
                    "Set DEEPSEEK_API_KEY for a live OpenAI-compatible model."
                ),
                "completed": False,
            }
        }


def build_client(*, provider: str = "deepseek") -> OpenAICompatibleClient | OfflineClient:
    """Factory: deepseek (requires DEEPSEEK_API_KEY) or explicit offline stub."""
    _load_package_dotenv()
    if provider == "offline":
        return OfflineClient()
    if provider == "deepseek":
        config = OpenAICompatibleConfig.from_env(require_key=True)
        return OpenAICompatibleClient(config)
    raise ValueError(f"unknown provider: {provider}")


__all__ = (
    "OfflineClient",
    "OpenAICompatibleClient",
    "OpenAICompatibleConfig",
    "build_client",
    "_load_dotenv_if_present",
    "_load_first_json_object",
    "_load_package_dotenv",
    "_strip_json_markdown",
)
