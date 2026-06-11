"""Product RAG retrieval over the product Chroma index."""


from langchain_core.documents import (
    Document,
)

from langchain_chroma import Chroma

from terramind.rag.product.config import (
    RETRIEVAL_K,
)
from terramind.rag.scoring import distance_to_relevance



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
    pairs = db.similarity_search_with_score(question, k=k)
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
        "fungal disease in citrus"
    )

    # Retrieve relevant chunks from Chroma
    from terramind.rag.product.store import load_vector_store

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
            f"{doc.metadata['retrieval_score']}"
        )

        print(
            "\nMetadata:"
        )

        print(
            doc.metadata
        )