"""Mode 3 — base OpenAI chat without retrieval (comparison baseline)."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from models.image_context import question_with_image_context

CHAT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You are TerraMind, a helpful agriculture support assistant.

You do NOT have access to a company product catalog or document knowledge base in this mode.
Give general agricultural guidance when appropriate.

Rules:
- Do not invent specific product names, dosages, or label instructions.
- If asked for exact product rates, say you cannot access the catalog in this mode.
- Recommend checking the product label or a licensed agronomist when needed.
- Be concise and practical.
"""


def answer(
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
    image_base64: str | None = None,
    image_mime: str | None = None,
    **_,
) -> dict:
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0.3)
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    for msg in (history or [])[-10:]:
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", "")
        content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
        if not (content or "").strip():
            continue
        if role in ("assistant", "bot"):
            messages.append(AIMessage(content=content))
        elif role in ("user", "human"):
            messages.append(HumanMessage(content=content))

    q = question_with_image_context(question, image_analysis)
    if image_base64 and image_mime and not image_analysis:
        messages.append(
            HumanMessage(
                content=[
                    {"type": "text", "text": q},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{image_mime};base64,{image_base64}"},
                    },
                ]
            )
        )
    else:
        messages.append(HumanMessage(content=q))

    response = llm.invoke(messages)

    return {
        "answer": response.content or "",
        "sources": [],
        "confidence": "medium",
        "retrieved_chunks": 0,
        "system": "base_llm",
    }
