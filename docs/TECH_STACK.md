# TerraMind — Technology stack

**Status:** Current as of June 2026. Lists libraries and services **actually used in this repo**, where they run, and why.

**Related:** runtime wiring → [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) · dependencies → [`requirements.txt`](../requirements.txt) · UI deps → [`web/frontend-react/package.json`](../web/frontend-react/package.json)

---

## At a glance

<p align="center">
  <img alt="Python" width="34px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/python/python-original.svg"/>
  <img alt="FastAPI" width="34px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/fastapi/fastapi-original.svg"/>
  <img alt="React" width="34px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/react/react-original.svg"/>
  <img alt="Vite" width="34px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/vite/vite-original.svg"/>
  <img alt="OpenAI" width="34px" src="https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/openai.svg"/>
  <img alt="Docker" width="34px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/docker/docker-original.svg"/>
  <img alt="nginx" width="34px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/nginx/nginx-original.svg"/>
  <img alt="Node.js" width="34px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/nodejs/nodejs-original.svg"/>
  <img alt="pandas" width="34px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/pandas/pandas-original.svg"/>
  <img alt="PyTorch" width="34px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/pytorch/pytorch-original.svg"/>
  <img alt="pytest" width="34px" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/pytest/pytest-original.svg"/>
</p>

<p align="center"><em>ChromaDB, LangChain, BM25, and pypdf are core to RAG but have no Devicon entry — see tables below.</em></p>

---

## 1. Backend & HTTP APIs

| Tool | Purpose | Where used |
| --- | --- | --- |
| **Python 3.11** | Runtime for both APIs, RAG pipelines, CLI, tests | `core/`, `web/app/`, Docker `python:3.11-slim` images |
| **FastAPI** | HTTP APIs, request models, streaming responses | Model API `core/api/app.py`; gateway `web/app/main.py` |
| **Uvicorn** | ASGI server | Local dev (`run_dev.py`, manual terminals); Docker `CMD` for `:8000` and `:8001` |
| **Pydantic / pydantic-settings** | Request/response schemas, gateway config | `core/api/app.py`, `web/app/schemas/`, `web/app/config.py` |
| **httpx** | Async HTTP client — gateway → model API | `web/app/services/rag_service.py` (proxy `/query`, compare, advisory, streams) |
| **python-dotenv** | Load `OPENAI_API_KEY` and service URLs from `.env` | Repo root `.env`; `core/api/app.py`, `web/app/main.py` |

---

## 2. AI, embeddings & chat

| Tool | Purpose | Where used |
| --- | --- | --- |
| **OpenAI API** (`openai`, `langchain-openai`) | Chat (`gpt-4o-mini`), embeddings (`text-embedding-3-small`), crop **vision** on uploaded images | All model backends under `core/models/`; `core/models/vision.py`; Chroma index build (`init-indexes`, local CLI) |
| **LangChain** (`langchain-core`, `langchain-classic`, `langchain-text-splitters`) | Prompt templates, `Document` types, text splitting, LLM wrappers | `core/rag/general/` and `core/rag/product/` (load → chunk → generate); `core/models/streaming.py` |

---

## 3. Vector store & retrieval

