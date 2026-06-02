from datetime import datetime

from fastapi import APIRouter

from app.config import _ENV_FILE, settings

router = APIRouter()


@router.get("/health")
def health():
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
        "rag_service_url": settings.rag_service_url or None,
        "llm_provider": settings.llm_provider or None,
        "env_file": str(_ENV_FILE),
        "version": "1.0.0",
    }
