"""Lightweight lexical re-ranking blended with vector retrieval order."""

import re

from langchain_core.documents import Document

from terramind.rag.general.config import HYBRID_LEXICAL_WEIGHT

_TOKEN = re.compile(r"[a-z0-9]+", re.I)


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN.findall(text) if len(t) > 2}


def lexical_score(query: str, document: Document) -> float:
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 0.0
    body = document.page_content or ""
    meta = " ".join(
        str(document.metadata.get(k, ""))
        for k in ("display_name", "filename", "h1", "h2", "h3")
    )
    d_tokens = _tokenize(body + " " + meta)
    if not d_tokens:
        return 0.0
    overlap = len(q_tokens & d_tokens)
    return overlap / len(q_tokens)


def rerank_with_lexical(
    query: str,
    candidates: list[Document],
    k: int,
) -> list[Document]:
    """
    Re-order candidates: vector order (implicit rank) + lexical overlap boost.
    candidates[0] is most similar from vector search.
    """
    if not candidates or k <= 0:
        return []

    scored: list[tuple[float, int, Document]] = []
    for rank, doc in enumerate(candidates):
        vector_prior = 1.0 - (rank / max(len(candidates), 1))
        lex = lexical_score(query, doc)
        combined = (1.0 - HYBRID_LEXICAL_WEIGHT) * vector_prior + HYBRID_LEXICAL_WEIGHT * lex
        scored.append((combined, rank, doc))

    scored.sort(key=lambda x: (-x[0], x[1]))
    return [doc for _, _, doc in scored[:k]]
