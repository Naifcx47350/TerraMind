"""Merge vision analysis into questions for RAG and base LLM."""


def question_with_image_context(question: str, image_analysis: str | None) -> str:
    """Attach vision notes for the answering model — not as a separate user-facing block."""
    if not (image_analysis or "").strip():
        return question
    notes = image_analysis.strip()
    return (
        f"{question.strip()}\n\n"
        "[Photo notes for you only — if relevant, blend briefly into your answer; "
        "do not repeat as a titled section or numbered vision report:]\n"
        f"{notes}"
    )
