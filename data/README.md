# `data/` — layout

What is **tracked in git** vs **ignored** (see root `.gitignore`).

| Path | Role | Git |
|------|------|-----|
| `raw/documents/` | General RAG PDF corpus | Tracked |
| `raw/text/` | Product Excel + optional extra text | Tracked (catalog files) |
| `sample/` | Short reference `.txt` for general RAG (allowlisted) | Tracked |
| `eval/` | Golden retrieval questions JSON | Tracked |
| `eval/runs/` | Optional full-answer eval exports | Ignored |
| `processed/` | Legacy/generated JSONL chunks | Ignored |
| `raw/PlantVillage/` | Image dataset (not web RAG) | Ignored |
| `raw/Fine tuning data/` | Fine-tuning JSONL (not web RAG) | Ignored |

**Indexes** built locally: `vectorstore/chroma/` (general), `vectorstore/chroma_products/` (product).

Docs: [docs/GENERAL_RAG_CORPUS.md](../docs/GENERAL_RAG_CORPUS.md), [docs/GENERAL_RAG_EVAL.md](../docs/GENERAL_RAG_EVAL.md).
