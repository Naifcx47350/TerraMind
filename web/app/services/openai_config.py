"""OpenAI key checks for the bring-your-own-key flow.

Visitors keep their key in their own browser tab and send it with each request
(X-OpenAI-Key). Nothing here stores a key: verify_openai_key only asks OpenAI
whether the key is accepted.

The validation rules mirror core/openai_keys.py; the gateway image does not ship
LangChain, so it cannot import that module.
"""

from __future__ import annotations

import logging
import re

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_OPENAI_KEY_RE = re.compile(r"^sk-(?:proj-)?[A-Za-z0-9_-]{20,}$")
_PLACEHOLDER_MARKERS = ("your", "here", "example", "placeholder", "***", "...")
_OPENAI_MODELS_URL = "https://api.openai.com/v1/models"


def _model_api_base_url() -> str | None:
    url = (settings.rag_service_url or "").strip()
    if not url:
        return None
    if url.endswith("/query"):
        return url[: -len("/query")]
    return url.rstrip("/")


def validate_openai_key(api_key: str | None) -> str:
    key = (api_key or "").strip()
    lower = key.lower()
    if any(marker in lower for marker in _PLACEHOLDER_MARKERS):
        raise ValueError("Paste the full OpenAI API key, not the placeholder or masked value.")
    if not _OPENAI_KEY_RE.match(key):
        raise ValueError("Enter a valid OpenAI API key that starts with sk- and contains only key characters.")
    return key


async def verify_openai_key(api_key: str) -> None:
    """
    Raise ValueError if OpenAI rejects the key, RuntimeError if OpenAI can't be reached.

    Listing models is free, so checking a key costs the visitor nothing.
    """
    key = validate_openai_key(api_key)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(_OPENAI_MODELS_URL, headers={"Authorization": f"Bearer {key}"})
    except httpx.HTTPError as e:
        logger.warning("OpenAI key check could not reach OpenAI: %s", type(e).__name__)
        raise RuntimeError("Could not reach OpenAI to check the key. Try again in a moment.") from e

    if resp.status_code in (401, 403):
        raise ValueError(
            "OpenAI did not accept this key. Check that you copied the whole key "
            "and that it has not been revoked."
        )
    if not resp.is_success:
        raise RuntimeError(f"OpenAI returned an unexpected response ({resp.status_code}). Try again in a moment.")


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
