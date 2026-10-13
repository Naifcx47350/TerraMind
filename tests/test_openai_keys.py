"""Bring-your-own-key: every request runs on the visitor's key, never a server key."""

import asyncio
import contextvars
import json

import pytest
from fastapi.testclient import TestClient

from core import openai_keys
from core.openai_keys import (
    MissingOpenAIKey,
    RequestKeyEmbeddings,
    chat_model,
    keyed_iter,
    resolve_openai_key,
    use_openai_key,
)

KEY_A = "sk-test-visitorA-" + "a" * 24
KEY_B = "sk-test-visitorB-" + "b" * 24
SERVER_KEY = "sk-test-server-" + "s" * 24


@pytest.fixture
def strict(monkeypatch):
    """Model API mode: a server key is present in the environment but must never be used."""
    monkeypatch.setattr(openai_keys, "_require_request_key", True)
    monkeypatch.setenv("OPENAI_API_KEY", SERVER_KEY)


def test_cli_falls_back_to_env_key(monkeypatch):
    monkeypatch.setattr(openai_keys, "_require_request_key", False)
    monkeypatch.setenv("OPENAI_API_KEY", SERVER_KEY)
    assert resolve_openai_key() == SERVER_KEY
    with use_openai_key(KEY_A):
        assert resolve_openai_key() == KEY_A


def test_strict_mode_never_uses_server_key(strict):
    with pytest.raises(MissingOpenAIKey):
        resolve_openai_key()


def test_concurrent_visitors_keep_their_own_key(strict):
    async def visitor(key):
        with use_openai_key(key):
            await asyncio.sleep(0)
            return await asyncio.to_thread(resolve_openai_key)

    async def main():
        return await asyncio.gather(visitor(KEY_A), visitor(KEY_B), visitor(KEY_A))

    assert asyncio.run(main()) == [KEY_A, KEY_B, KEY_A]


def test_keyed_iter_binds_key_on_every_step(strict):
    def gen():
        for _ in range(3):
            yield resolve_openai_key()

    # Starlette advances each step of a sync stream in a fresh context copy.
    it = keyed_iter(gen(), KEY_A)
    steps = [contextvars.copy_context().run(next, it) for _ in range(3)]
    assert steps == [KEY_A] * 3
    with pytest.raises(StopIteration):
        contextvars.copy_context().run(next, it)


def test_chat_model_uses_request_key(strict):
    with use_openai_key(KEY_A):
        llm = chat_model(model="gpt-4o-mini")
    assert llm.openai_api_key.get_secret_value() == KEY_A


def test_cached_embeddings_resolve_key_per_call(strict, monkeypatch):
    seen = []

    class FakeEmbeddings:
        def __init__(self, model, api_key):
            seen.append(api_key)

        def embed_query(self, text):
            return [0.0]

        def embed_documents(self, texts):
            return [[0.0] for _ in texts]

    monkeypatch.setattr(openai_keys, "OpenAIEmbeddings", FakeEmbeddings)
    emb = RequestKeyEmbeddings(model="text-embedding-3-small")  # built once, like the cached Chroma handle
    with use_openai_key(KEY_A):
        emb.embed_query("tomato")
    with use_openai_key(KEY_B):
        emb.embed_documents(["wheat"])
    assert seen == [KEY_A, KEY_B]


# --- Model API ---------------------------------------------------------------


@pytest.fixture
def model_api(strict, monkeypatch):
    import importlib

    import core.models.streaming as streaming

    # core.api re-exports the FastAPI object as `app`, shadowing the module name.
    api_app = importlib.import_module("core.api.app")

    def fake_run_model(model_id, question, *args, **kwargs):
        return {
            "answer": resolve_openai_key(),
            "sources": [],
            "confidence": "high",
            "retrieved_chunks": 0,
            "system": model_id,
        }

    def fake_stream(*args, **kwargs):
        for _ in range(3):
            yield json.dumps({"event": "token", "content": resolve_openai_key()}) + "\n"

    monkeypatch.setattr(api_app, "run_model", fake_run_model)
    monkeypatch.setattr(streaming, "stream_model_events", fake_stream)
    # No `with`: skip the lifespan warmup (Chroma/BM25/reranker) in unit tests.
    return TestClient(api_app.app)


def test_model_api_requires_visitor_key(model_api):
    r = model_api.post("/query", json={"question": "hi", "model": "base_llm"})
    assert r.status_code == 401


def test_model_api_rejects_malformed_key(model_api):
    r = model_api.post(
        "/query", json={"question": "hi", "model": "base_llm"}, headers={"X-OpenAI-Key": "sk-short"}
    )
    assert r.status_code == 400


def test_model_api_query_uses_visitor_key(model_api):
    r = model_api.post(
        "/query", json={"question": "hi", "model": "base_llm"}, headers={"X-OpenAI-Key": KEY_A}
    )
    assert r.status_code == 200
    assert r.json()["answer"] == KEY_A


def test_model_api_stream_uses_visitor_key_on_every_chunk(model_api):
    r = model_api.post(
        "/query/stream", json={"question": "hi", "model": "base_llm"}, headers={"X-OpenAI-Key": KEY_B}
    )
    assert r.status_code == 200
    tokens = [json.loads(line)["content"] for line in r.text.splitlines() if line.strip()]
    assert tokens == [KEY_B] * 3


def test_model_api_compare_uses_visitor_key_for_every_model(model_api):
    r = model_api.post("/query/compare", json={"question": "hi"}, headers={"X-OpenAI-Key": KEY_A})
    assert r.status_code == 200
    results = r.json()["results"]
    assert results and all(row["answer"] == KEY_A for row in results)


def test_image_analysis_runs_off_the_event_loop(model_api, monkeypatch):
    import importlib

    api_app = importlib.import_module("core.api.app")
    seen = {}

    def fake_analysis(*args, **kwargs):
        try:
            asyncio.get_running_loop()
            seen["on_loop"] = True
        except RuntimeError:
            seen["on_loop"] = False  # worker thread: other visitors keep being served
        seen["key"] = resolve_openai_key()
        return "leaf spots"

    monkeypatch.setattr(api_app, "resolve_image_analysis", fake_analysis)
    r = model_api.post(
        "/query",
        json={"question": "what is this?", "model": "base_llm", "image_base64": "aGk=", "image_mime": "image/jpeg"},
        headers={"X-OpenAI-Key": KEY_A},
    )
    assert r.status_code == 200
    assert seen == {"on_loop": False, "key": KEY_A}


def test_model_api_request_limits(model_api):
    headers = {"X-OpenAI-Key": KEY_A}
    r = model_api.post("/query", json={"question": "q", "history": [{}] * 41}, headers=headers)
    assert r.status_code == 422
    r = model_api.post(
        "/query", json={"question": "q", "image_base64": "aGk=", "image_mime": "text/html"}, headers=headers
    )
    assert r.status_code == 422


def test_global_key_endpoints_are_gone(model_api):
    assert model_api.post("/internal/openai-key", json={"api_key": KEY_A}).status_code == 404
    assert model_api.get("/config/openai-status").status_code == 404
