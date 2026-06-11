"""Product catalog RAG — translated Excel → Chroma → retrieve → answer."""

from terramind.rag.product.pipeline import (
    answer_with_rag,
    format_context,
    get_product_db,
    init_product_rag,
    retrieve_products,
    sources_from_retrieved,
    stream_answer_with_rag,
)

__all__ = [
    "answer_with_rag",
    "format_context",
    "get_product_db",
    "init_product_rag",
    "retrieve_products",
    "sources_from_retrieved",
    "stream_answer_with_rag",
]
