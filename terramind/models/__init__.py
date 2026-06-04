"""TerraMind model backends — one module per mode, same response shape."""

from terramind.models.base_llm import answer as base_llm_answer
from terramind.models.general_rag import answer as general_rag_answer
from terramind.models.product_rag import answer as product_rag_answer

MODEL_REGISTRY = {
    "product_rag": {
        "id": "product_rag",
        "name": "Product Catalog RAG",
        "description": "Client Excel product sheets — usage, dosage, manuals",
        "answer_fn": product_rag_answer,
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
    "base_llm": {
        "id": "base_llm",
        "name": "Base LLM",
        "description": "OpenAI only — no retrieval (comparison baseline)",
        "answer_fn": base_llm_answer,
    },
}

DEFAULT_MODEL_ID = "product_rag"


def list_models() -> list[dict]:
    return [
        {
            "id": m["id"],
            "name": m["name"],
            "description": m["description"],
        }
        for m in MODEL_REGISTRY.values()
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


def all_model_ids() -> list[str]:
    return list(MODEL_REGISTRY.keys())


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
    analysis = resolve_image_analysis(
        question, image_analysis, image_base64, image_mime, language
    )
    general = run_model(
        "general_rag",
        question,
        history=history,
        image_analysis=analysis,
    )
    product_question = (
        f"{question.strip()}\n\n"
        "Use the following agriculture reference summary when recommending "
        "a catalog product (if any):\n"
        f"{(general.get('answer') or '')[:2000]}"
    )
    product = run_model(
        "product_rag",
        product_question,
        history=history,
        image_analysis=analysis,
    )
    merged = (
        "### Public agriculture guidance\n\n"
        f"{general.get('answer', '').strip()}\n\n"
        "### Company product catalog\n\n"
        f"{product.get('answer', '').strip()}"
    )
    sources = list(general.get("sources") or []) + list(product.get("sources") or [])
    return {
        "answer": merged,
        "sources": sources,
        "confidence": general.get("confidence", "medium"),
        "retrieved_chunks": (general.get("retrieved_chunks") or 0)
        + (product.get("retrieved_chunks") or 0),
        "system": "advisory",
        "general": general,
        "product": product,
    }
