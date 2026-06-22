"""Infer corpus topic from user retrieval queries."""

from core.rag.general.config import TOPIC_QUERY_KEYWORDS


def infer_topics_from_query(query: str, max_topics: int = 2) -> list[str]:
    """Return topic tags sorted by keyword match count (best first)."""
    q = (query or "").lower()
    if not q:
        return []

    scores: list[tuple[int, str]] = []
    for topic, keywords in TOPIC_QUERY_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in q)
        if count:
            scores.append((count, topic))

    scores.sort(key=lambda x: (-x[0], x[1]))
    return [t for _, t in scores[:max_topics]]
