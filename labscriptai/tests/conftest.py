"""Ensure repo-root import path for labscriptai without editable install."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    expr = (getattr(config.option, "markexpr", None) or "").strip()
    wants_llm = expr == "llm" or expr.startswith("llm ") or expr.endswith(" llm") or " llm " in f" {expr} "
    if wants_llm and "not llm" in expr:
        wants_llm = False
    if wants_llm:
        return
    skip_llm = pytest.mark.skip(reason="live DeepSeek tests; run with pytest -m llm")
    for item in items:
        if item.get_closest_marker("llm"):
            item.add_marker(skip_llm)
