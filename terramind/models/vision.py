"""Shared crop image analysis — gpt-4o-mini vision for all TerraMind modes."""

import logging
import os

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from terramind.meta_questions import is_image_describe_question

VISION_MODEL = "gpt-4o-mini"
_log = logging.getLogger(__name__)
_VISION_CLIENTS: dict[tuple[str, str], ChatOpenAI] = {}


def _get_vision_client(api_key: str) -> ChatOpenAI:
    """Reuse the OpenAI/LangChain client so first image requests do less setup."""
    cache_key = (VISION_MODEL, api_key)
    if cache_key not in _VISION_CLIENTS:
        _VISION_CLIENTS[cache_key] = ChatOpenAI(
            model=VISION_MODEL,
            temperature=0.2,
            api_key=api_key,
        )
    return _VISION_CLIENTS[cache_key]


def warm_vision_model(api_key: str | None = None) -> bool:
    """
    Prepare the vision client at service startup.

    This intentionally does not call OpenAI, so warmup has no token cost and does
    not fail startup when the network is unavailable.
    """
    key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()
    if not key:
        _log.info("Vision warmup skipped: OPENAI_API_KEY is not set")
        return False
    _get_vision_client(key)
    _log.info("Vision client ready (%s)", VISION_MODEL)
    return True


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

    llm = _get_vision_client(api_key)
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
