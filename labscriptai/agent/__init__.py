"""Lean agent surface: llm, gate, tools, loop, cli, mcp_adapter."""

from .gate import GateDecision, evaluate, infer_context
from .llm import OfflineClient, OpenAICompatibleClient, OpenAICompatibleConfig

__all__ = (
    "GateDecision",
    "OfflineClient",
    "OpenAICompatibleClient",
    "OpenAICompatibleConfig",
    "evaluate",
    "infer_context",
)
