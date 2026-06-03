# RAG Migration Plan — `Rag_Pc.py` / `Rag_Gen.py` → `terramind/rag/`

Reference for splitting the two root RAG scripts into organized packages without breaking the web app.

**Paths:** run commands from **`<repo-root>`** (your clone directory). Data and indexes stay at `<repo-root>/data/` and `<repo-root>/vectorstore/`.

**Current state:** Full logic lives in `Rag_Pc.py` and `Rag_Gen.py`.  
`terramind/rag/product/` and `terramind/rag/general/` re-export those files so ports **8001 / 8000 / 3000** keep working.

**Target state:** Logic lives in `terramind/rag/*/`. Root scripts become thin CLIs or are removed.

---

## Principles

1. **One pipeline step per file** — load, store, retrieve, generate stay separate.
2. **Migrate one module at a time** — run `Rag_Pc.py --reset` and `/api/ask` after each step.
3. **Shared patterns** — product and general pipelines mirror each other; only `load.py` differs (Excel vs markdown).
4. **Do not change** vector paths (`vectorstore/chroma_products`, `vectorstore/chroma`) or FrontPage URLs during migration.

---

## Product RAG (`terramind/rag/product/`)

| Order | File | Move from `Rag_Pc.py` | Done when |
|-------|------|------------------------|-----------|
| 1 | `config.py` | `PROJECT_ROOT`, paths, `EMBEDDING_MODEL`, `CHAT_MODEL`, `PRODUCT_FIELDS`, column constants | Imports work; `Rag_Pc` can import from config |
| 2 | `load.py` | `load_catalog()`, Excel → `Document` list + metadata | Unit test: N documents loaded |
| 3 | `store.py` | `build_chroma_db()`, `_chroma_exists()`, reset logic | `python -m terramind.rag.product.cli --reset` builds index |
| 4 | `retrieve.py` | `retrieve_products()`, `format_context()` | Retrieval returns k chunks |
| 5 | `generate.py` | `RAG_PROMPT`, LLM invoke for answer | Prompt + answer without store |
| 6 | `pipeline.py` | `init_product_rag`, `get_product_db`, `answer_with_rag`, `sources_from_retrieved` | `__init__.py` imports from pipeline, not `Rag_Pc` |
| 7 | `cli.py` | `argparse` + `__main__` | Replace `python Rag_Pc.py` docs with `-m terramind.rag.product.cli` |
| 8 | `chunk.py` | Only if you add splitting later | Optional — products are often one doc per row |

**Skip for product:** `chunk.py` can stay a one-line “not used” note unless catalog rows need splitting.

---

## General RAG (`terramind/rag/general/`)

| Order | File | Move from `Rag_Gen.py` | Done when |
|-------|------|-------------------------|-----------|
| 1 | `config.py` | `DATA_PATH`, `CHROMA_PATH`, models, `RETRIEVAL_K` | Same as product step 1 |
| 2 | `load.py` | `load_document()`, `_guess_title()` | Markdown loads with metadata |
| 3 | `chunk.py` | `chunk_document()` | Chunks count matches today |
| 4 | `store.py` | `build_chroma_db()`, index load/save | `--reset` rebuilds `vectorstore/chroma` |
| 5 | `retrieve.py` | `retrieve_chunks()`, `format_context()` | Search works |
| 6 | `generate.py` | `RAG_PROMPT`, generation step | Answer matches old script |
| 7 | `pipeline.py` | `init_general_rag`, `get_general_db`, `answer_with_rag`, `sources_from_retrieved` | Package self-contained |
| 8 | `cli.py` | `__main__` | Replace `python Rag_Gen.py` |

**Later (optional):** `evaluate_chunk_similarity` → `general/eval.py` (not required for web).

---

## Wiring checklist (after each pipeline is complete)

- [ ] `terramind/rag/product/__init__.py` imports from `.pipeline` only (remove `from Rag_Pc import …`)
- [ ] `terramind/rag/general/__init__.py` imports from `.pipeline` only
- [ ] `terramind/models/product_rag.py` unchanged (still uses `terramind.rag.product`)
- [ ] `GET http://localhost:8001/health` shows vector counts
- [ ] UI: product_rag + general_rag + compare + image still work
- [ ] Update `RUN_LOCALLY.md` build commands to new CLI modules
- [ ] Root `Rag_Pc.py` / `Rag_Gen.py`: delete or keep as 3-line shims for old habits

---

## Suggested `config.py` shape (both pipelines)

```python
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]  # TerraMind/
CHROMA_PATH = ...
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
RETRIEVAL_K = 4
```

Use **`<repo-root>`** for `data/` and `vectorstore/`, not the `terramind/` package folder, so existing indexes keep working.

---

## Testing per step

```powershell
cd <repo-root>

# Product
python -m terramind.rag.product.cli --reset
python -m terramind.rag.product.cli "How do I use product X?"

# General
python -m terramind.rag.general.cli --reset
python -m terramind.rag.general.cli "What is IPM for late blight?"

# API
uvicorn terramind.api.app:app --reload --port 8001
# FrontPage + UI smoke test — see FrontPage/RUN_LOCALLY.md
```

---

## Out of scope (for later)

- Ingesting `doc/*.pdf` into general RAG (needs PDF → text step).
- Merging `scripts/` ingestion into `terramind/rag`.
- Moving `vectorstore/` or Excel paths without team agreement.

---

## Related docs

- [FILE_MAP_AND_PIPELINE.md](./FILE_MAP_AND_PIPELINE.md) — what runs today  
- [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md) — features and architecture  
- [terramind/README.md](../terramind/README.md) — package folder map  
