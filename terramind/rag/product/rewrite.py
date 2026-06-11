from langchain_openai import ChatOpenAI

from terramind.rag.product.config import (
    CHAT_MODEL,
)

REWRITE_PROMPT = """
You are a retrieval query optimizer for an agricultural product catalog.

Rules:
- Preserve product names exactly as written.
- Preserve crop names exactly as written.
- Preserve disease names exactly as written.
- Do not add new products, crops, diseases, or specifications.
- Do not broaden specific factual questions.
- Only rewrite when it improves retrieval.
- If the question is already clear and specific, return it unchanged.
- Return only the rewritten query.

Question:
{question}
"""


def rewrite_query(
    question: str,
) -> str:

    llm = ChatOpenAI(
        model=CHAT_MODEL,
        temperature=0,
    )

    response = llm.invoke(
        REWRITE_PROMPT.format(
            question=question
        )
    )

    return response.content.strip()


if __name__ == "__main__":

    query = (
        "How much water should I mix it with?"
    )

    print(
        rewrite_query(query)
    )