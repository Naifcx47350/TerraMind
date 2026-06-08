<div align="center">
  <img src="assets/logo/TM_Logo.png" width="20%" height="20%">
</div>

# TerraMind

Agriculture support assistant with **Auto RAG** (default), manual product/general RAG, base LLM baseline, and a **hidden Advisory mode** — plus a **React chat UI** with streaming answers, compare view, image upload, retrieval scores, and saved conversations.

**`<repo-root>`** = your clone (folder with `docker-compose.yml`, `terramind/`, `Rag_Pc.py`, `run_dev.py`, and `FrontPage/`).

---

## Choose how to run

| | **Docker** (recommended for demos / no local toolchain) | **Local dev** (Python + Node on your machine) |
| --- | --- | --- |
| **Needs** | [Docker Desktop](https://www.docker.com/products/docker-desktop/) only | Conda Python 3.11+, Node.js, `pip install -r requirements.txt` |
| **Indexes** | Docker volume `terramind-vectorstore` (build once with `init-indexes`) | Folder `vectorstore/` on disk (gitignored) |
| **Corpus (`data/`)** | Mounted from your clone — **not** baked into images | Used directly from repo |
| **Secrets** | Repo-root `.env` only (copy from `docker/env.example`) | Repo-root `.env` or `FrontPage/.env` |
| **Start** | `docker compose up --build` | `python run_dev.py` (or three terminals) |
| **Full guide** | **[docker/QUICKSTART.md](docker/QUICKSTART.md)** | **[FrontPage/RUN_LOCALLY.md](FrontPage/RUN_LOCALLY.md)** |

Both paths serve the app at **http://localhost:3000** (frontend **3000**, gateway **8000**, model API **8001**).

---

## Quick start — Docker

From **`<repo-root>`**:

```powershell
copy docker\env.example .env
# Edit .env — real RAG:
#   USE_MOCK=false
#   OPENAI_API_KEY=sk-...
# Demo without a key:
#   USE_MOCK=true
```

**Real RAG — one-time index build** (needs `OPENAI_API_KEY` in `.env`; reads corpus from mounted `./data`):

```powershell
docker compose --profile init run --rm init-indexes
```

**Start the stack** (always all three services via Compose):

```powershell
docker compose up --build
```

Open **http://localhost:3000**. Containers: `terramind-frontend`, `terramind-gateway`, `terramind-model-api`.

- **`data/`** — PDFs and product Excel; cloned with the repo, mounted into `model-api` / `init-indexes`.
- **`vectorstore/`** — Chroma indexes live in the named volume **`terramind-vectorstore`**, not in the image. Re-run `init-indexes` after `docker compose down -v` or corpus changes.
- **No key in images** — use `.env` or the browser key modal (`USE_MOCK=true` skips the modal).

Step-by-step, troubleshooting, Hub tags: **[docker/QUICKSTART.md](docker/QUICKSTART.md)** · Dockerfile details: **[docker/README.md](docker/README.md)**.

---

## Quick start — local dev

From **`<repo-root>`**:

```powershell
conda create -n terramind python=3.11 -y
conda activate terramind
pip install -r requirements.txt
# optional: pip install -r requirements-dev.txt
```

Set `OPENAI_API_KEY` in `.env` (repo root or `FrontPage/.env`).

**Build vector indexes once** (writes to `./vectorstore/`):

```powershell
python Rag_Pc.py --reset
python -m terramind.rag.general.cli --reset
```

**Run the app** — one terminal:

```powershell
conda activate terramind
python run_dev.py
```

Requires `npm install` once in `FrontPage/frontend-react/`. Manual three-terminal setup: **[FrontPage/RUN_LOCALLY.md](FrontPage/RUN_LOCALLY.md)**.

---

## Architecture

<div align="center">
  <img src="assets/architecture/system-flow.png" alt="TerraMind system flow — browser, APIs, RAG modes, and response" width="100%">
</div>

<p align="center"><em>Request flow and RAG boundaries: <a href="docs/SYSTEM_ARCHITECTURE.md">docs/SYSTEM_ARCHITECTURE.md</a>.</em></p>

```text
Browser → :3000 UI  →  :8000 FrontPage gateway  →  :8001 Model API (RAG / LLM)
```

Locally, Vite serves the UI; in Docker, nginx serves the production React build and proxies `/api` to the gateway container.

---

## Tech stack

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

| Layer | Tools | Role in TerraMind |
| --- | --- | --- |
| **APIs** | Python, FastAPI, Uvicorn, httpx | Model API (:8001) + FrontPage gateway (:8000); streaming proxy to RAG |
| **AI / RAG** | OpenAI, LangChain, ChromaDB | Chat, embeddings, vision; PDF + Excel → vector indexes; product hybrid (BM25 + dense) + rerank |
| **UI** | React, Vite, react-markdown | Chat, compare, sessions; Vite in dev, nginx in Docker |
| **Data** | pypdf, pandas, openpyxl | General PDF corpus; product Excel catalog |
| **Deploy** | Docker, nginx, Node (build) | Three-container stack; `data/` mount + `terramind-vectorstore` volume |
| **Tests** | pytest | Router, scoring, advisory tests under `tests/` |

Full list with file paths and purpose: **[docs/TECH_STACK.md](docs/TECH_STACK.md)** (linked from [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md) §9).

---

## Models (picker order)

| Mode | ID | Knowledge source |
| --- | --- | --- |
| Auto (recommended) | `auto_rag` | Router picks product RAG, general RAG, or base LLM |
| Agriculture Knowledge RAG | `general_rag` | PDFs in `data/raw/documents/` |
| Product Catalog RAG | `product_rag` | Client Excel (`ProductCatalog(En).xlsx`) |
| Base LLM | `base_llm` | OpenAI only — no retrieval |
| Advisory (hidden UI) | `advisory` | General then product — unlock via logo easter egg; see [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) |

Default chat/vision model: **`gpt-4o-mini`**. Corpus notes: [docs/GENERAL_RAG_CORPUS.md](docs/GENERAL_RAG_CORPUS.md).

---

## Project layout

```text
TerraMind/
├── docker-compose.yml         # Docker: three services + vectorstore volume
├── docker/                    # Dockerfiles, QUICKSTART, env.example
├── terramind/                 # Backend: api, models, rag/
├── Rag_Pc.py                  # Product RAG entry (CLI + re-export)
├── run_dev.py                 # Local: start :8001 + :8000 + :3000
├── vectorstore/               # Chroma indexes (local dev; gitignored)
├── data/                      # Corpus + eval; see data/README.md
├── FrontPage/                 # Gateway API (:8000) + React UI (:3000)
├── docs/                      # Architecture, corpus, eval, status
├── scripts/                   # e.g. eval_general_rag.py
└── tests/                     # pytest
```

---

## Features (web)

- Model picker (Auto default) and **Compare** (product / general / base LLM)
- **Streaming answers** — retrieval/routing status, then tokens (`POST /api/ask/stream`)
- **Hidden Advisory** — click the logo **6 times** (within 2.5s) to unlock Advisory mode
- **Show sources** / **Show scores**; plant **image upload** (vision → all modes)
- **Conversation history** + **localStorage** sessions + sidebar search
- **OpenAI key prompt** if `OPENAI_API_KEY` is missing (syncs gateway + model API)
- English / Arabic (RTL)

Details: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md).

