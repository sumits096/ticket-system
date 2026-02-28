"""Cohere embedding service for document and query embeddings."""

import logging
from typing import List

import cohere

from src.config import EMBED_MODEL, Settings

logger = logging.getLogger(__name__)

# Cohere embed API limit: max 96 texts per request
EMBED_BATCH_SIZE = 96


def _extract_embeddings(response) -> List[List[float]]:
    """Extract float embeddings from Cohere v2 API response."""
    emb = response.embeddings
    # v2 API returns embeddings.float (or .float_) for embedding_types=["float"]
    vectors = getattr(emb, "float", None) or getattr(emb, "float_", None)
    if vectors is None and hasattr(emb, "__iter__") and not isinstance(emb, (str, dict)):
        vectors = list(emb)
    if vectors is None:
        raise ValueError("Could not extract embeddings from response")
    return [list(v) for v in vectors]


class EmbeddingService:
    """Generates embeddings using Cohere's embed model (v2 API)."""

    def __init__(self, api_key: str | None = None):
        settings = Settings()
        self._client = cohere.ClientV2(api_key=api_key or settings.cohere_api_key)
        self._model = EMBED_MODEL

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents for storage. Use search_document input type. Batches by 96."""
        if not texts:
            return []
        all_embeddings: List[List[float]] = []
        try:
            for i in range(0, len(texts), EMBED_BATCH_SIZE):
                batch = texts[i : i + EMBED_BATCH_SIZE]
                response = self._client.embed(
                    texts=batch,
                    model=self._model,
                    input_type="search_document",
                    embedding_types=["float"],
                )
                all_embeddings.extend(_extract_embeddings(response))
            return all_embeddings
        except Exception as e:
            logger.error("Embedding failed for documents: %s", e)
            raise

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query for retrieval. Use search_query input type."""
        try:
            response = self._client.embed(
                texts=[query],
                model=self._model,
                input_type="search_query",
                embedding_types=["float"],
            )
            vectors = _extract_embeddings(response)
            return vectors[0]
        except Exception as e:
            logger.error("Embedding failed for query: %s", e)
            raise
