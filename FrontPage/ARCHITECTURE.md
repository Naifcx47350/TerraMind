# TerraMind — System Architecture

Compact architecture reference for the **web MVP** (React + FrontPage API + Model API).  
For full narrative documentation (models, storage, compare, images, history), see **[../PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md)**.  
For every file’s role and legacy vs active paths, see **[../docs/FILE_MAP_AND_PIPELINE.md](../docs/FILE_MAP_AND_PIPELINE.md)**.

---

## Runtime topology

```
┌─────────────────────────────────────────────────────────────┐
│  Browser  http://localhost:3000                             │
│  React (App.jsx) — chat, compare grid, model picker         │
│  localStorage: terramind_sessions_v1                        │
└───────────────────────────┬─────────────────────────────────┘
                            │ /api/*  (Vite proxy)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  FrontPage API  http://localhost:8000                       │
│  app/routers/ask.py      → /api/ask, /api/ask/compare       │
│  app/services/rag_service.py → vision + HTTP to 8001        │
└───────────────────────────┬─────────────────────────────────┘
                            │ POST /query, /query/compare
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Model API  http://localhost:8001  (rag_api.py)             │
│  models/__init__.py → run_model()                           │
├──────────────┬────────────────────┬─────────────────────────┤
│ product_rag  │ general_rag        │ base_llm                │
│ Rag_Pc.py    │ Rag_Gen.py         │ OpenAI chat only        │
│ chroma_products │ chroma         │ (no vectors)            │
└──────────────┴────────────────────┴─────────────────────────┘
```

---

## Model routing

| `model` id | Data store | Retrieval |
|------------|------------|-----------|
| `product_rag` | `vectorstore/chroma_products/` | Excel catalog chunks |
| `general_rag` | `vectorstore/chroma/` | IPM / FAO markdown chunks |
| `base_llm` | — | None |

All generation uses **OpenAI `gpt-4o-mini`** unless you change `CHAT_MODEL` in the RAG scripts / `models/base_llm.py`.

---

## Cross-cutting features

| Feature | Where it happens |
|---------|------------------|
| **Model picker** | UI → `model` field → `run_model()` |
| **Compare** | UI → `/api/ask/compare` → `/query/compare` (parallel ×3) |
| **Images** | `models/vision.py` (gpt-4o-mini) → text injected into all modes |
| **Chat memory** | UI `history[]` → `models/conversation.py` (RAG) or message list (base LLM) |
| **Session save** | Browser `localStorage` only |
| **Sources** | Retrieved chunk metadata → UI chips |

---

## Key files

| Path | Role |
|------|------|
| `frontend-react/src/App.jsx` | Entire UI |
| `app/services/rag_service.py` | Gateway logic |
| `rag_api.py` | Model router |
| `models/*.py` | Per-mode adapters |
| `Rag_Pc.py` / `Rag_Gen.py` | Index build + RAG core |

---

## Run order

See [RUN_LOCALLY.md](./RUN_LOCALLY.md): terminal 1 → `rag_api` :8001, terminal 2 → FrontPage :8000, terminal 3 → Vite :3000.
