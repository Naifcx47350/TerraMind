# TerraMind — File Map, Pipelines & What Is Actually Running

This guide walks through **every important file**, which of the **three servers** use it, **what calls what**, and what is **legacy / safe to remove** vs **required for the live web app**.

For product features and architecture narrative, see [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md) (repo root) or [FrontPage/ARCHITECTURE.md](../FrontPage/ARCHITECTURE.md).

---

## 1. The three servers (web app only)

These are the **only** processes needed to run the webpage today.

| # | Command (where to run) | Port | Entry file | Purpose |
|---|------------------------|------|------------|---------|
| **1** | `uvicorn terramind.api.app:app --reload --port 8001` | **8001** | `terramind/api/app.py` (or shim `rag_api.py`) | AI backends: 3 models, Chroma RAG, compare |
| **2** | `uvicorn app.main:app --reload --port 8000` | **8000** | `FrontPage/app/main.py` | API for UI: proxy, vision, mock |
| **3** | `npm run dev` in `FrontPage/frontend-react/` | **3000** | `frontend-react/src/main.jsx` → `App.jsx` | React chat in the browser |

```text
Browser :3000  ──proxy /api──►  FrontPage :8000  ──HTTP──►  rag_api :8001
                                    │                         │
                                    │                         ├── Rag_Pc / product_rag
                                    │                         ├── Rag_Gen / general_rag
                                    │                         └── models/base_llm
                                    └── models/vision.py (optional, from FrontPage too)
```

**Not used for the web app:** `scripts/`, `src/`, empty `app.py`, Phase 1 CLI flows.

---

## 2. Active request pipeline (single message)

What runs when a user sends one message (one model selected).

```text
App.jsx
  POST /api/ask  { question, model, history, image_base64?, image_mime? }
    │
    ▼
FrontPage/app/routers/ask.py  →  ask()
    │
    ▼
FrontPage/app/services/rag_service.py  →  call_rag()
    │   • detect language
    │   • _analyze_image() if image  →  models/vision.py (gpt-4o-mini)
    │   • build JSON payload
    ▼
HTTP POST  http://localhost:8001/query
    │
    ▼
terramind.api.app  →  query()
    │   • resolve_image_analysis() if needed
    ▼
terramind.models  →  run_model(model_id, ...)
    │
    ├── product_rag  →  terramind.rag.product  →  Rag_Pc.answer_with_rag()
    ├── general_rag  →  terramind.rag.general  →  Rag_Gen.answer_with_rag()
    └── base_llm     →  terramind.models.base_llm  →  ChatOpenAI only
    │
    ▼
JSON answer + sources  →  back to UI  →  localStorage session update
```

### Compare mode (extra path)

```text
App.jsx  POST /api/ask/compare
  → rag_service.call_rag_compare()
  → POST http://localhost:8001/query/compare
  → rag_api.query_compare()  (3× run_model in parallel, one shared image analysis)
  → App.jsx renders 3-column ComparePanels
```

---

## 3. Status legend

| Tag | Meaning |
|-----|---------|
| **ACTIVE** | Used by the live web stack (ports 3000 / 8000 / 8001) |
| **BUILD** | Run manually to create indexes; not a server |
| **DATA** | Inputs or generated storage |
| **LEGACY** | Initial bootcamp template; CLI only; not called by web |
| **OPTIONAL** | Docs, tests, Docker, helpers — not required to run UI |
| **UNUSED** | Empty or duplicate; safe to delete after review |

---

## 4. Repo root — file by file

### ACTIVE (runtime)

| File / folder | What it does | Called by |
|---------------|--------------|-----------|
| **`terramind/api/app.py`** | Model API: `/query`, `/query/compare`, `/models`, `/health` | FrontPage `rag_service.py` via HTTP |
| **`terramind/models/`** | Registry + 3 mode adapters + vision + conversation | `terramind.api.app` |
| **`terramind/rag/product/`** | Product RAG package (templates); **`__init__` re-exports `Rag_Pc.py`** | `terramind.models.product_rag` |
| **`terramind/rag/general/`** | General RAG package (templates); **`__init__` re-exports `Rag_Gen.py`** | `terramind.models.general_rag` |
| **`Rag_Pc.py`** | **Current** product RAG implementation (Excel → Chroma) | `terramind.rag.product` |
| **`Rag_Gen.py`** | **Current** general RAG implementation (markdown → Chroma) | `terramind.rag.general` |
| **`rag_api.py`** | Shim → `terramind.api.app` | Same as above (legacy command) |
| **`models/`** (root) | Shim → `terramind.models` | Backward-compatible imports only |
| **`requirements.txt`** | Python deps for root env | `pip install` at repo root |

