# TerraMind Docker — learning guide

**Orchestration** (start all services together) lives in the repo-root `docker-compose.yml`. This folder holds **Dockerfiles** for each service.

---

## 1. What Docker is doing here

| Concept           | Plain English                              | TerraMind                              |
| ----------------- | ------------------------------------------ | -------------------------------------- |
| **Image**         | Frozen recipe + filesystem snapshot        | e.g. `terramind-model-api`             |
| **Container**     | A running instance of an image             | one model-api process on :8001         |
| **Dockerfile**    | Instructions to build an image             | `docker/model-api/Dockerfile`          |
| **Build context** | Files Docker can `COPY`                    | repo root (`.`), minus `.dockerignore` |
| **Compose**       | Run several containers + network + volumes | `docker-compose.yml`                   |

Locally you run **3 processes** (`run_dev.py`):

```
Browser → :3000 React (Vite)
            ↓ /api/*
          :8000 FrontPage gateway
            ↓ HTTP
          :8001 Model API (RAG)
```

In Docker you run **3 containers** on an internal network:

```
Browser → :3000 frontend (nginx + built React)
            ↓ /api/*
          gateway:8000
            ↓ http://model-api:8001/query
          model-api:8001
```

Service names (`model-api`, `gateway`) are **hostnames inside the Compose network**. That is why `RAG_SERVICE_URL` uses `http://model-api:8001/query`, not `localhost`.

---

## 2. File map

```text
TerraMind/
├── docker-compose.yml       ← start everything: docker compose up --build
├── .dockerignore            ← exclude junk/secrets from build context
├── docker/
│   ├── README.md            ← this file
│   ├── model-api/Dockerfile ← Python RAG API (:8001)
│   ├── gateway/Dockerfile   ← FrontPage FastAPI (:8000)
│   └── frontend/
│       ├── Dockerfile       ← Node build + nginx (:80 → host :3000)
│       └── nginx.conf       ← proxy /api to gateway
```

**Old root `Dockerfile`:** was a single-service stub with wrong paths. Use Compose instead.

---

## 3. Dockerfile anatomy (read one line at a time)

Example from `model-api/Dockerfile`:

```dockerfile
FROM python:3.11-slim          # Start from official Python base image
WORKDIR /app                   # All following paths are inside /app
RUN apt-get update && ...      # Run shell commands (install compilers)
COPY requirements.txt .        # Copy from build context → image
RUN pip install -r ...         # Creates a layer (cached until requirements change)
COPY terramind/ terramind/     # Your source code layer
EXPOSE 8001                    # Documentation port (does not publish by itself)
CMD ["python", "-m", "uvicorn", ...]  # Default command when container starts
```

**Order matters for caching:** put slow, rarely-changing steps (`pip install`) **before** frequently-changing `COPY` of source.

**Multi-stage** (`frontend/Dockerfile`): first stage builds with Node; second stage copies only `dist/` into nginx → smaller final image, no Node in production.

---

## 4. `.dockerignore` — why it exists

Like `.gitignore`, but for `docker build`. Ignored files are **not sent** to the Docker daemon.

We exclude:

- `.env` / secrets → inject at runtime with Compose
- `node_modules/` → installed inside the frontend build stage
- `vectorstore/` → persisted in a **volume**, not baked into the image
- docs, `.git`, caches → smaller/faster builds

If `COPY` fails with "file not found", check whether `.dockerignore` excluded it.

---

## 5. `docker-compose.yml` — the important keys

| Key                                         | Purpose                                                |
| ------------------------------------------- | ------------------------------------------------------ |
| `services:`                                 | Each container (model-api, gateway, frontend)          |
| `build.context` + `dockerfile`              | Where to run `docker build`                            |
| `ports: "3000:80"`                          | Host port 3000 → container port 80                     |
| `environment` / `env_file`                  | Config and secrets                                     |
| `depends_on` + `condition: service_healthy` | Wait until `/health` OK                                |
| `volumes:`                                  | Data that survives container restarts (Chroma indexes) |
| `profiles: ["init"]`                        | Optional one-shot services (`init-indexes`)            |

---

## 6. Commands to run (any OS with Docker Desktop / Engine)

From repo root:

```bash
# 1. Secrets
cp docker/env.example .env
# Edit .env → set OPENAI_API_KEY

# 2. First time: build vector indexes (needs OpenAI for embeddings)
# Runs: python -m terramind.rag.product.cli --reset
#       python -m terramind.rag.general.cli --reset
docker compose --profile init run --rm init-indexes

# 3. Build images + start all services
docker compose up --build

# 4. Open UI
# http://localhost:3000
```

Other useful commands:

```bash
docker compose ps              # running containers
docker compose logs -f gateway # tail one service
docker compose down            # stop containers
docker compose down -v         # stop + delete vectorstore volume (re-run init-indexes)
docker compose build model-api # rebuild one image
```

---

## 7. Dev vs Docker production UI

|            | Local dev                        | Docker                              |
| ---------- | -------------------------------- | ----------------------------------- |
| Frontend   | `npm run dev` (Vite, hot reload) | `npm run build` → nginx             |
| API reload | `--reload` on uvicorn            | restart container after code change |
| API URL    | Vite proxy `/api` → :8000        | nginx proxy `/api` → gateway        |

For daily UI work, keep using `python run_dev.py`. Use Docker when you want **“clone repo → compose up → works”** on another machine.

---

## 8. Troubleshooting

| Symptom                   | Likely cause                                                        |
| ------------------------- | ------------------------------------------------------------------- |
| Gateway unhealthy         | model-api not up; check `docker compose logs model-api`             |
| Empty / mock answers      | `USE_MOCK=true` or missing `OPENAI_API_KEY`                         |
| Slow start / “Starting TerraMind…” in UI | Frontend up before gateway — wait for healthy services; normal on first boot |
| RAG errors / no retrieval | Indexes not built → run `init-indexes` profile                      |
| Frontend 502 on `/api`    | gateway not healthy yet; wait or check logs                         |
| Build slow                | first build downloads base images + pip/npm; later builds use cache |

---

## 9. What to try next

1. Change `gateway` `REQUEST_TIMEOUT` via Compose `environment`.
2. Add a fourth service (e.g. Redis) in `docker-compose.yml`.
3. Split dev Compose (`docker-compose.dev.yml`) with volume-mount source for hot reload.
4. Push images to a registry (Docker Hub / GHCR) and deploy on a VPS.

---

## 10. Relation to local docs

- Local run (no Docker): [FrontPage/RUN_LOCALLY.md](../FrontPage/RUN_LOCALLY.md)
- Architecture: [docs/SYSTEM_ARCHITECTURE.md](../docs/SYSTEM_ARCHITECTURE.md)
