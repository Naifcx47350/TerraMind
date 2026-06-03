# Run FrontPage locally (TerraMind)

## Path convention

Replace **`<repo-root>`** with wherever you cloned TerraMind (the folder that contains `Rag_Pc.py`, `terramind/`, and `FrontPage/`).

Examples (not literal — use your own path):

| OS | Example |
|----|---------|
| Windows | `cd C:\projects\TerraMind` |
| macOS / Linux | `cd ~/projects/TerraMind` |

After the first `cd <repo-root>`, other steps use **relative** folders (`FrontPage/`, `FrontPage/frontend-react/`).

---

## One command (dev launcher)

From **`<repo-root>`** with `terramind` env active:

```powershell
cd <repo-root>
conda activate terramind
python run_dev.py
```

Starts all three services in one terminal. Open **http://localhost:3000**. Press **Ctrl+C** to stop everything.

Requires `npm install` once in `<repo-root>/FrontPage/frontend-react`.

---

## Three terminals (manual)

| Terminal | Service                                        | Port     |
| -------- | ---------------------------------------------- | -------- |
| 1        | TerraMind Model API (`terramind.api.app` or `rag_api.py`) | **8001** |
| 2        | FrontPage API (`uvicorn app.main`)             | **8000** |
| 3        | React UI (`npm run dev`)                       | **3000** |

For mock-only demos you can skip terminal 1 and set `USE_MOCK=true` (two terminals only).

