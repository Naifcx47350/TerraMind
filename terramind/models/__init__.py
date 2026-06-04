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
            "Picks Product Catalog or Agriculture Knowledge RAG from your question "
            "(catalog vs field guidance)"
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

    q = question.strip()
    if is_meta_question(q):
        intro = advisory_meta_answer()
        catalog_note = (
            "No catalog search was needed for this question. "
            "Ask about a crop, pest, or product when you want a recommendation "
            "from the company catalog."
        )
        merged = (
            "### Public agriculture guidance\n\n"
            f"{intro}\n\n"
            "### Company product catalog\n\n"
            f"{catalog_note}"
        )
        return {
            "answer": merged,
            "sources": [],
            "confidence": "high",
            "retrieval_score": None,
            "retrieved_chunks": 0,
            "system": "advisory",
            "general": {
                "answer": intro,
                "sources": [],
                "confidence": "high",
                "retrieval_score": None,
                "retrieved_chunks": 0,
                "system": "general_rag",
            },
            "product": {
                "answer": catalog_note,
                "sources": [],
                "confidence": "high",
                "retrieval_score": None,
                "retrieved_chunks": 0,
                "system": "product_rag",
            },
        }

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
        f"{q}\n\n"
        "Use the following agriculture reference summary when recommending "
        "a catalog product (if any):\n"
        f"{(general.get('answer') or '')[:2000]}\n\n"
        "Only recommend a catalog product if the user asked about a crop problem, "
        "pest, disease, weed, or product need. Otherwise say in one or two sentences "
        "that the catalog does not apply — do not invent a product match."
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
    g_score = general.get("retrieval_score")
    p_score = product.get("retrieval_score")
    scores = [s for s in (g_score, p_score) if s is not None]
    retrieval_score = max(scores) if scores else None
    from terramind.rag.scoring import confidence_from_score

    total_chunks = (general.get("retrieved_chunks") or 0) + (
        product.get("retrieved_chunks") or 0
    )
    return {
        "answer": merged,
        "sources": sources,
        "confidence": confidence_from_score(
            retrieval_score, has_chunks=total_chunks > 0
        ),
        "retrieval_score": retrieval_score,
        "retrieved_chunks": total_chunks,
        "system": "advisory",
        "general": general,
        "product": product,
    }
