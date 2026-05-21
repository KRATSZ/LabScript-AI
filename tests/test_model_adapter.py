from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from labscriptai.runtime.model_adapter import (
    OpenAICompatibleConfig,
    OpenAICompatibleCandidateProvider,
    OpenAICompatibleChatProvider,
    parse_chat_completion_candidate,
    parse_chat_completion_text,
)
from labscriptai.runtime.state import RuntimeState


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class ModelAdapterTests(unittest.TestCase):
    def test_config_loads_dotenv_without_overwriting_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "export DEEPSEEK_API_KEY=dotenv-key",
                        "DEEPSEEK_BASE_URL=https://dotenv.example",
                        "DEEPSEEK_MODEL=dotenv-model",
                    ]
                ),
                encoding="utf-8",
            )
            original_open = open

            def fake_open(path, *args, **kwargs):  # noqa: ANN001, ANN202
                if path == ".env":
                    return original_open(env_path, *args, **kwargs)
                return original_open(path, *args, **kwargs)

            with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "shell-key"}, clear=True), patch(
                "os.path.exists", return_value=True
            ), patch("builtins.open", fake_open):
                config = OpenAICompatibleConfig.from_env()

        self.assertEqual(config.api_key, "shell-key")
        self.assertEqual(config.base_url, "https://dotenv.example")
        self.assertEqual(config.model, "dotenv-model")

    def test_parse_chat_completion_candidate_accepts_json_action(self) -> None:
        action = parse_chat_completion_candidate(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "action_type": "simulate_protocol",
                                    "reason": "Validate before execution.",
                                    "parameters": {},
                                }
                            )
                        }
                    }
                ]
            }
        )

        self.assertEqual(action.action_type, "simulate_protocol")

    def test_parse_chat_completion_candidate_rejects_non_allowlisted_action(self) -> None:
        with self.assertRaises(ValueError):
            parse_chat_completion_candidate(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "action_type": "aspirate",
                                        "reason": "unsafe",
                                        "parameters": {},
                                    }
                                )
                            }
                        }
                    ]
                }
            )

    def test_parse_chat_completion_candidate_accepts_markdown_json(self) -> None:
        action = parse_chat_completion_candidate(
            {
                "choices": [
                    {
                        "message": {
                            "content": "```json\n{\"action_type\":\"simulate_protocol\",\"reason\":\"Check it.\",\"parameters\":{}}\n```"
                        }
                    }
                ]
            }
        )

        self.assertEqual(action.action_type, "simulate_protocol")

    def test_provider_posts_openai_compatible_request(self) -> None:
        captured = {}

        def fake_opener(req, timeout):
            captured["url"] = req.full_url
            captured["timeout"] = timeout
            captured["body"] = json.loads(req.data.decode("utf-8"))
            captured["auth"] = req.headers["Authorization"]
            return FakeResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "action_type": "request_human_confirmation",
                                        "reason": "Need operator confirmation.",
                                        "parameters": {"question": "Confirm deck layout?"},
                                    }
                                )
                            }
                        }
                    ]
                }
            )

        provider = OpenAICompatibleCandidateProvider(
            OpenAICompatibleConfig(
                base_url="https://api.deepseek.com",
                api_key="test-key",
                model="deepseek-v4-pro",
                timeout_sec=12,
                max_tokens=123,
            ),
            opener=fake_opener,
        )

        action = provider(RuntimeState(run_id="run-1"))

        self.assertEqual(action.action_type, "request_human_confirmation")
        self.assertEqual(captured["url"], "https://api.deepseek.com/chat/completions")
        self.assertEqual(captured["timeout"], 12)
        self.assertEqual(captured["body"]["model"], "deepseek-v4-pro")
        self.assertEqual(captured["body"]["max_tokens"], 123)
        self.assertEqual(captured["auth"], "Bearer test-key")

    def test_parse_chat_completion_text_returns_message_content(self) -> None:
        text = parse_chat_completion_text(
            {
                "choices": [
                    {
                        "message": {
                            "content": "Hello from labscriptAI.",
                        }
                    }
                ]
            }
        )

        self.assertEqual(text, "Hello from labscriptAI.")

    def test_chat_provider_posts_plain_chat_request(self) -> None:
        captured = {}

        def fake_opener(req, timeout):
            captured["url"] = req.full_url
            captured["timeout"] = timeout
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return FakeResponse({"choices": [{"message": {"content": "I can help with this run."}}]})

        provider = OpenAICompatibleChatProvider(
            OpenAICompatibleConfig(
                base_url="https://api.deepseek.com",
                api_key="test-key",
                model="deepseek-v4-flash",
                timeout_sec=9,
                max_tokens=2000,
            ),
            opener=fake_opener,
        )

        text = provider(
            text="please introduce yourself!",
            state=RuntimeState(run_id="run-1", phase="recovering"),
            context={"intent": "general_chat"},
        )

        self.assertEqual(text, "I can help with this run.")
        self.assertEqual(captured["url"], "https://api.deepseek.com/chat/completions")
        self.assertEqual(captured["timeout"], 9)
        self.assertEqual(captured["body"]["model"], "deepseek-v4-flash")
        self.assertEqual(captured["body"]["max_tokens"], 700)
        self.assertNotIn("response_format", captured["body"])
        user_payload = json.loads(captured["body"]["messages"][1]["content"])
        self.assertEqual(user_payload["context"]["intent"], "general_chat")


if __name__ == "__main__":
    unittest.main()