| Tool | Purpose | Where used |
| --- | --- | --- |
| **ChromaDB** + **langchain-chroma** | On-disk vector indexes for general PDFs and product catalog | `vectorstore/chroma/` (general), `vectorstore/chroma_products/` (product); Docker volume `terramind-vectorstore`; `core/rag/general/store.py`, `core/rag/product/store.py`, `core/rag/product/` |
| **rank-bm25** (`BM25Okapi`) | Lexical (keyword) retrieval for product catalog | `core/rag/product/hybrid.py` — combined with dense vectors in hybrid search |
| **sentence-transformers** (`CrossEncoder`) | Re-rank product retrieval candidates | `core/rag/product/rerank.py` — model `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| **Custom lexical rerank** | Lightweight token overlap boost on general RAG candidates | `core/rag/general/hybrid.py` (no extra library — blends vector order + lexical score) |

---

## 4. Data ingestion

| Tool | Purpose | Where used |
| --- | --- | --- |
| **pypdf** | Extract text from agriculture PDF corpus | `core/rag/general/load.py` — sources under `data/raw/documents/` |
| **pandas** + **openpyxl** | Read translated product Excel catalog and category sheets | `core/rag/product/load.py` — `data/raw/product_catalog/translated/product_catalog_en.xlsx` |

Corpus layout: [GENERAL_RAG_CORPUS.md](./GENERAL_RAG_CORPUS.md) · [data/README.md](../data/README.md).

---

## 5. Frontend (browser UI)

| Tool | Purpose | Where used |
| --- | --- | --- |
| **React 18** | Chat UI, model picker, compare grid, sessions, streaming bubble | `web/frontend-react/src/` (`App.jsx`, components) |
| **Vite 5** | Dev server (:3000), HMR, production build | `web/frontend-react/vite.config.js`; local `npm run dev` via `run_dev.py` |
| **react-markdown** + **remark-gfm** | Render assistant answers (headings, lists, bold) | Chat message components in `frontend-react/src/` |
| **@fontsource/dm-sans** | UI typography | Loaded in `App.jsx` |
| **Web Speech API** (`SpeechRecognition` / `webkitSpeechRecognition`) | Browser speech-to-text for the composer mic button | `web/frontend-react/src/App.jsx` — transcribes speech into the prompt before normal send |
| **MediaDevices + Web Audio API** (`getUserMedia`, `enumerateDevices`, `AudioContext`) | Microphone permission, device list, and live voice level meter | `web/frontend-react/src/App.jsx`; visual styling in `src/theme/visuals.js` |
| **Browser storage** | Saved chats and hidden Advisory unlock | `localStorage` / `sessionStorage` keys in `App.jsx`, `uiSettings.js` |
| **Static UI assets** | Theme wallpapers and decor PNGs | Repo-root `assets/` via Vite alias `@assets` (`vite.config.js`); Docker frontend image copies `assets/` at build time |

Dev proxy: Vite forwards `/api/*` → `http://localhost:8000` (see `vite.config.js`).

---

## 6. Deployment (Docker)

| Tool | Purpose | Where used |
| --- | --- | --- |
| **Docker** + **Docker Compose** | Three-service stack without local Python/Node | `docker-compose.yml` — `model-api`, `gateway`, `frontend`; profile `init` for `init-indexes` |
| **nginx** | Serve production React build; proxy `/api` to gateway | `docker/frontend/Dockerfile`, `docker/frontend/nginx.conf` |
| **Node.js 20** (build stage only) | `npm ci` + `vite build` inside frontend image | `docker/frontend/Dockerfile` — not shipped in final nginx image |

Guides: [docker/QUICKSTART.md](../docker/QUICKSTART.md) · [docker/README.md](../docker/README.md).

**Note:** `data/` is **mounted** from the clone into `model-api` / `init-indexes`; Chroma indexes live in the **`terramind-vectorstore`** volume — not baked into images.

---

## 7. Development & quality

| Tool | Purpose | Where used |
| --- | --- | --- |
| **pytest** | Unit/integration tests | `tests/` — 64 tests (router, scoring, advisory, auto battery); `web/tests/` — 7 gateway smoke tests |
| **Git** | Version control | Repo; `.dockerignore` excludes `.git/` from build context |
| **Conda** (optional) | Recommended local Python env name `terramind` | Documented in [README.md](../README.md), [web/RUN_LOCALLY.md](../web/RUN_LOCALLY.md) — not required for Docker |

---

## 8. Not in the default stack

| Item | Notes |
| --- | --- |
| **OpenCV** | Not used in TerraMind (logo format in docs follows [Devicon](https://devicon.dev/) style only). |
| **Redis / Postgres** | No server-side session DB — chats are browser `localStorage` only. |
| **pymupdf** | Optional future PDF extractor — mentioned in [GENERAL_RAG_EVAL.md](./GENERAL_RAG_EVAL.md), not in `requirements.txt` today. |
| **Server-side TTS/STT** | Not used. Voice input is frontend-only browser speech-to-text; no backend audio upload or speech service is configured. |

---

## How to update this file

When you add or remove a dependency that affects runtime behavior:

1. Update `requirements.txt` or `package.json` first.
2. Add a row here with **purpose** and **concrete path** (module or folder).
3. If topology changes (new service/port), update [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md).
4. Refresh the logo strip in [README.md](../README.md) if a major tool was added and has a Devicon/Simple Icons asset.
