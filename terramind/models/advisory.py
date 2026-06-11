"""Advisory mode — combined general + product retrieval, single LLM generation."""

from __future__ import annotations

import re
from collections.abc import Iterator

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from terramind.models.conversation import build_prompt_question, build_retrieval_query
from terramind.rag.general import get_general_db, sources_from_retrieved as general_sources
from terramind.rag.general.config import CHAT_MODEL, RETRIEVAL_K as GENERAL_K
from terramind.rag.general.retrieve import format_context as format_general_context
from terramind.rag.general.retrieve import retrieve_chunks
from terramind.rag.llm_stream import stream_chat_tokens
from terramind.rag.product import (
    format_context as format_product_context,
    get_product_db,
    retrieve_products,
    sources_from_retrieved as product_sources,
)
from terramind.rag.product.config import RETRIEVAL_K as PRODUCT_K
from terramind.rag.scoring import aggregate_retrieval_score, confidence_from_score

ADVISORY_PROMPT = ChatPromptTemplate.from_template(
    """You are TerraMind Advisory — you combine trusted public agriculture guidance with
the company product catalog in ONE response.

Public agriculture reference excerpts (each block starts with a source label in brackets):
{general_context}

Company product catalog records:
{product_context}

User message (may include brief notes from an uploaded crop photo):
{question}

Structure your answer with exactly these two Markdown sections (in this order):

### Public agriculture guidance
Write practical guidance from the public excerpts: GAP, IPM, soil health, crop protection
principles. Do NOT recommend specific catalog products in this section. Cite source labels
from the excerpts when stating important facts. If the excerpts do not apply, say briefly in
1–3 sentences — do not invent rates or product names.

### Company product catalog
Answer from the catalog records only when the user has a crop problem, pest, disease, weed,
or product need. Name the best catalog match and explain why; include use/dilution/dosage only
when the catalog provides them. If the catalog does not apply, say so in one or two sentences
— do not invent products or SKUs.

Rules:
- Answer what they actually asked; match the user's language (English, Arabic, etc.).
- Product facts must come ONLY from the catalog records; general facts ONLY from public excerpts.
- If photo notes are included, weave them briefly — no separate "image analysis" report.
- Do NOT open with "Hello! I'm TerraMind..." unless they greeted you or asked who you are.
- Use clear Markdown: short paragraphs, **bold** for emphasis, bullet or numbered lists for steps.
- Prefer IPM before chemicals; remind users to follow local labels and regulations.
"""
)

_SECTION_GENERAL = re.compile(
    r"###\s*Public agriculture guidance\s*\n+(.*?)(?=###\s*Company product catalog|\Z)",
    re.DOTALL | re.IGNORECASE,
)
_SECTION_PRODUCT = re.compile(
    r"###\s*Company product catalog\s*\n+(.*)\Z",
    re.DOTALL | re.IGNORECASE,
)


def split_advisory_sections(answer: str) -> tuple[str, str]:
    """Split merged advisory answer into general and product section bodies."""
    text = (answer or "").strip()
    if not text:
        return "", ""
    general_match = _SECTION_GENERAL.search(text)
    product_match = _SECTION_PRODUCT.search(text)
    general = (general_match.group(1) if general_match else "").strip()
    product = (product_match.group(1) if product_match else "").strip()
    return general, product


def _retrieve_advisory(
    question: str,
    history: list | None,
    image_analysis: str | None,
) -> tuple[str, list, list, list[dict], list[dict], dict]:
    retrieval_q = build_retrieval_query(question, image_analysis)
    generation_q = build_prompt_question(question, history, image_analysis)

    general_retrieved = retrieve_chunks(get_general_db(), retrieval_q, k=GENERAL_K)
    product_retrieved = retrieve_products(get_product_db(), retrieval_q, k=PRODUCT_K)

    g_sources = general_sources(general_retrieved)
    p_sources = product_sources(product_retrieved)
    g_score = aggregate_retrieval_score(general_retrieved)
    p_score = aggregate_retrieval_score(product_retrieved)
    scores = [s for s in (g_score, p_score) if s is not None]
    retrieval_score = max(scores) if scores else None
    total_chunks = len(general_retrieved) + len(product_retrieved)

    metrics = {
        "sources": g_sources + p_sources,
        "confidence": confidence_from_score(
            retrieval_score, has_chunks=total_chunks > 0
        ),
        "retrieval_score": retrieval_score,
        "retrieved_chunks": total_chunks,
    }
    return (
        generation_q,
        general_retrieved,
        product_retrieved,
        g_sources,
        p_sources,
        metrics,
    )


def _prompt_messages(
    generation_q: str,
    general_retrieved: list,
    product_retrieved: list,
):
    general_context = format_general_context(general_retrieved)
    product_context = format_product_context(product_retrieved)
    return ADVISORY_PROMPT.invoke(
        {
            "general_context": general_context or "(No matching public excerpts retrieved.)",
            "product_context": product_context or "(No matching catalog records retrieved.)",
            "question": generation_q,
        }
    ).to_messages()


def answer_advisory(
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
) -> dict:
    """Retrieve from both indexes once, generate one combined advisory answer."""
    (
        generation_q,
        general_retrieved,
        product_retrieved,
        g_sources,
        p_sources,
        metrics,
    ) = _retrieve_advisory(question, history, image_analysis)

    messages = _prompt_messages(generation_q, general_retrieved, product_retrieved)
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0.3)
    answer = (llm.invoke(messages).content or "").strip()

    general_body, product_body = split_advisory_sections(answer)
    g_score = aggregate_retrieval_score(general_retrieved)
    p_score = aggregate_retrieval_score(product_retrieved)
    from terramind.rag.scoring import confidence_from_retrieval

    return {
        "answer": answer,
        **metrics,
        "system": "advisory",
        "general": {
            "answer": general_body,
            "sources": g_sources,
            "confidence": confidence_from_retrieval(general_retrieved),
            "retrieval_score": g_score,
            "retrieved_chunks": len(general_retrieved),
            "system": "general_rag",
        },
        "product": {
            "answer": product_body,
            "sources": p_sources,
            "confidence": confidence_from_retrieval(product_retrieved),
            "retrieval_score": p_score,
            "retrieved_chunks": len(product_retrieved),
            "system": "product_rag",
        },
    }


def stream_advisory_rag(
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
) -> Iterator[dict]:
    """Yield status/token events for one combined advisory RAG generation."""
    (
        generation_q,
        general_retrieved,
        product_retrieved,
        _g_sources,
        _p_sources,
        metrics,
    ) = _retrieve_advisory(question, history, image_analysis)

    yield {
        "event": "status",
        "message": "Searching agriculture references and product catalog…",
    }
    yield {
        "event": "status",
        "message": (
            f"Found {len(general_retrieved)} excerpts and "
            f"{len(product_retrieved)} catalog rows — writing answer…"
        ),
        "retrieved_chunks": metrics["retrieved_chunks"],
    }

    messages = _prompt_messages(generation_q, general_retrieved, product_retrieved)
    parts: list[str] = []
    for piece in stream_chat_tokens(messages, model=CHAT_MODEL, temperature=0.3):
        parts.append(piece)
        yield {"event": "token", "content": piece}

    yield {
        "event": "done",
        "answer": "".join(parts),
        **metrics,
        "system": "advisory",
        "model": "advisory",
    }