See **`terramind/README.md`** and **`docs/RAG_MIGRATION_PLAN.md`** for the planned RAG file split (`config`, `load`, `store`, …). Each template file has a short TODO in its docstring.

### BUILD (one-off commands)

| Command | What it does |
|---------|----------------|
| `python Rag_Pc.py --reset` | Rebuild product vector index |
| `python Rag_Gen.py --reset` | Rebuild general document index |
| `python Rag_Pc.py "question"` | CLI test of product RAG only |
| `python Rag_Gen.py "question"` | CLI test of general RAG only |

### DATA

| Path | What it does |
|------|----------------|
| **`data/raw/text/ProductCatalog(En).xlsx`** | Product catalog source (`Rag_Pc.py` `CATALOG_PATH`) |
| **`data/raw/text/Pest_Management_FAO.md`** | General RAG source (`Rag_Gen.py` `DATA_PATH`) |
| **`vectorstore/chroma_products/`** | Persisted embeddings for products (gitignored) |
| **`vectorstore/chroma/`** | Persisted embeddings for general docs (gitignored) |
| **`.env`** (root) | `OPENAI_API_KEY`, etc. |

### LEGACY (not in web path)

| File / folder | What it was for | Web uses instead |
|---------------|-----------------|------------------|
| **`src/`** (removed) | Phase 1 modular RAG pipeline | `terramind/`, `Rag_Pc.py`, `Rag_Gen.py` |
| **`src/rag_pipeline.py`** | Old `answer_with_rag()` | `Rag_Pc` / `Rag_Gen` |
| **`src/base_llm.py`** | Old baseline LLM | `models/base_llm.py` |
| **`src/config.py`** | Old paths/models | Constants inside `Rag_*.py` |
| **`src/document_loader.py`**, **`chunking.py`**, **`embeddings.py`**, **`vector_store.py`**, **`retriever.py`**, **`prompts.py`**, **`text_cleaner.py`**, **`utils.py`**, **`safety.py`** | Ingestion/retrieval building blocks | Logic duplicated in `Rag_Pc` / `Rag_Gen` |
| **`scripts/01_ingest_documents.py`** | Ingest sample docs | Not used if you use `Rag_Gen` / Excel path |
| **`scripts/02_create_chunks.py`** | Chunk step | — |
| **`scripts/03_build_vectorstore.py`** | Build Chroma from `src/` | — |
| **`scripts/04_run_base_llm.py`** | CLI base LLM | `models/base_llm` via API |
| **`scripts/05_run_rag.py`** | CLI RAG + `--compare` | Web compare + `rag_api` |
| **`scripts/_bootstrap.py`** | Path hack for scripts | — |

### OPTIONAL / docs / assets

| File | Notes |
|------|--------|
| **`README.md`** | Repo index |
| **`PROJECT_OVERVIEW.md`** | Feature & technical overview |
| **`docs/FILE_MAP_AND_PIPELINE.md`** | This file |
| **`Project_plan.md`** | Planning notes |
| **`doc/*.pdf`** | Reference PDFs; **not** wired into `Rag_Gen` unless you convert and point `DATA_PATH` |
| **`TM_Logo.png`** | Branding for README; **not** served to UI |
| **`TM_Logo_o.png`** | Old logo backup — **UNUSED** |
| **`app.py`** | Empty — **UNUSED** |

---

## 5. FrontPage — file by file

### ACTIVE — backend (:8000)

| File | What it does | Called by |
|------|--------------|-----------|
| **`app/main.py`** | FastAPI app, CORS, routers, loads root `.env`, adds repo to `sys.path` | `uvicorn app.main:app` |
| **`app/config.py`** | Settings: `RAG_SERVICE_URL`, `USE_MOCK`, vision defaults | All services |
| **`app/routers/ask.py`** | `POST /api/ask`, `POST /api/ask/compare` | Browser via Vite proxy |
| **`app/routers/models.py`** | `GET /api/models` (proxy or fallback list) | `App.jsx` on load |
| **`app/routers/health.py`** | `GET /api/health` — shows mock vs RAG mode | Debugging |
| **`app/routers/history.py`** | `GET/DELETE /api/history` — global in-memory log | Optional; **not** per-session storage |
| **`app/schemas/ask.py`** | Pydantic: `AskRequest`, `AskResponse`, compare types | Routers + `rag_service` |
| **`app/services/rag_service.py`** | Vision, HTTP to :8001, mock, LLM fallback | `ask.py` |
| **`app/middleware/error_handler.py`** | Global errors | `main.py` |
| **`app/middleware/logger.py`** | Request logging | `main.py` |
| **`requirements.txt`** | FrontPage Python deps | `pip install` in `FrontPage/` |

