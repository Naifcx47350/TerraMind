# TerraMind — File Map, Pipelines & What Is Actually Running

This guide walks through **every important file**, which of the **three servers** use it, **what calls what**, and what is **legacy / safe to remove** vs **required for the live web app**.

**Paths:** **`<repo-root>`** = your TerraMind git clone. All folder names below are relative to it (`web/`, `core/`, `data/`, `vectorstore/`).

For product features and architecture, see [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md) and [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md). Status and removed files: [PROJECT_STATUS.md](./PROJECT_STATUS.md).

---

## 1. The three servers (web app only)

These are the **only** processes needed to run the webpage today.

| #     | Command (where to run)                               | Port     | Entry file                                    | Purpose                             |
| ----- | ---------------------------------------------------- | -------- | --------------------------------------------- | ----------------------------------- |
| **1** | `uvicorn core.api.app:app --reload --port 8001` | **8001** | `core/api/app.py`  | Auto + RAG modes, compare, advisory |
| **2** | `uvicorn app.main:app --reload --port 8000`          | **8000** | `web/app/main.py`                       | API for UI: proxy, vision, mock     |
| **3** | `npm run dev` in `web/frontend-react/`         | **3000** | `frontend-react/src/main.jsx` → `App.jsx`     | React chat in the browser           |

```text
Browser :3000  ──proxy /api──►  web :8000  ──HTTP──►  Model API :8001
                                    │                         │
                                    │                         ├── auto_rag → router → product | general | base_llm
                                    │                         ├── product_rag / general_rag / base_llm (manual)
                                    │                         └── streaming: /query/stream (default UI)
                                    └── vision (optional, before stream)
```

**Not used for the web app:** Phase 1 `scripts/01_*` … `05_*` (removed) and fine-tuning JSONL under `data/raw/Fine tuning data/`.

---

## 2. Active request pipeline (single message)

What runs when a user sends one message (one model selected).

```text
App.jsx
  POST /api/ask/stream  { question, model, history, image_base64?, image_mime? }
    │
    ▼
web/app/routers/ask.py  →  ask_stream()
    │
    ▼
web/app/services/rag_service.py  →  stream_rag() | stream_rag_advisory()
    │   • detect language
    │   • _analyze_image() if image  →  models/vision.py (gpt-4o-mini)
    │   • proxy NDJSON from :8001
    ▼
HTTP POST  http://localhost:8001/query/stream  (or /query/advisory/stream)
    │
    ▼
core.api.app  →  query_stream() | query_advisory_stream()
    ▼
core.models.streaming  →  stream_model_events() | stream_advisory_events()
    │
    ├── auto_rag     →  router  →  product_rag | general_rag | base_llm
    ├── product_rag  →  retrieve + stream LLM tokens
    ├── general_rag  →  retrieve + stream LLM tokens
    └── base_llm     →  stream LLM only
    │
    ▼
NDJSON status + tokens + done  →  UI updates bot bubble  →  localStorage session update
```

Legacy non-streaming path: `POST /api/ask` → `call_rag()` → `POST /query`.

### Compare mode (extra path)

```text
App.jsx  POST /api/ask/compare
  → rag_service.call_rag_compare()
  → POST http://localhost:8001/query/compare
  → core.api.app query_compare()  (3× run_model in parallel, one shared image analysis)
  → App.jsx renders 3-column ComparePanels
```

---

## 3. Status legend

| Tag          | Meaning                                                |
| ------------ | ------------------------------------------------------ |
| **ACTIVE**   | Used by the live web stack (ports 3000 / 8000 / 8001)  |
| **BUILD**    | Run manually to create indexes; not a server           |
| **DATA**     | Inputs or generated storage                            |
| **LEGACY**   | Initial bootcamp template; CLI only; not called by web |
| **OPTIONAL** | Docs, tests, Docker, helpers — not required to run UI  |
| **UNUSED**   | Empty or duplicate; safe to delete after review        |

---

## 4. Repo root — file by file

### ACTIVE (runtime)

