<div align="center">
  <img src="assets/logo/TM_Logo.png" width="20%" height="20%">
</div>

# TerraMind

TerraMind is an agriculture assistant with a React chat UI, a FastAPI web gateway, and a FastAPI model API for product-catalog RAG, general agriculture RAG, Auto routing, a base LLM baseline, compare mode, image input, and a hidden Advisory workflow.

The current repository is organized for review and local execution:

```text
TerraMind/
├── core/                  # Model API, model registry, RAG pipelines, evaluation reports
├── web/                   # Gateway API (:8000) and React/Vite UI (:3000)
├── data/                  # Product catalog, agriculture corpus, eval fixtures, samples
├── assets/                # Logos, UI backgrounds, architecture images
├── docker/                # Dockerfiles, nginx config, Docker docs
├── docs/                  # Architecture, stack, corpus, validation notes
├── tests/                 # Backend pytest battery
├── docker-compose.yml     # Three-service Docker stack + init-indexes job
├── run_dev.py             # Starts local model API, gateway, and UI
└── .env.example           # Safe environment template; real .env is ignored
```

## Runtime Topology

```text
Browser :3000 -> web gateway :8000 -> model API :8001 -> RAG/LLM backends
```

- UI: `web/frontend-react` served by Vite locally or nginx in Docker.
- Gateway: `web/app/main.py` exposes `/api/*` and proxies model requests.
- Model API: `core.api.app:app` exposes `/query`, streaming, compare, advisory, `/models`, and `/health`.
- Vector stores: `vectorstore/chroma` and `vectorstore/chroma_products` are generated locally and ignored by Git. Docker uses the named volume `terramind-vectorstore`.

## Quick Start

Use the existing conda environment named `terramind`.

```powershell
conda activate terramind
pip install -r requirements.txt
```

Create a local secret file from the safe template:

```powershell
copy .env.example .env
# edit .env and set OPENAI_API_KEY for real RAG
```

Build indexes once:

```powershell
python -m core.rag.product.cli --reset
python -m core.rag.general.cli --reset
```

Start all three local services:

```powershell
python run_dev.py
```

Open http://localhost:3000.

## Docker

```powershell
copy .env.example .env
# edit .env, then build indexes once

docker compose --profile init run --rm init-indexes
docker compose up --build
```

Docker starts `frontend` on host `:3000`, `gateway` on `:8000`, and `model-api` on `:8001`. The model API reads `data/` as a read-only mount and writes indexes to the `terramind-vectorstore` volume.

## Models

| Mode | ID | Knowledge source |
| --- | --- | --- |
| Auto | `auto_rag` | Routes to product RAG, general RAG, or base LLM |
| Product Catalog RAG | `product_rag` | Excel catalog in `data/raw/product_catalog/translated/` |
| Agriculture Knowledge RAG | `general_rag` | PDFs/text under `data/raw/documents/` and `data/raw/reference_text/` |
| Base LLM | `base_llm` | OpenAI only, no retrieval |
| Advisory | `advisory` | Hidden UI mode; general guidance followed by product recommendations |

## Evaluation Results

The values below are copied from `core/evaluation/reports/*.json` and rounded to three decimals.

### LLM-Judge and Similarity Metrics

| Report group | Faithfulness | Factual correctness | Similarity | Questions |
| --- | ---: | ---: | ---: | ---: |
| Base LLM | 0.685 | 0.183 | 0.376 | 41/41 |
| General RAG | 0.959 | 0.203 | 0.782 | 17/17 |
| Product RAG basic | 0.771 | 0.289 | 0.621 | 24/24 |
| Product RAG optimized | 0.946 | 0.454 | 0.671 | 24/24 |

### Heuristic MCQ Checks

| Report group | Accuracy | Correct | Questions |
| --- | ---: | ---: | ---: |
| Base LLM MCQ | 1.000 | 10 | 10/10 |
| General RAG MCQ | 1.000 | 10 | 10/10 |
| Product base-LLM MCQ | 0.800 | 12 | 15/15 |
| Product RAG basic MCQ | 0.600 | 9 | 15/15 |
| Product RAG MCQ | 0.733 | 11 | 15/15 |

## Tests

```powershell
conda activate terramind
pytest tests/ -v
cd web
pytest tests/ -v
```

## Documentation

- `PROJECT_OVERVIEW.md` explains the product behavior and request flows.
- `docs/SYSTEM_ARCHITECTURE.md` covers topology, APIs, and RAG boundaries.
- `docs/FILE_MAP_AND_PIPELINE.md` maps files to runtime behavior.
- `docs/TECH_STACK.md` lists tools and libraries.
- `web/RUN_LOCALLY.md` gives manual three-terminal local setup.
- `docker/QUICKSTART.md` gives Docker setup and troubleshooting.

## Secrets

Do not commit a real `.env`. The repository ships only `.env.example`; `.env`, `web/.env`, and local override files are ignored.
