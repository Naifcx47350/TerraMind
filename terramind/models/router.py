"""Route a user question to product_rag, general_rag, or base_llm (Auto mode)."""

from __future__ import annotations

from terramind.meta_questions import (
    has_agriculture_intent,
    has_strong_product_intent,
    is_clarification_question,
    is_image_describe_question,
    is_meta_question,
    is_off_topic_question,
    is_translation_request,
)
from terramind.models.conversation import build_retrieval_query
from terramind.rag.general.topics import infer_topics_from_query
from terramind.rag.scoring import distance_to_relevance

# Strong catalog / label intent
PRODUCT_QUERY_KEYWORDS: tuple[str, ...] = (
    "product catalog",
    "catalog",
    "our product",
    "your product",
    "which product",
    "what product",
    "sku",
    "product name",
    "registered crop",
    "registered for",
    "label rate",
    "label says",
    "dosage",
    "dose rate",
    "mixing rate",
    "how to apply",
    "how do i apply",
    "application rate",
    "spray rate",
    "tank mix",
    "active ingredient",
    "herbicide",
    "insecticide",
    "fungicide product",
    "glufosinate",
    "glyphosate",
    "manufacturer",
    "product sheet",
    "product label",
    "msds",
    "sds",
)

# Mixed questions: catalog + field — route to advisory-style general-first only in Auto
# if both scores are close; here we bump general when disease/IPM dominates.
MIXED_GENERAL_HINTS: tuple[str, ...] = (
    "late blight",
    "ipm",
    "integrated pest",
    "integrated disease",
    "crop rotation",
    "soil health",
    "good agricultural",
    "gap",
    "monitoring",
    "threshold",
    "biological control",
    "sanitation",
    "from our catalog",
    "from the catalog",
)

ROUTE_SCORE_MARGIN = 0.06
MIN_RAG_ROUTE_SCORE = 0.38


def _keyword_counts(query: str) -> tuple[int, int, int]:
    """Returns (product_hits, general_topic_hits, mixed_general_hits)."""
    q = (query or "").lower()
    product = sum(1 for kw in PRODUCT_QUERY_KEYWORDS if kw in q)
    general_topics = len(infer_topics_from_query(q, max_topics=3))
    mixed = sum(1 for kw in MIXED_GENERAL_HINTS if kw in q)
    return product, general_topics, mixed


def _probe_top_score(db, query: str) -> float | None:
    q = (query or "").strip()
    if not q:
        return None
    try:
        pairs = db.similarity_search_with_score(q, k=1)
    except Exception:
        return None
    if not pairs:
        return None
    _, distance = pairs[0]
    return distance_to_relevance(distance)


def route_question(
    question: str,
    retrieval_query: str | None = None,
    image_analysis: str | None = None,
) -> tuple[str, str]:
    """
    Choose product_rag, general_rag, or base_llm.

    Meta / conversational questions skip retrieval and use base_llm.
    Photo-describe questions (with vision text) use base_llm, not document RAG.
    Explicit "what product…" requests prefer product_rag over general IPM docs.
    """
    if is_meta_question(question):
        return "base_llm", "conversational question — no agriculture retrieval"

    if is_clarification_question(question):
        return "base_llm", "unclear or vague question — no agriculture retrieval"

    if is_translation_request(question):
        return "base_llm", "translation request — use conversation context, no retrieval"

    if is_off_topic_question(question):
        return "base_llm", "off-topic question — no agriculture retrieval"

    if (image_analysis or "").strip() and is_image_describe_question(question):
        return "base_llm", "photo description — vision context, no document retrieval"

    if has_strong_product_intent(question):
        return "product_rag", "explicit product recommendation request"

    rq = (retrieval_query or question or "").strip()
    product_hits, general_topics, mixed_hints = _keyword_counts(question)

    from terramind.rag.general import get_general_db
    from terramind.rag.product import get_product_db

    general_score = _probe_top_score(get_general_db(), rq)
    product_score = _probe_top_score(get_product_db(), rq)

    # Clear catalog-only wording
    if product_hits >= 2 and general_topics == 0:
        return "product_rag", "catalog or product-label keywords"

    if general_topics >= 2 and product_hits == 0:
        return "general_rag", "agriculture knowledge topic keywords"

    # Dual-index comparison
    if product_score is not None and general_score is not None:
        diff = product_score - general_score
        if diff > ROUTE_SCORE_MARGIN:
            return (
                "product_rag",
                f"catalog retrieval stronger ({product_score:.2f} vs {general_score:.2f})",
            )
        if diff < -ROUTE_SCORE_MARGIN:
            return (
                "general_rag",
                f"reference retrieval stronger ({general_score:.2f} vs {product_score:.2f})",
            )
        # Scores tied — explicit product wording wins over mixed IPM + catalog
        if product_hits >= 1 and has_strong_product_intent(question):
            return "product_rag", "product recommendation wording with tied scores"
        if mixed_hints >= 1 and product_hits >= 1:
            return (
                "general_rag",
                "mixed field + catalog question — public guidance first",
            )

    # Single-index signal
    if product_score is not None and general_score is None:
        return "product_rag", "catalog index match"
    if general_score is not None and product_score is None:
        return "general_rag", "reference index match"

    # Keyword tie-break
    if product_hits > general_topics + mixed_hints:
        return "product_rag", "product-oriented wording"
    if general_topics > product_hits or mixed_hints > 0:
        return "general_rag", "field-practice oriented wording"

    # Default: public agriculture layer unless catalog clearly wins on score
    if product_score is not None and general_score is not None:
        if product_score >= general_score:
            return "product_rag", "default tie — catalog score at least as strong"
    if product_score is not None and (general_score is None or product_score > (general_score or 0)):
        return "product_rag", "catalog retrieval available"

    best_score = max(
        (s for s in (general_score, product_score) if s is not None),
        default=None,
    )
    if best_score is not None and best_score < MIN_RAG_ROUTE_SCORE:
        if not has_agriculture_intent(question) or is_clarification_question(question):
            return (
                "base_llm",
                f"weak document match ({best_score:.2f}) — conversational reply",
            )

    return "general_rag", "default — agriculture knowledge"


def build_retrieval_query_for_route(
    question: str,
    image_analysis: str | None = None,
) -> str:
    return build_retrieval_query(question, image_analysis)