| File / folder                     | What it does                                                                                    | Called by                                      |
| --------------------------------- | ----------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **`core/api/app.py`**        | Model API: `/query`, `/query/stream`, `/query/compare`, `/query/advisory`, `/models`, `/health` | web `rag_service.py` via HTTP            |
| **`core/models/`**           | Registry, `streaming.py`, `auto_rag`, `router`, RAG adapters, vision                            | `core.api.app`                            |
| **`core/meta_questions.py`** | Meta/identity detection (Auto → base LLM; Advisory short-circuit)                               | `router.py`, `run_advisory`, streaming         |
| **`core/rag/llm_stream.py`** | OpenAI token streaming via LangChain                                                            | `streaming.py`, `generate.py`                  |
| **`core/rag/general/`**      | Full general pipeline + CLI + eval                                                              | `core.models.general_rag`                 |
| **`core/rag/product/`**      | Product RAG package — Excel → Chroma → hybrid retrieve → answer | `core.models.product_rag` via `pipeline.py` |
| **`docker-compose.yml`**          | Docker: three services + `terramind-vectorstore` volume + `init-indexes` profile | `docker compose up --build` |
| **`core/rag/scoring.py`**    | Retrieval scores + confidence                                                                   | RAG answer dicts                               |
| **`run_dev.py`**                  | Starts :8001, :8000, :3000                                                                      | Local dev                                      |
| **`requirements.txt`**            | Python deps (full stack)                                                                        | `pip install -r requirements.txt` at repo root |
| **`requirements-dev.txt`**        | Dev extras (pytest)                                                                             | `pip install -r requirements-dev.txt`          |

Product RAG and General RAG are package-based under **`core/rag/product/`** and **`core/rag/general/`**.

**Product RAG modules (`core/rag/product/`):**

| Module | Role |
| --- | --- |
| `config.py` | Paths (`CATALOG_PATH`, `CHROMA_PATH`), models, RAG prompt |
| `load.py` | Excel → LangChain product documents |
| `chunk.py` | Product sections → retrieval chunks |
| `store.py` | Build/load Chroma index |
| `rewrite.py` | Query rewrite before retrieval |
| `retrieve.py` | Dense vector search |
| `hybrid.py` | BM25 + dense fusion (RRF) |
| `rerank.py` | Cross-encoder rerank |
| `generate.py` | Context formatting + LLM answer |
| `pipeline.py` | Public API used by model adapters (`init_product_rag`, `get_product_db`, …) |
| `cli.py` | `--reset` index build + smoke question |
| `clarification.py`, `catalog_agent.py` | Scaffolds for future catalog tools (not in Auto router yet) |

### BUILD (one-off commands)

| Command                                          | What it does                   |
| ------------------------------------------------ | ------------------------------ |
| `python -m core.rag.product.cli --reset`                       | Rebuild product vector index   |
| `python -m core.rag.general.cli --reset`    | Rebuild general document index |
| `python -m core.rag.product.cli "question"` | CLI test of product RAG only   |
| `python -m core.rag.general.cli "question"` | CLI test of general RAG only   |

### DATA

| Path                                        | What it does                                                                     |
| ------------------------------------------- | -------------------------------------------------------------------------------- |
| **`data/raw/product_catalog/translated/product_catalog_en.xlsx`** | Translated product catalog source (`core.rag.product.config.CATALOG_PATH`)  |
| **`data/raw/product_catalog/translated/product_categories_en.xlsx`** | Translated category source (`core.rag.product.config.CATEGORY_PATH`)        |
| **`data/raw/documents/`**                   | General RAG PDFs (IPM, GAP, soil, pesticides) — see `docs/GENERAL_RAG_CORPUS.md` |
| **`data/raw/product_catalog/translated/`**             | Translated product Excel files used by Product RAG                               |
| **`data/raw/product_catalog/original/`**               | Original/source product workbook artifacts; preserved, not used at runtime       |
| **`data/sample/`**                          | Allowlisted sample `.txt` (e.g. pesticide safety)                                |
| **`data/eval/`**                            | Golden questions; `runs/` gitignored                                             |
| **`data/README.md`**                        | What is tracked vs ignored                                                       |
| **`vectorstore/chroma_products/`**          | Persisted embeddings for products (gitignored)                                   |
| **`vectorstore/chroma/`**                   | Persisted embeddings for general docs (gitignored)                               |
| **`.env`** (root)                           | `OPENAI_API_KEY`, etc.                                                           |

