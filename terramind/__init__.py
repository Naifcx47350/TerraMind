"""
TerraMind backend package — model API, three modes, RAG pipelines.

Run model API:
    uvicorn terramind.api.app:app --reload --port 8001

Legacy entry (same app):
    uvicorn rag_api:app --reload --port 8001
"""

__version__ = "0.2.0"
