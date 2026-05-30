"""Base LLM answer without retrieval."""

import os

from openai import OpenAI

from src.config import CHAT_MODEL
from src.prompts import BASE_SYSTEM_PROMPT, build_base_user_message


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def answer_without_rag(question: str, model: str = CHAT_MODEL) -> str:
    """Generate an answer using only the base LLM (no retrieval)."""
    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        temperature=0.3,
        messages=[
            {"role": "system", "content": BASE_SYSTEM_PROMPT},
            {"role": "user", "content": build_base_user_message(question)},
        ],
    )
    return response.choices[0].message.content or ""
