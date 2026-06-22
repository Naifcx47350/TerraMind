"""General RAG — build, load, and reset the Chroma vector index."""

import shutil

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from core.rag.general.config import CHROMA_PATH, EMBEDDING_MODEL


def _chroma_exists() -> bool:
    return (CHROMA_PATH / "chroma.sqlite3").exists()


def build_chroma_db(chunk_docs: list[Document], reset: bool = False) -> Chroma:
    CHROMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    if reset and _chroma_exists():
        shutil.rmtree(CHROMA_PATH)
        print(f"Removed existing index at {CHROMA_PATH}")

    if _chroma_exists():
        db = Chroma(
            persist_directory=str(CHROMA_PATH),
            embedding_function=embeddings,
        )
        print(
            f"Loaded existing Chroma index ({db._collection.count()} vectors)"
        )
        return db

    db = Chroma.from_documents(
        chunk_docs,
        embedding=embeddings,
        persist_directory=str(CHROMA_PATH),
    )
    print(f"Built new index with {len(chunk_docs)} chunks")
    return db
