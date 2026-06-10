"""
Product RAG — similarity search over product vectors.

TODO: Move from Rag_Pc.py:
  - retrieve_products(db, question, k) -> list[Document]
  - format_context(retrieved) -> single string for the prompt
See docs/PROJECT_STATUS.md (product migration).
"""


from langchain_core.documents import (
    Document,
)

from langchain_chroma import Chroma

from terramind.rag.product.config import (
    RETRIEVAL_K,
)

from terramind.rag.product.store import (
    load_vector_store,
)



# Retrieval
# 
# Search the Product Chroma index and return the most relevant chunks
# for a user question. Each retrieved chunk is enriched with its
# similarity score to support debugging, evaluation, and future
# retrieval improvements (reranking, filtering, hybrid search).


def retrieve_chunks(
    question: str,
    k: int = RETRIEVAL_K,
) -> list[Document]:
    """
    Retrieve chunks with relevance scores.
    """
    # Load the Product RAG vector store
    db = load_vector_store()
    
    # Retrieve top-k chunks together with their similarity scores
    pairs = (
        db.similarity_search_with_score(
            question,
            k=k,
        )
    )
    
    # Attach retrieval scores to chunk metadata
    # so downstream components can inspect ranking quality
    results = []

    for doc, score in pairs:

        # Copy metadata to avoid mutating the original document
        metadata = dict(
            doc.metadata
        )
        # Store retrieval score for evaluation and debugging
        metadata[
            "relevance_score"
        ] = score


        # Create a new document containing the original content
        # plus retrieval metadata
        results.append(
            Document(
                page_content=doc.page_content,
                metadata=metadata,
            )
        )

    return results


# Retrieval Test
#
# Simple manual test used during development to verify that
# relevant chunks are returned from the Product RAG index.

if __name__ == "__main__":

    question = (
        "fungal disease in citrus"
    )

    # Retrieve relevant chunks from Chroma
    results = retrieve_chunks(
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