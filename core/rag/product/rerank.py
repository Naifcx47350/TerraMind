"""
Cross Encoder reranking for Product RAG.
"""

from sentence_transformers import (
    CrossEncoder,
)

from core.rag.product.hybrid import (
    hybrid_retrieve,
)

RERANK_MODEL = (
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

_model = None


def load_reranker():
    """
    Load Cross Encoder model once.
    """

    global _model

    if _model is None:

        _model = CrossEncoder(
            RERANK_MODEL
        )

    return _model


def rerank_chunks(
    question: str,
    chunks,
    top_k: int = 4,
):
    """
    Re-rank retrieved chunks using
    a Cross Encoder model.
    """

    if not chunks:

        return []

    model = load_reranker()

    pairs = [
        (
            question,
            chunk.page_content,
        )
        for chunk in chunks
    ]

    scores = model.predict(
        pairs
    )

    ranked = sorted(
        zip(
            chunks,
            scores,
        ),
        key=lambda x: x[1],
        reverse=True,
    )

    return [
        chunk
        for chunk, _
        in ranked[:top_k]
    ]


if __name__ == "__main__":

    question = (
        "fungal disease in citrus"
    )

    candidates = hybrid_retrieve(
        question,
        k=8,
    )

    reranked = rerank_chunks(
        question,
        candidates,
        top_k=4,
    )

    print(
        f"\nReranked: "
        f"{len(reranked)} chunks\n"
    )

    for i, doc in enumerate(
        reranked,
        start=1,
    ):

        print(
            f"\n--- Result {i} ---\n"
        )

        print(
            doc.page_content[:500]
        )

        print(
            "\nMetadata:"
        )

        print(
            doc.metadata
        )