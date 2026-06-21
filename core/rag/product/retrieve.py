"""Product RAG retrieval over the product Chroma index."""


from langchain_core.documents import (
    Document,
)

from langchain_chroma import Chroma

from core.rag.product.config import (
    RETRIEVAL_K,
)
from core.rag.scoring import distance_to_relevance

from core.rag.product.filters import (
    detect_product_id,
    detect_product_name,
)

# Retrieval
# 
# Search the Product Chroma index and return the most relevant chunks
# for a user question. Each retrieved chunk is enriched with its
# similarity score to support debugging, evaluation, and future
# retrieval improvements (reranking, filtering, hybrid search).


def retrieve_chunks(
    db: Chroma,
    question: str,
    k: int = RETRIEVAL_K,
) -> list[Document]:
    """Retrieve product chunks with UI-compatible relevance scores."""
    # pairs = db.similarity_search_with_score(question, k=k)
    # results = []
    product_id = detect_product_id(
    question
    )

    product_name = detect_product_name(    
    question
    )

    if product_id:    

        print(
            f"Metadata Filter (ID): {product_id}"
        )

        pairs = db.similarity_search_with_score(
            question,
            k=k,
            filter={
                "product_id": product_id
            },
        )

    elif product_name:

        print(    
        f"Metadata Filter (Name): {product_name}"
        )

        pairs = db.similarity_search_with_score(
            question,
            k=k,
            filter={
                "product_name": product_name
            },
        )

    else:

        pairs = db.similarity_search_with_score(
            question,
            k=k,
        )
    # for doc, _ in pairs:
    #     print(
    #         doc.metadata["product_id"]
    #     )
    results = []
    
    for doc, distance in pairs:
        metadata = dict(doc.metadata)
        metadata["relevance_score"] = distance_to_relevance(distance)
        results.append(
            Document(
                page_content=doc.page_content,
                metadata=metadata,
            )
        )

    return results


def retrieve_products(
    db: Chroma,
    question: str,
    k: int = RETRIEVAL_K,
) -> list[Document]:
    """Compatibility wrapper used by Auto routing and Advisory."""
    return retrieve_chunks(db, question, k=k)


# Retrieval Test
#
# Simple manual test used during development to verify that
# relevant chunks are returned from the Product RAG index.

if __name__ == "__main__":

    question = (
        "How should I apply Citrus Bacteria Clear?"
    )

    # Retrieve relevant chunks from Chroma
    from core.rag.product.store import load_vector_store

    results = retrieve_chunks(
        load_vector_store(),
        question
    )

    print(
        f"Retrieved: "
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
            f"\nScore: "
            f"{doc.metadata['relevance_score']}"
        )

        print(
            "\nMetadata:"
        )

        print(
            doc.metadata
        )