Pipeline overview: [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## Prerequisites

| Tool                                      | Used for                |
| ----------------------------------------- | ----------------------- |
| **Python 3.11+** (e.g. conda `terramind`) | Backend API             |
| **Node.js** via nvm (e.g. `24.15.0`)      | Frontend (Vite + React) |

---

## 1. TerraMind Model API — terminal 1 (`models/` + RAG scripts)

From **`<repo-root>`** (not `FrontPage/`):

```powershell
cd <repo-root>
conda activate terramind
```

Build indexes once (or after data changes):

```powershell
python Rag_Pc.py --reset    # product catalog Excel
python Rag_Gen.py --reset   # general agriculture docs (optional)
```

Start the unified model API (routes by `model` id):

```powershell
uvicorn terramind.api.app:app --reload --port 8001
# legacy: uvicorn rag_api:app --reload --port 8001
```

| Model id      | Backend                                | Data                       |
| ------------- | -------------------------------------- | -------------------------- |
| `product_rag` | `terramind/models/product_rag.py` → `terramind/rag/product/` → `Rag_Pc.py` | Client product Excel |
| `general_rag` | `terramind/models/general_rag.py` → `terramind/rag/general/` → `Rag_Gen.py` | FAO / IPM documents |
| `base_llm`    | `models/base_llm.py`                   | OpenAI only (no retrieval) |

Check:

- http://localhost:8001/health — vector counts per index
- http://localhost:8001/models — list of modes for the UI picker

In the React UI:

- **Model dropdown (top right)** — one mode per message
- **Compare** (near the input) — same question to all three modes, side-by-side
- **Image attach** — vision analysis included for every mode (`gpt-4o-mini`)
- Chats are saved in the browser (`localStorage`) and **history** is sent on each turn

Technical details: [../docs/PROJECT_OVERVIEW.md](../docs/PROJECT_OVERVIEW.md)

Leave this terminal running.

---

## 2. FrontPage backend (FastAPI) — terminal 2

**Important:** run `uvicorn` from **`<repo-root>/FrontPage`**, not from `<repo-root>` alone.  
From the wrong folder you get `Could not import module "app.main"` and the UI shows proxy `ECONNREFUSED`.

```powershell
cd <repo-root>/FrontPage
```

Activate your Python env and install deps (once):

```powershell
conda activate terramind
cd <repo-root>
pip install -r requirements.txt
```

Create `.env` (once) if you don’t have it:

```powershell
copy .env.example .env
```

**Product RAG connected to the website** (recommended after `rag_api` is running):

The API now defaults to RAG (`use_mock=false`, `RAG_SERVICE_URL=http://localhost:8001/query`) even without a `.env` file.

Optional — create `FrontPage/.env` explicitly:

```powershell
cd FrontPage
.\setup_env.ps1
```

Or paste into `FrontPage/.env`:

```env
USE_MOCK=false
RAG_SERVICE_URL=http://localhost:8001/query
REQUEST_TIMEOUT=90
```

OpenAI key: `<repo-root>/.env` or `<repo-root>/FrontPage/.env` with `OPENAI_API_KEY=...` (read by `Rag_Pc.py` / `rag_api`).

**Restart FrontPage uvicorn after any `.env` or config change.**

**Mock only** (no RAG / no OpenAI):

```env
USE_MOCK=true
```

**Direct LLM without retrieval** (optional):

```env
USE_MOCK=false
LLM_PROVIDER=openai
LLM_API_KEY=your_key_here
LLM_MODEL=gpt-4o-mini
```

Start the API:

```powershell
uvicorn app.main:app --reload --port 8000
```

Check:

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

Leave this terminal running.

---

## 3. Frontend (React + Vite) — terminal 3

**Important:** `package.json` is in `frontend-react/`, not in `FrontPage/`.  
If you run `npm install` from `FrontPage` only, you get `ENOENT ... package.json`.

```powershell
cd <repo-root>/FrontPage/frontend-react
nvm use 24.15.0
npm install
npm run dev
```

Open in the browser:

**http://localhost:3000**

Vite proxies `/api/*` to port 8000, so you do **not** need to change the frontend API URL.

Leave this terminal running.

### Node.js via nvm (Windows)

Use the same Node version every time before `npm install` / `npm run dev`:

```powershell
nvm use 24.15.0
node -v
```

You should see `v24.15.0`. If `nvm use` succeeds but `node -v` shows another version (e.g. `v22.x`):

1. Close and reopen the terminal, then run `nvm use 24.15.0` again.
2. Run `npm run dev` from `frontend-react` in that same terminal (do not mix shells).
3. If it still fails, check that nvm’s Node path comes **before** other Node installs in your PATH.

---

## 4. Quick checklist (product RAG + UI)

1. Terminal 1: `rag_api` on **8001** — `/health` OK
2. Terminal 2: FrontPage `uvicorn` on **8000** — `.env` has `RAG_SERVICE_URL` and `USE_MOCK=false`
3. Terminal 3: `npm run dev` on **3000**
4. Browser: http://localhost:3000 — ask a product question (e.g. “How do I use Citrus Bacteria Clear?”)
5. Answer should cite catalog products; enable **Show sources** in the sidebar

If the UI says _“Cannot connect to API”_, terminal 2 (port 8000) is down.

If answers look like mock tomato/wheat text, check `USE_MOCK` is `false` and `RAG_SERVICE_URL` is set; terminal 1 must be running.

---

## Troubleshooting

| Problem                                                   | What to do                                                                                     |
| --------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Cannot connect to API / Vite `ECONNREFUSED` on `/api/ask` | Start `uvicorn` **inside `FrontPage/`** on port 8000; confirm http://localhost:8000/api/health |
| `Could not import module "app.main"`                      | Wrong folder — `cd <repo-root>/FrontPage` before `uvicorn`                                       |
| Frontend won’t start                                      | `cd <repo-root>/FrontPage/frontend-react`, then `nvm use`, `npm install`, `npm run dev`          |
| Wrong Node version                                        | New terminal → `nvm use 24.15.0` → verify with `node -v`                                       |
| Port already in use                                       | Stop the other process on 3000 or 8000, or change Vite/API port in config                      |

---

## Optional: connect your TerraMind RAG scripts later

When you expose a small HTTP endpoint from `Rag_Gen.py` / `Rag_Pc.py`, set in `FrontPage/.env`:

```env
USE_MOCK=false
RAG_SERVICE_URL=http://localhost:8001/query
```

Until then, use `USE_MOCK=true` or `LLM_PROVIDER` + `LLM_API_KEY` as in `README.md`.

---

## Useful commands

| Task                        | Command                                  |
| --------------------------- | ---------------------------------------- |
| API tests                   | `cd <repo-root>/FrontPage` then `pytest tests/ -v`   |
| Production build (frontend) | `cd <repo-root>/FrontPage/frontend-react` then `npm run build` |
| Preview production build    | `npm run preview`                        |

---

## Port summary

| Service           | URL                        |
| ----------------- | -------------------------- |
| Frontend (Vite)   | http://localhost:3000      |
| Backend (FastAPI) | http://localhost:8000      |
| API docs          | http://localhost:8000/docs |

---

## Copy-paste recap (what worked)

**Terminal 1 — RAG**

```powershell
cd <repo-root>
conda activate terramind
uvicorn terramind.api.app:app --reload --port 8001
# legacy: uvicorn rag_api:app --reload --port 8001
```

**Terminal 2 — API**

```powershell
cd <repo-root>/FrontPage
conda activate terramind
uvicorn app.main:app --reload --port 8000
```

**Terminal 3 — UI** (must be `frontend-react`, not `FrontPage`)

```powershell
cd <repo-root>/FrontPage/frontend-react
nvm use 24.15.0
npm install
npm run dev
```

Then open **http://localhost:3000**.
