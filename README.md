<div align="center">
  <img src="assets/logo/TM_Logo.png" width="20%" height="20%">
</div>

# TerraMind

Agriculture support assistant with **three comparable AI modes**: product-catalog RAG, general-document RAG, and a base LLM baseline — plus a **React chat UI** with compare view, image upload, and saved conversations.

---

## Documentation

| Document | Description |
|----------|-------------|
| **[docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)** | **System architecture** — runtime topology, flows, RAG boundaries (update when stack changes) |
| **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** | **Main technical guide** — features, models, storage, compare, images, APIs |
| **[docs/FILE_MAP_AND_PIPELINE.md](docs/FILE_MAP_AND_PIPELINE.md)** | **File-by-file map** — what runs, what calls what, legacy vs active |
| **[terramind/README.md](terramind/README.md)** | Backend package layout |
| **[docs/GENERAL_RAG_CORPUS.md](docs/GENERAL_RAG_CORPUS.md)** | **General RAG** — source PDFs, folder layout, rebuild index |
| **[docs/GENERAL_RAG_VALIDATION_REPORT.md](docs/GENERAL_RAG_VALIDATION_REPORT.md)** | **General RAG validation** — May 2026 inspect/reset/eval results and methodology |
| **[docs/RAG_MIGRATION_PLAN.md](docs/RAG_MIGRATION_PLAN.md)** | **Next steps** — split RAG into `terramind/rag/` modules |
| [FrontPage/RUN_LOCALLY.md](FrontPage/RUN_LOCALLY.md) | Run all three services — uses **`<repo-root>`** (your clone path) |
| [FrontPage/ARCHITECTURE.md](FrontPage/ARCHITECTURE.md) | Short architecture diagram |
| [FrontPage/README.md](FrontPage/README.md) | FrontPage API quick start |

---

## Quick start (web MVP)

**Paths:** `<repo-root>` = your TerraMind clone (folder with `Rag_Pc.py` and `FrontPage/`). See [FrontPage/RUN_LOCALLY.md](FrontPage/RUN_LOCALLY.md) for full steps.

### 1. Environment

```powershell
cd <repo-root>
conda create -n terramind python=3.11 -y
conda activate terramind
pip install -r requirements.txt
# optional: pip install -r requirements-dev.txt
```

Set `OPENAI_API_KEY` in `<repo-root>/.env` or `FrontPage/.env`.

### 2. Build vector indexes (once)

```powershell
cd <repo-root>
python Rag_Pc.py --reset
python -m terramind.rag.general.cli --reset   # required after chunking/loader changes
```

### 3. Run the app

**One command:**

```powershell
cd <repo-root>
conda activate terramind
python run_dev.py
```

**Or three terminals** — see [FrontPage/RUN_LOCALLY.md](FrontPage/RUN_LOCALLY.md).

Open **http://localhost:3000**.

---

## The three models

| Mode | ID | Knowledge source |
|------|-----|------------------|
| Product Catalog RAG | `product_rag` | Client Excel (`ProductCatalog(En).xlsx`) |
| Agriculture Knowledge RAG | `general_rag` | Public refs in `data/raw/documents/` (IPM, GAP, soil health, pesticides) |
| Base LLM | `base_llm` | No retrieval — OpenAI only |

**General vs product:** The General Agriculture RAG uses trusted public references (good agricultural practices, soil health, cover crops, crop rotation, integrated pest management). The Product RAG handles **company-specific** catalog information only. Details: [docs/GENERAL_RAG_CORPUS.md](docs/GENERAL_RAG_CORPUS.md).

Default LLM: **`gpt-4o-mini`** for chat and vision.

---

## Project layout (high level)

```text
TerraMind/
├── docs/                      # Developer docs (not RAG sources)
│   ├── GENERAL_RAG_CORPUS.md  # General RAG sources & rebuild
│   └── FILE_MAP_AND_PIPELINE.md
├── terramind/                 # Backend package (API + models + RAG layout)
│   ├── api/app.py             # Model HTTP API (:8001)
│   ├── models/                # Three modes + vision + conversation
│   └── rag/product|general/   # RAG module templates (logic still in Rag_*.py)
├── Rag_Pc.py                  # Product RAG implementation (migrate → terramind/rag/product/)
├── terramind/rag/general/     # General RAG (migrated from Rag_Gen.py)
├── rag_api.py                 # Shim → terramind.api.app
├── models/                    # Shim → terramind.models (backward compat)
├── vectorstore/               # Chroma indexes (local)
├── data/raw/documents/        # General RAG PDFs (IPM, GAP, soil, etc.)
├── data/raw/text/             # Product Excel + optional extra text
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
