<div align="center">
  <img src="TM_Logo.png" width="20%" height="20%">
</div>

# TerraMind 

MVP agriculture knowledge assistant with Retrieval-Augmented Generation (RAG).

## Phase 1 — Quick start

### 1. Environment

```bash
conda create -n terramind python=3.11 -y
conda activate terramind
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set your OpenAI API key:

```bash
copy .env.example .env
```

### 2. Build the knowledge index

From the project root:

```bash
python scripts/01_ingest_documents.py
python scripts/02_create_chunks.py
python scripts/03_build_vectorstore.py
```

### 3. Ask a question

```bash
python scripts/05_run_rag.py "What is the dosage for chlorothalonil on tomato early blight?"
python scripts/05_run_rag.py "How do I treat wheat yellow rust?" --compare
python scripts/04_run_base_llm.py "How do I treat wheat yellow rust?"
```

## Project layout

- `data/sample/` — small text documents for Phase 1
- `src/` — RAG modules (loader, chunking, embeddings, vector store, retriever, pipeline)
- `scripts/` — runnable ingestion and query scripts
- `vectorstore/` — persisted Chroma database (gitignored)

## Next steps

1. **Phase 2** — process real product catalog Excel into `data/processed/`
2. **Phase 3** — source display and base vs RAG comparison (partially in `05_run_rag.py --compare`)
3. **Phase 4** — wire `src/safety.py` into the pipeline
4. **Phase 5** — connect to demo API (see `FrontPage/`)
