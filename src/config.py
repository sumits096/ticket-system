"""Application configuration and constants."""

from pathlib import Path
from typing import Dict, List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    cohere_api_key: str = ""
    chroma_persist_dir: str = "./chroma_db"
    log_level: str = "INFO"

    # Jira integration settings
    jira_url: str = ""           # e.g. https://yourorg.atlassian.net
    jira_email: str = ""         # Atlassian account email
    jira_api_token: str = ""     # API token from id.atlassian.com
    jira_project_key: str = "SUP"

    # Optional webhook security secret (HMAC validation)
    webhook_secret: str = ""

    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_persist_dir)

    @property
    def jira_configured(self) -> bool:
        return bool(self.jira_url and self.jira_email and self.jira_api_token)


# Supported regions for multi-region documentation
REGIONS: List[str] = [
    "All",
    "India",
    "US",
]

# Common departments for filter dropdown (empty = "All")
DEPARTMENTS: List[str] = [
    "",
    "Infra",
    "HR",
    "Finance",
    "General",
]

# ChromaDB collection name
COLLECTION_NAME = "knowledge_base"

# Embedding model (embed-v4.0 recommended for Cohere v2 API)
EMBED_MODEL = "embed-english-v3.0"

# Chat/Generation model (command-r deprecated Sept 2025; use command-a or command-r-08-2024)
CHAT_MODEL = "command-a-03-2025"

# RAG parameters
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RETRIEVAL = 5

# Query log file
QUERY_LOG_PATH = "query_logs.jsonl"

# Ticket resolutions JSON (relative to project root)
TICKET_RESOLUTIONS_PATH = "data/ticket_resolutions.json"

# Integration event log (one JSON record per line)
INTEGRATION_LOG_PATH = "integration_logs.jsonl"

# Department → default Jira assignee account-id or email
# Override these with real Atlassian account IDs from your Jira instance
ASSIGNEE_MAP: Dict[str, str] = {
    "Infra":   "infra-team@company.com",
    "HR":      "hr-team@company.com",
    "Finance": "finance-team@company.com",
    "General": "support-team@company.com",
}

# AI priority level → Jira priority name
JIRA_PRIORITY_MAP: Dict[str, str] = {
    "P1": "Highest",
    "P2": "High",
    "P3": "Medium",
    "P4": "Low",
}