### LEGACY / removed (not in web path)

| Item                              | Notes                                                   |
| --------------------------------- | ------------------------------------------------------- |
| **`src/`**                        | Phase 1 package — **removed** from repo                 |
| **`Rag_Gen.py`**                  | General RAG — **removed**; use `core/rag/general/` |
| **`doc/`**                        | Old PDF folder — **removed**; use `data/raw/documents/` |
| **`scripts/01_*` … `05_*`**       | Phase 1 CLI — **removed**                               |
| **`scripts/eval_general_rag.py`** | Optional full-answer eval export (still present)        |

### OPTIONAL / docs / assets

| File                                | Notes                                                    |
| ----------------------------------- | -------------------------------------------------------- |
| **`README.md`**                     | Repo index                                               |
| **`PROJECT_OVERVIEW.md`**           | Feature & technical overview                             |
| **`docs/FILE_MAP_AND_PIPELINE.md`** | This file                                                |
| **`data/README.md`**                | Data layout + gitignore                                  |
| **`docs/SYSTEM_ARCHITECTURE.md`**   | Canonical architecture                                   |
| **`assets/`**                       | UI wallpapers/decor (`assets/backgrounds/`), logos (`assets/logo/`); loaded via Vite `@assets` alias; copied into Docker frontend build |
| **`docs/`**                         | Developer documentation only (not ingested by RAG)       |
| **`docs/GENERAL_RAG_CORPUS.md`**    | General RAG corpus list and rebuild steps                |
| **`TM_Logo.png`**                   | Branding for README; **not** served to UI                |
| **`TM_Logo_o.png`**                 | Old logo backup — **UNUSED**                             |
| **`app.py`**                        | Empty — **UNUSED**                                       |

---

## 5. web — file by file

### ACTIVE — backend (:8000)

| File                                  | What it does                                                                                            | Called by                             |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| **`app/main.py`**                     | FastAPI app, CORS, routers, loads root `.env`, adds repo to `sys.path`                                  | `uvicorn app.main:app`                |
| **`app/config.py`**                   | Settings: `RAG_SERVICE_URL`, `USE_MOCK`, vision defaults                                                | All services                          |
| **`app/routers/ask.py`**              | `POST /api/ask`, `/api/ask/stream`, `/api/ask/compare`, `/api/ask/advisory`, `/api/ask/advisory/stream` | Browser via Vite proxy                |
| **`app/routers/models.py`**           | `GET /api/models` (proxy or fallback list)                                                              | `App.jsx` on load                     |
| **`app/routers/health.py`**           | `GET /api/health` — shows mock vs RAG mode                                                              | Debugging                             |
| **`app/routers/history.py`**          | `GET/DELETE /api/history` — global in-memory log                                                        | Optional; **not** per-session storage |
| **`app/schemas/ask.py`**              | Pydantic: `AskRequest`, `AskResponse`, compare types                                                    | Routers + `rag_service`               |
| **`app/services/rag_service.py`**     | Vision, HTTP to :8001, mock, LLM fallback                                                               | `ask.py`                              |
| **`app/middleware/error_handler.py`** | Global errors                                                                                           | `main.py`                             |
| **`app/middleware/logger.py`**        | Request logging                                                                                         | `main.py`                             |
| **`requirements.txt`**                | Points to root `requirements.txt` (`-r ../requirements.txt`)                                            | Same env as repo root                 |

### ACTIVE — frontend (:3000)

| File                                    | What it does                                                                                              |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **`frontend-react/src/main.jsx`**       | React mount → `App`                                                                                       |
| **`frontend-react/src/App.jsx`**        | Chat, streaming UI, Auto picker, hidden Advisory unlock (6× logo), compare, scores, startup `BootstrapOverlay`, voice input mic (`SpeechRecognition` + mic meter), `MarkdownMessage.jsx` |
| **`frontend-react/index.html`**         | HTML shell                                                                                                |
| **`frontend-react/vite.config.js`**     | Dev server port 3000; proxy `/api` → 8000; alias `@assets` → repo-root `assets/` |
| **`frontend-react/package.json`**       | npm deps & `dev` script                                                                                   |
| **`frontend-react/public/TM_Logo.png`** | Logo at `/TM_Logo.png` (**this** is the file the browser loads)                                           |
| **`frontend-react/src/theme/visuals.js`** | Shared UI CSS for glass theme, composer, compare, voice mic popover, live audio meter, and responsive behavior |
| **`frontend-react/src/i18n/strings.js`** | EN/AR labels for composer, compare, voice input, settings, and common UI copy |

