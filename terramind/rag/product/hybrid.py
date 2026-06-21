from rank_bm25 import BM25Okapi
from langchain_core.documents import Document
from langchain_chroma import Chroma

from terramind.rag.product.load import (
    load_products,
)

from terramind.rag.product.chunk import (
    build_all_chunks,
)

from terramind.rag.product.config import (
    CATALOG_PATH,
)
from terramind.rag.product.filters import (
    detect_product_id,
    detect_product_name,
)
from terramind.rag.product.store import load_vector_store

_BM25_CACHE: tuple[BM25Okapi, list[Document]] | None = None


def build_bm25_index():
    """
    Build a BM25 index from all
    Product RAG chunks.
    """

    global _BM25_CACHE
    if _BM25_CACHE is not None:
        return _BM25_CACHE

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

    _BM25_CACHE = (bm25, chunks)
    return _BM25_CACHE


def reset_bm25_cache() -> None:
    """Clear cached lexical index after rebuilding product chunks."""
    global _BM25_CACHE
    _BM25_CACHE = None


def bm25_retrieve(
    question: str,
    k: int = 4,
    product_id: str | None = None,
    product_name: str | None = None,
):
    """
    Retrieve top-k chunks using BM25, optionally
    restricted to a single product (same metadata
    filter dense retrieval applies) so lexical matches
    can't pull in another product's chunks.
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

    pairs = list(
        zip(chunks, scores)
    )

    if product_id:

        pairs = [
            (chunk, score)
            for chunk, score in pairs
            if chunk.metadata.get("product_id") == product_id
        ]

    elif product_name:

        pairs = [
            (chunk, score)
            for chunk, score in pairs
            if chunk.metadata.get("product_name") == product_name
        ]

    ranked = sorted(
        pairs,
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

    top = ranked[:k]
    best_score = top[0][1] if top else 1.0
    out = []
    for chunk_id, score in top:
        doc = documents[chunk_id]
        metadata = dict(doc.metadata)
        metadata["relevance_score"] = score / best_score if best_score else 0.0
        out.append(Document(page_content=doc.page_content, metadata=metadata))
    return out

def hybrid_retrieve(
    db: Chroma,
    question: str,
    k: int = 4,
):
    """
    Combine Dense Retrieval and BM25 Retrieval.

    Both branches are restricted to the same product
    (when one is detected in the question) so the BM25
    branch can't fuse in another product's chunks that
    the dense branch's metadata filter already excludes.
    """

    dense_results = retrieve_chunks(
        db,
        question,
        k=k,
    )

    product_id = detect_product_id(
        question
    )

    product_name = (
        None
        if product_id
        else detect_product_name(question)
    )

    bm25_results = bm25_retrieve(
        question,
        k=k,
        product_id=product_id,
        product_name=product_name,
    )

    return rrf_fusion(
        dense_results,
        bm25_results,
        k=k,
    )



if __name__ == "__main__":

    results = hybrid_retrieve(
        load_vector_store(),
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