"""Format prior turns for RAG and combined prompts."""

import re

from core.models.image_context import question_with_image_context


def format_conversation_history(history: list | None, max_turns: int = 5) -> str:
    if not history:
        return ""
    lines: list[str] = []
    for msg in history[-max_turns * 2 :]:
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", "")
        content = (msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")) or ""
        content = content.strip()
        if not content:
            continue
        if role in ("user", "human"):
            lines.append(f"User: {content}")
        elif role in ("assistant", "ai", "bot"):
            lines.append(f"Assistant: {content}")
    return "\n".join(lines)


def build_retrieval_query(
    question: str,
    image_analysis: str | None = None,
    max_image_chars: int = 400,
) -> str:
    """Short query for vector search — no chat history (avoids diluted embeddings)."""
    q = question.strip()
    if not image_analysis:
        return q
    vision = image_analysis.strip()
    if len(vision) > max_image_chars:
        vision = vision[:max_image_chars].rstrip() + "…"
    return f"{q}\n\nImage context: {vision}"


_FOLLOWUP_RE = re.compile(
    r"\b("
    r"it|this|that|they|them|those|same|previous|above|earlier|"
    r"more|details|detail|explain|continue|also|what about|how about|"
    r"dose|dosage|rate|sources?|confidence|product|recommend"
    r")\b",
    re.IGNORECASE,
)


def looks_like_contextual_followup(question: str) -> bool:
    """True when a short message likely depends on previous chat context."""
    q = (question or "").strip()
    if not q or len(q) > 120:
        return False
    return bool(_FOLLOWUP_RE.search(q)) or len(q.split()) <= 4


def build_contextual_retrieval_query(
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
    max_history_chars: int = 700,
) -> str:
    """Use recent chat context for short follow-ups, without diluting standalone queries."""
    base = build_retrieval_query(question, image_analysis)
    if not history or not looks_like_contextual_followup(question):
        return base

    context = format_conversation_history(history, max_turns=2)
    if not context:
        return base
    if len(context) > max_history_chars:
        context = context[-max_history_chars:].lstrip()
    return f"{base}\n\nRecent conversation context:\n{context}"


def build_prompt_question(
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
) -> str:
    """Merge prior conversation, optional vision text, and the current question."""
    q = question_with_image_context(question, image_analysis)
    convo = format_conversation_history(history)
    if not convo:
        return q
    return f"Previous conversation:\n{convo}\n\n{q}"
