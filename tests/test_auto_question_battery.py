"""
Auto-mode routing battery — standard TerraMind questions + stress cases.

Run: pytest tests/test_auto_question_battery.py -v
"""

from __future__ import annotations

import pytest

from terramind.models.router import build_retrieval_query_for_route, route_question

# (question, expected_route, category)
AUTO_QUESTION_BATTERY: list[tuple[str, str, str]] = [
    # --- Meta / conversational → base_llm ---
    ("who are you", "base_llm", "meta"),
    ("hello again", "base_llm", "meta"),
    ("thanks", "base_llm", "meta"),
    ("summarize our conversation in three bullet points", "base_llm", "meta"),
    ("how would u help me if i asked for a product?", "base_llm", "meta_hypothetical"),
    ("what if i asked about general agricultural info", "base_llm", "meta_hypothetical"),
    ("كيف تستطيع مساعدتي؟", "base_llm", "meta_ar"),
    ("من أنت", "base_llm", "meta_ar"),
    ("ماذا؟", "base_llm", "meta_ar"),
    ("لماذا تطبع جوابي", "base_llm", "meta_ar"),
    # --- Gibberish / vague → base_llm ---
    ("dadada", "base_llm", "clarification"),
    ("noncess", "base_llm", "clarification"),
    ("why", "base_llm", "clarification"),
    ("me wnt to plant how", "base_llm", "clarification"),
    ("?are you ok", "base_llm", "clarification"),
    # --- Product catalog → product_rag ---
    (
        "what product should I use to manage potato late blight infection",
        "product_rag",
        "product",
    ),
    (
        "what product is best to enhance soil health on my farm",
        "product_rag",
        "product",
    ),
    (
        "which of your catalog fungicides would fit the potato problem we discussed",
        "product_rag",
        "product",
    ),
    (
        "what product should I spray if I already see blight on the leaves",
        "product_rag",
        "product",
    ),
    (
        "اريد ان تعطيني منتج يساعد في تحسين التربة",
        "product_rag",
        "product_ar",
    ),
    (
        "هل تستطيع اعطائي نصيحة لمنتج لتحسين الري",
        "product_rag",
        "product_ar",
    ),
    # --- General agriculture → general_rag ---
    (
        "what are the main integrated pest management steps for potato diseases",
        "general_rag",
        "general",
    ),
    (
        "how can crop rotation help soil fertility without buying anything new",
        "general_rag",
        "general",
    ),
    (
        "is late blight more about prevention or treatment",
        "general_rag",
        "general",
    ),
    (
        "what is water management in agriculture",
        "general_rag",
        "general",
    ),
    (
        "ما هي خطوات إدارة الآفات المتكاملة للبطاطس",
        "general_rag",
        "general_ar",
    ),
    # --- Follow-ups (still valid ag) → general_rag ---
    (
        "can u tell me this but in arabic",
        "base_llm",
        "translation",
    ),
    ("who are you tho?", "base_llm", "meta"),
    ("translate the last answer to arabic", "base_llm", "translation"),
    ("هل يمكنك أن تخبرني هذا بالعربية", "base_llm", "translation_ar"),
    # --- Stress / weak-point probes ---
    ("what is the weather today", "base_llm", "off_topic"),
    ("tell me a joke about farmers", "base_llm", "off_topic"),
    (
        "what fungicide from catalog for tomato early blight",
        "product_rag",
        "product",
    ),
]


@pytest.mark.parametrize(
    "question,expected_route,category",
    AUTO_QUESTION_BATTERY,
    ids=[f"{cat}:{q[:40]}" for q, _, cat in AUTO_QUESTION_BATTERY],
)
def test_auto_route_battery(question: str, expected_route: str, category: str):
    rq = build_retrieval_query_for_route(question)
    route, reason = route_question(question, rq)
    assert route == expected_route, (
        f"[{category}] expected {expected_route}, got {route} ({reason})\n"
        f"Q: {question!r}"
    )
