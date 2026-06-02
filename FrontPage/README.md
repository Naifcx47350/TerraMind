# TerraMind — Web Application (FrontPage)

Agricultural chat UI and API gateway for the TerraMind **three-model** stack (product RAG, general RAG, base LLM).

**Full technical documentation:** [../docs/PROJECT_OVERVIEW.md](../docs/PROJECT_OVERVIEW.md)  
**Architecture summary:** [ARCHITECTURE.md](./ARCHITECTURE.md)  
**Local run guide:** [RUN_LOCALLY.md](./RUN_LOCALLY.md)

---

## What users see

- Chat interface with sidebar conversations (saved in the browser)
- **Model dropdown** (top right): Product Catalog RAG, Agriculture Knowledge RAG, Base LLM
- **Compare** button: same question → three answers in parallel columns
- Image upload for crop/plant diagnosis (vision via **gpt-4o-mini**)
- Optional source chips, dark/light mode, Arabic RTL

---

## Project structure

```text
FrontPage/
├── app/
│   ├── main.py                  # FastAPI :8000
│   ├── config.py                # .env, RAG URL, vision defaults
│   ├── routers/
│   │   ├── ask.py               # POST /api/ask, /api/ask/compare
│   │   ├── models.py            # GET /api/models
│   │   ├── health.py            # GET /api/health
│   │   └── history.py           # GET/DELETE /api/history (global log)
│   ├── schemas/ask.py
│   └── services/rag_service.py  # Proxy to :8001, vision, mock
├── frontend-react/
│   ├── src/App.jsx              # UI (sessions, compare, logo)
│   └── public/TM_Logo.png       # Logo served at /TM_Logo.png
├── ARCHITECTURE.md
├── RUN_LOCALLY.md
└── requirements.txt
```

Repo root (not inside `FrontPage/`):

- `rag_api.py` — model API on **port 8001**
- `models/` — `product_rag`, `general_rag`, `base_llm`
- `Rag_Pc.py`, `Rag_Gen.py` — Chroma indexes

---

## Quick start

See **[RUN_LOCALLY.md](./RUN_LOCALLY.md)** for all three terminals.

```powershell
# 1) Model API (from repo root)
uvicorn rag_api:app --reload --port 8001

# 2) This API (from FrontPage/)
uvicorn app.main:app --reload --port 8000

# 3) UI
cd frontend-react && npm run dev
```

Open http://localhost:3000

---

## Environment

Create `FrontPage/.env` (or use defaults + root `OPENAI_API_KEY`):

```env
USE_MOCK=false
RAG_SERVICE_URL=http://localhost:8001/query
REQUEST_TIMEOUT=90
```

Vision uses **gpt-4o-mini** automatically when `OPENAI_API_KEY` is set (no extra vars required).

Optional overrides:

```env
VISION_PROVIDER=openai
VISION_API_KEY=sk-...
VISION_MODEL=gpt-4o-mini
```

---

## API endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/ask` | Single model (`model` in body) |
| POST | `/api/ask/compare` | All three models in parallel |
| GET | `/api/models` | Model list for UI dropdown |
| GET | `/api/health` | Backend status |
| GET | `/api/history` | In-memory global Q&A log |
| DELETE | `/api/history` | Clear global log |

### POST /api/ask (example)

```json
{
  "question": "How do I use 10% Glufosinate-Ammonium?",
  "model": "product_rag",
  "history": [
    { "role": "user", "content": "Earlier question" },
    { "role": "assistant", "content": "Earlier answer" }
  ],
  "image_base64": "optional",
  "image_mime": "image/jpeg"
}
```

### POST /api/ask/compare

Same body (no `model` required). Returns `results[]` with one entry per mode.

---

## How requests flow

1. React sends question + **history** (last 20 messages) + optional image.
2. FrontPage may run **vision** once → `image_analysis` text.
3. FrontPage calls `http://localhost:8001/query` or `/query/compare`.
4. Model API runs `Rag_Pc` / `Rag_Gen` / `base_llm` via `models/`.
5. Answer + sources return to the UI; session saved to **localStorage**.

---

## Features

| Feature | Implementation |
|---------|----------------|
| Three models | `model` id → `rag_api` → `models/` |
| Compare | `/api/ask/compare` → 3-column UI |
| Images | `models/vision.py` + prompt injection for all modes |
| Session memory | `history` in API body; RAG uses `models/conversation.py` |
| Persist chats | `localStorage` key `terramind_sessions_v1` |
| Mock mode | `USE_MOCK=true` — no port 8001 needed |

---

## Optional LLM providers

If `RAG_SERVICE_URL` is unset, FrontPage can call external LLMs directly (Groq, Anthropic, etc.) via `LLM_PROVIDER` in `.env`. **Recommended path for TerraMind MVP** is RAG on port **8001**.

---

## Tests

```bash
cd FrontPage
pytest tests/ -v
```

---

## Docker

```bash
docker build -t terramind .
docker run -p 8000:8000 --env-file .env terramind
```

Note: Docker here runs the FrontPage API only; you still need `rag_api` and built vector indexes for full RAG.
