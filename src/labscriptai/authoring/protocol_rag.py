"""ChromaDB-backed protocol library retrieval for KB context."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

EMBED_DIM = 384
COLLECTION_NAME = "protocol_library"
INDEX_VERSION = "1"


def _mock_embed(text: str) -> list[float]:
    """Deterministic pseudo-embedding when no local model is available."""

    vector = [0.0] * EMBED_DIM
    for token in re.findall(r"[a-z0-9_]+", text.lower()):
        digest = hashlib.sha256(token.encode()).digest()
        vector[digest[0] % EMBED_DIM] += 1.0
        vector[digest[1] % EMBED_DIM] += 0.5
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _load_search_protocols_module(repo_root: Path) -> Any:
    script = (
        repo_root
        / "skills"
        / "opentrons-protocol-library"
        / "scripts"
        / "search_protocols.py"
    )
    spec = importlib.util.spec_from_file_location("search_protocols", script)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(f"protocol search script not found: {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _catalog_documents(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for proto in catalog.get("protocols", []):
        if not isinstance(proto, dict) or proto.get("hidden"):
            continue
        slug = str(proto.get("slug") or "")
        if not slug:
            continue
        searchable = " ".join(
            [
                slug,
                str(proto.get("title") or ""),
                str(proto.get("description") or ""),
                " ".join(str(tag) for tag in proto.get("method_tags", [])),
                " ".join(
                    f"{category} {' '.join(subs)}"
                    for category, subs in (proto.get("categories") or {}).items()
                    if isinstance(subs, list)
                ),
                " ".join(str(item) for item in proto.get("pipettes", [])),
                " ".join(str(item) for item in proto.get("labware", [])),
                " ".join(str(item) for item in proto.get("reagents", [])),
            ]
        ).strip()
        if not searchable:
            continue
        documents.append(
            {
                "id": slug,
                "document": searchable,
                "metadata": {
                    "name": slug,
                    "title": str(proto.get("title") or slug),
                    "path": slug,
                    "description": str(proto.get("description") or "")[:500],
                },
            }
        )
    return documents


def _filesystem_documents(search_module: Any, library_path: Path) -> list[dict[str, Any]]:
    protocols_dir = library_path / "protocols"
    if not protocols_dir.exists():
        return []
    documents: list[dict[str, Any]] = []
    for proto_folder in sorted(protocols_dir.iterdir()):
        if not proto_folder.is_dir():
            continue
        search_document, _sections = search_module.build_protocol_document(proto_folder)
        readme_path = proto_folder / "README.md"
        description = (
            search_module.extract_summary_from_readme(readme_path)
            if readme_path.exists()
            else f"Protocol at {proto_folder.name}"
        )
        documents.append(
            {
                "id": proto_folder.name,
                "document": search_document,
                "metadata": {
                    "name": proto_folder.name,
                    "title": proto_folder.name,
                    "path": str(proto_folder),
                    "description": description or f"Protocol at {proto_folder.name}",
                },
            }
        )
    return documents


class _Collection(Protocol):
    def count(self) -> int: ...

    def add(
        self,
        *,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None: ...

    def query(
        self,
        *,
        query_texts: list[str],
        n_results: int,
    ) -> dict[str, Any]: ...


@dataclass
class _StoredDocument:
    doc_id: str
    document: str
    metadata: dict[str, Any]
    embedding: list[float]


class _InMemoryCollection:
    """Fallback vector store when chromadb is not installed."""

    def __init__(self) -> None:
        self._documents: list[_StoredDocument] = []

    def count(self) -> int:
        return len(self._documents)

    def add(
        self,
        *,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        existing = {item.doc_id for item in self._documents}
        for doc_id, document, metadata in zip(ids, documents, metadatas):
            if doc_id in existing:
                continue
            self._documents.append(
                _StoredDocument(
                    doc_id=doc_id,
                    document=document,
                    metadata=metadata,
                    embedding=_mock_embed(document),
                )
            )

    def query(
        self,
        *,
        query_texts: list[str],
        n_results: int,
    ) -> dict[str, Any]:
        if not self._documents or not query_texts:
            return {"ids": [[]], "metadatas": [[]], "distances": [[]]}
        query_vector = _mock_embed(query_texts[0])
        ranked = sorted(
            self._documents,
            key=lambda item: _cosine(query_vector, item.embedding),
            reverse=True,
        )[: max(1, n_results)]
        return {
            "ids": [[item.doc_id for item in ranked]],
            "metadatas": [[item.metadata for item in ranked]],
            "distances": [[1.0 - _cosine(query_vector, item.embedding) for item in ranked]],
        }


class MockEmbeddingFunction:
    """Chroma-compatible embedding function using deterministic mock vectors."""

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [_mock_embed(text) for text in input]

    def name(self) -> str:
        return "mock_hash_embedding"


class ProtocolRAGStore:
    """ChromaDB client wrapper with mock embeddings and in-memory fallback."""

    def __init__(
        self,
        *,
        repo_root: Path,
        persist_dir: Path | None = None,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        self.repo_root = repo_root
        self.persist_dir = persist_dir or (repo_root / ".cache" / "chromadb" / "protocol_library")
        self.collection_name = collection_name
        self._collection: _Collection | None = None
        self._using_chroma = False

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            return []
        collection = self._get_collection()
        self._ensure_indexed(collection)
        payload = collection.query(query_texts=[query], n_results=max(1, limit))
        return self._format_hits(payload)

    def _get_collection(self) -> _Collection:
        if self._collection is not None:
            return self._collection
        try:
            import chromadb
        except ImportError:
            self._collection = _InMemoryCollection()
            self._using_chroma = False
            return self._collection

        self.persist_dir.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._collection = client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=MockEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"},
        )
        self._using_chroma = True
        return self._collection

    def _ensure_indexed(self, collection: _Collection) -> None:
        # resolve_library_path raises SystemExit when no protocol library is
        # configured (CLI-style signal); degrade to empty results instead of
        # crashing KB-context building.
        try:
            search_module = _load_search_protocols_module(self.repo_root)
            library_path = search_module.resolve_library_path(None, repo_root=self.repo_root)
        except (FileNotFoundError, OSError, SystemExit):
            return
        marker_path = self.persist_dir / "index_meta.json"
        library_signature = _library_signature(library_path)
        if marker_path.exists() and collection.count() > 0:
            try:
                marker = json.loads(marker_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                marker = {}
            if marker.get("signature") == library_signature and marker.get("version") == INDEX_VERSION:
                return

        documents = _load_protocol_documents(search_module, library_path)
        if not documents:
            return

        if isinstance(collection, _InMemoryCollection):
            collection._documents.clear()
        elif self._using_chroma:
            try:
                import chromadb

                client = chromadb.PersistentClient(path=str(self.persist_dir))
                client.delete_collection(self.collection_name)
                self._collection = client.get_or_create_collection(
                    name=self.collection_name,
                    embedding_function=MockEmbeddingFunction(),
                    metadata={"hnsw:space": "cosine"},
                )
                collection = self._collection
            except Exception:
                pass

        batch_size = 128
        for start in range(0, len(documents), batch_size):
            batch = documents[start : start + batch_size]
            collection.add(
                ids=[item["id"] for item in batch],
                documents=[item["document"] for item in batch],
                metadatas=[item["metadata"] for item in batch],
            )

        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(
            json.dumps(
                {
                    "version": INDEX_VERSION,
                    "signature": library_signature,
                    "document_count": len(documents),
                    "backend": "chromadb" if self._using_chroma else "in_memory",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _format_hits(payload: dict[str, Any]) -> list[dict[str, Any]]:
        ids = (payload.get("ids") or [[]])[0]
        metadatas = (payload.get("metadatas") or [[]])[0]
        distances = (payload.get("distances") or [[]])[0]
        hits: list[dict[str, Any]] = []
        for index, doc_id in enumerate(ids):
            metadata = metadatas[index] if index < len(metadatas) else {}
            if not isinstance(metadata, dict):
                metadata = {}
            hit = {
                "name": str(metadata.get("name") or doc_id),
                "title": str(metadata.get("title") or metadata.get("name") or doc_id),
                "path": str(metadata.get("path") or doc_id),
                "description": str(metadata.get("description") or ""),
            }
            if index < len(distances):
                hit["score"] = 1.0 - float(distances[index])
            hits.append(hit)
        return hits


def _load_protocol_documents(search_module: Any, library_path: Path) -> list[dict[str, Any]]:
    catalog = search_module.load_catalog(library_path)
    if catalog is not None:
        return _catalog_documents(catalog)
    return _filesystem_documents(search_module, library_path)


def _library_signature(library_path: Path) -> str:
    catalog_path = library_path / "protocol-catalog.json"
    if catalog_path.exists():
        return hashlib.sha256(catalog_path.read_bytes()).hexdigest()
    protocols_dir = library_path / "protocols"
    if not protocols_dir.exists():
        return ""
    parts = [path.name for path in sorted(protocols_dir.iterdir()) if path.is_dir()]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


_STORES: dict[str, ProtocolRAGStore] = {}


def get_protocol_rag_store(repo_root: Path) -> ProtocolRAGStore:
    key = str(repo_root.resolve())
    store = _STORES.get(key)
    if store is None:
        store = ProtocolRAGStore(repo_root=repo_root)
        _STORES[key] = store
    return store


def search_protocol_library(
    query: str,
    *,
    repo_root: Path,
    limit: int = 10,
) -> list[dict[str, Any]]:
    return get_protocol_rag_store(repo_root).search(query, limit=limit)
