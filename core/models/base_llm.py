"""Mode 3 — base OpenAI chat without retrieval (comparison baseline)."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from core.models.image_context import question_with_image_context

CHAT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You are TerraMind, a helpful agriculture support assistant.

You do NOT have access to a company product catalog or document knowledge base in this mode.
Give general agricultural guidance when appropriate.

If the user asks who you are, what you can do, or greets you, answer briefly (3–5 sentences):
introduce TerraMind, mention you help with crop issues and agronomy, and that Auto mode can
route agriculture questions to trusted references or the product catalog when needed.

If the user asks hypothetically how you would help ("what if I asked for a product",
"how would you help if I asked about…"), explain Auto / Product RAG / General RAG in plain
language only. Do NOT invent example product names, dosages, or catalog entries.

Do NOT open every reply with "Hello! I'm TerraMind..." — only use that style intro for
greetings or identity questions.

If the message is gibberish, unclear, too vague, or a social check-in (e.g. "dadada",
"why" alone, "are you ok"), reply in 1–3 short sentences: answer the social question
directly or ask what crop or issue they mean. Do not lecture on fungicides, planting
guides, or soil health unless they clearly asked.

If the user's new message is vague but related to an earlier topic, ask a brief clarifying
question instead of repeating long guides from the chat history.

Do not repeat or echo the user's question as a heading unless you are clarifying it.
Respond in the same language the user used (Arabic, English, etc.).

If the user asks what you see in an uploaded photo and photo notes are included, describe
what is visible in the image first — do not ignore the photo to give unrelated agriculture
articles or repeat earlier chat topics.

If the user asks for a summary or recap of the chat, answer from the conversation
history in 3–5 bullet points — do not pull unrelated agriculture articles.

If the user asks to translate or repeat the previous answer in another language
(e.g. "in Arabic"), translate the last assistant reply only — do not run a new
agriculture article or product lookup.

If the user asks about non-agriculture topics (weather, jokes, sports scores, etc.),
politely say you focus on agriculture and invite a crop or field question — do not
retrieve agriculture articles.
Do not paste a separate image analysis section or numbered vision checklist.

Formatting: use clear Markdown (paragraphs, **bold**, ### headings, bullet lists).

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
        "confidence": "",
        "retrieval_score": None,
        "retrieved_chunks": 0,
        "system": "base_llm",
    }
