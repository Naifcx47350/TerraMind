"""Shared crop image analysis — gpt-4o-mini vision for all TerraMind modes."""

import os

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from terramind.meta_questions import is_image_describe_question

VISION_MODEL = "gpt-4o-mini"


def analyze_image(image_base64: str, mime: str, question: str, lang: str = "en") -> str:
    """Return text description of an uploaded image for the answering model."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set — cannot analyze images")

    lang_label = "Arabic" if lang == "ar" else "English"
    if is_image_describe_question(question):
        prompt = (
            "Describe what you see in this image clearly and accurately in 3-6 sentences. "
            "Include visible text, diagrams, charts, labels, UI elements, or crops — "
            "whatever is actually shown. Answer the user's question directly.\n"
            f"User question: {question}\n"
            f"Language: {lang_label}."
        )
    else:
        prompt = (
            "Expert agronomist. In 2-4 short plain sentences, describe this crop/plant photo: "
            "main issue (if any), affected parts, severity (mild/moderate/severe), and one "
            "practical note tied to the user's question. "
            "Plain sentences only (the main assistant will format the final reply).\n"
            f"User question: {question}\n"
            f"Language: {lang_label}."
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
