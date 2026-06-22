"""
General agriculture document RAG — markdown/docs → Chroma → retrieve → answer.

Modules:
  config.py    paths, models, prompt
  load.py      read files → Documents + metadata
  chunk.py     RecursiveCharacterTextSplitter
  store.py     Chroma build / load
  retrieve.py  similarity search
  generate.py  prompt + LLM
  pipeline.py  init_general_rag, get_general_db, answer_with_rag
  cli.py       python -m core.rag.general.cli
  evaluate.py  optional chunk similarity (dev)

After adding or changing sources, rebuild: python -m core.rag.general.cli --reset
Sources: data/raw/documents/ (PDF + text). See docs/GENERAL_RAG_CORPUS.md.
"""

from core.rag.general.pipeline import (
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
