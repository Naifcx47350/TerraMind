"""Detect and apply OpenAI API keys for local dev (FrontPage + Model API)."""

from __future__ import annotations

import logging
import os

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def _local_openai_key() -> str:
    return (settings.vision_api_key or os.getenv("OPENAI_API_KEY", "")).strip()


def _model_api_base_url() -> str | None:
    url = (settings.rag_service_url or "").strip()
    if not url:
        return None
    if url.endswith("/query"):
        return url[: -len("/query")]
    return url.rstrip("/")


def validate_openai_key(api_key: str) -> str:
    key = (api_key or "").strip()
    if not key.startswith(("sk-", "sk-proj-")):
        raise ValueError("Enter a valid OpenAI API key (starts with sk-).")
    if len(key) < 20:
        raise ValueError("API key looks too short.")
    return key


def apply_openai_key_local(api_key: str) -> None:
    key = validate_openai_key(api_key)
    os.environ["OPENAI_API_KEY"] = key
    settings.vision_api_key = key
    if not settings.vision_provider:
        settings.vision_provider = "openai"
    try:
        from terramind.models.vision import warm_vision_model

        warm_vision_model(key)
    except Exception as e:
        logger.debug("Vision warmup after key update skipped: %s", e)


async def sync_openai_key_to_model_api(api_key: str) -> None:
    base = _model_api_base_url()
    if not base:
        return
    key = validate_openai_key(api_key)
    url = f"{base}/internal/openai-key"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json={"api_key": key})
            resp.raise_for_status()
    except Exception as e:
        logger.warning("Could not sync OpenAI key to Model API (%s): %s", url, e)
        raise RuntimeError(
            "Key saved for FrontPage but Model API did not respond in time. "
            "Wait for model-api to finish starting, then try again."
        ) from e


async def apply_openai_key(api_key: str) -> None:
    apply_openai_key_local(api_key)
    await sync_openai_key_to_model_api(api_key)


async def model_api_has_openai_key() -> bool:
    base = _model_api_base_url()
    if not base:
        return True
    url = f"{base}/config/openai-status"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url)
            if resp.is_success:
                return bool(resp.json().get("openai_configured"))
    except Exception as e:
        logger.debug("Model API key check failed (%s): %s", url, e)
    return False


async def is_openai_ready() -> bool:
    if settings.use_mock:
        return True
    if not _local_openai_key():
        return False
    if settings.rag_service_url:
        return await model_api_has_openai_key()
    return True