### ACTIVE — frontend (:3000)

| File | What it does |
|------|--------------|
| **`frontend-react/src/main.jsx`** | React mount → `App` |
| **`frontend-react/src/App.jsx`** | Full UI: chat, sessions, model picker, compare, images, `localStorage` |
| **`frontend-react/index.html`** | HTML shell |
| **`frontend-react/vite.config.js`** | Dev server port 3000; proxy `/api` → 8000 |
| **`frontend-react/package.json`** | npm deps & `dev` script |
| **`frontend-react/public/TM_Logo.png`** | Logo at `/TM_Logo.png` (**this** is the file the browser loads) |

### OPTIONAL

| File | Notes |
|------|--------|
| **`setup_env.ps1`** | Creates `.env` snippet |
| **`env.rag.snippet`** | Template env lines |
| **`Dockerfile`** | API container only; still needs :8001 + indexes for full RAG |
| **`tests/test_api.py`** | API smoke tests |
| **`claude prompt.md`** | Prompt notes for UI generation — not executed |
| **`pyrightconfig.json`** | IDE typing |
| **`package-lock.json`** (under `FrontPage/`) | Orphan lockfile if no `package.json` there — **likely UNUSED** |

---

## 6. What is NOT operating in the current system

These exist in the repo but are **not** on the path from browser → answer:

```text
app.py                          (empty)
src/*                           (entire Phase 1 package)
scripts/01 … 05                 (CLI pipeline)
src/safety.py                   (never wired)
doc/*.pdf                       (not ingested unless you add conversion)
FrontPage GET /api/history      (log only; UI uses localStorage for sessions)
Direct LLM providers in rag_service  (only if RAG_SERVICE_URL unset + LLM_PROVIDER set)
TM_Logo.png at repo root        (UI uses public/TM_Logo.png only)
```

---

## 7. Duplicate / confusion warnings

| Issue | Detail |
|-------|--------|
| **Two `base_llm` files** | `src/base_llm.py` = legacy CLI. **`models/base_llm.py`** = web. |
| **Two logo paths** | Update **`FrontPage/frontend-react/public/TM_Logo.png`** for the site; bump `LOGO_SRC ?v=` in `App.jsx`. |
| **Two Chroma folders** | `chroma_products` = products; `chroma` = general docs. |
| **`docs/` vs root docs** | Overview may live as `PROJECT_OVERVIEW.md` at root; this file is under `docs/`. |

---

## 8. Safe to remove later (after team agrees)

Only remove after confirming nobody uses CLI demos:

| Remove candidate | Reason |
|------------------|--------|
| `app.py` | Empty |
| `src/` entire folder | Replaced by `Rag_Pc`, `Rag_Gen`, `models/` |
| `scripts/` | Replaced by `Rag_*.py` + web |
| `TM_Logo_o.png` | Backup |
| `FrontPage/claude prompt.md` | Dev notes only |
| `FrontPage/package-lock.json` | If no `FrontPage/package.json` |

**Do not remove:** `rag_api.py`, `Rag_Pc.py`, `Rag_Gen.py`, `models/`, `FrontPage/app/`, `FrontPage/frontend-react/`, `vectorstore/` (your indexes), `data/raw/text/` sources.

---

## 9. Minimal “who calls whom” cheat sheet

```text
main.jsx → App.jsx
App.jsx → ask.py (via /api/ask)
ask.py → rag_service.call_rag | call_rag_compare
rag_service → rag_api (/query | /query/compare)
rag_api → models.run_model
run_model → product_rag | general_rag | base_llm
product_rag → Rag_Pc.get_product_db + answer_with_rag
general_rag → Rag_Gen.get_general_db + answer_with_rag
run_model → resolve_image_analysis → vision.analyze_image (if image)
product_rag/general_rag → conversation.build_prompt_question (if history/image text)
```

---

## 10. Quick health check

| Check | URL / action |
|-------|----------------|
| Model API up | http://localhost:8001/health |
| Models list | http://localhost:8001/models |
| FrontPage up | http://localhost:8000/api/health → `"backend": "rag"` |
| UI up | http://localhost:3000 |
| Indexes exist | health shows `product_vectors` / `general_vectors` counts |

---

*Use this file when onboarding: start with §1 (three servers), then §2 (pipeline), then §4–5 for any file you open in the IDE.*
