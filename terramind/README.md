# terramind/ — Backend package

Organized backend for the TerraMind web MVP.

## Layout

```text
terramind/
├── api/
│   └── app.py              # FastAPI :8001 — /query, /query/compare, /query/advisory, /models, /health
├── models/
│   ├── __init__.py         # Registry, run_model(), run_advisory(), auto default
│   ├── auto_rag.py         # Routes → product_rag | general_rag
│   ├── router.py           # Dual-index + keyword routing
│   ├── product_rag.py      # → terramind.rag.product
│   ├── general_rag.py      # → terramind.rag.general
│   ├── base_llm.py
│   ├── vision.py
│   ├── conversation.py
│   └── image_context.py
└── rag/
    ├── scoring.py          # Retrieval scores + confidence
    ├── source_display.py   # UI source labels
    ├── general/            # Full general RAG pipeline
    └── product/            # Re-exports Rag_Pc.py (migration in progress)
```

## Run

From **`<repo-root>`**:

```powershell
cd <repo-root>
uvicorn terramind.api.app:app --reload --port 8001
```

Or `python run_dev.py` (starts UI + FrontPage + model API). `rag_api.py` is a shim to `terramind.api.app`.

## Build indexes

```powershell
python Rag_Pc.py --reset
python -m terramind.rag.general.cli --reset
```

## Migration

Product logic still lives in root **`Rag_Pc.py`**. General RAG is fully in **`terramind/rag/general/`**. Status: [docs/PROJECT_STATUS.md](../docs/PROJECT_STATUS.md).
