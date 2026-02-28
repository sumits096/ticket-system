"""Application configuration and constants."""

from pathlib import Path
from typing import List

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

    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_persist_dir)


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
