# TerraMind — System Architecture

**Status:** Current as of June 2026. This file is the **canonical architecture reference** — update it when the stack or boundaries change (e.g. after migrations, new services, or deployment).

**Related (not duplicated here):** feature walkthrough → [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md); file-by-file map → [FILE_MAP_AND_PIPELINE.md](./FILE_MAP_AND_PIPELINE.md); local run → [FrontPage/RUN_LOCALLY.md](../FrontPage/RUN_LOCALLY.md).

---

## 1. Purpose

TerraMind is a **multi-mode agriculture assistant**: users ask questions in a web chat, optionally attach crop images, and choose how answers are produced — company product catalog (RAG), public agriculture references (RAG), plain LLM baseline, or a **combined advisory** path (general then product).

Architecture is a **three-process dev stack** (React UI → BFF API → Model API) with **two on-disk vector indexes** and **one shared OpenAI stack** for chat, embeddings, and vision.

---

## 2. Runtime topology

| Layer             | Port | Entry                             | Role                                                                  |
| ----------------- | ---- | --------------------------------- | --------------------------------------------------------------------- |
| **React UI**      | 3000 | `FrontPage/frontend-react` (Vite) | Chat, compare grid, model picker, sessions, sources, Markdown answers |
| **FrontPage API** | 8000 | `FrontPage/app/main.py`           | BFF: vision (optional), proxy to Model API, mock fallback             |
| **Model API**     | 8001 | `terramind.api.app:app`           | Route to model backends; compare & advisory orchestration             |

**Dev orchestration:** `python run_dev.py` from repo root starts all three.

**Browser → API path:** Vite proxies `/api/*` → `http://localhost:8000`. The UI does not call port 8001 directly in dev.

```mermaid
flowchart TB
  subgraph browser ["Browser port 3000"]
    UI["React App.jsx"]
    LS[("localStorage sessions")]
    UI --- LS
  end

  subgraph fp ["FrontPage port 8000"]
    Ask["POST /api/ask"]
    Cmp["POST /api/ask/compare"]
    Adv["POST /api/ask/advisory"]
    RAGSvc["rag_service.py"]
    Ask --> RAGSvc
    Cmp --> RAGSvc
    Adv --> RAGSvc
  end

  subgraph model ["Model API port 8001"]
    Q["POST /query"]
    QC["POST /query/compare"]
    QA["POST /query/advisory"]
    Reg["terramind.models"]
    Q --> Reg
    QC --> Reg
    QA --> Reg
  end

  subgraph knowledge ["On-disk knowledge"]
    CP[("chroma_products")]
    CG[("chroma general")]
    Excel["data/raw/text catalog"]
    PDFs["data/raw/documents"]
  end

  subgraph openai ["OpenAI"]
    Chat["gpt-4o-mini"]
    Emb["text-embedding-3-small"]
    Vis["vision"]
  end

  UI -->|"proxy /api/*"| fp
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

### 3.1 Single model (streaming — default UI)

1. User sends message (+ optional image) from React.
2. `POST /api/ask/stream` → `FrontPage/app/services/rag_service.py` → proxies to Model API.
3. If image present: **one** vision call on FrontPage before stream starts.
4. `POST http://localhost:8001/query/stream` with `{ question, model, history, image_analysis?, … }`.
5. `terramind.models.streaming.stream_model_events()` emits **NDJSON**:
   - `{"event":"status","message":"…"}` — routing / retrieval progress
   - `{"event":"token","content":"…"}` — LLM tokens
   - `{"event":"done",…}` — full metadata (`sources`, `routed_to`, `latency_ms`, …)
6. React updates the bot bubble incrementally; finalizes on `done`.

Non-streaming `POST /query` and `POST /api/ask` remain for scripts and integration tests.

### 3.1b Single model (JSON — legacy)

Same as above but waits for one JSON body from `POST /query` / `POST /api/ask`.

### 3.2 Compare (three models in parallel)

1. UI enables Compare → `POST /api/ask/compare`.
2. FrontPage runs vision **once**, then `POST /query/compare`.
3. Model API: `asyncio.gather` over `product_rag`, `general_rag`, `base_llm`.
4. UI renders three columns (same question, three answers).

### 3.3 Advisory (general + product)

1. User selects **Advisory** after unlocking it in the UI (logo easter egg — not in public dropdown).
2. `POST /api/ask/advisory/stream` → `POST /query/advisory/stream` → `stream_advisory_events()`.
3. **Sequential:** general RAG stream, then product RAG stream, merged in the final `done` event.
4. **Meta questions** (_who are you_, greetings): short intro only — **no** Chroma retrieval (`terramind/meta_questions.py`).

Non-streaming `/query/advisory` and `/api/ask/advisory` remain available.

---

## 4. Model layer

Registry: `terramind/models/__init__.py` (`MODEL_REGISTRY`, `run_model`, `run_advisory`).

| UI / API `model`         | Backend module                            | Retrieval                                       | Vector store                                               |
| ------------------------ | ----------------------------------------- | ----------------------------------------------- | ---------------------------------------------------------- |
| `auto_rag` (**default**) | `terramind.models.auto_rag` → `router.py` | One of product, general, or **base LLM**        | Probed both indexes when agronomy-related; meta → base LLM |
| `product_rag`            | `terramind.models.product_rag`            | Yes — catalog rows                              | `vectorstore/chroma_products/`                             |
| `general_rag`            | `terramind.models.general_rag`            | Yes — public PDFs + sample text                 | `vectorstore/chroma/`                                      |
| `base_llm`               | `terramind.models.base_llm`               | No                                              | —                                                          |
| `advisory` (hidden UI)   | `run_advisory` / `stream_advisory_events` | Both RAG chains when needed; meta short-circuit | Both stores                                                |

