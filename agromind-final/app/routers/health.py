from fastapi import APIRouter
from datetime import datetime
from app.config import settings

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "mode": "mock" if settings.use_mock else "live",
        "version": "1.0.0",
    }
