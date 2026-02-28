"""Data models for the knowledge base agent."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


@dataclass
class DocumentChunk:
    """A chunk of text extracted from a document with metadata."""

    content: str
    source: str
    region: str
    department: str
    chunk_index: int


@dataclass
class RetrievedChunk:
    """A chunk retrieved from the vector store with similarity score."""

    content: str
    source: str
    region: str
    department: str
    score: float
    metadata: Dict[str, Any]


class IngestResult(BaseModel):
    """Result of document ingestion."""

    source: str
    region: str
    department: str
    chunks_created: int
    success: bool
    error: Optional[str] = None


class QueryRequest(BaseModel):
    """Incoming query from a user."""

    question: str
    region: str
    department: Optional[str] = None
    user_id: Optional[str] = None


class SourceCitation(BaseModel):
    """A cited source from the retrieved context."""

    source: str
    region: str
    excerpt: Optional[str] = None


class QueryResponse(BaseModel):
    """Response from the RAG pipeline."""

    answer: str
    sources: List[SourceCitation]
    confidence: float
    has_answer: bool


class DocumentMetadata(BaseModel):
    """Metadata for an uploaded document."""

    source: str
    region: str
    department: str
    chunk_count: int
    uploaded_at: Optional[str] = None
