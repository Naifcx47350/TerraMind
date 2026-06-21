"""Mode 2 — general agriculture document RAG."""

import logging

from core.models.conversation import (
    build_prompt_question,
    build_retrieval_query,
)
from core.models.router import skips_document_retrieval
from core.rag.general import answer_with_rag, get_general_db, sources_from_retrieved

logger = logging.getLogger(__name__)


def answer(
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
    **_,
) -> dict:
    if skips_document_retrieval(question, image_analysis):
        from core.models.base_llm import answer as base_llm_answer

        out = base_llm_answer(
            question,
            history=history,
            image_analysis=image_analysis,
        )
        out["system"] = "general_rag"
        out["confidence"] = ""
        out["retrieval_score"] = None
        out["retrieved_chunks"] = 0
        out["sources"] = []
        return out

    db = get_general_db()
    retrieval_q = build_retrieval_query(question, image_analysis)
    generation_q = build_prompt_question(question, history, image_analysis)
    result = answer_with_rag(
        db,
        retrieval_q,
        generation_prompt=generation_q,
    )
    retrieved = result["retrieved"]
    sources = sources_from_retrieved(retrieved)
    filenames = sorted(
        {d.metadata.get("filename") for d in retrieved if d.metadata.get("filename")}
    )
    logger.debug(
        "general_rag retrieval_q_len=%s chunks=%s source_files=%s",
        len(retrieval_q),
        len(retrieved),
        filenames,
    )
    from core.rag.scoring import rag_metrics

    return {
        "answer": result["answer"] or "",
        "system": "general_rag",
        **rag_metrics(retrieved, sources),
    }
