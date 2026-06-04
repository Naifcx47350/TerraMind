"""
Product RAG — load Excel catalog into LangChain Documents.

TODO: Move from Rag_Pc.py:
  - Read ProductCatalog(En).xlsx (and category sheet if used)
  - Build one Document per product row with metadata: product_id, product_name, source file
  - Export: load_catalog() -> list[Document]
See docs/PROJECT_STATUS.md (product migration).
"""
