<div align="center">
  <img src="TM_Logo.png" width="20%" height="20%">
</div>

# TerraMind

Agriculture support assistant with **three comparable AI modes**: product-catalog RAG, general-document RAG, and a base LLM baseline — plus a **React chat UI** with compare view, image upload, and saved conversations.

---

## Documentation

| Document | Description |
|----------|-------------|
| **[docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md)** | **Main technical guide** — architecture, models, storage, compare, images, APIs |
| [FrontPage/RUN_LOCALLY.md](FrontPage/RUN_LOCALLY.md) | Run all three services (ports 8001, 8000, 3000) |
| [FrontPage/ARCHITECTURE.md](FrontPage/ARCHITECTURE.md) | Short architecture diagram |
| [FrontPage/README.md](FrontPage/README.md) | FrontPage API quick start |

---

## Quick start (web MVP)

### 1. Environment

```powershell
conda create -n terramind python=3.11 -y
conda activate terramind
pip install -r requirements.txt
pip install -r FrontPage/requirements.txt
```

Set `OPENAI_API_KEY` in `.env` at repo root (or `FrontPage/.env`).

### 2. Build vector indexes (once)

```powershell
python Rag_Pc.py --reset
python Rag_Gen.py --reset
```

### 3. Run three terminals

```powershell
# Terminal 1 — repo root
uvicorn rag_api:app --reload --port 8001

# Terminal 2 — FrontPage
cd FrontPage
uvicorn app.main:app --reload --port 8000

# Terminal 3 — UI
cd FrontPage/frontend-react
npm install
npm run dev
```

Open **http://localhost:3000**.

---

## The three models

| Mode | ID | Knowledge source |
|------|-----|------------------|
| Product Catalog RAG | `product_rag` | Client Excel (`ProductCatalog(En).xlsx`) |
| Agriculture Knowledge RAG | `general_rag` | General docs (e.g. FAO pest management markdown) |
| Base LLM | `base_llm` | No retrieval — OpenAI only |

Default LLM: **`gpt-4o-mini`** for chat and vision.

---

## Project layout (high level)

```text
TerraMind/
├── docs/PROJECT_OVERVIEW.md   # Technical introduction
├── models/                    # One adapter per mode
├── Rag_Pc.py                  # Product RAG pipeline
├── Rag_Gen.py                 # General document RAG
├── rag_api.py                 # Unified model HTTP API (:8001)
├── vectorstore/               # Chroma indexes (local)
├── data/raw/text/             # Source files
├── FrontPage/                 # Web API (:8000) + React UI (:3000)
├── src/                       # Earlier CLI RAG modules
└── scripts/                   # Ingestion utilities
```

---

## Features (web)

- Model picker (top right) and **Compare all 3** side-by-side
- Plant **image upload** (vision → all modes)
- **Conversation history** in-thread + **localStorage** session restore
- Sources display for RAG answers
- English / Arabic (RTL)

---

## Phase 1 CLI (optional)

Older script-based flow under `scripts/` and `src/`:

```bash
python scripts/01_ingest_documents.py
python scripts/02_create_chunks.py
python scripts/03_build_vectorstore.py
python scripts/05_run_rag.py "Your question"
```

The **recommended demo path** is the FrontPage stack above.

---

## License / context

Bootcamp MVP (RCP #9) — TerraMind focuses on grounded agricultural Q&A with explicit comparison between RAG and non-RAG behavior.