**Auto routing:** `route_question()` in `router.py` checks **`is_meta_question()`** first → `base_llm` (no retrieval). Otherwise uses dual-index top-1 relevance plus keyword hints → `product_rag` or `general_rag`. Response includes `routed_to` and `router_reason`. Compare mode still runs only the three fixed backends (not Auto).

**Meta detection:** `terramind/meta_questions.py` — greetings, identity, capability questions (English + some Arabic).

**Shared cross-cutting:**

| Concern                                       | Location                                                       |
| --------------------------------------------- | -------------------------------------------------------------- |
| Chat history in prompts                       | `terramind/models/conversation.py`                             |
| Meta / identity detection                     | `terramind/meta_questions.py`                                  |
| Streaming orchestration                       | `terramind/models/streaming.py`, `terramind/rag/llm_stream.py` |
| Retrieval vs generation query split (general) | `build_retrieval_query` / `build_prompt_question`              |
| Image context in prompts                      | `terramind/models/image_context.py`                            |
| Friendly source titles                        | `terramind/rag/source_display.py`                              |

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

| Layer      | General                                 | Product                            |
| ---------- | --------------------------------------- | ---------------------------------- |
| Purpose    | Public IPM, GAP, soil, pesticide policy | Company labels, dosage, crops      |
| Index path | `vectorstore/chroma/`                   | `vectorstore/chroma_products/`     |
| Must not   | Invent catalog dosages                  | Replace regulatory public guidance |

---

## 6. Data and persistence

| Store                                               | Scope                                                           | Technology        |
| --------------------------------------------------- | --------------------------------------------------------------- | ----------------- |
| `vectorstore/chroma/`                               | General chunks + metadata (`filename`, `corpus_topic`, headers) | ChromaDB on disk  |
| `vectorstore/chroma_products/`                      | Product row chunks                                              | ChromaDB on disk  |
| `localStorage` (`terramind_sessions_v1`)            | Per-browser chat sessions                                       | Client only       |
| `sessionStorage` (`terramind_advisory_unlocked_v1`) | Hidden Advisory unlock (current tab)                            | Client only       |
| FrontPage in-memory history                         | Dev audit log (optional)                                        | Not user sessions |

**Runtime caches:** `get_general_db()` / `get_product_db()` hold in-process Chroma handles; **restart Model API after `--reset`** so indexes reload.

---

## 7. API surface (architecture-relevant)

### Model API (`terramind/api/app.py`, port 8001)

| Method | Path                     | Behavior                    |
| ------ | ------------------------ | --------------------------- |
| GET    | `/health`                | Status + vector counts      |
| GET    | `/models`                | Registry for UI             |
| POST   | `/query`                 | Single model (JSON)         |
| POST   | `/query/stream`          | Single model NDJSON stream  |
| POST   | `/query/compare`         | Parallel three models       |
| POST   | `/query/advisory`        | General then product (JSON) |
| POST   | `/query/advisory/stream` | Advisory NDJSON stream      |

**Shim:** `rag_api.py` re-exports `terramind.api.app` for older docs/commands.

### FrontPage API (port 8000)

| Method | Path                       | Proxies to               |
| ------ | -------------------------- | ------------------------ |
| POST   | `/api/ask`                 | `/query` (JSON)          |
| POST   | `/api/ask/stream`          | `/query/stream`          |
| POST   | `/api/ask/compare`         | `/query/compare`         |
| POST   | `/api/ask/advisory`        | `/query/advisory`        |
| POST   | `/api/ask/advisory/stream` | `/query/advisory/stream` |
| GET    | `/api/models`              | `/models`                |

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
│   ├── models/              # Per-mode adapters, advisory, streaming, vision
│   ├── meta_questions.py    # Meta / identity detection (Auto + Advisory)
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

| System               | Use                                   |
| -------------------- | ------------------------------------- |
| **OpenAI API**       | Chat, embeddings, vision              |
| **LangChain**        | Prompts, `ChatOpenAI`, document types |
| **langchain-chroma** | Vector store wrapper                  |
| **ChromaDB**         | Local persistence                     |
| **FastAPI + httpx**  | APIs and BFF proxy                    |
| **pypdf**            | General PDF text extraction           |
| **pandas**           | Product Excel load                    |

Secrets: `.env` / environment (`OPENAI_API_KEY`, optional `RAG_SERVICE_URL`).

---

## 10. Planned evolution (not current)

**Status, legacy, and roadmap:** [PROJECT_STATUS.md](./PROJECT_STATUS.md)

| Feature                | Summary                                                                                  |
| ---------------------- | ---------------------------------------------------------------------------------------- |
| **Auto RAG mode**      | **Shipped** — routes to product, general, or **base LLM**; meta questions skip retrieval |
| **Streaming chat**     | **Shipped** — NDJSON `/query/stream`; UI uses `/api/ask/stream`                          |
| **Hidden Advisory UI** | **Shipped** — 6× logo click unlock; `/query/advisory/stream`                             |
| **Scores in UI**       | **Shipped** — “Show scores” toggle; `retrieval_score` + `confidence`                     |
| Product RAG migration  | Full move off root `Rag_Pc.py` — see PROJECT_STATUS §2                                   |
| Deployment             | Not defined in repo yet                                                                  |
| PDF extraction         | Optional `pymupdf` — see GENERAL_RAG_EVAL runbook                                        |

---

## 11. How to update this document

When architecture changes (new service, port, model mode, index layout, or advisory flow):

1. Edit **this file** only for structure/topology/contracts.
2. Keep feature-level narrative in `PROJECT_OVERVIEW.md`.
3. Keep file-level inventory in `FILE_MAP_AND_PIPELINE.md`.
4. Note the date or PR in the **Status** line at the top if helpful.
