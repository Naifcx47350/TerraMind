"""Shared crop image analysis — gpt-4o-mini vision for all TerraMind modes."""

import os

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

VISION_MODEL = "gpt-4o-mini"


def analyze_image(image_base64: str, mime: str, question: str, lang: str = "en") -> str:
    """Return agronomy-focused text description of an uploaded image."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set — cannot analyze images")

    prompt = (
        "You are an expert agronomist. Analyze this plant/crop image:\n"
        "1. Visible diseases, pests, or abnormalities\n"
        "2. Affected plant parts\n"
        "3. Severity (mild/moderate/severe)\n"
        "4. Initial recommendations\n\n"
        f"User question: {question}\n"
        f"Reply in {'Arabic' if lang == 'ar' else 'English'}. Be concise."
    )

    llm = ChatOpenAI(model=VISION_MODEL, temperature=0.2, api_key=api_key)
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{image_base64}"},
            },
        ]
    )
    response = llm.invoke([message])
    return (response.content or "").strip()
