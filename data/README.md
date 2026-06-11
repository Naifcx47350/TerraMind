# `data/` — layout

What is **tracked in git** vs **ignored** (see root `.gitignore`).

| Path | Role | Git |
|------|------|-----|
| `raw/documents/` | General RAG PDF corpus | Tracked |
| `raw/product_catalog/translated/` | Translated product Excel files used by Product RAG | Tracked |
| `raw/product_catalog/original/` | Original/source product workbook artifacts; preserved but not used by runtime RAG | Tracked |
| `raw/reference_text/` | Optional extra `.md` / `.txt` references for General RAG | Tracked when present |
| `sample/` | Short reference `.txt` for general RAG (allowlisted) | Tracked |
| `eval/` | Golden retrieval questions JSON | Tracked |
| `eval/runs/` | Optional full-answer eval exports | Ignored |
| `processed/` | Legacy/generated JSONL chunks | Ignored |
| `raw/PlantVillage/` | Image dataset (not web RAG) | Ignored |
| `raw/Fine tuning data/` | Fine-tuning JSONL (not web RAG) | Ignored |

**Indexes** built locally: `vectorstore/chroma/` (general), `vectorstore/chroma_products/` (product).

Product RAG currently reads the translated files:

- `raw/product_catalog/translated/product_catalog_en.xlsx`
- `raw/product_catalog/translated/product_categories_en.xlsx`

After catalog path or filename changes, rebuild the product index: `python -m terramind.rag.product.cli --reset` (local) or `docker compose --profile init run --rm init-indexes` (Docker).

## Runtime relevance

- `sample/` is used by General RAG, but only allowlisted files are indexed. Today that allowlist is `pesticide_safety_general.txt` in `terramind/rag/general/config.py`.
- `eval/` is used by General RAG evaluation (`general_rag_questions.json`); generated answer exports go to ignored `eval/runs/`.
- `processed/` is not used by the current web app or RAG pipelines. It is reserved for legacy/generated artifacts and remains gitignored.

Docs: [docs/GENERAL_RAG_CORPUS.md](../docs/GENERAL_RAG_CORPUS.md), [docs/GENERAL_RAG_EVAL.md](../docs/GENERAL_RAG_EVAL.md).
