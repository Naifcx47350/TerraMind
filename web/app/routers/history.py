"""Recent-questions audit log — an admin/debug tool, off unless HISTORY_ADMIN_TOKEN is set.

Visitors' questions are private: with no token configured nothing is recorded and
both routes return 404. With a token, callers must send it as X-Admin-Token.
"""

import secrets
from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, Optional

from fastapi import APIRouter, Header, HTTPException

from app.config import settings

router = APIRouter()

_MAX_ENTRIES = 200
_history: Deque[Dict[str, Any]] = deque(maxlen=_MAX_ENTRIES)


def _enabled() -> bool:
    return bool(settings.history_admin_token)


def add_to_history(question: str, response):
    if not _enabled():
        return
    _history.append({
        "question": question,
        "answer": response.answer[:120] + "..." if len(response.answer) > 120 else response.answer,
        "confidence": response.confidence,
        "latency_ms": response.latency_ms,
        "sources": [s.title for s in response.sources],
        "timestamp": datetime.utcnow().isoformat(),
    })


def _require_admin(token: Optional[str]) -> None:
    if not _enabled():
        raise HTTPException(status_code=404, detail="Not Found")
    if not token or not secrets.compare_digest(token, settings.history_admin_token):
        raise HTTPException(status_code=401, detail="Admin token required")


@router.get("/history")
def get_history(limit: int = 20, x_admin_token: Optional[str] = Header(default=None)):
    _require_admin(x_admin_token)
    limit = max(1, min(limit, _MAX_ENTRIES))
    items = list(_history)[-limit:][::-1]
    return {"total": len(_history), "items": items}


@router.delete("/history")
def clear_history(x_admin_token: Optional[str] = Header(default=None)):
    _require_admin(x_admin_token)
    _history.clear()
    return {"message": "History cleared"}
