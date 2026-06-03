"""
Product RAG — public API used by terramind.models.product_rag.

TODO: Move from Rag_Pc.py and wire submodules:
  - init_product_rag(reset) -> Chroma
  - get_product_db() -> cached Chroma handle
  - answer_with_rag(db, question) -> {answer, retrieved, context, ...}
  - sources_from_retrieved(retrieved) -> list[dict] for UI sources
When done: terramind.rag.product.__init__ imports from HERE, not from Rag_Pc.
See docs/RAG_MIGRATION_PLAN.md step 6 (product).
"""
