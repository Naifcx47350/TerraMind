# TerraMind — System Architecture

**Status:** Current as of May 2026. This file is the **canonical architecture reference** — update it when the stack or boundaries change (e.g. after migrations, new services, or deployment).

**Related (not duplicated here):** feature walkthrough → [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md); file-by-file map → [FILE_MAP_AND_PIPELINE.md](./FILE_MAP_AND_PIPELINE.md); local run → [FrontPage/RUN_LOCALLY.md](../FrontPage/RUN_LOCALLY.md).

---

## 1. Purpose

TerraMind is a **multi-mode agriculture assistant**: users ask questions in a web chat, optionally attach crop images, and choose how answers are produced — company product catalog (RAG), public agriculture references (RAG), plain LLM baseline, or a **combined advisory** path (general then product).

Architecture is a **three-process dev stack** (React UI → BFF API → Model API) with **two on-disk vector indexes** and **one shared OpenAI stack** for chat, embeddings, and vision.

---

## 2. Runtime topology

| Layer | Port | Entry | Role |
|-------|------|-------|------|
| **React UI** | 3000 | `FrontPage/frontend-react` (Vite) | Chat, compare grid, model picker, sessions, sources, Markdown answers |
| **FrontPage API** | 8000 | `FrontPage/app/main.py` | BFF: vision (optional), proxy to Model API, mock fallback |
| **Model API** | 8001 | `terramind.api.app:app` | Route to model backends; compare & advisory orchestration |

**Dev orchestration:** `python run_dev.py` from repo root starts all three.

**Browser → API path:** Vite proxies `/api/*` → `http://localhost:8000`. The UI does not call port 8001 directly in dev.

```mermaid
flowchart TB
  subgraph browser [Browser :3000]
    UI[React App.jsx]
    LS[(localStorage sessions)]
    UI --- LS
  end

  subgraph fp [FrontPage :8000]
    Ask[/api/ask]
    Cmp[/api/ask/compare]
    Adv[/api/ask/advisory]
    RAGSvc[rag_service.py]
    Ask --> RAGSvc
    Cmp --> RAGSvc
    Adv --> RAGSvc
  end

  subgraph model [Model API :8001]
    Q[/query]
    QC[/query/compare]
    QA[/query/advisory]
    Reg[terramind.models]
    Q --> Reg
    QC --> Reg
    QA --> Reg
  end

  subgraph knowledge [On-disk knowledge]
    CP[(chroma_products)]
    CG[(chroma general)]
    Excel[data/raw/text catalog]
    PDFs[data/raw/documents]
  end

  subgraph openai [OpenAI]
    Chat[gpt-4o-mini]
    Emb[text-embedding-3-small]
    Vis[vision]
  end

  UI -->|/api/*| fp
  RAGSvc -->|httpx| model
  Reg --> CP
  Reg --> CG
  CP --> Excel
  CG --> PDFs
  Reg --> Chat
  CP --> Emb
  CG --> Emb
  RAGSvc --> Vis
```

---

## 3. Request flows

### 3.1 Single model

1. User sends message (+ optional image) from React.
2. `POST /api/ask` → `FrontPage/app/services/rag_service.py`.
3. If image present and no pre-analysis: **one** vision call (`terramind.models.vision`).
4. `POST http://localhost:8001/query` with `{ question, model, history, image_analysis?, … }`.
5. `terramind.models.run_model(model_id, …)` → mode-specific `answer()`.
6. Uniform JSON: `answer`, `sources`, `confidence`, `retrieved_chunks`, `system`.

### 3.2 Compare (three models in parallel)

1. UI enables Compare → `POST /api/ask/compare`.
2. FrontPage runs vision **once**, then `POST /query/compare`.
3. Model API: `asyncio.gather` over `product_rag`, `general_rag`, `base_llm`.
4. UI renders three columns (same question, three answers).

### 3.3 Advisory (general + product)

1. UI model id `advisory` → `POST /api/ask/advisory`.
2. `POST /query/advisory` → `terramind.models.run_advisory()`.
3. **Sequential:** `general_rag` first, then `product_rag` with a shortened general summary appended to the product question.
4. Merged answer returned for the chat bubble; payload includes `general` and `product` parts.

---

## 4. Model layer

Registry: `terramind/models/__init__.py` (`MODEL_REGISTRY`, `run_model`, `run_advisory`).

| UI / API `model` | Backend module | Retrieval | Vector store |
|------------------|----------------|-----------|--------------|
| `auto_rag` (**default**) | `terramind.models.auto_rag` → `router.py` | One of product or general | Probed both; answers one |
| `product_rag` | `terramind.models.product_rag` | Yes — catalog rows | `vectorstore/chroma_products/` |
| `general_rag` | `terramind.models.general_rag` | Yes — public PDFs + sample text | `vectorstore/chroma/` |
| `base_llm` | `terramind.models.base_llm` | No | — |
| `advisory` (UI only) | `run_advisory` in `__init__.py` | Both chains above | Both stores |

**Auto routing:** `route_question()` uses top-1 relevance on each index plus keyword hints; response includes `routed_to` and `router_reason`. Compare mode still runs only the three fixed backends (not Auto).

**Shared cross-cutting:**

| Concern | Location |
|---------|----------|
| Chat history in prompts | `terramind/models/conversation.py` |
| Retrieval vs generation query split (general) | `build_retrieval_query` / `build_prompt_question` |
| Image context in prompts | `terramind/models/image_context.py` |
| Friendly source titles | `terramind/rag/source_display.py` |

**LLM defaults:** OpenAI `gpt-4o-mini` (chat), `text-embedding-3-small` (embeddings). Configured via env / RAG config modules.

---

## 5. RAG subsystems

