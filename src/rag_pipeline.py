"""Main RAG answering logic: retrieve, generate, return sources."""

import os
from typing import Any

from openai import OpenAI

from src.config import CHAT_MODEL, TOP_K
from src.prompts import RAG_SYSTEM_PROMPT, build_rag_user_message
from src.retriever import format_context, retrieve


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def _build_sources(chunks: list[dict]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    sources: list[dict[str, str]] = []

    for chunk in chunks:
        meta = chunk.get("metadata", {})
        key = (meta.get("title", ""), meta.get("source", ""))
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "title": meta.get("title", "Unknown"),
                "source": meta.get("source", ""),
                "category": meta.get("category", ""),
            }
        )
    return sources


def answer_with_rag(
    question: str,
    top_k: int = TOP_K,
    model: str = CHAT_MODEL,
) -> dict[str, Any]:
    """
    Run the full RAG pipeline.

    Returns:
        answer: generated text
        sources: list of source metadata dicts
        retrieved_chunks: raw retrieval hits
        context: formatted context sent to the LLM
    """
    chunks = retrieve(question, top_k=top_k)
    context = format_context(chunks)

    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user", "content": build_rag_user_message(question, context)},
        ],
    )

    answer = response.choices[0].message.content or ""
    return {
        "answer": answer,
        "sources": _build_sources(chunks),
        "retrieved_chunks": chunks,
        "context": context,
        "mode": "rag",
    }
