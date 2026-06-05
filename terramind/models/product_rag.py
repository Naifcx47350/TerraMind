"""Mode 1 — product catalog RAG (client Excel data)."""

from terramind.models.conversation import build_prompt_question
from terramind.models.router import skips_document_retrieval
from terramind.rag.product import answer_with_rag, get_product_db, sources_from_retrieved


def answer(
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
    **_,
) -> dict:
    if skips_document_retrieval(question, image_analysis):
        from terramind.models.base_llm import answer as base_llm_answer

        out = base_llm_answer(
            question,
            history=history,
            image_analysis=image_analysis,
        )
        out["system"] = "product_rag"
        out["confidence"] = ""
        out["retrieval_score"] = None
        out["retrieved_chunks"] = 0
        out["sources"] = []
        return out

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
