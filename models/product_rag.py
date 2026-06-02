"""Mode 1 — product catalog RAG (client Excel data via Rag_Pc.py)."""

from models.conversation import build_prompt_question
from Rag_Pc import answer_with_rag, get_product_db, sources_from_retrieved


def answer(
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
    **_,
) -> dict:
    db = get_product_db()
    q = build_prompt_question(question, history, image_analysis)
    result = answer_with_rag(db, q)
    sources = sources_from_retrieved(result["retrieved"])
    return {
        "answer": result["answer"] or "",
        "sources": sources,
        "confidence": "high" if sources else "low",
        "retrieved_chunks": len(result["retrieved"]),
        "system": "product_rag",
    }
