"""ChromaDB vector store with region-aware metadata filtering."""

import logging
import uuid
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config import COLLECTION_NAME, Settings
from src.models import DocumentChunk, RetrievedChunk

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB-backed vector store with metadata support."""

    def __init__(self, persist_directory: str | None = None):
        settings = Settings()
        persist_dir = str(persist_directory or settings.chroma_path)
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Enterprise knowledge base"},
        )

    def add_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
        uploaded_at: str | None = None,
    ) -> None:
        """Add document chunks with embeddings to the store."""
        if not chunks or not embeddings:
            return
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings count must match")

        ids = [str(uuid.uuid4()) for _ in chunks]
        base_meta: Dict[str, Any] = {
            "source": chunks[0].source,
            "region": chunks[0].region,
            "department": chunks[0].department,
        }
        if uploaded_at:
            base_meta["uploaded_at"] = uploaded_at

        metadatas = [
            {
                **base_meta,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]
        documents = [c.content for c in chunks]

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info("Added %d chunks to vector store", len(chunks))

    def search(
        self,
        query_embedding: List[float],
        region: str,
        top_k: int = 5,
        department: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        """
        Search for similar chunks with region-aware filtering.
        When region is "All", returns chunks with region="All".
        When region is specific (e.g. India), returns chunks for that region OR region="All".
        """
        if region == "All":
            region_filter: Dict[str, Any] = {"region": {"$eq": "All"}}
        else:
            region_filter = {
                "$or": [
                    {"region": {"$eq": region}},
                    {"region": {"$eq": "All"}},
                ]
            }

        where_filter = region_filter
        if department:
            where_filter = {
                "$and": [region_filter, {"department": {"$eq": department}}],
            }

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        if not results or not results["documents"][0]:
            return []

        chunks: List[RetrievedChunk] = []
        docs = results["documents"][0]
        metadatas = results["metadatas"][0] or []
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

        for i, doc in enumerate(docs):
            meta = metadatas[i] if i < len(metadatas) else {}
            # ChromaDB uses L2 distance - lower is better; convert to similarity-like score (0-1)
            dist = distances[i] if i < len(distances) else 0
            score = 1.0 / (1.0 + dist) if dist else 1.0

            chunks.append(
                RetrievedChunk(
                    content=doc or "",
                    source=meta.get("source", "unknown"),
                    region=meta.get("region", "unknown"),
                    department=meta.get("department", "unknown"),
                    score=score,
                    metadata=dict(meta),
                )
            )

        return chunks

    def get_collection_stats(self) -> Dict[str, int]:
        """Get counts for admin reporting."""
        count = self._collection.count()
        return {"total_chunks": count}

    def delete_by_source(self, source: str) -> int:
        """Delete all chunks from a specific source. Returns deleted count."""
        return self._delete_chunks(where={"source": {"$eq": source}})

    def delete_by_source_region_department(
        self,
        source: str,
        region: str,
        department: str,
    ) -> int:
        """Delete chunks matching source, region, and department. Returns deleted count."""
        return self._delete_chunks(
            where={
                "$and": [
                    {"source": {"$eq": source}},
                    {"region": {"$eq": region}},
                    {"department": {"$eq": department}},
                ]
            }
        )

    def _delete_chunks(self, where: dict) -> int:
        """Delete chunks matching the where filter. Returns deleted count."""
        try:
            existing = self._collection.get(where=where, include=[])
            ids = existing["ids"]
            if ids:
                self._collection.delete(ids=ids)
                logger.info("Deleted %d chunks", len(ids))
                return len(ids)
        except Exception as e:
            logger.error("Delete failed: %s", e)
        return 0

    def list_sources(self) -> List[Dict[str, Any]]:
        """List unique sources in the collection with chunk counts and uploaded_at."""
        try:
            all_data = self._collection.get(include=["metadatas"])
            metadatas = all_data.get("metadatas") or []
            # Aggregate per (source, region, department): count and latest uploaded_at
            agg: Dict[tuple, tuple[int, str | None]] = {}
            for m in metadatas:
                if m:
                    key = (m.get("source"), m.get("region"), m.get("department"))
                    prev_count, prev_ts = agg.get(key, (0, None))
                    ts = m.get("uploaded_at") or prev_ts
                    agg[key] = (prev_count + 1, ts or prev_ts)
            return [
                {
                    "source": k[0],
                    "region": k[1],
                    "department": k[2],
                    "chunk_count": v[0],
                    "uploaded_at": v[1],
                }
                for k, v in agg.items()
            ]
        except Exception as e:
            logger.error("List sources failed: %s", e)
            return []
