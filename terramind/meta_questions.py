"""Detect conversational / identity questions that should not run full RAG."""

from __future__ import annotations

import re

_META_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"^\s*(hi|hello|hey|greetings|good morning|good afternoon|good evening)\s*[!.?]*\s*$",
        r"\bwho are you\b",
        r"\bwhat are you\b",
        r"\bwhat is terramind\b",
        r"\bwhat'?s terramind\b",
        r"\bintroduce yourself\b",
        r"\bwhat can you do\b",
        r"\bwhat do you do\b",
        r"\bhow can you help\b",
        r"\bwhat are your capabilities\b",
        r"^\s*help\s*[!.?]*\s*$",
        r"^\s*thanks?\s*[!.?]*\s*$",
        r"\bthank you\b",
        r"من أنت",
        r"ما هي terramind",
        r"^\s*مرحبا\s*[!.?]*\s*$",
        r"السلام عليكم",
    )
)

_IMAGE_DESCRIBE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bwhat can you see\b",
        r"\bwhat can u see\b",
        r"\bwhat do you see\b",
        r"\bwhat can you tell me about (this|the) (image|photo|picture)\b",
        r"\bwhat is in (this|the) (image|photo|picture)\b",
        r"\bwhat'?s in (this|the) (image|photo|picture)\b",
        r"\bdescribe (this|the) (image|photo|picture)\b",
        r"\banalyze (this|the) (image|photo|picture)\b",
        r"\blook at (this|the) (image|photo|picture)\b",
    )
)

_STRONG_PRODUCT_INTENT: tuple[str, ...] = (
    "what product",
    "which product",
    "what products",
    "which products",
    "recommend a product",
    "recommend product",
    "from your catalog",
    "from the catalog",
    "from our catalog",
    "in your catalog",
    "best product",
)


def is_meta_question(question: str, *, max_len: int = 120) -> bool:
    """True for greetings, identity, or capability questions — not field/agronomy tasks."""
    q = (question or "").strip()
    if not q or len(q) > max_len:
        return False
    return any(p.search(q) for p in _META_PATTERNS)


def is_image_describe_question(question: str) -> bool:
    """User wants a description of an uploaded image, not document RAG."""
    q = (question or "").strip()
    if not q:
        return False
    return any(p.search(q) for p in _IMAGE_DESCRIBE_PATTERNS)


def has_strong_product_intent(question: str) -> bool:
    """Explicit ask for a catalog product recommendation."""
    q = (question or "").lower()
    return any(phrase in q for phrase in _STRONG_PRODUCT_INTENT)


def advisory_meta_answer() -> str:
    """Short intro when Advisory mode gets a non-agronomy conversational question."""
    return (
        "I am **TerraMind**, an agriculture support assistant for farmers, growers, "
        "and agronomists.\n\n"
        "In **Advisory** mode I combine two knowledge layers:\n"
        "- **Public agriculture guidance** — IPM, GAP, soil health, and crop protection "
        "from trusted references\n"
        "- **Company product catalog** — usage, dosage, and crop fit from your product sheets\n\n"
        "Ask about a crop issue, field practice, or which catalog product fits your "
        "situation. I can use uploaded plant photos and respond in English, Arabic, "
        "or other languages."
    )
