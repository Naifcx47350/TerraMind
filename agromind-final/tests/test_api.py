import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ask_basic():
    r = client.post("/api/ask", json={"question": "What causes brown spots on tomato leaves?"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "sources" in data


def test_ask_with_history():
    r = client.post("/api/ask", json={
        "question": "Tell me more",
        "history": [
            {"role": "user", "content": "What causes brown spots on tomato?"},
            {"role": "assistant", "content": "Early blight caused by Alternaria solani."},
        ],
    })
    assert r.status_code == 200


def test_ask_empty():
    r = client.post("/api/ask", json={"question": "  "})
    assert r.status_code in [400, 422]


def test_history():
    client.post("/api/ask", json={"question": "Test question"})
    r = client.get("/api/history")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_clear_history():
    r = client.delete("/api/history")
    assert r.status_code == 200
