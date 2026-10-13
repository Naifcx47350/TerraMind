from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.services.openai_config import model_api_ready, verify_openai_key

router = APIRouter()


class OpenAIKeyRequest(BaseModel):
    api_key: str = Field(..., min_length=20, max_length=512)


@router.get("/config")
async def get_app_config():
    return {
        "model_api_ready": await model_api_ready(),
        "requires_openai_key": not settings.use_mock,
        "use_mock": settings.use_mock,
        "demo_available": True,
    }


@router.post("/config/verify-key")
async def verify_key(body: OpenAIKeyRequest):
    """Check a visitor's key with OpenAI. The key is not stored."""
    if settings.use_mock:
        return {"ok": True, "use_mock": True}
    try:
        await verify_openai_key(body.api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return {"ok": True}
