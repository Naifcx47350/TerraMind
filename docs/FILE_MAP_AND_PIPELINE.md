# TerraMind — File Map, Pipelines & What Is Actually Running

This guide walks through **every important file**, which of the **three servers** use it, **what calls what**, and what is **legacy / safe to remove** vs **required for the live web app**.

**Paths:** **`<repo-root>`** = your TerraMind git clone. All folder names below are relative to it (`FrontPage/`, `terramind/`, `data/`, `vectorstore/`).

For product features and architecture, see [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md) and [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md). Status and removed files: [PROJECT_STATUS.md](./PROJECT_STATUS.md).

---

## 1. The three servers (web app only)

These are the **only** processes needed to run the webpage today.

| # | Command (where to run) | Port | Entry file | Purpose |
|---|------------------------|------|------------|---------|
| **1** | `uvicorn terramind.api.app:app --reload --port 8001` | **8001** | `terramind/api/app.py` (or shim `rag_api.py`) | Auto + RAG modes, compare, advisory |
| **2** | `uvicorn app.main:app --reload --port 8000` | **8000** | `FrontPage/app/main.py` | API for UI: proxy, vision, mock |
| **3** | `npm run dev` in `FrontPage/frontend-react/` | **3000** | `frontend-react/src/main.jsx` → `App.jsx` | React chat in the browser |

```text
Browser :3000  ──proxy /api──►  FrontPage :8000  ──HTTP──►  rag_api :8001
                                    │                         │
                                    │                         ├── auto_rag → router
                                    │                         ├── product_rag → Rag_Pc
                                    │                         ├── general_rag → terramind.rag.general
                                    │                         └── base_llm
                                    └── models/vision.py (optional, from FrontPage too)
```

**Not used for the web app:** Phase 1 `scripts/01_*` … `05_*` (removed), `data/processed/` JSONL, fine-tuning JSONL under `data/raw/Fine tuning data/`.

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
    ├── auto_rag     →  terramind.models.router  →  product_rag | general_rag
    ├── product_rag  →  terramind.rag.product  →  Rag_Pc.answer_with_rag()
    ├── general_rag  →  terramind.rag.general  →  pipeline.answer_with_rag()
    └── base_llm     →  terramind.models.base_llm
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
| **`terramind/models/`** | Registry: `auto_rag`, `product_rag`, `general_rag`, `base_llm`, `router`, vision | `terramind.api.app` |
| **`terramind/rag/general/`** | Full general pipeline + CLI + eval | `terramind.models.general_rag` |
| **`terramind/rag/product/`** | Re-exports **`Rag_Pc.py`** (migration in progress) | `terramind.models.product_rag` |
| **`terramind/rag/scoring.py`** | Retrieval scores + confidence | RAG answer dicts |
| **`Rag_Pc.py`** | Product RAG implementation (Excel → Chroma) | `terramind.rag.product` |
| **`rag_api.py`** | Shim → `terramind.api.app` | Legacy uvicorn target |
| **`run_dev.py`** | Starts :8001, :8000, :3000 | Local dev |
| **`requirements.txt`** | Python deps (full stack) | `pip install -r requirements.txt` at repo root |
| **`requirements-dev.txt`** | Dev extras (pytest) | `pip install -r requirements-dev.txt` |

Product RAG migration: **`docs/PROJECT_STATUS.md`** §2. General RAG is complete under **`terramind/rag/general/`**.

### BUILD (one-off commands)

| Command | What it does |
|---------|----------------|
| `python Rag_Pc.py --reset` | Rebuild product vector index |
| `python -m terramind.rag.general.cli --reset` | Rebuild general document index |
| `python Rag_Pc.py "question"` | CLI test of product RAG only |
| `python -m terramind.rag.general.cli "question"` | CLI test of general RAG only |

### DATA

| Path | What it does |
|------|----------------|
| **`data/raw/text/ProductCatalog(En).xlsx`** | Product catalog source (`Rag_Pc.py` `CATALOG_PATH`) |
| **`data/raw/documents/`** | General RAG PDFs (IPM, GAP, soil, pesticides) — see `docs/GENERAL_RAG_CORPUS.md` |
| **`data/raw/text/`** | Product Excel; optional extra text for general RAG |
| **`data/sample/`** | Allowlisted sample `.txt` (e.g. pesticide safety) |
| **`data/eval/`** | Golden questions; `runs/` gitignored |
| **`data/README.md`** | What is tracked vs ignored |
| **`vectorstore/chroma_products/`** | Persisted embeddings for products (gitignored) |
| **`vectorstore/chroma/`** | Persisted embeddings for general docs (gitignored) |
| **`.env`** (root) | `OPENAI_API_KEY`, etc. |

### LEGACY / removed (not in web path)

