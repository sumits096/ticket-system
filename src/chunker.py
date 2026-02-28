"""Text chunking for RAG document ingestion."""

import re
from typing import List

from src.config import CHUNK_OVERLAP, CHUNK_SIZE
from src.models import DocumentChunk


def chunk_text(
    text: str,
    source: str,
    region: str,
    department: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[DocumentChunk]:
    """
    Split text into overlapping chunks with metadata.
    Uses sentence-aware splitting where possible.
    """
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    chunks: List[DocumentChunk] = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(text):
            sentence_end = text.rfind(". ", start, end + 1)
            if sentence_end > start:
                end = sentence_end + 1
            else:
                # Break at word boundary
                word_end = text.rfind(" ", start, end + 1)
                if word_end > start:
                    end = word_end + 1

        chunk_text_slice = text[start:end].strip()
        if chunk_text_slice:
            chunks.append(
                DocumentChunk(
                    content=chunk_text_slice,
                    source=source,
                    region=region,
                    department=department,
                    chunk_index=chunk_index,
                )
            )
            chunk_index += 1

        if end >= len(text):
            break

        # Move start with overlap for next chunk
        start = end - chunk_overlap
        if start < 0:
            start = 0

    return chunks
