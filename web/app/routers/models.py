import httpx
from fastapi import APIRouter

from app.config import settings

router = APIRouter()

FALLBACK_MODELS = [
    {
        "id": "auto_rag",
        "name": "Auto (recommended)",
        "description": (
            "Picks Product Catalog or Agriculture Knowledge RAG from your question"
        ),
    },
    {
        "id": "general_rag",
        "name": "Agriculture Knowledge RAG",
        "description": (
            "Trusted public agriculture references: GAP, soil health, "
            "crop rotation, IPM, pesticide stewardship"
        ),
    },
    {
        "id": "product_rag",
        "name": "Product Catalog RAG",
        "description": "Client Excel product sheets — usage, dosage, manuals",
    },
    {
        "id": "base_llm",
        "name": "Base LLM",
        "description": "OpenAI only — no retrieval (comparison baseline)",
    },
]


def _models_url() -> str | None:
    url = (settings.rag_service_url or "").strip()
    if not url:
        return None
    if url.endswith("/query"):
        return url[: -len("/query")] + "/models"
    base = url.rstrip("/")
    return f"{base}/models"


@router.get("/models")
async def list_models():
    models_url = _models_url()
    if models_url:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(models_url)
                resp.raise_for_status()
                data = resp.json()
                return {
                    "models": data.get("models", FALLBACK_MODELS),
                    "default": data.get("default", "auto_rag"),
                }
        except Exception:
            pass
    return {"models": FALLBACK_MODELS, "default": "auto_rag"}
