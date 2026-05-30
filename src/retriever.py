"""Retrieve relevant knowledge chunks for a user question."""

from src.config import TOP_K
from src.vector_store import query_collection


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    """Return top-k chunks ranked by vector similarity."""
    return query_collection(question, top_k=top_k)


def format_context(chunks: list[dict]) -> str:
    """Format retrieved chunks for the LLM prompt."""
    if not chunks:
        return ""

    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata", {})
        header = f"[Source {i}] {meta.get('title', 'Unknown')} ({meta.get('source', '')})"
        parts.append(header + "\n" + chunk["text"])
    return "\n\n".join(parts)
