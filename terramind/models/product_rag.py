"""Mode 1 — product catalog RAG (client Excel data)."""

from terramind.models.conversation import build_prompt_question
from terramind.rag.product import answer_with_rag, get_product_db, sources_from_retrieved


def answer(
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
    **_,
) -> dict:
    db = get_product_db()
    q = build_prompt_question(question, history, image_analysis)
    result = answer_with_rag(db, q)
    retrieved = result["retrieved"]
    sources = sources_from_retrieved(retrieved)
    from terramind.rag.scoring import rag_metrics

    return {
        "answer": result["answer"] or "",
        "system": "product_rag",
        **rag_metrics(retrieved, sources),
    }
