"""Per-request OpenAI API key (bring-your-own-key).

The web app sends each visitor's key with every request. The model API binds it
to a ContextVar for that request only, so one visitor's key can never answer for
another visitor, and nothing is written to os.environ or disk.

CLI tools and evaluation scripts never set a request key and fall back to
OPENAI_API_KEY from the environment. The model API calls require_request_key()
at import so that fallback is disabled there: a request without its own key
fails instead of silently using a server key.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

_OPENAI_KEY_RE = re.compile(r"^sk-(?:proj-)?[A-Za-z0-9_-]{20,}$")
_PLACEHOLDER_MARKERS = ("your", "here", "example", "placeholder", "***", "...")

_request_key: ContextVar[str | None] = ContextVar("openai_request_key", default=None)
_require_request_key = False


class MissingOpenAIKey(RuntimeError):
    """No usable OpenAI key for this call."""


def validate_openai_key(api_key: str | None) -> str:
    key = (api_key or "").strip()
    lower = key.lower()
    if any(marker in lower for marker in _PLACEHOLDER_MARKERS):
        raise ValueError("Paste the full OpenAI API key, not the placeholder or masked value.")
    if not _OPENAI_KEY_RE.match(key):
        raise ValueError("Invalid OpenAI API key format.")
    return key


def require_request_key(required: bool = True) -> None:
    """Disable (or re-enable) the OPENAI_API_KEY environment fallback for this process."""
    global _require_request_key
    _require_request_key = required


@contextmanager
def use_openai_key(api_key: str) -> Iterator[None]:
    """Bind a visitor's key to the current context (inherited by asyncio.to_thread)."""
    token = _request_key.set(api_key)
    try:
        yield
    finally:
        _request_key.reset(token)


def keyed_iter(iterator: Iterator, api_key: str) -> Iterator:
    """
    Run each step of a sync generator with the visitor's key bound.

    Starlette advances StreamingResponse generators in worker threads with a
    fresh context copy per step, so a key set inside the generator would not
    survive between yields.
    """
    while True:
        with use_openai_key(api_key):
            try:
                item = next(iterator)
            except StopIteration:
                return
        yield item


def resolve_openai_key() -> str:
    key = _request_key.get()
    if key:
        return key
    if _require_request_key:
        raise MissingOpenAIKey("An OpenAI API key is required. Add your key in TerraMind settings.")
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise MissingOpenAIKey("OPENAI_API_KEY is not set.")
    return key


def chat_model(**kwargs) -> ChatOpenAI:
    """ChatOpenAI bound to the current request's key."""
    return ChatOpenAI(api_key=resolve_openai_key(), **kwargs)


class RequestKeyEmbeddings(Embeddings):
    """
    OpenAI embeddings that look up the key on every call.

    The Chroma handles are cached for the life of the process, so the embedding
    function they hold must not capture whichever key was active at load time.
    """

    def __init__(self, model: str):
        self.model = model

    def _client(self) -> OpenAIEmbeddings:
        return OpenAIEmbeddings(model=self.model, api_key=resolve_openai_key())

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._client().embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._client().embed_query(text)
