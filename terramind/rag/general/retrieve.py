"""General RAG — topic-aware MMR + lexical rerank and context formatting."""

from langchain_chroma import Chroma
from langchain_core.documents import Document

from terramind.rag.general.config import (
    MMR_LAMBDA,
    RETRIEVAL_FETCH_K,
    RETRIEVAL_K,
    TOPIC_BOOST_FETCH_MULTIPLIER,
    display_name_for_file,
)
from terramind.rag.general.hybrid import rerank_with_lexical
from terramind.rag.general.topics import infer_topics_from_query


def _section_label(doc: Document) -> str | None:
    parts = [
        doc.metadata.get("h1"),
        doc.metadata.get("h2"),
        doc.metadata.get("h3"),
    ]
    labels = [p.strip() for p in parts if p and str(p).strip()]
    return " > ".join(labels) if labels else None


def _source_label(doc: Document) -> str:
    fn = doc.metadata.get("filename")
    if fn:
        named = display_name_for_file(str(fn))
        if named:
            return named
    return doc.metadata.get("display_name") or doc.metadata.get("title") or "Document"


def _topic_boost_candidates(
    candidates: list[Document], topics: list[str]
) -> list[Document]:
    if not topics:
        return candidates
    topic_set = set(topics)
    preferred = [d for d in candidates if d.metadata.get("corpus_topic") in topic_set]
    other = [d for d in candidates if d.metadata.get("corpus_topic") not in topic_set]
    return preferred + other


def retrieve_chunks(
    db: Chroma,
    query: str,
    k: int = RETRIEVAL_K,
    fetch_k: int | None = None,
) -> list[Document]:
    """MMR over a larger pool, topic boost, then lexical rerank."""
    q = (query or "").strip()
    if not q:
        return []

    topics = infer_topics_from_query(q)
    base_fetch = fetch_k or RETRIEVAL_FETCH_K
    if topics:
        base_fetch = min(base_fetch * TOPIC_BOOST_FETCH_MULTIPLIER, 48)

    pool_k = max(base_fetch, k * 3)
    pool = db.max_marginal_relevance_search(
        q,
        k=pool_k,
        fetch_k=max(pool_k, base_fetch),
        lambda_mult=MMR_LAMBDA,
    )
    pool = _topic_boost_candidates(pool, topics)
    return rerank_with_lexical(q, pool, k=k)


def format_context(retrieved: list[Document]) -> str:
    blocks: list[str] = []
    for doc in retrieved:
        body = (doc.page_content or "").strip()
        if not body:
            continue
        label = _source_label(doc)
        section = _section_label(doc)
        if section:
            blocks.append(f"[{label} > {section}]\n{body}")
        else:
            blocks.append(f"[{label}]\n{body}")
    return "\n\n---\n\n".join(blocks)
