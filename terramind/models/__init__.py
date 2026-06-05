"""TerraMind model backends — one module per mode, same response shape."""

from terramind.models.auto_rag import answer as auto_rag_answer
from terramind.models.base_llm import answer as base_llm_answer
from terramind.models.general_rag import answer as general_rag_answer
from terramind.models.product_rag import answer as product_rag_answer

MODEL_REGISTRY = {
    "auto_rag": {
        "id": "auto_rag",
        "name": "Auto (recommended)",
        "description": (
            "Picks Product Catalog, Agriculture Knowledge RAG, or Base LLM "
            "from your question (catalog vs field vs conversational)"
        ),
        "answer_fn": auto_rag_answer,
    },
    "general_rag": {
        "id": "general_rag",
        "name": "Agriculture Knowledge RAG",
        "description": (
            "Trusted public references: GAP, soil health, crop rotation, IPM, and "
            "pesticide stewardship (not company product labels)"
        ),
        "answer_fn": general_rag_answer,
    },
    "product_rag": {
        "id": "product_rag",
        "name": "Product Catalog RAG",
        "description": "Client Excel product sheets — usage, dosage, manuals",
        "answer_fn": product_rag_answer,
    },
    "base_llm": {
        "id": "base_llm",
        "name": "Base LLM",
        "description": "OpenAI only — no retrieval (comparison baseline)",
        "answer_fn": base_llm_answer,
    },
}

# Picker order on the website (Advisory is UI-only on port 8000).
MODEL_LIST_ORDER = ("auto_rag", "general_rag", "product_rag", "base_llm")

DEFAULT_MODEL_ID = "auto_rag"


def list_models() -> list[dict]:
    return [
        {
            "id": MODEL_REGISTRY[mid]["id"],
            "name": MODEL_REGISTRY[mid]["name"],
            "description": MODEL_REGISTRY[mid]["description"],
        }
        for mid in MODEL_LIST_ORDER
        if mid in MODEL_REGISTRY
    ]


def resolve_image_analysis(
    question: str,
    image_analysis: str | None = None,
    image_base64: str | None = None,
    image_mime: str | None = None,
    language: str | None = None,
) -> str | None:
    if image_analysis and image_analysis.strip():
        return image_analysis.strip()
    if image_base64 and image_mime:
        from terramind.models.vision import analyze_image

        lang = language or ("ar" if any("\u0600" <= c <= "\u06ff" for c in question) else "en")
        return analyze_image(image_base64, image_mime, question, lang=lang)
    return None


def run_model(
    model_id: str,
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
    image_base64: str | None = None,
    image_mime: str | None = None,
    language: str | None = None,
) -> dict:
    if model_id not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model: {model_id}. Choose from {list(MODEL_REGISTRY)}")
    analysis = resolve_image_analysis(
        question, image_analysis, image_base64, image_mime, language
    )
    return MODEL_REGISTRY[model_id]["answer_fn"](
        question,
        history=history or [],
        image_analysis=analysis,
        image_base64=image_base64,
        image_mime=image_mime,
    )


COMPARE_MODEL_IDS = ("product_rag", "general_rag", "base_llm")


def all_model_ids() -> list[str]:
    """Models run in parallel for /query/compare (excludes auto_rag)."""
    return list(COMPARE_MODEL_IDS)


def model_display_name(model_id: str) -> str:
    return MODEL_REGISTRY.get(model_id, {}).get("name", model_id)


def run_advisory(
    question: str,
    history: list | None = None,
    image_analysis: str | None = None,
    image_base64: str | None = None,
    image_mime: str | None = None,
    language: str | None = None,
) -> dict:
    """
    General RAG (field/IPM guidance) then product RAG (catalog), one vision pass.
    Returns general + product payloads and a merged answer for the UI.
    """
    from terramind.meta_questions import advisory_meta_answer, is_meta_question
    from terramind.models.base_llm import answer as base_llm_answer
    from terramind.models.router import skips_document_retrieval

    q = question.strip()
    if skips_document_retrieval(q, image_analysis):
        if is_meta_question(q):
            return {
                "answer": advisory_meta_answer(),
                "sources": [],
                "confidence": "",
                "retrieval_score": None,
                "retrieved_chunks": 0,
                "system": "advisory",
                "general": {
                    "answer": advisory_meta_answer(),
                    "sources": [],
                    "confidence": "",
                    "retrieval_score": None,
                    "retrieved_chunks": 0,
                    "system": "general_rag",
                },
                "product": {
                    "answer": "",
                    "sources": [],
                    "confidence": "",
                    "retrieval_score": None,
                    "retrieved_chunks": 0,
                    "system": "product_rag",
                },
            }
        plain = base_llm_answer(
            question,
            history=history,
            image_analysis=image_analysis,
        )
        return {
            "answer": plain.get("answer", ""),
            "sources": [],
            "confidence": "",
            "retrieval_score": None,
            "retrieved_chunks": 0,
            "system": "advisory",
            "general": {**plain, "system": "general_rag"},
            "product": {
                "answer": "",
                "sources": [],
                "confidence": "",
                "retrieval_score": None,
                "retrieved_chunks": 0,
                "system": "product_rag",
            },
        }

    from terramind.models.advisory import answer_advisory

    analysis = resolve_image_analysis(
        question, image_analysis, image_base64, image_mime, language
    )
    return answer_advisory(question, history=history, image_analysis=analysis)
