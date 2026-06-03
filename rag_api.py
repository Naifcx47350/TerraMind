"""
Legacy entry point — forwards to terramind.api.app.

Run from repo root:
    uvicorn rag_api:app --reload --port 8001

Preferred:
    uvicorn terramind.api.app:app --reload --port 8001
"""

from terramind.api.app import app

__all__ = ["app"]
