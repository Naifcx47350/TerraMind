"""Create embeddings with the OpenAI API."""

import os

from openai import OpenAI

from src.config import EMBEDDING_MODEL


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to your environment or a .env file."
        )
    return OpenAI(api_key=api_key)


def embed_texts(texts: list[str], model: str = EMBEDDING_MODEL) -> list[list[float]]:
    """Embed a batch of texts. Returns vectors in the same order."""
    if not texts:
        return []

    client = get_openai_client()
    response = client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in response.data]
