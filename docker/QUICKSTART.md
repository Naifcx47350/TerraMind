# TerraMind Docker — quick start (Docker Desktop)

Run the full app (UI + APIs) without installing Python, conda, or Node on your machine.

**Prerequisite:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running (whale icon in the system tray).

---

## Choose your path

| Goal | What you need | Steps |
|------|----------------|-------|
| **Just click around** (mock answers) | Docker Desktop only | Path A below |
| **Real RAG** (product + agriculture knowledge) | Docker Desktop + OpenAI API key | Path B below |
| **Already have a key, no `.env` yet** | Docker Desktop | Path C — UI asks for key in browser |

---

## Path A — Demo with no OpenAI key (easiest)

1. **Clone** the repo and open a terminal in the repo root.

2. **Create `.env`** from the example:

   ```powershell
   copy docker\env.example .env
   ```

   On macOS/Linux:

   ```bash
   cp docker/env.example .env
   ```

   Leave `USE_MOCK=true` in `.env` (that is the default in `env.example`).

3. **Start the stack** (first run downloads images and builds — can take several minutes):

   ```bash
   docker compose up --build
   ```

4. **Open** http://localhost:3000

   - No API key prompt (mock mode).
   - Answers are canned demo text, not live RAG.
   - **Skip** `init-indexes` — not needed for mock mode.

5. **Stop:** press `Ctrl+C` in the terminal, or in Docker Desktop → Containers → stop `terramind`.

---

## Path B — Full RAG with OpenAI key in `.env`

**Do this once before the first real chat** — otherwise model-api rebuilds the corpus on the first question (slow, can cause 502 on key submit).

1. Copy env file and edit:

   ```powershell
   copy docker\env.example .env
   ```

2. Set in `.env`:

   ```env
   USE_MOCK=false
   OPENAI_API_KEY=sk-your-key-here
   ```

3. **Build vector indexes once** (embeddings need your key; may take a few minutes):

   ```bash
   docker compose --profile init run --rm init-indexes
   ```

   You should see `Indexed N document(s)` and `Built new index` / `Loaded existing Chroma index` without errors.

4. **Start the app:**

   ```bash
   docker compose up --build
   ```

5. Open http://localhost:3000 — enter key in browser if not in `.env`, or skip if already in `.env`.

Indexes are stored in Docker volume `terramind-vectorstore` (survives restarts). Re-run step 3 only after changing corpus data.

**PDF log lines** like `Ignoring wrong pointing object` are harmless pypdf warnings, not failures.

---

## Path C — No `.env` key; enter key in the website

If `USE_MOCK=false` and `OPENAI_API_KEY` is empty:

1. Still run `docker compose up --build` (you may need `init-indexes` first for RAG to work after you add a key).
2. Open http://localhost:3000.
3. The **OpenAI key modal** appears (same as local dev).
4. Paste your key → it is sent to the gateway and model API for this session.

This works in Docker the same as locally. The key is **not** baked into the image; it comes from the browser or from `.env`.

---

## What Docker Desktop shows you

After `docker compose up`, under **Containers** you should see:

| Container | Role | Port on your PC |
|-----------|------|-----------------|
| `terramind-frontend-1` | React UI (nginx) | **3000** |
| `terramind-gateway-1` | FrontPage API | **8000** |
| `terramind-model-api-1` | RAG / models | **8001** |

Click a container → **Logs** to debug. **Exec** opens a shell inside a running container (advanced).

---

## Common commands

```bash
docker compose up --build      # build + start (foreground)
docker compose up -d --build   # start in background
docker compose ps              # status
docker compose logs -f gateway # follow logs
docker compose down            # stop
docker compose down -v         # stop + delete index volume (re-run init-indexes)
```

---

## Local dev vs Docker

| | Local (`run_dev.py`) | Docker |
|---|----------------------|--------|
| Install | Python, conda, Node | Docker Desktop only |
| UI | Vite hot reload | Production build |
| Best for | Developing UI/backend | Trying the project on a new machine |

Local setup: [FrontPage/RUN_LOCALLY.md](../FrontPage/RUN_LOCALLY.md)

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `docker compose` not found | Install Docker Desktop; restart terminal |
| Port 3000 / 8000 in use | Stop other apps or change ports in `docker-compose.yml` |
| Key gate but RAG errors after paste | Run `init-indexes` (Path B step 3) |
| Build fails on `npm ci` | Ensure `FrontPage/frontend-react/package-lock.json` exists in repo |
| Empty/mock answers with key set | Check `.env` has `USE_MOCK=false`; restart `docker compose up` |
| `host not found in upstream "gateway"` | Rebuild frontend (`docker compose up --build frontend`); start **all** services with Compose |
| Frontend works but `/api` fails | Do not run the frontend container alone — use `docker compose up` so `gateway` is on the same network |
| UI usable before key modal (Docker) | Rebuild frontend; “Starting TerraMind…” overlay until `/api/config` responds |
| **502 on API key Continue** | Run `init-indexes` once; rebuild model-api + gateway; wait for startup, retry |
| Slow start / corpus reload logs | Missing indexes in volume — run `init-indexes` with `OPENAI_API_KEY` in `.env` |
| `Ignoring wrong pointing object` | Harmless pypdf PDF warnings — safe to ignore |

Concepts and file layout: see sections below in this folder’s longer guide, or read [README.md](README.md) from the top.