---

## Documentation

| Document | Description |
| --- | --- |
| **[docker/QUICKSTART.md](docker/QUICKSTART.md)** | **Docker** — clone → `.env` → init indexes → compose up |
| **[FrontPage/RUN_LOCALLY.md](FrontPage/RUN_LOCALLY.md)** | **Local dev** — ports, env, three terminals |
| **[docker/README.md](docker/README.md)** | Docker concepts, Dockerfiles, compose file map |
| **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** | Features, models, APIs, compare, Advisory |
| **[docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)** | Shipped work and remaining tasks |
| **[docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)** | Runtime topology |
| **[docs/TECH_STACK.md](docs/TECH_STACK.md)** | Tools, libraries, logos, where each is used |
| **[docs/README.md](docs/README.md)** | Index of all `docs/` files |
| **[data/README.md](data/README.md)** | Data folders — tracked vs gitignored |

---

## Tests

From **`<repo-root>`** with `terramind` env active:

```powershell
pytest tests/ -v
```

Routing battery: `pytest tests/test_auto_question_battery.py -v`.

---

## Optional eval

```powershell
python scripts/eval_general_rag.py
```

Writes under `data/eval/runs/` (gitignored). Retrieval-only: `python -m terramind.rag.general.cli --eval-retrieval`.

---

## License / context

SDA - AI Engineering Bootcamp MVP (RCP #9) — TerraMind focuses on grounded agricultural Q&A with explicit comparison between RAG and non-RAG behavior.
