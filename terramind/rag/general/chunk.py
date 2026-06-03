"""
General RAG — split documents into retrieval chunks.

TODO: Move from Rag_Gen.py:
  - chunk_document(doc) -> list[Document] using RecursiveCharacterTextSplitter
  - Keep chunk size/overlap same as today so the index does not change unexpectedly
See docs/RAG_MIGRATION_PLAN.md step 3 (general).
"""
