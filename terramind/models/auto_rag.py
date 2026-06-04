"""Auto mode — route to product or general RAG, then answer."""

from terramind.models.conversation import build_retrieval_query
from terramind.models.general_rag import answer as general_rag_answer
from terramind.models.product_rag import answer as product_rag_answer
from terramind.models.router import route_question

_BACKENDS = {
    "product_rag": product_rag_answer,
    "general_rag": general_rag_answer,
}


def answer(
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
    image_base64: str | None = None,
    image_mime: str | None = None,
    **_,
) -> dict:
    retrieval_q = build_retrieval_query(question, image_analysis)
    routed_to, router_reason = route_question(question, retrieval_q)
    backend = _BACKENDS[routed_to]
    result = backend(
        question,
        history=history,
        image_analysis=image_analysis,
        image_base64=image_base64,
        image_mime=image_mime,
    )
    return {
        **result,
        "system": "auto_rag",
        "routed_to": routed_to,
        "router_reason": router_reason,
    }
