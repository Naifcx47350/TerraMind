"""Format prior turns for RAG and combined prompts."""


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


def build_prompt_question(
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
) -> str:
    """Merge prior conversation, optional vision text, and the current question."""
    from models.image_context import question_with_image_context

    q = question_with_image_context(question, image_analysis)
    convo = format_conversation_history(history)
    if not convo:
        return q
    return f"Previous conversation:\n{convo}\n\n{q}"
