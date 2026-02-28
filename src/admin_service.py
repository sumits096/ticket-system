"""Admin document manager for the knowledge base."""

import logging
from pathlib import Path
from typing import List, Optional

from src.config import DEPARTMENTS, REGIONS
from src.ingestion_service import IngestionService
from src.models import DocumentMetadata, IngestResult
from src.vector_store import VectorStore

logger = logging.getLogger(__name__)


class AdminService:
    """Administrative operations for document and knowledge base management."""

    def __init__(self):
        self._ingestion = IngestionService()
        self._vector_store = VectorStore()

    def sync_ticket_resolutions(self, json_path: Path | str | None = None) -> IngestResult:
        """Load and ingest ticket resolutions from JSON file."""
        return self._ingestion.ingest_ticket_resolutions(json_path=json_path)

    def upload_document(
        self,
        file_path: Path,
        region: str,
        department: str = "General",
        source_name: Optional[str] = None,
    ) -> IngestResult:
        """Upload and ingest a document (PDF/DOCX) with region and department metadata."""
        return self._ingestion.ingest_file(
            file_path=file_path,
            region=region,
            department=department,
            source_name=source_name,
        )

    def delete_document(
        self,
        source: str,
        region: str | None = None,
        department: str | None = None,
    ) -> int:
        """
        Delete chunks for a document.
        If region and department are provided, deletes only that specific doc.
        Otherwise deletes all chunks with that source name.
        """
        if region and department:
            return self._vector_store.delete_by_source_region_department(
                source=source,
                region=region,
                department=department,
            )
        return self._vector_store.delete_by_source(source)

    def list_documents(self) -> List[DocumentMetadata]:
        """List all unique documents in the knowledge base."""
        sources = self._vector_store.list_sources()
        return [
            DocumentMetadata(
                source=s.get("source", ""),
                region=s.get("region", ""),
                department=s.get("department", ""),
                chunk_count=s.get("chunk_count", 0),
                uploaded_at=s.get("uploaded_at"),
            )
            for s in sources
        ]

    def get_stats(self) -> dict:
        """Get knowledge base statistics."""
        return self._vector_store.get_collection_stats()

    @staticmethod
    def get_regions() -> List[str]:
        """Return supported regions."""
        return list(REGIONS)

    @staticmethod
    def get_departments() -> List[str]:
        """Return department options for filter. Empty string = All."""
        return list(DEPARTMENTS)