| Item | Notes |
|------|--------|
| **`src/`** | Phase 1 package — **removed** from repo |
| **`Rag_Gen.py`** | General RAG — **removed**; use `terramind/rag/general/` |
| **`doc/`** | Old PDF folder — **removed**; use `data/raw/documents/` |
| **`scripts/01_*` … `05_*`** | Phase 1 CLI — **removed** |
| **`scripts/eval_general_rag.py`** | Optional full-answer eval export (still present) |
| **`data/processed/`** | Generated JSONL — gitignored |

### OPTIONAL / docs / assets

| File | Notes |
|------|--------|
| **`README.md`** | Repo index |
| **`PROJECT_OVERVIEW.md`** | Feature & technical overview |
| **`docs/FILE_MAP_AND_PIPELINE.md`** | This file |
| **`data/README.md`** | Data layout + gitignore |
| **`docs/SYSTEM_ARCHITECTURE.md`** | Canonical architecture |
| **`assets/`** | Logo, architecture diagram |
| **`docs/`** | Developer documentation only (not ingested by RAG) |
| **`docs/GENERAL_RAG_CORPUS.md`** | General RAG corpus list and rebuild steps |
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
| **`app/routers/ask.py`** | `POST /api/ask`, `/api/ask/compare`, `/api/ask/advisory` | Browser via Vite proxy |
| **`app/routers/models.py`** | `GET /api/models` (proxy or fallback list) | `App.jsx` on load |
| **`app/routers/health.py`** | `GET /api/health` — shows mock vs RAG mode | Debugging |
| **`app/routers/history.py`** | `GET/DELETE /api/history` — global in-memory log | Optional; **not** per-session storage |
| **`app/schemas/ask.py`** | Pydantic: `AskRequest`, `AskResponse`, compare types | Routers + `rag_service` |
| **`app/services/rag_service.py`** | Vision, HTTP to :8001, mock, LLM fallback | `ask.py` |
| **`app/middleware/error_handler.py`** | Global errors | `main.py` |
| **`app/middleware/logger.py`** | Request logging | `main.py` |
| **`requirements.txt`** | Points to root `requirements.txt` (`-r ../requirements.txt`) | Same env as repo root |

### ACTIVE — frontend (:3000)

| File | What it does |
|------|--------------|
| **`frontend-react/src/main.jsx`** | React mount → `App` |
| **`frontend-react/src/App.jsx`** | Chat, Auto picker, compare, scores, routed hint, `MarkdownMessage.jsx` |
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
| **`pyrightconfig.json`** | IDE typing |
| **`package-lock.json`** (under `FrontPage/`) | Orphan lockfile if no `package.json` there — **likely UNUSED** |

---

## 6. What is NOT operating in the current system

These exist in the repo but are **not** on the path from browser → answer:

```text
data/processed/                 (generated JSONL — gitignored)
data/raw/Fine tuning data/      (training JSONL — gitignored)
data/eval/runs/                 (eval exports — gitignored)
vectorstore/                    (rebuild locally — gitignored)
docs/                           (developer docs only — not ingested)
FrontPage GET /api/history      (global log; UI uses localStorage)
TM_Logo at repo root assets/    (UI uses FrontPage/frontend-react/public/TM_Logo.png)
```

---

## 7. Duplicate / confusion warnings

| Issue | Detail |
|-------|--------|
| **`terramind/models` vs old root `models/`** | Use **`terramind/models/`** only; root `models/` shim removed. |
| **Two logo paths** | Update **`FrontPage/frontend-react/public/TM_Logo.png`** for the site; bump `LOGO_SRC ?v=` in `App.jsx`. |
| **Two Chroma folders** | `chroma_products` = products; `chroma` = general docs. |
| **`docs/` vs root docs** | Overview may live as `PROJECT_OVERVIEW.md` at root; this file is under `docs/`. |

---

## 8. Safe to remove later (after team agrees)

Only remove after confirming nobody uses CLI demos:

| Remove candidate | Reason |
|------------------|--------|
| `app.py` | Empty |
| `app.py` (root) | Empty if present |
| Phase 1 `scripts/01_*` … `05_*` | Already removed |
| `TM_Logo_o.png` | Backup |
| `FrontPage/package-lock.json` | If no `FrontPage/package.json` |

**Do not remove:** `terramind/`, `rag_api.py`, `Rag_Pc.py`, `run_dev.py`, `FrontPage/`, corpus under `data/raw/`, local `vectorstore/` (rebuild if deleted).

---

## 9. Minimal “who calls whom” cheat sheet

```text
main.jsx → App.jsx
App.jsx → ask.py (via /api/ask)
ask.py → rag_service.call_rag | call_rag_compare
rag_service → rag_api (/query | /query/compare)
rag_api → models.run_model
run_model → auto_rag | product_rag | general_rag | base_llm
auto_rag → router.route_question → one RAG backend
product_rag → Rag_Pc.get_product_db + answer_with_rag
general_rag → terramind.rag.general.get_general_db + answer_with_rag
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
