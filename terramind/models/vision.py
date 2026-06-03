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
        "Expert agronomist. In 2-4 short plain sentences, describe this crop/plant photo: "
        "main issue (if any), affected parts, severity (mild/moderate/severe), and one "
        "practical note tied to the user's question. "
        "Plain sentences only (the main assistant will format the final reply).\n"
        f"User question: {question}\n"
        f"Language: {'Arabic' if lang == 'ar' else 'English'}."
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
