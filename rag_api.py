"""
Legacy entry point — forwards to terramind.api.app.

Run from <repo-root> (your TerraMind clone):
    uvicorn terramind.api.app:app --reload --port 8001
    # legacy: uvicorn rag_api:app --reload --port 8001
"""

from terramind.api.app import app

__all__ = ["app"]
