from fastapi import APIRouter
from datetime import datetime
from typing import List, Dict, Any

router = APIRouter()

_history: List[Dict[str, Any]] = []


def add_to_history(question: str, response):
    _history.append({
        "question": question,
        "answer": response.answer[:120] + "..." if len(response.answer) > 120 else response.answer,
        "confidence": response.confidence,
        "latency_ms": response.latency_ms,
        "sources": [s.title for s in response.sources],
        "timestamp": datetime.utcnow().isoformat(),
    })


@router.get("/history")
def get_history(limit: int = 20):
    return {"total": len(_history), "items": _history[-limit:][::-1]}


@router.delete("/history")
def clear_history():
    _history.clear()
    return {"message": "History cleared"}
