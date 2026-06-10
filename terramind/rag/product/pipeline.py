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


from terramind.rag.product.generate import (
    generate_answer_with_metadata,
)

from terramind.rag.product.store import (
    load_vector_store,
)


_DB = None


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
