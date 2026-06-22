"""Detect conversational / identity questions that should not run full RAG."""

from __future__ import annotations

import re

from core.rag.general.topics import infer_topics_from_query

_META_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"^\s*(hi|hello|hey|greetings|good morning|good afternoon|good evening)\s*[!.?]*\s*$",
        r"^\s*(hi|hello|hey)\s+again\s*[!.?]*\s*$",
        r"\bwho are you\b",
        r"\bwhat are you\b",
        r"\bwhat is core\b",
        r"\bwhat'?s core\b",
        r"\bintroduce yourself\b",
        r"\bwhat can you do\b",
        r"\bwhat can you do for me\b",
        r"\bwhat can u do\b",
        r"\bwhat can u do for me\b",
        r"\bwhat u can do\b",
        r"\bwhat do you do\b",
        r"\bwhat do u do\b",
        r"\bhow can you help\b",
        r"\bhow can u help\b",
        r"\bwhat are your capabilities\b",
        r"^\s*help\s*[!.?]*\s*$",
        r"^\s*thanks?\s*[!.?]*\s*$",
        r"\bthank you\b",
        r"\bsummarize (our |this |the )?(conversation|chat|discussion)\b",
        r"\b(summary|recap) (of )?(our |this |the )?(conversation|chat|discussion)\b",
        r"\bthree bullet points\b.*\b(conversation|chat|summary)\b",
        r"\bgive me (a )?(brief )?summary\b",
        r"^\s*\?\s*$",
        r"^\s*why\s*[!.?]*\s*$",
        r"^\s*how\s*[!.?]*\s*$",
        r"^\s*what\s*[!.?]*\s*$",
        r"^\s*\?+\s*are you ok",
        r"\bare you (ok|okay|alright)\b",
        r"^\s*you ok\s*[!.?]*\s*$",
        r"\bhow would (you|u) help\b.*\bif i (asked|ask)\b",
        r"\bwhat if i (asked|ask)\b",
        r"\bthen what if i asked\b",
        r"\bwhat would you do if i (asked|ask)\b",
        r"\bhow do you (work|handle|respond)\b.*\bif i\b",
        r"من أنت",
        r"ما هي terramind",
        r"^\s*مرحبا\s*[!.?]*\s*$",
        r"السلام عليكم",
    )
)

_AR_META_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p)
    for p in (
        r"كيف\s+(تستطيع|يمكنك|تقدر)\s+مساعد",
        r"ماذا\s+(تستطيع|يمكنك)\s+(أن\s+)?(تفعل|مساعد)",
        r"ما\s+(الذي\s+)?يمكنك\s+(أن\s+)?(تفعل|مساعد)",
        r"^\s*ماذا\s*[؟?]+\s*$",
        r"^\s*لماذا\s*[؟?]+\s*$",
        r"^\s*كيف\s*[؟?]+\s*$",
        r"لماذا\s+تطبع",
        r"لماذا\s+تكر",
        r"تكرار\s+(السؤال|الجواب|رسالت)",
        r"^\s*شكرا\s*",
        r"^\s*شكراً\s*",
        r"بالعربية",
        r"باللغة العربية",
        r"ترجم",
    )
)

_TRANSLATION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\b(in|to)\s+arabic\b",
        r"\btell me (this |it )?(but )?in arabic\b",
        r"\btranslate (this |it )?(to )?arabic\b",
        r"\bsay (this |it )?(in )?arabic\b",
        r"بالعربية",
        r"باللغة العربية",
        r"ترجم( إلى|لي)?",
        r"هل\s+يمكنك.*بالعربية",
    )
)

_OFF_TOPIC_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bweather\b",
        r"\bforecast\b",
        r"\btell me a joke\b",
        r"\bjoke about\b",
        r"\bwho won (the )?(world cup|game|match)\b",
        r"\bstock price\b",
        r"\bbitcoin\b",
        r"\bwrite (me )?a poem\b",
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
    "from catalog",
    "in your catalog",
    "your catalog",
    "our catalog",
    "best product",
    "catalog fungicide",
    "catalog fungicides",
    "catalog herbicide",
    "catalog insecticide",
    "give me a product",
    "give me product",
    "product that helps",
    "product for ",
    "product to ",
    "a product for",
    "a product to",
    "a product that",
    "recommend something from",
    "something from your catalog",
    "something from the catalog",
)

_STRONG_PRODUCT_INTENT_AR: tuple[str, ...] = (
    "منتج",
    "منتجات",
    "كتالوج",
    "نصيحة لمنتج",
    "اعطني منتج",
    "أعطني منتج",
    "اريد منتج",
    "أريد منتج",
    "منتج يساعد",
    "منتج من",
    "من الكتالوج",
    "من كتالوج",
)

_CATALOG_PRODUCT_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bwhich\b.+\bcatalog\b",
        r"\bcatalog\b.+\b(fungicide|herbicide|insecticide|product)s?\b",
        r"\bwhat\s+(fungicide|herbicide|insecticide)\b.+\bcatalog\b",
        r"\b(fungicide|herbicide|insecticide)\b.+\bfrom (the |your |our )?catalog\b",
    )
)

_CATALOG_PRODUCT_PATTERNS_AR: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p)
    for p in (
        r"(اعط|أعط|اريد|أريد).{0,24}منتج",
        r"منتج.{0,24}(لل|يساعد|تحسين|تربة|ري|مياه)",
        r"نصيحة.{0,16}منتج",
    )
)

