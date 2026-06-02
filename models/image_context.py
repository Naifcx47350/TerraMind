"""Merge vision analysis into questions for RAG and base LLM."""


def question_with_image_context(question: str, image_analysis: str | None) -> str:
    if not (image_analysis or "").strip():
        return question
    return (
        "The user uploaded a crop/plant image. Vision analysis:\n"
        f"{image_analysis.strip()}\n\n"
        f"User question: {question}"
    )
