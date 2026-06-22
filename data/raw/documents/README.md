# General Agriculture RAG — source documents

Place **PDF**, **Markdown**, or **plain text** references here for the **Agriculture Knowledge RAG** (`general_rag`).

## Current corpus

| File | Source name in the UI |
|------|----------------------|
| `2020-Guide-to-Integrated-Pest-Management.pdf` | Guide to Integrated Pest Management (Univ. of Minnesota, 2020) |
| `Building-Soils-for-Better-Crops.pdf` | Building Soils for Better Crops — Ecological Soil Management (4th ed.) |
| `fungicideefficacytiming.pdf` | Fungicides & Bactericides: Efficacy & Timing (UC Fruit & Nut Crops) |
| `Managing pesticides in agriculture and public health.pdf` | FAO/WHO International Code of Conduct on Pesticide Management |
| `Pest_Mangment_FAO.pdf` | FAO IPM Guidance for Major Crop Pests & Diseases (2025) |
| `Training manual(GAP).pdf` | FAO Good Agricultural Practices (GAP) Training Manual |

Also indexed when present: `.md`/`.txt` under `data/raw/reference_text/` and `data/sample/`.

Display names are defined in `core/rag/general/config.py` → `DOCUMENT_DISPLAY_NAMES`.

## Rebuild index after changes

```powershell
cd <repo-root>
python -m core.rag.general.cli --reset
```

Index output: `vectorstore/chroma/`

**Note:** `docs/` at the repo root is for **developer documentation**, not for RAG ingestion.
