"""General RAG — prompt template and LLM generation."""

from collections.abc import Iterator

from langchain_openai import ChatOpenAI

from core.rag.general.config import CHAT_MODEL, RAG_PROMPT
from core.rag.llm_stream import stream_chat_tokens


def generate_answer(context: str, question: str) -> str:
    messages = RAG_PROMPT.invoke({"document": context, "question": question})
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0.35)
    response = llm.invoke(messages)
    return response.content or ""


def stream_generate_answer(context: str, question: str) -> Iterator[str]:
    prompt_value = RAG_PROMPT.invoke({"document": context, "question": question})
    yield from stream_chat_tokens(
        prompt_value.to_messages(),
        model=CHAT_MODEL,
        temperature=0.35,
    )
