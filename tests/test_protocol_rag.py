from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from labscriptai.authoring import protocol_rag


def test_mock_embed_is_deterministic() -> None:
    first = protocol_rag._mock_embed("serial dilution pcr")
    second = protocol_rag._mock_embed("serial dilution pcr")
    assert first == second
    assert len(first) == protocol_rag.EMBED_DIM


def test_search_protocol_library_returns_hits(tmp_path: Path) -> None:
    store = protocol_rag.ProtocolRAGStore(repo_root=ROOT, persist_dir=tmp_path / "chroma")
    hits = store.search("serial dilution", limit=3)
    assert hits
    assert all("name" in hit and "title" in hit for hit in hits)


def test_kb_context_uses_protocol_rag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from labscriptai.authoring import kb_context
    from labscriptai.benchmark.tasks import AuthoringTask

    def fake_search(query: str, *, repo_root: Path, limit: int = 10):
        assert query == "serial dilution"
        return [
            {
                "name": "00222e",
                "title": "Serial Dilution",
                "path": "00222e",
                "description": "Example serial dilution protocol.",
            }
        ]

    monkeypatch.setattr(kb_context, "search_protocol_library", fake_search)
    task = AuthoringTask(
        task_id="T001",
        source="test",
        difficulty="Easy",
        holdout=True,
        output_contract="package",
        prompt="Create a serial dilution protocol.",
    )
    context = kb_context.build_kb_context(task, repo_root=tmp_path, context_mode="full")
    assert context.protocol_hits
    assert context.protocol_hits[0]["title"] == "Serial Dilution"
