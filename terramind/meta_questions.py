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


def is_meta_question(question: str, *, max_len: int = 120) -> bool:
    """True for greetings, identity, or capability questions — not field/agronomy tasks."""
    q = (question or "").strip()
    if not q or len(q) > max_len:
        return False
    return any(p.search(q) for p in _META_PATTERNS)


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
