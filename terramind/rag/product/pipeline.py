"""
Product RAG — public API used by terramind.models.product_rag.

TODO: Move from Rag_Pc.py and wire submodules:
  - init_product_rag(reset) -> Chroma
  - get_product_db() -> cached Chroma handle
  - answer_with_rag(db, question) -> {answer, retrieved, context, ...}
  - sources_from_retrieved(retrieved) -> list[dict] for UI sources
When done: terramind.rag.product.__init__ imports from HERE, not from Rag_Pc.
See docs/PROJECT_STATUS.md (product migration).
"""
from terramind.rag.product.rewrite import (
    rewrite_query,
)

from terramind.rag.product.load import (
    load_products,
)

from terramind.rag.product.chunk import (
    build_all_chunks,
)

from terramind.rag.product.store import (
    load_vector_store,
    build_vector_store,
)

from terramind.rag.product.config import (
    CATALOG_PATH,
)

from terramind.rag.product.generate import (
    generate_answer_with_metadata,
    format_context,
)

from terramind.rag.product.hybrid import (
    hybrid_retrieve,
)

from terramind.rag.product.rerank import (
    rerank_chunks,
)

from terramind.rag.llm_stream import (
    stream_chat_tokens,
)

from terramind.rag.product.config import (
    CHAT_MODEL,
    RAG_PROMPT,
)




_DB = None

def init_product_rag(
    reset: bool = False,
):

    products = load_products(
        CATALOG_PATH
    )

    chunks = build_all_chunks(
        products
    )

    db = build_vector_store(
        chunks,
        reset=reset,
    )

    global _DB

    _DB = db

    return db

def get_product_db():

    global _DB

    if _DB is None:

        _DB = load_vector_store()

    return _DB

  
def answer_with_rag(
    db,
    question: str,
):

    return generate_answer_with_metadata(
        question
    )

def stream_answer_with_rag(
    db,
    question: str,
):
    retrieval_query = rewrite_query(
        question
    )

    print(
        f"\nOriginal Query: {question}"
    )

    print(
        f"Rewritten Query: {retrieval_query}\n"
    )

    candidates = hybrid_retrieve(
        retrieval_query,
        k=8,
    )

    chunks = rerank_chunks(
        question,
        candidates,
        top_k=4,
    )
    if not chunks:

        return (    
            [],
            iter(
                [
                "I could not find relevant information in the product catalog."
            ]
            ),
        )
    
    
    context = format_context(
        chunks
    )

    prompt = RAG_PROMPT.invoke(
        {
            "context": context,
            "question": question,
        }
    )

    messages = (
        prompt.to_messages()
    )

    token_gen = stream_chat_tokens(
        messages,
        model=CHAT_MODEL,
        temperature=0,
    )

    return (
        chunks,
        token_gen,
    )


def sources_from_retrieved(
    retrieved,
):

    sources = []

    seen = set()

    for chunk in retrieved:

        product_id = chunk.metadata.get(
            "product_id"
        )

        product_name = chunk.metadata.get(
            "product_name"
        )

        key = (
            product_id,
            product_name,
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        sources.append(
            {
                "id": product_id,
                "title": product_name,
            }
        )

    return sources


#####
if __name__ == "__main__":

    db = get_product_db()

    retrieved, token_gen = stream_answer_with_rag(
        db,
        "How much water should I mix it with?"
    )

    print("\nRetrieved:")
    print(len(retrieved))

    print("\nAnswer:\n")


    for token in token_gen:
        print(token, end="")