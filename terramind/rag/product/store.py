"""
Product RAG — build, load, and reset the Chroma vector index.

TODO: Move from Rag_Pc.py:
  - _chroma_exists(), build_chroma_db(docs, reset=False)
  - OpenAIEmbeddings + Chroma persist to vectorstore/chroma_products
  - Export: build_chroma_db(), get_or_create_db() helpers
See docs/RAG_MIGRATION_PLAN.md step 3 (product).
"""