### 5.1 General agriculture RAG (`terramind/rag/general/`)

**Corpus:** `data/raw/documents/*.pdf`, optional `.md`/`.txt` from `data/raw/text/` (with exclusions), allowlisted sample under `data/sample/`.

**Pipeline:**

```
discover → load (pypdf) → chunk → embed → Chroma
                ↓
         retrieve (MMR + topic boost + lexical rerank)
                ↓
         generate (LangChain + OpenAI)
```

**Index CLI:** `python -m terramind.rag.general.cli --reset | --inspect | --eval-retrieval`

**Package modules:** `config`, `load`, `chunk`, `store`, `retrieve`, `hybrid`, `topics`, `generate`, `pipeline`, `eval`, `cli`.

### 5.2 Product catalog RAG (`terramind/rag/product/`)

**Corpus:** Excel catalog in `data/raw/text/` (e.g. `ProductCatalog(En).xlsx`).

**Pipeline:** Same shape as general (load → chunk → store → retrieve → generate), exposed via `terramind.rag.product` and `terramind.models.product_rag`.

**Index:** Built via product CLI / pipeline (see `terramind/rag/product/cli.py`). Legacy root script `Rag_Pc.py` may still exist for teammates during migration; **active path** is the `terramind.rag.product` package.

### 5.3 Separation of concerns

| Layer | General | Product |
|-------|---------|---------|
| Purpose | Public IPM, GAP, soil, pesticide policy | Company labels, dosage, crops |
| Index path | `vectorstore/chroma/` | `vectorstore/chroma_products/` |
| Must not | Invent catalog dosages | Replace regulatory public guidance |

---

## 6. Data and persistence

| Store | Scope | Technology |
|-------|-------|------------|
| `vectorstore/chroma/` | General chunks + metadata (`filename`, `corpus_topic`, headers) | ChromaDB on disk |
| `vectorstore/chroma_products/` | Product row chunks | ChromaDB on disk |
| `localStorage` (`terramind_sessions_v1`) | Per-browser chat sessions | Client only |
| FrontPage in-memory history | Dev audit log (optional) | Not user sessions |

**Runtime caches:** `get_general_db()` / `get_product_db()` hold in-process Chroma handles; **restart Model API after `--reset`** so indexes reload.

---

## 7. API surface (architecture-relevant)

### Model API (`terramind/api/app.py`, port 8001)

| Method | Path | Behavior |
|--------|------|----------|
| GET | `/health` | Status + vector counts |
| GET | `/models` | Registry for UI |
| POST | `/query` | Single model |
| POST | `/query/compare` | Parallel three models |
| POST | `/query/advisory` | General then product |

**Shim:** `rag_api.py` re-exports `terramind.api.app` for older docs/commands.

### FrontPage API (port 8000)

| Method | Path | Proxies to |
|--------|------|------------|
| POST | `/api/ask` | `/query` |
| POST | `/api/ask/compare` | `/query/compare` |
| POST | `/api/ask/advisory` | `/query/advisory` |
| GET | `/api/models` | `/models` |

Config: `RAG_SERVICE_URL` (default `http://localhost:8001/query`), `USE_MOCK` for offline UI.

---

## 8. Repository layout (logical)

```
<repo-root>/
├── FrontPage/
│   ├── app/                 # FastAPI BFF (8000)
│   └── frontend-react/      # React + Vite (3000)
├── terramind/
│   ├── api/app.py           # Model API (8001)
│   ├── models/              # Per-mode adapters + advisory + vision
│   └── rag/
│       ├── general/         # Public docs RAG (active)
│       ├── product/         # Catalog RAG (active)
│       └── source_display.py
├── data/
│   ├── raw/documents/       # General PDF corpus
│   ├── raw/text/            # Product Excel (+ optional general text)
│   ├── sample/              # Allowlisted short references
│   └── eval/                # Retrieval golden set
├── vectorstore/             # Chroma persistence (gitignored)
├── docs/                    # Developer docs (this file)
├── run_dev.py               # Start 8001 + 8000 + 3000
└── Rag_Pc.py                # Legacy / migration (product)
```

---

## 9. External dependencies

| System | Use |
|--------|-----|
| **OpenAI API** | Chat, embeddings, vision |
| **LangChain** | Prompts, `ChatOpenAI`, document types |
| **langchain-chroma** | Vector store wrapper |
| **ChromaDB** | Local persistence |
| **FastAPI + httpx** | APIs and BFF proxy |
| **pypdf** | General PDF text extraction |
| **pandas** | Product Excel load |

Secrets: `.env` / environment (`OPENAI_API_KEY`, optional `RAG_SERVICE_URL`).

---

## 10. Planned evolution (not current)

**Detailed specs:** [PLANNED_FEATURES.md](./PLANNED_FEATURES.md)

| Feature | Summary |
|---------|---------|
| **Auto RAG mode** | **Shipped** — `auto_rag` default; dual-index probe + keywords → `routed_to` in API/UI |
| **Scores in UI** | **Shipped** — “Show scores” toggle; `retrieval_score` + `confidence` |
| Product RAG migration | Full move off root `Rag_Pc.py` (teammate scope) |
| Deployment | Single host vs split services — not defined yet |
| PDF extraction | Optional `pymupdf` / stronger extractors — see general RAG eval runbook |

---

## 11. How to update this document

When architecture changes (new service, port, model mode, index layout, or advisory flow):

1. Edit **this file** only for structure/topology/contracts.
2. Keep feature-level narrative in `PROJECT_OVERVIEW.md`.
3. Keep file-level inventory in `FILE_MAP_AND_PIPELINE.md`.
4. Note the date or PR in the **Status** line at the top if helpful.
