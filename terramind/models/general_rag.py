"""Mode 2 — general agriculture document RAG."""

import logging

from terramind.models.conversation import (
    build_prompt_question,
    build_retrieval_query,
)
from terramind.rag.general import answer_with_rag, get_general_db, sources_from_retrieved

logger = logging.getLogger(__name__)


def answer(
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
    **_,
) -> dict:
    db = get_general_db()
    retrieval_q = build_retrieval_query(question, image_analysis)
    generation_q = build_prompt_question(question, history, image_analysis)
    result = answer_with_rag(
        db,
        retrieval_q,
        generation_prompt=generation_q,
    )
    sources = sources_from_retrieved(result["retrieved"])
    filenames = sorted(
        {d.metadata.get("filename") for d in result["retrieved"] if d.metadata.get("filename")}
    )
    logger.debug(
        "general_rag retrieval_q_len=%s chunks=%s source_files=%s",
        len(retrieval_q),
        len(result["retrieved"]),
        filenames,
    )
    return {
        "answer": result["answer"] or "",
        "sources": sources,
        "confidence": "high" if sources else "low",
        "retrieved_chunks": len(result["retrieved"]),
        "system": "general_rag",
    }
