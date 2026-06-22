import logging
import sys
from pathlib import Path

# TerraMind repo root (for models/vision when analyzing images)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(_REPO_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.error_handler import add_error_handler
from app.middleware.logger import add_logger
from app.routers import ask, config, health, history, models

logger = logging.getLogger(__name__)

app = FastAPI(
    title="TerraMind API",
    description="Agriculture RAG System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_error_handler(app)
add_logger(app)

app.include_router(config.router, prefix="/api", tags=["Config"])
app.include_router(ask.router, prefix="/api", tags=["Ask"])
app.include_router(models.router, prefix="/api", tags=["Models"])
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(history.router, prefix="/api", tags=["History"])


@app.on_event("startup")
def log_startup_config():
    if settings.use_mock:
        mode = "MOCK (canned answers)"
    elif settings.rag_service_url:
        mode = f"RAG → {settings.rag_service_url}"
    else:
        mode = "LLM or mock fallback"
    logger.info("web API started — mode: %s", mode)

    try:
        from core.models.vision import warm_vision_model

        warm_vision_model(settings.vision_api_key)
    except Exception as exc:
        logger.warning("Vision warmup skipped: %s", exc)


@app.get("/")
def root():
    return {"message": "TerraMind API is running", "docs": "/docs", "health": "/api/health"}