### OPTIONAL

| File                                         | Notes                                                          |
| -------------------------------------------- | -------------------------------------------------------------- |
| **`setup_env.ps1`**                          | Creates `.env` snippet                                         |
| **`env.rag.snippet`**                        | Template env lines                                             |
| **`Dockerfile`**                             | API container only; still needs :8001 + indexes for full RAG   |
| **`tests/test_api.py`**                      | Gateway smoke tests (health, config, ask)                      |
| **`../tests/`** (repo root)                  | Router, scoring, advisory meta, auto question battery (64 tests) |
| **`pyrightconfig.json`**                     | IDE typing                                                     |

---

## 6. What is NOT operating in the current system

These exist in the repo but are **not** on the path from browser → answer:

```text
data/raw/Fine tuning data/      (training JSONL — gitignored)
data/eval/runs/                 (eval exports — gitignored)
vectorstore/                    (rebuild locally — gitignored)
docs/                           (developer docs only — not ingested)
web GET /api/history      (global log; UI uses localStorage)
TM_Logo at repo root assets/    (UI uses web/frontend-react/public/TM_Logo.png)
```

---

## 7. Duplicate / confusion warnings

| Issue                                        | Detail                                                                                                   |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **`core/models` vs old root `models/`** | Use **`core/models/`** only; root `models/` shim removed.                                           |
| **Two logo paths**                           | Update **`web/frontend-react/public/TM_Logo.png`** for the site; bump `LOGO_SRC ?v=` in `App.jsx`. |
| **Two Chroma folders**                       | `chroma_products` = products; `chroma` = general docs.                                                   |
| **`docs/` vs root docs**                     | Overview may live as `PROJECT_OVERVIEW.md` at root; this file is under `docs/`.                          |

---

## 8. Safe to remove later (after team agrees)

Only remove after confirming nobody uses CLI demos:

| Remove candidate                | Reason                         |
| ------------------------------- | ------------------------------ |
| `app.py`                        | Empty                          |
| `app.py` (root)                 | Empty if present               |
| Phase 1 `scripts/01_*` … `05_*` | Already removed                |
| `TM_Logo_o.png`                 | Backup                         |

**Do not remove:** `core/`, `run_dev.py`, `web/`, corpus under `data/raw/`, local `vectorstore/` (rebuild if deleted).

---

## 9. Minimal “who calls whom” cheat sheet

```text
main.jsx → App.jsx
App.jsx → ask.py (via /api/ask)
ask.py → rag_service.stream_rag | stream_rag_advisory | call_rag_compare
rag_service → /query/stream | /query/advisory/stream | /query/compare
streaming → stream_model_events | stream_advisory_events
run_model (JSON path) → auto_rag | product_rag | general_rag | base_llm
auto_rag → router.route_question → product_rag | general_rag | base_llm
product_rag → core.rag.product.get_product_db + answer_with_rag
general_rag → core.rag.general.get_general_db + answer_with_rag
run_model → resolve_image_analysis → vision.analyze_image (if image)
product_rag/general_rag → conversation.build_prompt_question (if history/image text)
```

---

## 10. Quick health check

| Check         | URL / action                                              |
| ------------- | --------------------------------------------------------- |
| Model API up  | http://localhost:8001/health                              |
| Models list   | http://localhost:8001/models                              |
| web up  | http://localhost:8000/api/health → `"backend": "rag"`     |
| UI up         | http://localhost:3000                                     |
| Indexes exist | health shows `product_vectors` / `general_vectors` counts |

---

_Use this file when onboarding: start with §1 (three servers), then §2 (pipeline), then §4–5 for any file you open in the IDE._
