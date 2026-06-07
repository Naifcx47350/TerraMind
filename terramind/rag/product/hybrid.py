from rank_bm25 import BM25Okapi

from terramind.rag.product.load import (
    load_products,
)

from terramind.rag.product.chunk import (
    build_all_chunks,
)

from terramind.rag.product.config import (
    CATALOG_PATH,
)


def build_bm25_index():
    """
    Build a BM25 index from all
    Product RAG chunks.
    """

    products = load_products(
        CATALOG_PATH
    )

    chunks = build_all_chunks(
        products
    )

    texts = [
        chunk.page_content
        for chunk in chunks
    ]

    tokenized_corpus = [
        text.lower().split()
        for text in texts
    ]

    bm25 = BM25Okapi(
        tokenized_corpus
    )

    return bm25, chunks
def bm25_retrieve(
    question: str,
    k: int = 4,
):
    """
    Retrieve top-k chunks using BM25.
    """

    bm25, chunks = (
        build_bm25_index()
    )

    query_tokens = (
        question.lower().split()
    )

    scores = bm25.get_scores(
        query_tokens
    )

    ranked = sorted(
        zip(chunks, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    return ranked[:k]

from terramind.rag.product.retrieve import (
    retrieve_chunks,
)

def rrf_score(
    rank: int,
    k: int = 60,
) -> float:
    """
    Reciprocal Rank Fusion score.
    """

    return 1.0 / (
        k + rank
    )
def rrf_fusion(
    dense_results,
    bm25_results,
    k: int = 4,
):
    """
    Combine dense and BM25 rankings
    using Reciprocal Rank Fusion.
    """
    scores = {}
    documents = {}

    for rank, doc in enumerate(
        dense_results,
        start=1,
    ):

        chunk_id = (
            doc.metadata.get(
                "product_id"
            ),
            doc.metadata.get(
                "chunk_type"
            ),
            doc.metadata.get(
                "chunk_index"
            ),
        )

        documents[
            chunk_id
        ] = doc

        scores[
            chunk_id
        ] = scores.get(
            chunk_id,
            0,
        ) + rrf_score(rank)

    for rank, (
        doc,
        _
    ) in enumerate(
        bm25_results,
        start=1,
    ):

        chunk_id = (
            doc.metadata.get(
                "product_id"
            ),
            doc.metadata.get(
                "chunk_type"
            ),
            doc.metadata.get(
                "chunk_index"
            ),
        )

        documents[
            chunk_id
        ] = doc

        scores[
            chunk_id
        ] = scores.get(
            chunk_id,
            0,
        ) + rrf_score(rank)

    ranked = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    return [
        documents[
            chunk_id
        ]
        for chunk_id, _
        in ranked[:k]
    ]

def hybrid_retrieve(
    question: str,
    k: int = 4,
):
    """
    Combine Dense Retrieval and BM25 Retrieval.
    """

    dense_results = retrieve_chunks(
        question,
        k=k,
    )

    bm25_results = bm25_retrieve(
        question,
        k=k,
    )

    return rrf_fusion(
        dense_results,
        bm25_results,
        k=k,
    )



if __name__ == "__main__":

    results = hybrid_retrieve(
        "fungal disease in citrus"
    )

    print(
        f"\nRetrieved: "
        f"{len(results)} chunks\n"
    )

    for i, doc in enumerate(
        results,
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