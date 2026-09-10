#!/usr/bin/env python3
"""Thin CLI: {user_intent, protocol_source} → llmreview dict. Never mutates logic_pass."""

from __future__ import annotations

import json
import sys
from typing import Any


def fail(reason: str) -> dict[str, Any]:
    return {
        "match": False,
        "findings": [
            {
                "severity": "error",
                "claim": "reviewer_exception",
                "evidence": reason[:400],
                "suggestion": "Return JSON {match, findings}.",
            }
        ],
        "reason": reason,
    }


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if not isinstance(payload, dict):
            raise ValueError("payload was not an object")
    except Exception as exc:
        print(json.dumps(fail(f"invalid_review_json:{exc}")))
        return 0

    try:
        from labscriptai.agent.llmreview import run_llmreview
    except ImportError:
        print(json.dumps(fail("llmreview_package_missing")))
        return 0

    result = run_llmreview(
        user_intent=str(payload.get("user_intent") or ""),
        protocol_source=str(payload.get("protocol_source") or ""),
        sim_error=str(payload["sim_error"]) if payload.get("sim_error") else None,
    )
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
