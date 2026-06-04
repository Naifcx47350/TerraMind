# General RAG — evaluation runbook

Quick regression checks after changing loaders, chunking, retrieval, or prompts.

**Latest baseline results (what we ran, why, and outcomes):** [GENERAL_RAG_VALIDATION_REPORT.md](./GENERAL_RAG_VALIDATION_REPORT.md) — May 2026: 7-file corpus, 2,354 vectors, **20/20** retrieval eval after FAO `.md` removal.

## Prerequisites

```powershell
cd <repo-root>
conda activate terramind
pip install -r requirements.txt
```

`OPENAI_API_KEY` required for full `--reset` and answer export (not for `--inspect`).

## 0. After removing or adding corpus files (e.g. FAO `.md` deleted, PDF only)

1. Confirm the file is gone from disk (e.g. no `data/raw/text/Pest_Management_FAO.md`).
2. Run **`--inspect`** — you should see **7** sources (6 PDFs + `pesticide_safety_general.txt`), with **no** `Pest_Management_FAO.md`.
3. Run **`--reset`** before **`--eval-retrieval`**. The existing Chroma index still holds old chunks until you rebuild.
4. **Restart** the model API (`run_dev.py` or port **8001**) after `--reset` so the in-memory index reloads.

If you skip step 3, eval may still show `.md` in top-k hits and pass rates will not reflect the new corpus.

## 1. Corpus inspect (no index)

```powershell
python -m terramind.rag.general.cli --inspect
```

- Each PDF should show **≥ 5,000 characters** after extraction.
- If **LOW**, improve extraction (`pypdf` → `pymupdf` / `pdfplumber`) or add a cleaned `.md` export.

## 2. Rebuild index

```powershell
python -m terramind.rag.general.cli --reset
```

## 3. Retrieval golden set (no LLM)

```powershell
python -m terramind.rag.general.cli --eval-retrieval
```

- Questions: [`data/eval/general_rag_questions.json`](../data/eval/general_rag_questions.json)
- **Pass target:** ≥ 80% hits (expected `filename` appears in top-6 chunks)
- Exit code `1` if below threshold (for CI/scripts)

## 4. Full answer export (optional)

```powershell
python scripts/eval_general_rag.py
```

Writes timestamped answers under `data/eval/runs/` (gitignored).

## 5. UI smoke (5 minutes)

With `run_dev.py` or three terminals running:

1. **Agriculture Knowledge RAG** — soil/IPM question; sources show friendly manual names (not file paths).
2. **Product Catalog RAG** — specific product question.
3. **Advisory (General + Product)** — image + “what is wrong with my potatoes and what product helps?”
4. **Compare** — still returns three columns.
5. `GET http://localhost:8001/health` — `general_vectors` > 0.

## 6. API debug logs

Enable debug logging for `terramind.models.general_rag` to see retrieval file list per request.

## When to re-run

| Change | Re-index? | Re-run eval? |
|--------|-----------|--------------|
| `DOCUMENT_DISPLAY_NAMES` only | No | No |
| PDF/text content or chunking | Yes (`--reset`) | Yes |
| `retrieve.py` / topics / hybrid | No | Yes (`--eval-retrieval`) |
| Prompt only | No | Manual UI spot-check |
