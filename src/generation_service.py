"""Cohere-based generation with RAG documents, citations, and confidence."""

import logging
from typing import Generator, List

import cohere

from src.config import CHAT_MODEL, Settings, TOP_K_RETRIEVAL
from src.embedding_service import EmbeddingService
from src.models import QueryRequest, QueryResponse, RetrievedChunk, SourceCitation
from src.query_logger import QueryLogger
from src.vector_store import VectorStore

logger = logging.getLogger(__name__)

# System prompt for grounded, conservative answering
RAG_SYSTEM_PROMPT = """You are an enterprise knowledge base assistant. Use ONLY the provided context documents to answer. 
- Cite sources by referencing the document when giving information.
- If the context does not contain relevant information, say "I don't have enough information to answer that based on the available documentation."
- Be concise and accurate. Do not hallucinate or invent information.
- When citing, mention the source document name."""


class GenerationService:
    """Handles retrieval + generation with Cohere, citations, and confidence."""

    def __init__(self):
        settings = Settings()
        self._client = cohere.ClientV2(api_key=settings.cohere_api_key)
        self._embedding_service = EmbeddingService()
        self._vector_store = VectorStore()
        self._query_logger = QueryLogger()
        self._model = CHAT_MODEL
        self._top_k = TOP_K_RETRIEVAL

    def _documents_for_cohere(self, chunks: List[RetrievedChunk]) -> List[dict]:
        """Format retrieved chunks as Cohere RAG documents."""
        return [
            {
                "data": {
                    "text": c.content,
                    "title": c.source,
                    "region": c.region,
                }
            }
            for c in chunks
        ]

    def _extract_citations(
        self, chunks: List[RetrievedChunk], response_citations: list | None
    ) -> List[SourceCitation]:
        """Build source citations from response and chunks."""
        seen: set[tuple] = set()
        citations: List[SourceCitation] = []
        for c in chunks:
            key = (c.source, c.region)
            if key not in seen:
                seen.add(key)
                citations.append(
                    SourceCitation(
                        source=c.source,
                        region=c.region,
                        excerpt=c.content[:200] + "..." if len(c.content) > 200 else c.content,
                    )
                )
        return citations

    def _estimate_confidence(
        self, answer: str, chunks: List[RetrievedChunk], has_citations: bool
    ) -> float:
        """Estimate confidence based on answer content and retrieval quality."""
        low_confidence_phrases = [
            "i don't",
            "i do not",
            "don't have",
            "not have",
            "no information",
            "cannot find",
            "unable to",
            "not sure",
            "not found",
        ]
        answer_lower = answer.lower()
        if any(p in answer_lower for p in low_confidence_phrases):
            return 0.2
        if not chunks:
            return 0.0
        # Base confidence on retrieval score and citation presence
        avg_score = sum(c.score for c in chunks) / len(chunks)
        base = min(0.95, 0.5 + avg_score * 0.5)
        if has_citations:
            base = min(0.95, base + 0.1)
        return round(base, 2)

    def answer(self, request: QueryRequest) -> QueryResponse:
        """
        End-to-end RAG: retrieve by region and department, generate with Cohere,
        cite sources, estimate confidence, and log the query.
        """
        chunks = self._retrieve(
            question=request.question,
            region=request.region,
            department=request.department,
        )
        if not chunks:
            response = QueryResponse(
                answer="I don't have enough information to answer that based on the available documentation. No relevant documents were found for your region.",
                sources=[],
                confidence=0.0,
                has_answer=False,
            )
            self._query_logger.log_query(
                question=request.question,
                region=request.region,
                answer=response.answer,
                confidence=response.confidence,
                sources=[],
                user_id=request.user_id,
                has_answer=False,
            )
            return response

        documents = self._documents_for_cohere(chunks)

        try:
            answer_text, citations_from_response = self._stream_and_collect(
                documents=documents,
                question=request.question,
            )
        except Exception as e:
            logger.exception("Cohere chat failed: %s", e)
            return QueryResponse(
                answer="Sorry, I encountered an error while generating a response. Please try again.",
                sources=[],
                confidence=0.0,
                has_answer=False,
            )
        source_citations = self._extract_citations(chunks, citations_from_response)
        confidence = self._estimate_confidence(
            answer_text, chunks, len(citations_from_response) > 0
        )
        has_answer = "don't" not in answer_text.lower()[:50] and "no information" not in answer_text.lower()[:80]

        result = QueryResponse(
            answer=answer_text,
            sources=source_citations,
            confidence=confidence,
            has_answer=has_answer,
        )

        self._query_logger.log_query(
            question=request.question,
            region=request.region,
            answer=result.answer,
            confidence=result.confidence,
            sources=[s.model_dump() for s in result.sources],
            user_id=request.user_id,
            has_answer=result.has_answer,
        )
        return result

    def _stream_and_collect(
        self,
        documents: List[dict],
        question: str,
    ) -> tuple[str, list]:
        """Use chat_stream to generate response, accumulate text and citations."""
        answer_parts: List[str] = []
        citations: list = []

        stream = self._client.chat_stream(
            model=self._model,
            messages=[
                {"role": "system", "content": RAG_SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            documents=documents,
        )

        for event in stream:
            if not event:
                continue
            ev_type = getattr(event, "type", None) or getattr(event, "event_type", None)
            if ev_type == "content-delta":
                delta = getattr(event, "delta", None)
                if delta and hasattr(delta, "message"):
                    msg = delta.message
                    if hasattr(msg, "content") and msg.content:
                        txt = getattr(msg.content, "text", None) or (
                            msg.content.get("text") if isinstance(msg.content, dict) else None
                        )
                        if txt:
                            answer_parts.append(txt)
            elif ev_type == "citation-start":
                delta = getattr(event, "delta", None)
                if delta and hasattr(delta, "message") and hasattr(delta.message, "citations"):
                    citations.append(delta.message.citations)

        answer_text = "".join(answer_parts)
        return answer_text, citations

    def answer_stream(
        self,
        request: QueryRequest,
    ) -> Generator[dict, None, None]:
        """
        Stream the answer token-by-token. Yields {"type": "token", "content": str}
        for each token, then {"type": "done", "response": QueryResponse}.
        """
        chunks = self._retrieve(
            question=request.question,
            region=request.region,
            department=request.department,
        )
        if not chunks:
            resp = QueryResponse(
                answer="I don't have enough information to answer that based on the available documentation. No relevant documents were found for your region.",
                sources=[],
                confidence=0.0,
                has_answer=False,
            )
            self._query_logger.log_query(
                question=request.question,
                region=request.region,
                answer=resp.answer,
                confidence=resp.confidence,
                sources=[],
                user_id=request.user_id,
                has_answer=False,
            )
            yield {"type": "done", "response": resp}
            return

        documents = self._documents_for_cohere(chunks)
        try:
            stream = self._client.chat_stream(
                model=self._model,
                messages=[
                    {"role": "system", "content": RAG_SYSTEM_PROMPT},
                    {"role": "user", "content": request.question},
                ],
                documents=documents,
            )
        except Exception as e:
            logger.exception("Cohere chat_stream failed: %s", e)
            yield {
                "type": "done",
                "response": QueryResponse(
                    answer="Sorry, I encountered an error while generating a response. Please try again.",
                    sources=[],
                    confidence=0.0,
                    has_answer=False,
                ),
            }
            return

        answer_parts: List[str] = []
        citations: list = []

        for event in stream:
            if not event:
                continue
            ev_type = getattr(event, "type", None) or getattr(event, "event_type", None)
            if ev_type == "content-delta":
                delta = getattr(event, "delta", None)
                if delta and hasattr(delta, "message"):
                    msg = delta.message
                    if hasattr(msg, "content") and msg.content:
                        txt = getattr(msg.content, "text", None) or (
                            msg.content.get("text") if isinstance(msg.content, dict) else None
                        )
                        if txt:
                            answer_parts.append(txt)
                            yield {"type": "token", "content": txt}
            elif ev_type == "citation-start":
                delta = getattr(event, "delta", None)
                if delta and hasattr(delta, "message") and hasattr(delta.message, "citations"):
                    citations.append(delta.message.citations)

        answer_text = "".join(answer_parts)
        source_citations = self._extract_citations(chunks, citations)
        confidence = self._estimate_confidence(
            answer_text, chunks, len(citations) > 0
        )
        has_answer = "don't" not in answer_text.lower()[:50] and "no information" not in answer_text.lower()[:80]

        result = QueryResponse(
            answer=answer_text,
            sources=source_citations,
            confidence=confidence,
            has_answer=has_answer,
        )

        self._query_logger.log_query(
            question=request.question,
            region=request.region,
            answer=result.answer,
            confidence=result.confidence,
            sources=[s.model_dump() for s in result.sources],
            user_id=request.user_id,
            has_answer=result.has_answer,
        )

        yield {"type": "done", "response": result}

    def _retrieve(
        self,
        question: str,
        region: str,
        department: str | None = None,
    ) -> List[RetrievedChunk]:
        """Embed query and retrieve top-k chunks filtered by region and department."""
        embedding = self._embedding_service.embed_query(question)
        return self._vector_store.search(
            query_embedding=embedding,
            region=region,
            top_k=self._top_k,
            department=department or None,
        )
