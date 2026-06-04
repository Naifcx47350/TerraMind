# terramind/ — Backend package

Organized backend for the TerraMind web MVP.

## Layout

```text
terramind/
├── api/
│   └── app.py              # FastAPI :8001 — /query, /query/stream, compare, advisory, /models, /health
├── meta_questions.py       # Meta/identity detection (Auto → base LLM; Advisory short-circuit)
├── models/
│   ├── __init__.py         # Registry, run_model(), run_advisory(), auto default
│   ├── streaming.py        # NDJSON stream orchestration (status, tokens, done)
│   ├── auto_rag.py         # Routes → product_rag | general_rag | base_llm
│   ├── router.py           # Dual-index + keyword routing; meta → base_llm
│   ├── product_rag.py      # → terramind.rag.product
│   ├── general_rag.py      # → terramind.rag.general
│   ├── base_llm.py
│   ├── vision.py
│   ├── conversation.py
│   └── image_context.py
└── rag/
    ├── llm_stream.py       # LangChain OpenAI token streaming
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

## Streaming (dev / scripts)

```powershell
curl -N -X POST http://localhost:8001/query/stream -H "Content-Type: application/json" -d "{\"question\":\"What is IPM?\",\"model\":\"auto_rag\"}"
```

Each line is JSON: `status`, `token`, or `done`.

## Migration

Product logic still lives in root **`Rag_Pc.py`**. General RAG is fully in **`terramind/rag/general/`**. Status: [docs/PROJECT_STATUS.md](../docs/PROJECT_STATUS.md).
