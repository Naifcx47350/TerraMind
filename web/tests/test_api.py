import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, settings
from app.main import app
from app.services import openai_config, rag_service

client = TestClient(app)

VISITOR_KEY = "sk-test-visitor-" + "v" * 24


class _FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self.is_success = 200 <= status_code < 300
        self._payload = payload or {}

    def raise_for_status(self):
        if not self.is_success:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def _fake_async_client(calls, response):
    """Stand-in for httpx.AsyncClient that records each outgoing request."""

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, json=None, headers=None):
            calls.append({"method": "POST", "url": url, "json": json, "headers": headers or {}})
            return response

        async def get(self, url, headers=None):
            calls.append({"method": "GET", "url": url, "headers": headers or {}})
            return response

    return FakeAsyncClient


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_config_endpoint():
    r = client.get("/api/config")
    assert r.status_code == 200
    data = r.json()
    assert "requires_openai_key" in data
    assert "use_mock" in data
    assert data["demo_available"] is True
    # No server-side key state is reported any more.
    assert "openai_configured" not in data


def test_ask_requires_key_or_demo():
    r = client.post("/api/ask", json={"question": "What causes brown spots on tomato leaves?"})
    assert r.status_code == 401


def test_ask_rejects_malformed_key():
    r = client.post(
        "/api/ask",
        json={"question": "Tomato spots?"},
        headers={"X-OpenAI-Key": "sk-your-key-here"},
    )
    assert r.status_code == 400


def test_ask_demo():
    r = client.post(
        "/api/ask", json={"question": "What causes brown spots on tomato leaves?", "demo": True}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["system"] == "mock"
    assert "Early Blight" in data["answer"]
    assert data["sources"]


@pytest.mark.parametrize(
    "question, expected",
    [
        ("Best irrigation for corn?", "tasseling"),
        ("Which product works for aphids on cotton?", "flonicamid"),
        ("ما أفضل حل للمن على القطن؟", "فلونيكاميد"),
        ("How do I store seeds?", "local agronomist"),
    ],
)
def test_demo_answers_match_starter_prompts(question, expected):
    r = client.post("/api/ask", json={"question": question, "demo": True})
    assert r.status_code == 200
    assert expected in r.json()["answer"]


def test_ask_with_history():
    r = client.post("/api/ask", json={
        "question": "Tell me more",
        "demo": True,
        "history": [
            {"role": "user", "content": "What causes brown spots on tomato?"},
            {"role": "assistant", "content": "Early blight caused by Alternaria solani."},
        ],
    })
    assert r.status_code == 200


def test_ask_empty():
    r = client.post("/api/ask", json={"question": "  ", "demo": True})
    assert r.status_code in [400, 422]


def test_demo_stream():
    r = client.post("/api/ask/stream", json={"question": "Yellow rust in wheat?", "demo": True})
    assert r.status_code == 200
    events = [json.loads(line) for line in r.text.splitlines() if line.strip()]
    assert events[0]["event"] == "status"
    assert any(e["event"] == "token" for e in events)
    assert events[-1]["event"] == "done" and "Propiconazole" in events[-1]["answer"]


def test_demo_compare_and_advisory():
    r = client.post("/api/ask/compare", json={"question": "Tomato spots?", "demo": True})
    assert r.status_code == 200
    assert len(r.json()["results"]) == 3
    r = client.post("/api/ask/advisory", json={"question": "Tomato spots?", "demo": True})
    assert r.status_code == 200
    assert r.json()["model"] == "advisory"


def test_visitor_key_is_forwarded_to_model_api(monkeypatch):
    calls = []
    payload = {"answer": "ok", "sources": [], "confidence": "high", "retrieved_chunks": 0}
    monkeypatch.setattr(
        rag_service.httpx, "AsyncClient", _fake_async_client(calls, _FakeResponse(200, payload))
    )
    r = client.post(
        "/api/ask",
        json={"question": "Tomato spots?"},
        headers={"X-OpenAI-Key": VISITOR_KEY},
    )
    assert r.status_code == 200
    assert calls[0]["headers"] == {"X-OpenAI-Key": VISITOR_KEY}
    # The key travels only as a header, never inside the JSON body.
    assert VISITOR_KEY not in json.dumps(calls[0]["json"])


def test_verify_key_accepted(monkeypatch):
    calls = []
    monkeypatch.setattr(
        openai_config.httpx, "AsyncClient", _fake_async_client(calls, _FakeResponse(200))
    )
    r = client.post("/api/config/verify-key", json={"api_key": VISITOR_KEY})
    assert r.status_code == 200
    assert calls[0]["url"] == "https://api.openai.com/v1/models"
    assert calls[0]["headers"]["Authorization"] == f"Bearer {VISITOR_KEY}"


def test_verify_key_rejected_by_openai(monkeypatch):
    monkeypatch.setattr(
        openai_config.httpx, "AsyncClient", _fake_async_client([], _FakeResponse(401))
    )
    r = client.post("/api/config/verify-key", json={"api_key": VISITOR_KEY})
    assert r.status_code == 400
    assert "did not accept" in r.json()["detail"]


def test_old_save_key_endpoint_is_gone():
    r = client.post("/api/config/openai-key", json={"api_key": VISITOR_KEY})
    assert r.status_code in (404, 405)


def test_server_env_key_is_not_used_for_vision(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-server-" + "s" * 24)
    monkeypatch.delenv("VISION_API_KEY", raising=False)
    assert Settings().vision_api_key == ""


ADMIN_TOKEN = "test-admin-token-123"


@pytest.fixture
def history_enabled(monkeypatch):
    from app.routers import history

    monkeypatch.setattr(settings, "history_admin_token", ADMIN_TOKEN)
    history._history.clear()
    yield
    history._history.clear()


def test_history_is_off_by_default(monkeypatch):
    from app.routers import history

    monkeypatch.setattr(settings, "history_admin_token", "")
    history._history.clear()
    client.post("/api/ask", json={"question": "My private question", "demo": True})
    assert len(history._history) == 0  # nothing recorded
    assert client.get("/api/history").status_code == 404
    assert client.delete("/api/history").status_code == 404


def test_history_requires_admin_token(history_enabled):
    assert client.get("/api/history").status_code == 401
    assert client.get("/api/history", headers={"X-Admin-Token": "wrong"}).status_code == 401
    assert client.delete("/api/history").status_code == 401


def test_history_with_admin_token(history_enabled):
    client.post("/api/ask", json={"question": "Test question", "demo": True})
    headers = {"X-Admin-Token": ADMIN_TOKEN}
    r = client.get("/api/history", headers=headers)
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["question"] == "Test question"
    assert client.delete("/api/history", headers=headers).status_code == 200
    assert client.get("/api/history", headers=headers).json()["total"] == 0


def test_history_is_bounded(history_enabled):
    from app.routers import history

    for i in range(history._MAX_ENTRIES + 25):
        history.add_to_history(f"q{i}", rag_service._mock_response(
            rag_service.AskRequest(question="tomato", demo=True), 0))
    assert len(history._history) == history._MAX_ENTRIES
