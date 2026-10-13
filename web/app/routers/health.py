from datetime import datetime

from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/health")
def health():
    # Public endpoint: report status only, not file paths or internal service URLs.
    if settings.use_mock:
        backend = "mock"
    elif settings.rag_service_url:
        backend = "rag"
    elif settings.llm_provider and settings.llm_api_key:
        backend = "llm_only"
    else:
        backend = "mock_fallback"

    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "backend": backend,
        "use_mock": settings.use_mock,
        "version": "1.0.0",
    }
