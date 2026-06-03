"""
General agriculture document RAG — markdown/docs → Chroma → retrieve → answer.

Planned modules (templates in this folder):
  config.py    paths, models
  load.py      read files → Documents + metadata
  chunk.py     RecursiveCharacterTextSplitter
  store.py     Chroma build / load
  retrieve.py  similarity search
  generate.py  prompt + LLM
  pipeline.py  init_general_rag, get_general_db, answer_with_rag
  cli.py       python -m terramind.rag.general.cli

Today: implementation re-exported from Rag_Gen.py at repo root.

Next: docs/RAG_MIGRATION_PLAN.md — move code into sibling .py files, then import from pipeline.py here.
"""

from Rag_Gen import (
    answer_with_rag,
    get_general_db,
    init_general_rag,
    sources_from_retrieved,
)

__all__ = [
    "answer_with_rag",
    "get_general_db",
    "init_general_rag",
    "sources_from_retrieved",
]
