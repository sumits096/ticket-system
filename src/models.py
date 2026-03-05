"""Data models for the knowledge base agent."""

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

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


# ── Integration / Webhook models ──────────────────────────────────────────────

class IncomingTicket(BaseModel):
    """Normalised ticket received from any external system (ServiceNow, Zendesk, …)."""

    source_system: Literal["servicenow", "zendesk", "manual"]
    external_id: str
    subject: str
    description: str
    reporter: Optional[str] = None
    region: str = "All"
    raw_payload: Optional[Dict[str, Any]] = None


class TicketDecision(BaseModel):
    """AI-generated decision for an incoming ticket."""

    department: str
    priority: Literal["P1", "P2", "P3", "P4"]
    priority_reason: str
    assignee_name: str
    resolution: str
    confidence: float
    sources: List[SourceCitation] = []


class JiraIssueResult(BaseModel):
    """Result of creating a Jira issue."""

    success: bool
    issue_key: Optional[str] = None
    issue_url: Optional[str] = None
    error: Optional[str] = None


class IntegrationLog(BaseModel):
    """Audit record for a processed webhook event."""

    timestamp: str
    source_system: str
    external_id: str
    subject: str
    department: str
    priority: str
    assignee_name: str
    jira_issue_key: Optional[str] = None
    jira_issue_url: Optional[str] = None
    success: bool
    error: Optional[str] = None
