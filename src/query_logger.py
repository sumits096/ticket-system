"""Query logging for analytics and audit trail."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.config import QUERY_LOG_PATH

logger = logging.getLogger(__name__)


class QueryLogger:
    """Appends query/response logs to a JSONL file."""

    def __init__(self, log_path: str | Path | None = None):
        self._path = Path(log_path or QUERY_LOG_PATH)

    def log_query(
        self,
        question: str,
        region: str,
        answer: str,
        confidence: float,
        sources: list,
        user_id: Optional[str] = None,
        has_answer: bool = True,
    ) -> None:
        """Log a single query and its response."""
        entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "question": question,
            "region": region,
            "answer": answer[:500] + "..." if len(answer) > 500 else answer,
            "confidence": confidence,
            "has_answer": has_answer,
            "sources": [
                {"source": s.get("source"), "region": s.get("region")}
                for s in sources
            ],
            "user_id": user_id,
        }
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning("Failed to log query: %s", e)
