"""General RAG — MMR retrieval and context formatting."""

from langchain_chroma import Chroma
from langchain_core.documents import Document

from terramind.rag.general.config import (
    MMR_LAMBDA,
    RETRIEVAL_FETCH_K,
    RETRIEVAL_K,
)


def _section_label(doc: Document) -> str | None:
    parts = [
        doc.metadata.get("h1"),
        doc.metadata.get("h2"),
        doc.metadata.get("h3"),
    ]
    labels = [p.strip() for p in parts if p and str(p).strip()]
    return " > ".join(labels) if labels else None


def retrieve_chunks(
    db: Chroma,
    query: str,
    k: int = RETRIEVAL_K,
    fetch_k: int = RETRIEVAL_FETCH_K,
) -> list[Document]:
    """Maximal Marginal Relevance — diverse, relevant chunks for the raw query."""
    q = (query or "").strip()
    if not q:
        return []

    fetch_k = max(fetch_k, k)
    return db.max_marginal_relevance_search(
        q,
        k=k,
        fetch_k=fetch_k,
        lambda_mult=MMR_LAMBDA,
    )


def format_context(retrieved: list[Document]) -> str:
    blocks: list[str] = []
    for doc in retrieved:
        body = (doc.page_content or "").strip()
        if not body:
            continue
        label = _section_label(doc)
        if label:
            blocks.append(f"[{label}]\n{body}")
        else:
            blocks.append(body)
    return "\n\n---\n\n".join(blocks)
