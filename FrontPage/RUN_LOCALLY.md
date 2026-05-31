# Run FrontPage locally (TerraMind)

You need **two terminals**: one for the **FastAPI backend** (port 8000) and one for the **React frontend** (port 3000). The UI talks to the API through Vite’s proxy (`/api` → `http://localhost:8000`).

---

## Prerequisites

| Tool | Used for |
|------|----------|
| **Python 3.11+** (e.g. conda `terramind`) | Backend API |
| **Node.js** via nvm (e.g. `24.15.0`) | Frontend (Vite + React) |

---

## 1. Backend (FastAPI) — terminal 1

From the repo root:

```powershell
cd C:\Users\Nc47\Desktop\TerraMind\FrontPage
```

Activate your Python env and install deps (once):

```powershell
conda activate terramind
pip install -r requirements.txt
```

Create `.env` (once) if you don’t have it:

```powershell
copy .env.example .env
```

**Easiest first run — mock mode** (no API key; canned tomato/wheat answers):

```env
USE_MOCK=true
```

**Real LLM** (example with OpenAI):

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

## 2. Frontend (React + Vite) — terminal 2

```powershell
cd C:\Users\Nc47\Desktop\TerraMind\FrontPage\frontend-react
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

## 3. Quick checklist (verified flow)

1. Terminal 1: `uvicorn` on **8000** — no errors  
2. Terminal 2: `npm run dev` on **3000** — shows local URL  
3. Browser: http://localhost:3000  
4. Ask a question (e.g. tomato / wheat in mock mode)

If the UI says *“Cannot connect to API”*, the backend is not running or not on port 8000.

**Order matters:** start **uvicorn** (terminal 1) first, then **npm run dev** (terminal 2).

When both are running, the chat UI at http://localhost:3000 should answer (mock mode returns sample tomato/wheat-style replies).

---

## Troubleshooting

| Problem | What to do |
|---------|------------|
| Cannot connect to API | Start `uvicorn` in `FrontPage` on port 8000; confirm http://localhost:8000/api/health |
| Frontend won’t start | `cd frontend-react`, `nvm use 24.15.0`, `node -v`, then `npm install` and `npm run dev` |
| Wrong Node version | New terminal → `nvm use 24.15.0` → verify with `node -v` |
| Port already in use | Stop the other process on 3000 or 8000, or change Vite/API port in config |

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

| Task | Command |
|------|---------|
| API tests | `cd FrontPage` then `pytest tests/ -v` |
| Production build (frontend) | `cd frontend-react` then `npm run build` |
| Preview production build | `npm run preview` |

---

## Port summary

| Service | URL |
|---------|-----|
| Frontend (Vite) | http://localhost:3000 |
| Backend (FastAPI) | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

---

## Copy-paste recap (what worked)

**Terminal 1 — API**

```powershell
cd C:\Users\Nc47\Desktop\TerraMind\FrontPage
conda activate terramind
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — UI**

```powershell
cd C:\Users\Nc47\Desktop\TerraMind\FrontPage\frontend-react
nvm use 24.15.0
npm run dev
```

Then open **http://localhost:3000**.
