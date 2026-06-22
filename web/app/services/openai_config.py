"""Detect and apply OpenAI API keys for local dev (web + Model API)."""

from __future__ import annotations

import logging
import os
import re

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_OPENAI_KEY_RE = re.compile(r"^sk-(?:proj-)?[A-Za-z0-9_-]{20,}$")
_PLACEHOLDER_MARKERS = ("your", "here", "example", "placeholder", "***", "...")


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
    lower = key.lower()
    if any(marker in lower for marker in _PLACEHOLDER_MARKERS):
        raise ValueError("Paste the full OpenAI API key, not the placeholder or masked value.")
    if not _OPENAI_KEY_RE.match(key):
        raise ValueError("Enter a valid OpenAI API key that starts with sk- and contains only key characters.")
    return key


def apply_openai_key_local(api_key: str) -> None:
    key = validate_openai_key(api_key)
    os.environ["OPENAI_API_KEY"] = key
    settings.vision_api_key = key
    if not settings.vision_provider:
        settings.vision_provider = "openai"
    try:
        from core.models.vision import warm_vision_model

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
            "Key saved for web but Model API did not respond in time. "
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


async def model_api_ready() -> bool:
    base = _model_api_base_url()
    if not base:
        return True
    url = f"{base}/health"
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            resp = await client.get(url)
            return resp.is_success
    except Exception as e:
        logger.debug("Model API readiness check failed (%s): %s", url, e)
        return False


def is_openai_ready() -> bool:
    if settings.use_mock:
        return True
    try:
        validate_openai_key(_local_openai_key())
    except ValueError:
        return False
    # A valid local/root .env key is enough for the key gate. Model API startup
    # can lag behind the gateway, and that should show as service readiness,
    # not as a request for the user to paste a key again.
    return True
