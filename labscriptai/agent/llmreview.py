"""Authoring llmreview: flash, no tools, no motion authority.

Not part of LogicPass. Never mutates ``logic_pass``. Never play/resume.
"""

from __future__ import annotations

import json
import re
from typing import Any

from labscriptai.agent.llm import _load_first_json_object

REVIEW_SYSTEM_PROMPT = """You are LabscriptAI protocol reviewer. No tools. Never play/resume.
If a SimPass error is present in the user message: name the blocking setup fix only (D3 vs waste chute, tip_racks, pipette name). match=false. Do not grade biology.
If no SimPass error is in the user message: never mention pipette names or SimPass setup. match=false only for real intent mismatches (tips, volumes, wells). Do not invent hardware errors.
If named tip wells in intent (TIPS:A1 through TIPS:H1) are not covered by PICK_TIPS, match=false.
Judge liquid-handling vs intent, not syntax.
JSON only: {"match":bool,"findings":[{"severity":"error"|"warning"|"info","claim":str,"evidence":str,"suggestion":str}]}
match=true only if intent, biology, and code agree.
"""

_MOTION_RE = re.compile(
    r"(?i)\b(resume_run|play_run|control_run|resume|play)\b"
)


_MAX_SIM_ERROR_CHARS = 800


def build_review_messages(
    *,
    user_intent: str,
    protocol_source: str,
    sim_error: str | None = None,
) -> list[dict[str, str]]:
    parts = [f"User intent:\n{user_intent.strip() or '(empty)'}\n"]
    if sim_error and sim_error.strip():
        parts.append(
            "SimPass error (blocking; do not treat as passed):\n"
            f"{sim_error.strip()[:_MAX_SIM_ERROR_CHARS]}\n"
        )
    parts.append(f"Protocol source:\n```python\n{protocol_source}\n```\n")
    return [
        {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
        {"role": "user", "content": "".join(parts)},
    ]


def _strip_motion_text(text: str) -> str:
    return _MOTION_RE.sub("[redacted]", text)


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return _strip_motion_text(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _sanitize_value(v) for k, v in value.items()}
    return value


def _normalize_findings(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    findings: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        findings.append(
            {
                "severity": str(item.get("severity") or "warning"),
                "claim": str(item.get("claim") or ""),
                "evidence": str(item.get("evidence") or ""),
                "suggestion": str(item.get("suggestion") or ""),
            }
        )
    return findings


def parse_review_payload(content: str) -> dict[str, Any]:
    try:
        parsed = _load_first_json_object(content)
    except (json.JSONDecodeError, ValueError, TypeError):
        return {
            "match": False,
            "findings": [
                {
                    "severity": "error",
                    "claim": "reviewer_unparseable",
                    "evidence": (content or "")[:400],
                    "suggestion": "Return JSON {match, findings}.",
                }
            ],
        }
    match = parsed.get("match")
    if not isinstance(match, bool):
        match = False
    payload = {
        "match": match,
        "findings": _normalize_findings(parsed.get("findings")),
    }
    return _sanitize_value(payload)


def _final_content(response: dict[str, Any]) -> str:
    final = response.get("final")
    if isinstance(final, dict):
        msg = final.get("message")
        if isinstance(msg, str) and msg.strip():
            return msg
        return json.dumps(final, ensure_ascii=False)
    if isinstance(final, str) and final.strip():
        return final
    content = response.get("content")
    if isinstance(content, str):
        return content
    return json.dumps(response, ensure_ascii=False, default=str)


def run_llmreview(
    *,
    user_intent: str,
    protocol_source: str,
    client: Any | None = None,
    sim_error: str | None = None,
) -> dict[str, Any]:
    """Call the flash reviewer with tools=None. Does not touch LogicPass."""
    if client is None:
        from labscriptai.agent.llm import build_review_client

        client = build_review_client()
    messages = build_review_messages(
        user_intent=user_intent,
        protocol_source=protocol_source,
        sim_error=sim_error,
    )
    try:
        response = client.complete(messages, tools=None)
    except Exception as exc:  # noqa: BLE001 — never look like SimPass failure
        return {
            "match": False,
            "findings": [
                {
                    "severity": "error",
                    "claim": "reviewer_exception",
                    "evidence": str(exc)[:400],
                    "suggestion": "Return JSON {match, findings}.",
                }
            ],
        }
    return parse_review_payload(_final_content(response))
