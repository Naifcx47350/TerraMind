# General Agriculture RAG — corpus and layout

## Purpose

**Agriculture Knowledge RAG** (`general_rag`) answers questions using **trusted public agriculture references** — not the company product catalog.

> The General Agriculture RAG is built from trusted public agriculture references covering good agricultural practices, soil health, cover crops, crop rotation, and integrated pest management. This gives TerraMind a broader knowledge layer, while the Product RAG remains responsible for company-specific product information.

## Folder layout

| Path | Role |
|------|------|
| **`data/raw/documents/`** | **RAG source PDFs** (primary corpus) |
| **`data/raw/reference_text/`** | Optional extra `.md`/`.txt` references for General RAG |
| **`data/raw/product_catalog/`** | Product Excel files for Product RAG (`translated/` + `original/`) |
| **`data/sample/`** | Short reference `.txt` (e.g. pesticide safety) |
| **`data/eval/`** | Golden questions + eval run outputs |
| **`docs/`** | Developer documentation (not ingested) |
## Indexed files and UI source labels

| File | Website source label |
|------|----------------------|
| `2020-Guide-to-Integrated-Pest-Management.pdf` | Guide to Integrated Pest Management (Univ. of Minnesota, 2020) |
| `Building-Soils-for-Better-Crops.pdf` | Building Soils for Better Crops — Ecological Soil Management (4th ed.) |
| `fungicideefficacytiming.pdf` | Fungicides & Bactericides: Efficacy & Timing (UC Fruit & Nut Crops) |
| `Managing pesticides in agriculture and public health.pdf` | FAO/WHO International Code of Conduct on Pesticide Management |
| `Pest_Mangment_FAO.pdf` | FAO IPM Guidance for Major Crop Pests & Diseases (2025) |
| `Training manual(GAP).pdf` | FAO Good Agricultural Practices (GAP) Training Manual |
| `pesticide_safety_general.txt` | General Pesticide Safety Guidelines |

**FAO IPM:** use `Pest_Mangment_FAO.pdf` only (the duplicate `Pest_Management_FAO.md` was removed from the repo). `EXCLUDED_FILENAMES` in config still blocks that filename if it is re-added under `data/raw/reference_text/`.

Labels: `terramind/rag/general/config.py` → `DOCUMENT_DISPLAY_NAMES` and `FILENAME_TO_TOPIC`.

## Pipeline features

- PDF ingest via `pypdf` ([`load.py`](../terramind/rag/general/load.py))
- Scored vector retrieval + topic boost + lexical rerank ([`retrieve.py`](../terramind/rag/general/retrieve.py), [`hybrid.py`](../terramind/rag/general/hybrid.py))
- Retrieval eval: [GENERAL_RAG_EVAL.md](./GENERAL_RAG_EVAL.md)

## Build or rebuild

```powershell
python -m terramind.rag.general.cli --reset
python -m terramind.rag.general.cli --eval-retrieval
```

**Validated baseline (inspect + reset + 20/20 eval):** [GENERAL_RAG_VALIDATION_REPORT.md](./GENERAL_RAG_VALIDATION_REPORT.md)

## Advisory mode (general + product)

`POST /query/advisory` and **`POST /query/advisory/stream`** on port **8001** — general guidance first, then product catalog.

**UI:** Advisory is **not** in the public model dropdown. Unlock by clicking the TerraMind logo **6 times** within 2.5s (`App.jsx` → `sessionStorage` key `terramind_advisory_unlocked_v1`). Meta questions (*who are you*, greetings) return a short intro without RAG retrieval.

## Product RAG

Company catalog remains **`product_rag`** from translated Excel in `data/raw/product_catalog/translated/`.
