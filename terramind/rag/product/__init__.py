"""
Product catalog RAG — Excel → Chroma → retrieve → answer.

Planned modules (templates in this folder):
  config.py    paths, models, Excel column maps
  load.py      read Excel → LangChain Documents
  chunk.py     split / row documents (if needed)
  store.py     build / load Chroma index
  retrieve.py  similarity search
  generate.py  prompt + LLM
  pipeline.py  init_product_rag, get_product_db, answer_with_rag
  cli.py       python -m terramind.rag.product.cli

Today: implementation re-exported from Rag_Pc.py at repo root.

Next: docs/RAG_MIGRATION_PLAN.md — move code into sibling .py files, then import from pipeline.py here.
"""

from Rag_Pc import (
    answer_with_rag,
    get_product_db,
    init_product_rag,
    sources_from_retrieved,
)

__all__ = [
    "answer_with_rag",
    "get_product_db",
    "init_product_rag",
    "sources_from_retrieved",
]
