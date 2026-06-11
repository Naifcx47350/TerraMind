# terramind/ — Model API, Models, and RAG

`terramind/` is the backend package behind the TerraMind model service. It owns the
FastAPI model API on port `8001`, the model registry, routing logic, streaming
orchestration, image analysis helpers, and the general/product RAG packages.

The browser does not call this package directly in normal use. Requests flow through
the FrontPage gateway first:

```text
React UI (:3000) → FrontPage API (:8000) → terramind Model API (:8001)
```

For the full system view, see [docs/SYSTEM_ARCHITECTURE.md](../docs/SYSTEM_ARCHITECTURE.md).

---

## Package layout

```text
terramind/
├── api/
│   └── app.py              # FastAPI model API (:8001)
├── models/
│   ├── __init__.py         # Model registry, run_model(), run_advisory()
│   ├── auto_rag.py         # Default mode; routes to product/general/base
│   ├── router.py           # Routing rules, dual-index probes, meta handling
│   ├── product_rag.py      # Product catalog answer adapter
│   ├── general_rag.py      # Agriculture knowledge answer adapter
│   ├── base_llm.py         # OpenAI answer without retrieval
│   ├── advisory.py         # Combined general + product advisory answer
│   ├── streaming.py        # NDJSON streaming for single/compare/advisory flows
│   ├── vision.py           # Crop/image analysis with OpenAI vision
│   ├── conversation.py     # Chat history formatting for prompts
│   └── image_context.py    # Inject image analysis into model prompts
├── rag/
│   ├── general/            # General agriculture RAG pipeline
│   ├── product/            # Product catalog RAG package
│   ├── llm_stream.py       # LangChain token streaming helpers
│   ├── scoring.py          # Retrieval scores + confidence labels
│   └── source_display.py   # Friendly source names for the UI
├── meta_questions.py       # Greetings, identity, and capability questions
└── README.md
```

---

## Model API (`terramind.api.app`)

The model API is the service that actually runs the LLM and RAG logic. It can be
started directly for backend testing:

```powershell
cd <repo-root>
uvicorn terramind.api.app:app --reload --port 8001
```

In normal local development, `python run_dev.py` starts this API together with the
FrontPage gateway and React UI. In Docker, the same app runs inside the `model-api`
container.

Important endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Lightweight service status and index presence |
| `GET` | `/models` | Model picker metadata for the UI |
| `POST` | `/query` | One model, JSON response |
| `POST` | `/query/stream` | One model, NDJSON stream (`status`, `token`, `done`) |
| `POST` | `/query/compare` | Product, general, and base LLM in parallel |
| `POST` | `/query/advisory` | Combined advisory response |
| `POST` | `/query/advisory/stream` | Advisory response as an NDJSON stream |

`rag_api.py` at the repo root is only a compatibility shim that re-exports this app.

---

## Models

Model modes are registered in `terramind/models/__init__.py`. Each mode returns the
same response shape so the gateway and UI can render sources, confidence, routed mode,
and answer text consistently.

| Model ID | Module | Description |
| --- | --- | --- |
| `auto_rag` | `models/auto_rag.py` + `models/router.py` | Default mode. Detects meta questions first, then routes agronomy questions to product RAG, general RAG, or base LLM. |
| `general_rag` | `models/general_rag.py` | Uses public agriculture references for IPM, soil, crop rotation, pesticide stewardship, and field guidance. |
| `product_rag` | `models/product_rag.py` | Uses the company product catalog for product names, usage, dosage, crops, ingredients, and label-style details. |
| `base_llm` | `models/base_llm.py` | Uses OpenAI chat only, with no retrieval. Useful as a baseline and fallback for conversational/meta questions. |
| `advisory` | `models/advisory.py` + `run_advisory()` | Hidden UI mode. Combines general guidance first, then product-specific recommendations when needed. |

Shared model helpers:

- `streaming.py` emits NDJSON events used by the chat UI streaming experience.
- `vision.py` analyzes uploaded crop images once, then passes text context into the selected model.
- `conversation.py` formats previous messages so follow-up questions keep useful context.
- `meta_questions.py` prevents greetings and identity questions from triggering unnecessary Chroma retrieval.

---

## RAG subsystems

### General agriculture RAG

Location: `terramind/rag/general/`

Purpose: answer broad agriculture questions from trusted public references, such as
IPM, GAP, soil health, cover crops, crop rotation, and pesticide stewardship.

Data source:

```text
data/raw/documents/   # PDF corpus
data/raw/reference_text/   # optional text references
data/sample/          # allowlisted sample references
```

Pipeline shape:

```text
load PDFs/text → chunk → embed → Chroma → retrieve/rerank → generate answer
```

Index path:

```text
vectorstore/chroma/
```

Build/reset command:

```powershell
python -m terramind.rag.general.cli --reset
```

Useful CLI options include `--inspect` and `--eval-retrieval`.

### Product catalog RAG

Location: `terramind/rag/product/`

Purpose: answer company product catalog questions from the Excel catalog. This is the
only RAG path that should provide product-specific dosage, crop labels, product IDs,
ingredients, and manual-style catalog details.

Data source:

```text
data/raw/product_catalog/translated/product_catalog_en.xlsx
data/raw/product_catalog/translated/product_categories_en.xlsx
```

Pipeline shape:

```text
load Excel rows → build product documents → chunk → embed → Chroma → retrieve/rerank → generate answer
```

Index path:

```text
vectorstore/chroma_products/
```

Build/reset command:

```powershell
python -m terramind.rag.product.cli --reset
```

The archived legacy script is kept under `archive/Rag_Pc_legacy.py` for reference only.

---

## Indexes, data, and Docker

Both RAG systems need indexes before real retrieval works:

```powershell
python -m terramind.rag.product.cli --reset
python -m terramind.rag.general.cli --reset
```

Local development writes indexes under `vectorstore/` in the repo root. Docker uses
the named volume `terramind-vectorstore` instead.

Important Docker behavior:

- `data/` is mounted into `model-api` and `init-indexes`; it is not baked into the images.
- The `model-api` image contains `terramind/`; corpus files are mounted at runtime.
- If the Docker volume is deleted with `docker compose down -v`, run `init-indexes` again.

Docker index command:

```powershell
docker compose --profile init run --rm init-indexes
```

---

## Streaming example

```powershell
curl -N -X POST http://localhost:8001/query/stream -H "Content-Type: application/json" -d "{\"question\":\"What is IPM?\",\"model\":\"auto_rag\"}"
```

Each line is JSON:

- `status` — routing/retrieval progress
- `token` — partial LLM output
- `done` — final answer metadata, sources, confidence, and routing info

---

## Boundaries

- `terramind/` owns model execution and RAG logic.
- `FrontPage/app/` owns the user-facing gateway API and browser key sync.
- `FrontPage/frontend-react/` owns UI state, rendering, sessions, and user controls.
- `data/` owns corpus files; `vectorstore/` owns generated indexes.

More detail:

- [docs/SYSTEM_ARCHITECTURE.md](../docs/SYSTEM_ARCHITECTURE.md)
- [docs/TECH_STACK.md](../docs/TECH_STACK.md)
- [docs/GENERAL_RAG_CORPUS.md](../docs/GENERAL_RAG_CORPUS.md)
- [docs/PROJECT_STATUS.md](../docs/PROJECT_STATUS.md)
