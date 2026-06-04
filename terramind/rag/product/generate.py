"""
Product RAG — prompt template and LLM answer generation.

TODO: Move from Rag_Pc.py:
  - RAG_PROMPT ChatPromptTemplate (context + question + answer rules)
  - Function: generate_answer(context, question) -> str (ChatOpenAI gpt-4o-mini)
  - Keep “answer only from context” rules in the template
See docs/PROJECT_STATUS.md (product migration).
"""
