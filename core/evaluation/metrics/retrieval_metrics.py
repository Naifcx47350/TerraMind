"""
Retrieval-stage ranking metrics (ground-truth based).

These compare the product_id of each retrieved chunk against a known
relevant product_id for the question. They require a dataset that maps
each question to the correct product (see the "product_id" field in
datasets/golden_product_rag.jsonl), not just a coarse category label.
"""

import math

from core.rag.product.store import load_vector_store


def relevance_flags(
    chunks,
    relevant_product_id: str,
) -> list[int]:
    """
    Binary relevance per retrieved chunk,
    in retrieval rank order.
    """

    return [
        1 if chunk.metadata.get("product_id") == relevant_product_id else 0
        for chunk in chunks
    ]


def precision_at_k(flags: list[int]) -> float:
    """
    Fraction of retrieved chunks that
    are relevant.
    """

    if not flags:
        return 0.0

    return sum(flags) / len(flags)


def recall_at_k(
    flags: list[int],
    total_relevant: int,
) -> float:
    """
    Fraction of all relevant chunks
    that were retrieved.
    """

    if total_relevant == 0:
        return 1.0

    return sum(flags) / total_relevant


def hit_rate(flags: list[int]) -> float:
    """
    1.0 if at least one retrieved chunk
    is relevant, else 0.0.
    """

    return 1.0 if any(flags) else 0.0


def ndcg_at_k(
    flags: list[int],
    total_relevant: int,
) -> float:
    """
    Normalized Discounted Cumulative Gain
    over binary relevance.
    """

    dcg = sum(
        flag / math.log2(rank + 1)
        for rank, flag in enumerate(flags, start=1)
    )

    ideal_hits = min(total_relevant, len(flags))

    idcg = sum(
        1 / math.log2(rank + 1)
        for rank in range(1, ideal_hits + 1)
    )

    if idcg == 0:
        return 1.0

    return dcg / idcg


_relevant_chunk_count_cache: dict[str, int] = {}


def count_relevant_chunks(product_id: str) -> int:
    """
    Total number of indexed chunks belonging
    to a product (ground truth for recall).

    Metadata-only lookup, no embedding call.
    """

    if product_id in _relevant_chunk_count_cache:
        return _relevant_chunk_count_cache[product_id]

    db = load_vector_store()

    result = db.get(
        where={"product_id": product_id}
    )

    count = len(result.get("ids", []))

    _relevant_chunk_count_cache[product_id] = count

    return count


def retrieval_metrics(
    chunks,
    relevant_product_id: str,
) -> dict:
    """
    Compute all ground-truth retrieval
    metrics for one question.
    """

    flags = relevance_flags(
        chunks,
        relevant_product_id,
    )

    total_relevant = count_relevant_chunks(
        relevant_product_id
    )

    return {
        "precision_at_k": precision_at_k(flags),
        "recall_at_k": recall_at_k(flags, total_relevant),
        "hit_rate": hit_rate(flags),
        "ndcg_at_k": ndcg_at_k(flags, total_relevant),
    }
