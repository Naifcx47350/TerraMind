# TerraMind Docker — quick start

Run the full app (UI + two APIs) with **Docker Desktop only** — no Python, conda, or Node on the host.

**Prerequisite:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

Longer explanation of Docker files: [README.md](README.md) · Local dev without Docker: [FrontPage/RUN_LOCALLY.md](../FrontPage/RUN_LOCALLY.md)

---

## Docker setup (clone → run)

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd TerraMind
```

All commands below assume your shell is in the **repo root** (the folder that contains `docker-compose.yml`).

---

### 2. Create `.env` at the project root

**One file only:** `<repo-root>/.env` — same directory as `docker-compose.yml`.

**Not** `docker/.env`. Docker Compose does **not** read secrets from the `docker/` folder.

Copy the template (optional if you write `.env` yourself):

```bash
# Windows
copy docker\env.example .env

# macOS / Linux
cp docker/env.example .env
```

Edit `<repo-root>/.env`. For **real RAG** (recommended):

```env
USE_MOCK=false
OPENAI_API_KEY=sk-your-key-here
```

You do **not** need `RAG_SERVICE_URL` in `.env` for Docker — `docker-compose.yml` sets `http://model-api:8001/query` for the gateway container automatically.

| Variable | Required? | Notes |
|----------|-----------|--------|
| `OPENAI_API_KEY` | For RAG + `init-indexes` | Never committed; not baked into images |
| `USE_MOCK` | No | `true` = demo answers, no key, skip index build |
| `RAG_SERVICE_URL` | No in Docker | Compose sets this internally |

**Verify Compose sees your `.env`** (from repo root):

```bash
docker compose config | findstr OPENAI_API_KEY    # Windows
docker compose config | grep OPENAI_API_KEY       # macOS / Linux
```

If the value is empty, you are in the wrong directory or the variable name is misspelled.

---

### 3. One-time index build (real RAG only)

**Run once** after clone (or after `docker compose down -v`). Embeddings need `OPENAI_API_KEY` in repo-root `.env`.

```bash
docker compose --profile init run --rm init-indexes
```

Expect output like `Indexed N document(s)` and `Built new index` or `Loaded existing Chroma index`.  
Lines like `Ignoring wrong pointing object` are harmless **pypdf** PDF warnings.

Indexes are stored in the Docker volume **`terramind-vectorstore`** (persists across restarts).  
Corpus files under **`data/`** stay on your machine (cloned with the repo) and are **mounted** into `model-api` / `init-indexes` — they are not baked into the image.  
Re-run this step only if you wipe the volume or change corpus data under `data/`.

**Skip this step** if `USE_MOCK=true` (demo mode).

---

### 4. Build and start all three containers

```bash
docker compose up --build
```

Background mode:

```bash
docker compose up -d --build
```

Open **http://localhost:3000**

| Service | Container role | Host port |
|---------|------------------|-----------|
| `frontend` | React UI (nginx) | **3000** |
| `gateway` | FrontPage API | **8000** |
| `model-api` | RAG / models | **8001** |

**Always start all three with Compose** — do not run the frontend image alone in Docker Desktop (nginx needs the `gateway` hostname on the Compose network).

Stop: `Ctrl+C` in the terminal, or Docker Desktop → Containers → stop **terramind**.

---

### 5. API key behavior (what new users should expect)

| Situation | What happens |
|-----------|----------------|
| `OPENAI_API_KEY` in repo-root `.env` | Key modal may be **skipped** on your machine (injected at runtime) |
| No key in `.env`, `USE_MOCK=false` | **Key modal** in the browser (intended for shared / cloned setups) |
| `USE_MOCK=true` | No key modal; canned demo answers |
| Pulled images from Docker Hub | **No key inside images** — each user uses their own `.env` or the modal |

Keys typed in the browser apply to **running** containers only (not baked into images).  
Sharing the three images does **not** share your API key.

---

## Quick paths

### Path A — Demo (no OpenAI account)

In repo-root `.env`:

```env
USE_MOCK=true
```

Then:

```bash
docker compose up --build
```

No `init-indexes`. Open http://localhost:3000.

---

### Path B — Full RAG (recommended)

1. Repo-root `.env` with `USE_MOCK=false` and `OPENAI_API_KEY=...`
2. `docker compose --profile init run --rm init-indexes` **once**
3. `docker compose up --build`
4. Open http://localhost:3000

---

### Path C — Key in the website only

Repo-root `.env`:

```env
USE_MOCK=false
```

(leave `OPENAI_API_KEY` empty)

1. Run `init-indexes` **after** you have a key (embeddings require it — use Path B step 2 with key in `.env` first, or add key to `.env` then run `init-indexes`)
2. `docker compose up --build`
3. Paste key in the modal when prompted

---

## Commands to know

```bash
# Daily
docker compose up --build       # build (if needed) + start (foreground, logs here)
docker compose up -d --build    # start in background
docker compose down             # stop containers
docker compose ps               # status
docker compose logs -f          # all logs
docker compose logs -f gateway  # one service

# Indexes
docker compose --profile init run --rm init-indexes   # once per machine / volume
docker compose down -v          # wipe index volume → run init-indexes again

# After code changes
docker compose build frontend   # UI changed
docker compose build gateway    # FrontPage API changed
docker compose build model-api  # RAG / models changed
docker compose up --build       # rebuild everything

# Debug
docker compose config           # resolved config (checks .env)
docker images                   # local image tags
```

---

## Using pre-built images (Docker Hub)

If you publish images (e.g. `naifcx4735/terramind-*:1.0`), others still need:

- `docker-compose.yml` from the repo (or equivalent)
- Their own repo-root `.env` (optional)
- `init-indexes` once for real RAG

Images contain **code only** — not `.env`, not vector indexes, not API keys.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `docker compose` not found | Install Docker Desktop; restart terminal |
| Wrong directory | `cd` to repo root (where `docker-compose.yml` is) |
| Empty `OPENAI_API_KEY` in `docker compose config` | Fix repo-root `.env`; exact name `OPENAI_API_KEY` |
| Port 3000 / 8000 in use | Stop other apps or change ports in `docker-compose.yml` |
| `host not found in upstream "gateway"` | Rebuild frontend; start full stack with `docker compose up` |
| **502 on API key Continue** | Run `init-indexes`; wait for model-api to finish starting; retry |
| Slow start / corpus loading in logs | Run `init-indexes` once; ensure volume has indexes |
| Key gate but RAG errors | Run `init-indexes` with key in `.env` |
| Empty/mock answers with real key | Set `USE_MOCK=false`; restart compose |
| `Ignoring wrong pointing object` | Harmless PDF parser warnings |

---

## Local dev vs Docker

| | `run_dev.py` / RUN_LOCALLY | Docker |
|---|---------------------------|--------|
| Install | Python, conda, Node | Docker Desktop |
| UI | Vite hot reload | Production build in nginx |
| Best for | Day-to-day development | Clone → run anywhere |
