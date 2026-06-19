"""Product RAG public API used by model adapters, Auto routing, and Advisory."""

from __future__ import annotations

import threading
from collections.abc import Iterator

from langchain_chroma import Chroma
from langchain_core.documents import Document

from terramind.rag.llm_stream import stream_chat_tokens
from terramind.rag.product.chunk import build_all_chunks
from terramind.rag.product.config import CATALOG_PATH, CHAT_MODEL, RAG_PROMPT, RETRIEVAL_K
from terramind.rag.product.generate import format_context, generate_answer_with_metadata
from terramind.rag.product.hybrid import hybrid_retrieve, reset_bm25_cache
from terramind.rag.product.load import load_products
from terramind.rag.product.rerank import rerank_chunks
from terramind.rag.product.rewrite import rewrite_query
from terramind.rag.product.store import build_vector_store, chroma_exists, load_vector_store
from terramind.rag.scoring import sources_from_retrieved as _sources_from_retrieved
from terramind.rag.product.catalog_agent import (
    answer_catalog_question_from_request,
    build_catalog_request,
    route_product_question,
)


_DB: Chroma | None = None
_INIT_LOCK = threading.Lock()


def init_product_rag(reset: bool = False) -> Chroma:
    """Build or load the product Chroma index from translated catalog files."""
    products = load_products(CATALOG_PATH)
    chunks = build_all_chunks(products)
    db = build_vector_store(chunks, reset=reset)
    reset_bm25_cache()

    global _DB
    _DB = db
    return db


def get_product_db() -> Chroma:
    """Return cached product Chroma handle; build the index if it is missing."""
    global _DB
    if _DB is not None:
        return _DB

    with _INIT_LOCK:
        if _DB is None:
            _DB = load_vector_store() if chroma_exists() else init_product_rag(reset=False)
    return _DB


def warm_product_rag() -> None:
    """Eager-load Chroma, BM25, and CrossEncoder so the first user query is not slow."""
    import logging

    from terramind.rag.product.hybrid import build_bm25_index
    from terramind.rag.product.rerank import load_reranker

    log = logging.getLogger(__name__)

    db = get_product_db()
    log.info("Product RAG: Chroma ready (%s vectors)", db._collection.count())

    build_bm25_index()
    log.info("Product RAG: BM25 index ready")

    load_reranker()
    log.info("Product RAG: CrossEncoder reranker ready")


def _retrieve_ranked(db: Chroma, question: str, k: int = RETRIEVAL_K) -> list[Document]:
    retrieval_query = rewrite_query(question)
    print(f"\nOriginal Query: {question}")
    print(f"Rewritten Query: {retrieval_query}\n")
    candidates = hybrid_retrieve(db, retrieval_query, k=max(k * 2, 8))
    return rerank_chunks(question, candidates, top_k=k)


def retrieve_products(
    db: Chroma,
    question: str,
    k: int = RETRIEVAL_K,
) -> list[Document]:
    """Retrieve product chunks using query rewrite, dense+BM25 fusion, and rerank."""
    return _retrieve_ranked(db, question, k=k)


# def answer_with_rag(
#     db: Chroma,
#     question: str,
#     k: int = RETRIEVAL_K,
# ) -> dict:
#     """Route structured catalog questions to Catalog Agent, otherwise use Product RAG."""

#     catalog_request = build_catalog_request(
#         question
#     )

#     route = route_product_question(
#         catalog_request
#     )

#     if route == "catalog_agent":
#         return {
#             "answer": answer_catalog_question_from_request(
#                 catalog_request
#             ),
#             "retrieved": [],
#         }

#     return generate_answer_with_metadata(
#         db,
#         question,
#     )

def answer_with_rag(
    db: Chroma,
    question: str,
    k: int = RETRIEVAL_K,
) -> dict:
    """Route structured catalog questions to Catalog Agent, otherwise use Product RAG."""

    catalog_request = build_catalog_request(
        question
    )

    route = route_product_question(
        catalog_request
    )

    if route == "catalog_agent":
        return {
            "answer": answer_catalog_question_from_request(
                catalog_request
            ),
            "retrieved": [],
            "sources": [],
        }

    result = generate_answer_with_metadata(
        db,
        question,
    )

    retrieved = result.get(
        "retrieved",
        []
    )

    result["sources"] = sources_from_retrieved(
        retrieved
    )

    return result


def stream_answer_with_rag(
    db: Chroma,
    question: str,
    k: int = RETRIEVAL_K,
) -> tuple[list[Document], Iterator[str]]:
    """Route structured catalog questions to Catalog Agent, otherwise stream Product RAG."""

    catalog_request = build_catalog_request(
        question
    )

    route = route_product_question(
        catalog_request
    )

    if route == "catalog_agent":

        answer = answer_catalog_question_from_request(
            catalog_request
        )

        return [], iter([answer])

    chunks = _retrieve_ranked(
        db,
        question,
        k=k,
    )

    if not chunks:
        return [], iter(
            ["I could not find relevant information in the product catalog."]
        )

    prompt = RAG_PROMPT.invoke(
        {
            "context": format_context(chunks),
            "question": question,
        }
    )

    token_gen = stream_chat_tokens(
        prompt.to_messages(),
        model=CHAT_MODEL,
        temperature=0,
    )

    return chunks, token_gen

def sources_from_retrieved(retrieved: list[Document]) -> list[dict]:
    """Format product source chips for API/UI response models."""
    return _sources_from_retrieved("product", retrieved)


__all__ = [
    "answer_with_rag",
    "format_context",
    "get_product_db",
    "init_product_rag",
    "retrieve_products",
    "sources_from_retrieved",
    "stream_answer_with_rag",
    "warm_product_rag",
]