# TerraMind — project status, history, and artifacts

Single place for **what is done**, **what is left**, and **legacy / removed** items. Operational docs stay in the other `docs/*.md` files listed in [README.md](../README.md).

_Last updated: June 2026_

---

## 1. Current MVP (shipped)

| Area                          | Status             | Where                                                                                         |
| ----------------------------- | ------------------ | --------------------------------------------------------------------------------------------- |
| Web stack                     | Done               | `run_dev.py` → React :3000, web :8000, `core.api.app` :8001                        |
| General RAG                   | Done               | `core/rag/general/` — PDF corpus, CLI, retrieval eval                                    |
| Product RAG                   | Done               | `core/rag/product/` — translated Excel → `vectorstore/chroma_products/`                              |
| **Auto RAG** (default)        | Done               | `auto_rag.py`, `router.py` — routes to product, general, or **base LLM** (meta questions)     |
| Retrieval scores + confidence | Done               | `core/rag/scoring.py`, UI **Show scores**                                                |
| **Streaming answers**         | Done               | `core/models/streaming.py`, `POST /api/ask/stream` — NDJSON status + tokens              |
| Advisory mode (hidden UI)     | Done               | `/query/advisory` — general then product; **6× logo click** unlock in `App.jsx`               |
| Meta / identity questions     | Done               | `core/meta_questions.py` — Auto → base LLM; Advisory short-circuit                       |
| Compare mode                  | Done               | Product + general + base LLM (Auto excluded)                                                  |
| Vision + history + sessions   | Done               | `core/models/vision.py`, `localStorage`                                                  |
| Voice input                   | Done               | Browser speech-to-text mic in `web/frontend-react/src/App.jsx`; styled in `theme/visuals.js` |
| General RAG validation        | Done               | [GENERAL_RAG_VALIDATION_REPORT.md](./GENERAL_RAG_VALIDATION_REPORT.md) — 20/20 retrieval eval |
| **Product RAG package**       | Done               | `core/rag/product/` — replaces runtime `Rag_Pc.py`; Excel under `data/raw/product_catalog/translated/` |
| **Docker Compose stack**      | Done               | `docker-compose.yml` — `model-api`, `gateway`, `frontend`; profile `init` → `init-indexes` |
| UI startup bootstrap          | Done               | `BootstrapOverlay` in `App.jsx` — polls `/api/config` until gateway :8000 is up |

---

## 2. Remaining work

| Item                              | Notes                                                                                                                |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Product catalog tools**     | Clarification classifier and SQL-like catalog agent are scaffolded; implementation still pending            |
| **Deployment**                    | Not defined in repo (single host vs split services)                                                                  |
| **Stronger PDF extraction**       | Optional (`pymupdf`) if a manual scores poorly on `--inspect`                                                        |

---

## 3. Legacy and removed (do not expect in repo)

Bootcamp **Phase 1–4** plan (small Python RAG → React → Tri-RAG → eval deck) is **superseded** by the web MVP above. Removed or never wired for production:

| Artifact                                           | Was                      | Now                                                                  |
| -------------------------------------------------- | ------------------------ | -------------------------------------------------------------------- |
| `Rag_Gen.py`                                       | General RAG monolith     | **`core/rag/general/`**                                         |
| `Rag_Pc.py`                                        | Product RAG monolith     | **Removed; active path is `core/rag/product/`** |
| `doc/`                                             | PDF drop folder          | **`data/raw/documents/`**                                            |
| `src/`                                             | Phase 1 modular pipeline | **Removed**                                                          |
| `scripts/01_ingest_documents.py` … `05_run_rag.py` | Phase 1 CLI              | **Removed** — only `scripts/eval_general_rag.py` remains             |
| `models/` (repo root)                              | Shim to terramind        | **Removed** — use `core/models/`                                |
| Phase 1 “Tri-RAG” naming                           | Three separate apps      | **One UI**, modes + compare + advisory                               |
| `web/claude prompt.md`                       | AI UI generation notes   | **Removed** — dev-only, not maintained                               |
| `Project_plan.md`                                  | Early bootcamp week plan | **Removed** — summary kept here                                      |
| `web/ARCHITECTURE.md`                        | Short duplicate diagram  | **Removed** — use [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) |
| `docs/PLANNED_FEATURES.md`                         | Feature specs            | **Merged into this file**                                            |
| `docs/RAG_MIGRATION_PLAN.md`                       | Migration checklist      | **Merged into this file**                                            |
| Duplicate FAO `.md`                                | Same content as FAO PDF  | **Deleted** — PDF only (`Pest_Mangment_FAO.pdf`)                     |

---

## 4. Documentation map (canonical)

| Read this                                                              | For                                      |
| ---------------------------------------------------------------------- | ---------------------------------------- |
| [README.md](../README.md)                                              | Entry point, quick start                 |
| [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md)                          | Features, APIs, storage, compare, images |
| [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)                     | Topology and boundaries                  |
| [FILE_MAP_AND_PIPELINE.md](./FILE_MAP_AND_PIPELINE.md)                 | Every important file                     |
| [GENERAL_RAG_CORPUS.md](./GENERAL_RAG_CORPUS.md)                       | PDF corpus and rebuild                   |
| [GENERAL_RAG_EVAL.md](./GENERAL_RAG_EVAL.md)                           | How to run retrieval eval                |
| [GENERAL_RAG_VALIDATION_REPORT.md](./GENERAL_RAG_VALIDATION_REPORT.md) | May 2026 baseline results                |
| [data/README.md](../data/README.md)                                    | Gitignore vs tracked data                |
| [web/RUN_LOCALLY.md](../web/RUN_LOCALLY.md)                | Terminals, ports, env                    |
| [core/README.md](../core/README.md)                          | Backend package layout                   |

---

## 5. Future ideas (not scheduled)

Add rows here when planning; move to §1 when shipped.

| Idea                           | Notes                                                                |
| ------------------------------ | -------------------------------------------------------------------- |
| LLM-based router for Auto      | v1 uses keywords + dual-index scores + meta detection                |
| Streaming in Compare mode      | Single-message chat streams today; compare still waits for full JSON |
| Per-source similarity on chips | v1 shows answer-level score only                                     |
| Parent–child chunks            | Not implemented                                                      |
| Product eval golden set        | General set exists in `data/eval/`                                   |
