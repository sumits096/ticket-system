"""Document loading and text extraction for PDF and DOCX files."""

import logging
from pathlib import Path
from typing import List, Optional

from pypdf import PdfReader
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: Path) -> Optional[str]:
    """Extract text content from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text_parts: List[str] = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n\n".join(text_parts) if text_parts else None
    except Exception as e:
        logger.error("Failed to extract PDF text: %s", e)
        return None


def extract_text_from_docx(file_path: Path) -> Optional[str]:
    """Extract text content from a DOCX file."""
    try:
        doc = DocxDocument(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs) if paragraphs else None
    except Exception as e:
        logger.error("Failed to extract DOCX text: %s", e)
        return None


def load_document(file_path: Path) -> Optional[str]:
    """
    Load and extract text from a document (PDF or DOCX).
    Returns the raw text content or None if extraction fails.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in (".docx", ".doc"):
        return extract_text_from_docx(file_path)
    else:
        logger.warning("Unsupported file type: %s", suffix)
        return None
