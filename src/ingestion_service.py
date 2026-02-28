"""Document ingestion pipeline: load, chunk, embed, store."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.chunker import chunk_text
from src.config import REGIONS, Settings, TICKET_RESOLUTIONS_PATH
from src.document_loader import load_document
from src.embedding_service import EmbeddingService
from src.models import DocumentChunk, IngestResult
from src.vector_store import VectorStore

logger = logging.getLogger(__name__)
TICKET_SOURCE = "ticket_resolutions"


class IngestionService:
    """Orchestrates document upload, chunking, embedding, and storage."""

    def __init__(self):
        self._embedding_service = EmbeddingService()
        self._vector_store = VectorStore()

    def ingest_file(
        self,
        file_path: Path,
        region: str,
        department: str = "General",
        source_name: Optional[str] = None,
    ) -> IngestResult:
        """
        Ingest a single document (PDF/DOCX).
        source_name overrides the filename for display purposes.
        """
        if region not in REGIONS:
            return IngestResult(
                source=file_path.name,
                region=region,
                department=department,
                chunks_created=0,
                success=False,
                error=f"Invalid region. Must be one of: {REGIONS}",
            )

        text = load_document(file_path)
        if not text or not text.strip():
            return IngestResult(
                source=file_path.name,
                region=region,
                department=department,
                chunks_created=0,
                success=False,
                error="Could not extract text from document",
            )

        source = source_name or file_path.name
        chunks = chunk_text(text, source=source, region=region, department=department)
        if not chunks:
            return IngestResult(
                source=source,
                region=region,
                department=department,
                chunks_created=0,
                success=False,
                error="No chunks produced from document",
            )

        try:
            embeddings = self._embedding_service.embed_documents(
                [c.content for c in chunks]
            )
            uploaded_at = datetime.utcnow().isoformat() + "Z"
            self._vector_store.add_chunks(chunks, embeddings, uploaded_at=uploaded_at)
            return IngestResult(
                source=source,
                region=region,
                department=department,
                chunks_created=len(chunks),
                success=True,
            )
        except Exception as e:
            logger.exception("Ingestion failed: %s", e)
            return IngestResult(
                source=source,
                region=region,
                department=department,
                chunks_created=0,
                success=False,
                error=str(e),
            )

    def ingest_ticket_resolutions(
        self,
        json_path: Path | str | None = None,
    ) -> IngestResult:
        """
        Load ticket resolutions from JSON and ingest into the vector store.
        Replaces any existing ticket_resolutions. Each ticket becomes one chunk.
        """
        path = Path(json_path or TICKET_RESOLUTIONS_PATH)
        if not path.is_absolute():
            path = Path.cwd() / path

        if not path.exists():
            return IngestResult(
                source=TICKET_SOURCE,
                region="",
                department="",
                chunks_created=0,
                success=False,
                error=f"File not found: {path}",
            )

        try:
            with open(path, encoding="utf-8") as f:
                tickets: List[dict] = json.load(f)
        except json.JSONDecodeError as e:
            return IngestResult(
                source=TICKET_SOURCE,
                region="",
                department="",
                chunks_created=0,
                success=False,
                error=f"Invalid JSON: {e}",
            )

        if not tickets:
            return IngestResult(
                source=TICKET_SOURCE,
                region="",
                department="",
                chunks_created=0,
                success=True,
            )

        chunks: List[DocumentChunk] = []
        for i, t in enumerate(tickets):
            ticket = t.get("ticket", "")
            region_raw = str(t.get("region", "")).strip() or "All"
            resolution = t.get("resolution", "")
            department = t.get("department", "General")
            region = next(
                (r for r in REGIONS if r.upper() == region_raw.upper()),
                REGIONS[0],
            )

            content = f"Ticket: {ticket}. Resolution: {resolution}."
            if not content.strip() or content == "Ticket: . Resolution: .":
                continue

            chunks.append(
                DocumentChunk(
                    content=content,
                    source=TICKET_SOURCE,
                    region=region,
                    department=department,
                    chunk_index=i,
                )
            )

        if not chunks:
            return IngestResult(
                source=TICKET_SOURCE,
                region="",
                department="",
                chunks_created=0,
                success=False,
                error="No valid tickets found in JSON",
            )

        # Remove existing ticket resolutions, then add new ones
        self._vector_store.delete_by_source(TICKET_SOURCE)

        try:
            embeddings = self._embedding_service.embed_documents(
                [c.content for c in chunks]
            )
            uploaded_at = datetime.utcnow().isoformat() + "Z"
            self._vector_store.add_chunks(chunks, embeddings, uploaded_at=uploaded_at)
            logger.info("Ingested %d ticket resolutions", len(chunks))
            return IngestResult(
                source=TICKET_SOURCE,
                region="",
                department="",
                chunks_created=len(chunks),
                success=True,
            )
        except Exception as e:
            logger.exception("Ticket ingestion failed: %s", e)
            return IngestResult(
                source=TICKET_SOURCE,
                region="",
                department="",
                chunks_created=0,
                success=False,
                error=str(e),
            )
