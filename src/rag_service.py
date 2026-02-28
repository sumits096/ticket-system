"""
RAG service - main entry point for the knowledge base agent.

Use this module from Streamlit or any other UI to:
- Ask questions (answer)
- Upload documents (admin)
- List/delete documents (admin)
"""

from src.admin_service import AdminService
from src.generation_service import GenerationService
from src.models import QueryRequest, QueryResponse

# Lazy-initialized singletons for use across the app
_generation_service: GenerationService | None = None
_admin_service: AdminService | None = None


def get_generation_service() -> GenerationService:
    """Get or create the generation service instance."""
    global _generation_service
    if _generation_service is None:
        _generation_service = GenerationService()
    return _generation_service


def get_admin_service() -> AdminService:
    """Get or create the admin service instance."""
    global _admin_service
    if _admin_service is None:
        _admin_service = AdminService()
    return _admin_service


def answer(
    question: str,
    region: str,
    department: str | None = None,
    user_id: str | None = None,
) -> QueryResponse:
    """Ask a question and get an answer with sources and confidence."""
    svc = get_generation_service()
    return svc.answer(
        QueryRequest(
            question=question,
            region=region,
            department=department,
            user_id=user_id,
        )
    )


def answer_stream(
    question: str,
    region: str,
    department: str | None = None,
    user_id: str | None = None,
):
    """
    Stream the answer token-by-token. Yields {"type": "token", "content": str}
    or {"type": "done", "response": QueryResponse}.
    """
    svc = get_generation_service()
    return svc.answer_stream(
        QueryRequest(
            question=question,
            region=region,
            department=department,
            user_id=user_id,
        )
    )
