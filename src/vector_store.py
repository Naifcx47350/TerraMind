"""Create and query a persistent Chroma vector store."""

from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.chunking import Chunk
from src.config import COLLECTION_NAME, VECTORSTORE_DIR
from src.embeddings import embed_texts


def get_chroma_client() -> chromadb.PersistentClient:
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(VECTORSTORE_DIR),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_or_create_collection(client: chromadb.PersistentClient | None = None):
    client = client or get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def reset_collection() -> None:
    """Delete and recreate the collection (use when rebuilding the index)."""
    client = get_chroma_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except ValueError:
        pass
    get_or_create_collection(client)


def add_chunks(chunks: list[Chunk], batch_size: int = 32) -> int:
    """Embed chunks and upsert them into Chroma. Returns number stored."""
    if not chunks:
        return 0

    collection = get_or_create_collection()

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        vectors = embed_texts([c.text for c in batch])

        collection.add(
            ids=[c.id for c in batch],
            documents=[c.text for c in batch],
            embeddings=vectors,
            metadatas=[
                {
                    "document_id": c.document_id,
                    "source": c.source,
                    "title": c.title,
                    "category": c.category,
                    "chunk_index": c.chunk_index,
                }
                for c in batch
            ],
        )

    return len(chunks)


def query_collection(
    question: str,
    top_k: int = 4,
) -> list[dict[str, Any]]:
    """Return retrieved chunks with text, metadata, and distance."""
    collection = get_or_create_collection()
    query_vector = embed_texts([question])[0]

    result = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    hits: list[dict[str, Any]] = []
    if not result["ids"] or not result["ids"][0]:
        return hits

    for i, chunk_id in enumerate(result["ids"][0]):
        hits.append(
            {
                "id": chunk_id,
                "text": result["documents"][0][i],
                "metadata": result["metadatas"][0][i],
                "distance": result["distances"][0][i],
            }
        )
    return hits
