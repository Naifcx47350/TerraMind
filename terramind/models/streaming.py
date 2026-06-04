"""NDJSON event streams for model answers (status + tokens + done metadata)."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Iterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from terramind.models.base_llm import CHAT_MODEL, SYSTEM_PROMPT
from terramind.models.conversation import build_prompt_question, build_retrieval_query
from terramind.models.image_context import question_with_image_context
from terramind.models.router import route_question
from terramind.models import MODEL_REGISTRY, resolve_image_analysis
from terramind.meta_questions import advisory_meta_answer, is_meta_question
from terramind.rag.llm_stream import stream_chat_tokens


def _status(message: str, **extra) -> dict:
    return {"event": "status", "message": message, **extra}


def _token(content: str) -> dict:
    return {"event": "token", "content": content}


def _yield_text_as_tokens(text: str) -> Iterator[dict]:
    for part in re.findall(r"\S+\s*", text or ""):
        yield _token(part)


def _stream_base_llm(
    question: str,
    history: list | None,
    image_analysis: str | None,
) -> Iterator[dict]:
    yield _status("Generating answer…")
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in (history or [])[-10:]:
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", "")
        content = (msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")) or ""
        if not content.strip():
            continue
        if role in ("assistant", "bot"):
            messages.append(AIMessage(content=content))
        elif role in ("user", "human"):
            messages.append(HumanMessage(content=content))
    q = question_with_image_context(question, image_analysis)
    messages.append(HumanMessage(content=q))

    parts: list[str] = []
    for piece in stream_chat_tokens(messages, model=CHAT_MODEL, temperature=0.3):
        parts.append(piece)
        yield _token(piece)

    yield {
        "event": "done",
        "answer": "".join(parts),
        "sources": [],
        "confidence": "medium",
        "retrieval_score": None,
        "retrieved_chunks": 0,
        "system": "base_llm",
        "model": "base_llm",
    }


def _stream_general_rag(
    question: str,
    history: list | None,
    image_analysis: str | None,
) -> Iterator[dict]:
    from terramind.rag.general import get_general_db, sources_from_retrieved
    from terramind.rag.general.generate import stream_generate_answer
    from terramind.rag.general.retrieve import format_context, retrieve_chunks
    from terramind.rag.general.config import RETRIEVAL_K
    from terramind.rag.scoring import rag_metrics

    db = get_general_db()
    retrieval_q = build_retrieval_query(question, image_analysis)
    generation_q = build_prompt_question(question, history, image_analysis)

    yield _status("Searching agriculture references…")
    retrieved = retrieve_chunks(db, retrieval_q, k=RETRIEVAL_K)
    sources = sources_from_retrieved(retrieved)
    metrics = rag_metrics(retrieved, sources)
    yield _status(
        f"Found {len(retrieved)} excerpts — writing answer…",
        retrieved_chunks=len(retrieved),
    )

    parts: list[str] = []
    context = format_context(retrieved)
    for piece in stream_generate_answer(context, generation_q):
        parts.append(piece)
        yield _token(piece)

    yield {
        "event": "done",
        "answer": "".join(parts),
        "sources": sources,
        **metrics,
        "system": "general_rag",
        "model": "general_rag",
    }


def _stream_product_rag(
    question: str,
    history: list | None,
    image_analysis: str | None,
) -> Iterator[dict]:
    from terramind.rag.product import get_product_db, sources_from_retrieved, stream_answer_with_rag
    from terramind.rag.scoring import rag_metrics

    db = get_product_db()
    q = build_prompt_question(question, history, image_analysis)

    yield _status("Searching product catalog…")
    retrieved, token_gen = stream_answer_with_rag(db, q)
    sources = sources_from_retrieved(retrieved)
    metrics = rag_metrics(retrieved, sources)
    yield _status(
        f"Found {len(retrieved)} catalog rows — writing answer…",
        retrieved_chunks=len(retrieved),
    )

    parts: list[str] = []
    for piece in token_gen:
        parts.append(piece)
        yield _token(piece)

    yield {
        "event": "done",
        "answer": "".join(parts),
        "sources": sources,
        **metrics,
        "system": "product_rag",
        "model": "product_rag",
    }


def _stream_auto_rag(
    question: str,
    history: list | None,
    image_analysis: str | None,
) -> Iterator[dict]:
    retrieval_q = build_retrieval_query(question, image_analysis)
    yield _status("Choosing knowledge source…")
    routed_to, router_reason = route_question(question, retrieval_q, image_analysis)
    label = MODEL_REGISTRY[routed_to]["name"]
    yield _status(
        f"Using {label}…",
        routed_to=routed_to,
        router_reason=router_reason,
    )

    if routed_to == "base_llm":
        backend = _stream_base_llm
    elif routed_to == "general_rag":
        backend = _stream_general_rag
    else:
        backend = _stream_product_rag

    for event in backend(question, history, image_analysis):
        if event.get("event") == "done":
            event["system"] = "auto_rag"
            event["model"] = "auto_rag"
            event["routed_to"] = routed_to
            event["router_reason"] = router_reason
        yield event


def stream_model_events(
    model_id: str,
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
    image_base64: str | None = None,
    image_mime: str | None = None,
    language: str | None = None,
) -> Iterator[str]:
    """Yield NDJSON lines: status, token, then done."""
    if model_id not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model: {model_id}")

    start = time.time()
    analysis = resolve_image_analysis(
        question, image_analysis, image_base64, image_mime, language
    )
    if analysis and image_base64:
        yield json.dumps(_status("Analyzing image…"), ensure_ascii=False) + "\n"

    streams = {
        "base_llm": _stream_base_llm,
        "general_rag": _stream_general_rag,
        "product_rag": _stream_product_rag,
        "auto_rag": _stream_auto_rag,
    }
    stream_fn = streams[model_id]

    for event in stream_fn(question, history, analysis):
        if event.get("event") == "done":
            event["latency_ms"] = int((time.time() - start) * 1000)
            if "model" not in event:
                event["model"] = model_id
        yield json.dumps(event, ensure_ascii=False) + "\n"


def stream_advisory_events(
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
    image_base64: str | None = None,
    image_mime: str | None = None,
    language: str | None = None,
) -> Iterator[str]:
    """Stream advisory mode: general section then product section."""
    start = time.time()
    q = question.strip()
    analysis = resolve_image_analysis(
        question, image_analysis, image_base64, image_mime, language
    )
    if analysis and image_base64:
        yield json.dumps(_status("Analyzing image…"), ensure_ascii=False) + "\n"

    if is_meta_question(q):
        intro = advisory_meta_answer()
        catalog_note = (
            "No catalog search was needed for this question. "
            "Ask about a crop, pest, or product when you want a recommendation "
            "from the company catalog."
        )
        merged_parts: list[str] = []
        header = "### Public agriculture guidance\n\n"
        for event in _yield_text_as_tokens(header):
            merged_parts.append(event["content"])
            yield json.dumps(event, ensure_ascii=False) + "\n"
        for event in _yield_text_as_tokens(intro + "\n\n"):
            merged_parts.append(event["content"])
            yield json.dumps(event, ensure_ascii=False) + "\n"
        section2 = "### Company product catalog\n\n"
        for event in _yield_text_as_tokens(section2):
            merged_parts.append(event["content"])
            yield json.dumps(event, ensure_ascii=False) + "\n"
        for event in _yield_text_as_tokens(catalog_note):
            merged_parts.append(event["content"])
            yield json.dumps(event, ensure_ascii=False) + "\n"
        yield json.dumps(
            {
                "event": "done",
                "answer": "".join(merged_parts),
                "sources": [],
                "confidence": "high",
                "retrieval_score": None,
                "retrieved_chunks": 0,
                "system": "advisory",
                "model": "advisory",
                "latency_ms": int((time.time() - start) * 1000),
            },
            ensure_ascii=False,
        ) + "\n"
        return

    yield json.dumps(_status("Public agriculture guidance…"), ensure_ascii=False) + "\n"
    header = "### Public agriculture guidance\n\n"
    for event in _yield_text_as_tokens(header):
        yield json.dumps(event, ensure_ascii=False) + "\n"

    general_parts: list[str] = [header]
    general_done: dict | None = None
    for event in _stream_general_rag(q, history, analysis):
        if event.get("event") == "token":
            general_parts.append(event["content"])
            yield json.dumps(event, ensure_ascii=False) + "\n"
        elif event.get("event") == "done":
            general_done = event

    yield json.dumps(_status("Company product catalog…"), ensure_ascii=False) + "\n"
    section_hdr = "\n\n### Company product catalog\n\n"
    for event in _yield_text_as_tokens(section_hdr):
        general_parts.append(event["content"])
        yield json.dumps(event, ensure_ascii=False) + "\n"

    product_question = (
        f"{q}\n\n"
        "Use the following agriculture reference summary when recommending "
        "a catalog product (if any):\n"
        f"{(general_done or {}).get('answer', '')[:2000]}\n\n"
        "Only recommend a catalog product if the user asked about a crop problem, "
        "pest, disease, weed, or product need. Otherwise say in one or two sentences "
        "that the catalog does not apply — do not invent a product match."
    )
    product_parts: list[str] = []
    product_done: dict | None = None
    for event in _stream_product_rag(product_question, history, analysis):
        if event.get("event") == "status":
            continue
        if event.get("event") == "token":
            product_parts.append(event["content"])
            yield json.dumps(event, ensure_ascii=False) + "\n"
        elif event.get("event") == "done":
            product_done = event

    merged = "".join(general_parts) + "".join(product_parts)
    sources = list((general_done or {}).get("sources") or []) + list(
        (product_done or {}).get("sources") or []
    )
    g_score = (general_done or {}).get("retrieval_score")
    p_score = (product_done or {}).get("retrieval_score")
    scores = [s for s in (g_score, p_score) if s is not None]
    retrieval_score = max(scores) if scores else None
    from terramind.rag.scoring import confidence_from_score

    total_chunks = (general_done or {}).get("retrieved_chunks", 0) + (
        product_done or {}
    ).get("retrieved_chunks", 0)
    yield json.dumps(
        {
            "event": "done",
            "answer": merged,
            "sources": sources,
            "confidence": confidence_from_score(
                retrieval_score, has_chunks=total_chunks > 0
            ),
            "retrieval_score": retrieval_score,
            "retrieved_chunks": total_chunks,
            "system": "advisory",
            "model": "advisory",
            "latency_ms": int((time.time() - start) * 1000),
        },
        ensure_ascii=False,
    ) + "\n"
