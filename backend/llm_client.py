# -*- coding: utf-8 -*-
"""OpenAI-compatible HTTP client for Opentrons code generation."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List, Optional, TypedDict

import httpx

from backend.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_INTENT_MODEL,
    REQUEST_TIMEOUT,
)

CONNECT_TIMEOUT = 30.0
MAX_RETRIES = 2  # 3 total attempts
_RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 504}


class StreamPart(TypedDict):
    kind: str  # "reasoning" | "content"
    text: str


def _chat_url() -> str:
    base = (DEEPSEEK_BASE_URL or "").rstrip("/")
    if not base:
        raise RuntimeError("DEEPSEEK_BASE_URL is not configured")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }


def _timeout() -> httpx.Timeout:
    return httpx.Timeout(REQUEST_TIMEOUT, connect=CONNECT_TIMEOUT)


def _payload(prompt: str, stream: bool) -> Dict[str, Any]:
    return {
        "model": DEEPSEEK_INTENT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "stream": stream,
    }


def _nonempty_str(value: Any) -> str:
    return value if isinstance(value, str) and value else ""


def _extract_message_content(data: Dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    # Ignore reasoning_content; only use message.content.
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if not isinstance(item, dict):
                continue
            part_type = str(item.get("type") or "").lower()
            if part_type in {"reasoning", "thinking", "reasoning_content"}:
                continue
            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)
        return "".join(parts)
    return ""


def _extract_delta_content(data: Dict[str, Any]) -> str:
    for part in _extract_delta_parts(data):
        if part["kind"] == "content":
            return part["text"]
    return ""


def _extract_delta_parts(data: Dict[str, Any]) -> List[StreamPart]:
    """Pull reasoning and content increments from a stream delta."""
    choices = data.get("choices") or []
    if not choices:
        return []
    delta = choices[0].get("delta") or {}
    parts: List[StreamPart] = []

    reasoning = _nonempty_str(delta.get("reasoning_content")) or _nonempty_str(
        delta.get("reasoning")
    )
    if reasoning:
        parts.append({"kind": "reasoning", "text": reasoning})

    content = delta.get("content")
    if isinstance(content, str) and content:
        parts.append({"kind": "content", "text": content})
        return parts
    if not isinstance(content, list):
        return parts
    for item in content:
        if isinstance(item, str) and item:
            parts.append({"kind": "content", "text": item})
            continue
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if not isinstance(text, str) or not text:
            continue
        part_type = str(item.get("type") or "").lower()
        if part_type in {"reasoning", "thinking", "reasoning_content"}:
            parts.append({"kind": "reasoning", "text": text})
        else:
            parts.append({"kind": "content", "text": text})
    return parts


def _should_retry(exc: BaseException, status_code: Optional[int] = None) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in _RETRYABLE_STATUS
    if status_code is not None:
        return status_code in _RETRYABLE_STATUS
    return False


async def complete(prompt: str) -> str:
    """Non-streaming chat completion. Returns assistant content only."""
    last_error: Optional[BaseException] = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=_timeout()) as client:
                response = await client.post(
                    _chat_url(),
                    headers=_headers(),
                    json=_payload(prompt, stream=False),
                )
                if response.status_code in _RETRYABLE_STATUS and attempt < MAX_RETRIES:
                    last_error = httpx.HTTPStatusError(
                        f"HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                    continue
                response.raise_for_status()
                return _extract_message_content(response.json())
        except Exception as exc:
            last_error = exc
            if attempt >= MAX_RETRIES or not _should_retry(exc):
                raise
    if last_error:
        raise last_error
    return ""


async def astream_parts(prompt: str) -> AsyncIterator[StreamPart]:
    """Yield non-empty stream parts: reasoning first, then content."""
    last_error: Optional[BaseException] = None
    for attempt in range(MAX_RETRIES + 1):
        yielded = False
        try:
            async with httpx.AsyncClient(timeout=_timeout()) as client:
                async with client.stream(
                    "POST",
                    _chat_url(),
                    headers=_headers(),
                    json=_payload(prompt, stream=True),
                ) as response:
                    if response.status_code in _RETRYABLE_STATUS and attempt < MAX_RETRIES:
                        last_error = httpx.HTTPStatusError(
                            f"HTTP {response.status_code}",
                            request=response.request,
                            response=response,
                        )
                        continue
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data:"):
                            payload = line[5:].strip()
                        else:
                            continue
                        if payload == "[DONE]":
                            return
                        try:
                            chunk = json.loads(payload)
                        except json.JSONDecodeError:
                            continue
                        for part in _extract_delta_parts(chunk):
                            if part["text"]:
                                yielded = True
                                yield part
            return
        except Exception as exc:
            last_error = exc
            if yielded or attempt >= MAX_RETRIES or not _should_retry(exc):
                raise
    if last_error:
        raise last_error


async def astream(prompt: str) -> AsyncIterator[str]:
    """Yield non-empty assistant content tokens. Skip reasoning_content."""
    async for part in astream_parts(prompt):
        if part["kind"] == "content" and part["text"]:
            yield part["text"]
