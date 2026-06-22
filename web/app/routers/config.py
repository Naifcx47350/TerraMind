from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import _ENV_FILE, _ROOT_ENV_FILE, settings
from app.services.openai_config import apply_openai_key, is_openai_ready, model_api_ready

router = APIRouter()


class OpenAIKeyRequest(BaseModel):
    api_key: str = Field(..., min_length=20, max_length=512)


@router.get("/config")
async def get_app_config():
    configured = is_openai_ready()
    model_ready = await model_api_ready()
    return {
        "openai_configured": configured,
        "model_api_ready": model_ready,
        "requires_openai_key": not settings.use_mock,
        "use_mock": settings.use_mock,
        "env_file_hint": str(_ROOT_ENV_FILE),
        "web_env_file_hint": str(_ENV_FILE),
    }


@router.post("/config/openai-key")
async def set_openai_key(body: OpenAIKeyRequest):
    if settings.use_mock:
        return {"ok": True, "openai_configured": True, "use_mock": True}
    try:
        await apply_openai_key(body.api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return {"ok": True, "openai_configured": True}
