"""Paths, model names, and constants for TerraMind RAG."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data paths
SAMPLE_DOCS_DIR = PROJECT_ROOT / "data" / "sample"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHUNKS_PATH = PROCESSED_DIR / "chunks.jsonl"
DOCUMENTS_PATH = PROCESSED_DIR / "documents.jsonl"

# Vector store
VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore" / "chroma"
COLLECTION_NAME = "terramind_knowledge"

# OpenAI models
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

# Chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80

# Retrieval
TOP_K = 4