_AG_INTENT_WORDS: tuple[str, ...] = (
    "crop",
    "crops",
    "plant",
    "planting",
    "seed",
    "soil",
    "pest",
    "disease",
    "fungicide",
    "herbicide",
    "insecticide",
    "harvest",
    "irrigation",
    "fertilizer",
    "blight",
    "aphid",
    "potato",
    "tomato",
    "wheat",
    "rice",
    "maize",
    "corn",
    "cotton",
    "gap",
    "ipm",
    "rotation",
    "livestock",
    "field",
    "farm",
    "agriculture",
    "agronomy",
    "spray",
    "infection",
)

_AR_AG_INTENT_WORDS: tuple[str, ...] = (
    "تربة",
    "محصول",
    "زراع",
    "ري",
    "مياه",
    "ماء",
    "آفة",
    "افة",
    "مرض",
    "فطر",
    "مبيد",
    "سماد",
    "محصول",
    "زراعة",
)

_COMMON_SHORT_WORDS: frozenset[str] = frozenset(
    {
        "hello",
        "help",
        "thanks",
        "thank",
        "yes",
        "no",
        "ok",
        "okay",
        "hi",
        "hey",
        "why",
        "how",
        "what",
        "when",
        "where",
    }
)

_VAGUE_PLANT_RE = re.compile(
    r"\b(plant|planting|grow|growing|sow|sowing|crop|crops)\b",
    re.IGNORECASE,
)


def is_translation_request(question: str, *, max_len: int = 120) -> bool:
    """User wants prior content rephrased in another language — not document RAG."""
    q = (question or "").strip()
    if not q or len(q) > max_len:
        return False
    return any(p.search(q) for p in _TRANSLATION_PATTERNS)


def is_off_topic_question(question: str, *, max_len: int = 160) -> bool:
    """Non-agriculture asks (weather, jokes, etc.) — polite base_llm, no RAG."""
    q = (question or "").strip()
    if not q or len(q) > max_len:
        return False
    if has_strong_product_intent(q):
        return False
    if infer_topics_from_query(q.lower(), max_topics=2):
        return False
    return any(p.search(q) for p in _OFF_TOPIC_PATTERNS)


def is_meta_question(question: str, *, max_len: int = 120) -> bool:
    """True for greetings, identity, or capability questions — not field/agronomy tasks."""
    q = (question or "").strip()
    if not q or len(q) > max_len:
        return False
    if any(p.search(q) for p in _META_PATTERNS):
        return True
    return any(p.search(q) for p in _AR_META_PATTERNS)


def is_image_describe_question(question: str) -> bool:
    """User wants a description of an uploaded image, not document RAG."""
    q = (question or "").strip()
    if not q:
        return False
    return any(p.search(q) for p in _IMAGE_DESCRIBE_PATTERNS)


def has_agriculture_intent(question: str) -> bool:
    """True when the message looks like a real agronomy question, not noise."""
    q = (question or "").lower()
    raw = (question or "").strip()
    if not q.strip():
        return False
    if any(word in raw for word in _AR_AG_INTENT_WORDS):
        return True
    if infer_topics_from_query(q, max_topics=1):
        return True
    return any(word in q for word in _AG_INTENT_WORDS)


def _has_arabic_script(question: str) -> bool:
    return bool(re.search(r"[\u0600-\u06ff]", question or ""))


def is_clarification_question(question: str, *, max_len: int = 80) -> bool:
    """Gibberish, social check-ins, or too vague for document retrieval."""
    q = (question or "").strip()
    if not q or len(q) > max_len:
        return False
    if is_meta_question(q, max_len=max_len):
        return False
    if has_agriculture_intent(q) and not _looks_vague_agriculture(q):
        return False

    if _has_arabic_script(q) and has_strong_product_intent(q):
        return False

    if _has_arabic_script(q):
        if has_agriculture_intent(q) and not _looks_vague_agriculture(q):
            return False
        ar_words = re.findall(r"[\u0600-\u06ff]+", q)
        if len(ar_words) <= 2 and len(q) <= 48 and not has_agriculture_intent(q):
            return True
        return False

    tokens = re.findall(r"[a-zA-Z]{2,}", q)
    if not tokens:
        return True

    if len(tokens) == 1:
        word = tokens[0].lower()
        if word in _COMMON_SHORT_WORDS:
            return True
        alpha = word
        if len(set(alpha)) <= 3 and len(alpha) >= 4:
            return True
        if len(alpha) <= 12:
            return True

    if len(q.split()) <= 4 and not has_agriculture_intent(q):
        return True

    return _looks_vague_agriculture(q)


def _looks_vague_agriculture(question: str) -> bool:
    """Has planting/growing words but no specific crop or clear ask."""
    q = (question or "").strip().lower()
    if len(q) > 60 or not _VAGUE_PLANT_RE.search(q):
        return False
    if len(q.split()) > 8:
        return False
    specific = (
        "potato",
        "tomato",
        "wheat",
        "rice",
        "maize",
        "corn",
        "cotton",
        "chickpea",
        "groundnut",
        "sesame",
        "pepper",
        "chili",
        "onion",
        "garlic",
        "bean",
        "barley",
        "oat",
        "sorghum",
        "blight",
        "rust",
        "aphid",
    )
    if any(term in q for term in specific):
        return False
    return True


def has_strong_product_intent(question: str) -> bool:
    """Explicit ask for a catalog product recommendation."""
    q = (question or "").strip()
    lower = q.lower()
    if any(phrase in lower for phrase in _STRONG_PRODUCT_INTENT):
        return True
    if any(phrase in q for phrase in _STRONG_PRODUCT_INTENT_AR):
        return True
    if any(p.search(q) for p in _CATALOG_PRODUCT_PATTERNS):
        return True
    return any(p.search(q) for p in _CATALOG_PRODUCT_PATTERNS_AR)


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
