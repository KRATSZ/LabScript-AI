"""Recorded OpenAI-compatible candidate provider for frozen runtime studies."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request

from .actions import CandidateAction
from .model_adapter import OpenAICompatibleConfig, parse_chat_completion_candidate
from .model_visible_state import model_visible_runtime_state
from .state import RuntimeState


class RecordedCandidateProvider:
    """Call a model while retaining the exact request and raw response payload."""

    def __init__(
        self,
        config: OpenAICompatibleConfig,
        *,
        system_prompt: str,
        record_path: Path,
        opener: Any | None = None,
    ) -> None:
        self.config = config
        self.system_prompt = system_prompt
        self.record_path = record_path
        self.opener = opener or request.urlopen

    def __call__(
        self,
        state: RuntimeState,
        *,
        format_feedback: str | None = None,
    ) -> CandidateAction:
        user_payload: dict[str, Any] = {
            "runtime_state": model_visible_runtime_state(state),
            "instruction": "Return the next safe JSON candidate action only.",
        }
        if format_feedback:
            user_payload["gatekeeper_format_feedback"] = format_feedback
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            "temperature": 0,
            "max_tokens": self.config.max_tokens,
            "response_format": {"type": "json_object"},
        }
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        req = request.Request(
            url=f"{self.config.base_url}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
        )
        response_payload: Any = None
        error: str | None = None
        action: CandidateAction | None = None
        try:
            with self.opener(req, timeout=self.config.timeout_sec) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
            action = parse_chat_completion_candidate(response_payload)
            return action
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            self._append_record(
                {
                    "schema_version": "recorded_candidate_call.v1",
                    "created_at": _utc_now(),
                    "request_sha256": hashlib.sha256(body).hexdigest(),
                    "request": payload,
                    "response": response_payload,
                    "parsed_action": action.to_dict() if action else None,
                    "error": error,
                }
            )

    def _append_record(self, payload: dict[str, Any]) -> None:
        self.record_path.parent.mkdir(parents=True, exist_ok=True)
        with self.record_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
