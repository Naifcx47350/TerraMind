"""Stream tokens from OpenAI via LangChain ChatOpenAI."""

from __future__ import annotations

from collections.abc import Iterator

from langchain_core.messages import BaseMessage
from core.openai_keys import chat_model


def stream_chat_tokens(
    messages: list[BaseMessage],
    *,
    model: str,
    temperature: float = 0.3,
) -> Iterator[str]:
    llm = chat_model(model=model, temperature=temperature, streaming=True)
    for chunk in llm.stream(messages):
        part = chunk.content
        if part:
            yield part
