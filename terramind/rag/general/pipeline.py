"""
General RAG — public API used by terramind.models.general_rag.

TODO: Move from Rag_Gen.py:
  - init_general_rag(reset), get_general_db()
  - answer_with_rag(db, question)
  - sources_from_retrieved(retrieved)
When done: terramind.rag.general.__init__ imports from HERE, not from Rag_Gen.
See docs/RAG_MIGRATION_PLAN.md step 7 (general).
"""
