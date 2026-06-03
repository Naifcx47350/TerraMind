"""General RAG — prompt template and LLM generation."""

from langchain_openai import ChatOpenAI

from terramind.rag.general.config import CHAT_MODEL, RAG_PROMPT


def generate_answer(context: str, question: str) -> str:
    messages = RAG_PROMPT.invoke({"document": context, "question": question})
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0.2)
    response = llm.invoke(messages)
    return response.content or ""
