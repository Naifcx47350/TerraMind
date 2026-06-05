# TerraMind — Web Application (FrontPage)

Agricultural chat UI and API gateway for TerraMind (**Auto**, product RAG, general RAG, base LLM, hidden **Advisory**).

**Full technical documentation:** [../docs/PROJECT_OVERVIEW.md](../docs/PROJECT_OVERVIEW.md)  
**Architecture:** [../docs/SYSTEM_ARCHITECTURE.md](../docs/SYSTEM_ARCHITECTURE.md)  
**Local run guide:** [RUN_LOCALLY.md](./RUN_LOCALLY.md)

---

## What users see

- Chat interface with sidebar conversations (saved in the browser)
- **Model dropdown** (top right): Auto (default), Agriculture Knowledge RAG, Product Catalog RAG, Base LLM — **not** Advisory (hidden; see below)
- **Streaming answers** — status + token-by-token generation in the chat bubble
- **Hidden Advisory** — click the TerraMind logo **6 times** within 2.5s to unlock **Advisory (General + Product)**
- **Compare** button: same question → three answers in parallel columns
- Image upload for crop/plant diagnosis (vision via **gpt-4o-mini**)
- Optional source chips, dark/light mode, Arabic RTL
- **Stylized themes** — per-appearance wallpapers, decor, and settings; see [../assets/README.md](../assets/README.md)

---

## Project structure

```text
FrontPage/
├── app/
│   ├── main.py                  # FastAPI :8000
│   ├── config.py                # .env, RAG URL, vision defaults
│   ├── routers/
│   │   ├── ask.py               # POST /api/ask/stream, /compare, /advisory/stream
│   │   ├── models.py            # GET /api/models
│   │   ├── health.py            # GET /api/health
│   │   └── history.py           # GET/DELETE /api/history (global log)
│   ├── schemas/ask.py
│   └── services/rag_service.py  # Proxy to :8001, vision, mock
├── frontend-react/
│   ├── src/App.jsx              # UI (streaming, sessions, compare, logo unlock)
│   └── public/TM_Logo.png       # Logo served at /TM_Logo.png
├── RUN_LOCALLY.md
└── requirements.txt
```

Repo root (not inside `FrontPage/`):

- `terramind/api/app.py` or `rag_api.py` — model API on **port 8001**
- `terramind/models/` — `auto_rag`, `product_rag`, `general_rag`, `base_llm`
- `Rag_Pc.py` — product Chroma index; `terramind/rag/general/` — general index
- `run_dev.py` — start all three services

---

## Quick start

See **[RUN_LOCALLY.md](./RUN_LOCALLY.md)** for all three terminals. Use **`<repo-root>`** for your clone path (see path convention there).

```powershell
# 1) Model API — <repo-root>
cd <repo-root>
uvicorn terramind.api.app:app --reload --port 8001

# 2) FrontPage API — <repo-root>/FrontPage
cd <repo-root>/FrontPage
uvicorn app.main:app --reload --port 8000

# 3) UI — <repo-root>/FrontPage/frontend-react
cd <repo-root>/FrontPage/frontend-react
npm run dev
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
| POST | `/api/ask/stream` | **Default UI** — NDJSON stream (status, tokens, done) |
| POST | `/api/ask` | Single model (full JSON; scripts/tests) |
| POST | `/api/ask/advisory/stream` | Hidden Advisory mode stream |
| POST | `/api/ask/advisory` | Advisory full JSON |
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
3. FrontPage proxies **NDJSON** from `http://localhost:8001/query/stream` (or `/query/advisory/stream`).
4. Model API streams routing/retrieval status, then LLM tokens, then `done` metadata.
5. UI finalizes the bot message; session saved to **localStorage**.

---

## Features

| Feature | Implementation |
|---------|----------------|
| Models | `model` id → `terramind.api.app` → `terramind.models` / `streaming.py` |
| Streaming | `/api/ask/stream` → NDJSON; status + tokens in `App.jsx` |
| Hidden Advisory | 6× logo click → `sessionStorage`; `/api/ask/advisory/stream` |
| Auto routing | `router.py` → product, general, or **base LLM** (meta questions) |
| Compare | `/api/ask/compare` → 3-column UI (non-streaming) |
| Images | `terramind.models.vision` + prompt injection for all modes |
| Session memory | `history` in API body; RAG uses `terramind.models.conversation` |
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
