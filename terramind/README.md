# terramind/ — Backend package

Organized backend for the TerraMind web MVP.

## Layout

```text
terramind/
├── api/
│   └── app.py              # FastAPI :8001 — /query, /query/compare, /models, /health
├── models/
│   ├── __init__.py         # Registry: run_model(), list_models()
│   ├── product_rag.py      # Adapter → rag.product
│   ├── general_rag.py      # Adapter → rag.general
│   ├── base_llm.py         # OpenAI chat only
│   ├── vision.py           # Image analysis
│   ├── conversation.py     # Chat history → prompt text
│   └── image_context.py
└── rag/
    ├── product/            # Product Excel RAG (templates + re-export from Rag_Pc.py)
    │   ├── config.py       # TODO
    │   ├── load.py
    │   ├── chunk.py
    │   ├── store.py
    │   ├── retrieve.py
    │   ├── generate.py
    │   ├── pipeline.py
    │   └── cli.py
    └── general/            # Document RAG (load → chunk → store → retrieve → generate)
        └── (same module names)
```

## Run

From **`<repo-root>`** (your TerraMind clone):

```powershell
cd <repo-root>
uvicorn terramind.api.app:app --reload --port 8001
```

`rag_api.py` at repo root still works (shim).

## Migration plan

**Full reference:** [docs/RAG_MIGRATION_PLAN.md](../docs/RAG_MIGRATION_PLAN.md)

1. **Now:** `Rag_Pc.py` / `Rag_Gen.py` at repo root hold full logic; `terramind.rag.*` re-exports them.
2. **Next:** Follow TODOs in each `terramind/rag/*/*.py` file (config → load → store → … → pipeline).
3. **Then:** Root `Rag_Pc.py` / `Rag_Gen.py` become thin CLIs or are removed.

Build indexes (unchanged until CLI moves):

```powershell
cd <repo-root>
python Rag_Pc.py --reset
python -m terramind.rag.general.cli --reset
```
